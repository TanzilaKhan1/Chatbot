import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from langchain_core.documents import Document
from supabase import Client
import fitz  # PyMuPDF
import re

from config import config

class DocumentProcessor:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Use a more sophisticated text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
        
        # Markdown splitter for structured content
        self.markdown_splitter = MarkdownTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        
    async def download_pdf_from_supabase(self, storage_path: str) -> str:
        """Download PDF from Supabase storage to temp file"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=config.TEMP_DIR)
        temp_path = temp_file.name
        temp_file.close()
        
        # Download file from Supabase
        file_bytes = self.supabase.storage.from_(config.SUPABASE_BUCKET).download(storage_path)
        
        with open(temp_path, 'wb') as f:
            f.write(file_bytes)
            
        return temp_path
    
    def _extract_text_with_pymupdf(self, pdf_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Extract text from PDF using PyMuPDF with better formatting preservation"""
        doc = fitz.open(pdf_path)
        full_text = ""
        page_metadata = []
        
        for page_num, page in enumerate(doc):
            # Extract text with layout preservation
            text = page.get_text("text", sort=True)
            
            # Extract tables if present
            tables = []
            try:
                # Try to find tables
                tabs = page.find_tables()
                for tab in tabs:
                    table_text = "\n".join(["\t".join(row) for row in tab.extract()])
                    tables.append(table_text)
            except:
                pass
            
            # Combine text and tables
            page_text = text
            if tables:
                page_text += "\n\nTables:\n" + "\n\n".join(tables)
            
            full_text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
            
            # Store page metadata
            page_metadata.append({
                "page": page_num + 1,
                "text_length": len(page_text),
                "has_tables": len(tables) > 0
            })
        
        doc.close()
        return full_text, page_metadata
    
    def _clean_and_normalize_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace while preserving structure
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Add space between camelCase
        text = re.sub(r'(?<=\w)(?=[.!?;:])', '', text)  # Remove space before punctuation
        text = re.sub(r'(?<=[.!?;:])(?=\w)', ' ', text)  # Add space after punctuation
        
        # Fix hyphenated words at line breaks
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        
        return text.strip()
    
    def _create_chunks_with_overlap(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Create overlapping chunks with proper metadata"""
        chunks = []
        
        # First try to split by pages if page markers exist
        page_splits = re.split(r'--- Page \d+ ---', text)
        
        if len(page_splits) > 1:
            # Process each page separately to maintain context
            for i, page_text in enumerate(page_splits[1:], 1):  # Skip empty first split
                if not page_text.strip():
                    continue
                    
                # Create chunks for this page
                page_chunks = self.text_splitter.split_text(page_text)
                
                for j, chunk in enumerate(page_chunks):
                    chunk_metadata = {
                        **metadata,
                        "page": i,
                        "chunk_index": j,
                        "total_chunks_in_page": len(page_chunks),
                        "chunk_id": hashlib.md5(chunk.encode()).hexdigest()[:8]
                    }
                    chunks.append(Document(page_content=chunk, metadata=chunk_metadata))
        else:
            # Fall back to regular splitting
            text_chunks = self.text_splitter.split_text(text)
            
            for i, chunk in enumerate(text_chunks):
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "chunk_id": hashlib.md5(chunk.encode()).hexdigest()[:8]
                }
                chunks.append(Document(page_content=chunk, metadata=chunk_metadata))
        
        return chunks
    
    def _process_pdf_sync(self, pdf_path: str, file_id: str, folder_id: str, original_filename: str) -> List[Document]:
        """Synchronous PDF processing with improved text extraction"""
        try:
            # Extract text using PyMuPDF
            full_text, page_metadata = self._extract_text_with_pymupdf(pdf_path)
            
            # Clean and normalize text
            cleaned_text = self._clean_and_normalize_text(full_text)
            
            # Also try loading with PyMuPDFLoader for comparison
            loader = PyMuPDFLoader(pdf_path)
            langchain_docs = loader.load()
            
            # Combine both extraction methods for better coverage
            if len(langchain_docs) > 0 and len(langchain_docs[0].page_content) > len(cleaned_text):
                # Use LangChain extraction if it got more content
                primary_text = "\n\n".join([doc.page_content for doc in langchain_docs])
            else:
                primary_text = cleaned_text
            
            # Create base metadata
            base_metadata = {
                "file_id": file_id,
                "folder_id": folder_id,
                "filename": original_filename,
                "total_pages": len(page_metadata),
                "extraction_method": "pymupdf_enhanced"
            }
            
            # Create chunks with overlap
            chunks = self._create_chunks_with_overlap(primary_text, base_metadata)
            
            # Validate chunks
            print(f"Processed {original_filename}: {len(chunks)} chunks from {len(primary_text)} characters")
            
            return chunks
            
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            # Fallback to basic extraction
            try:
                with open(pdf_path, 'rb') as file:
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n\n"
                
                chunks = self.text_splitter.split_text(text)
                return [
                    Document(
                        page_content=chunk,
                        metadata={
                            "file_id": file_id,
                            "folder_id": folder_id,
                            "filename": original_filename,
                            "chunk_index": i,
                            "extraction_method": "pypdf2_fallback"
                        }
                    )
                    for i, chunk in enumerate(chunks)
                ]
            except Exception as fallback_error:
                print(f"Fallback extraction also failed: {str(fallback_error)}")
                raise
    
    async def process_pdf(self, storage_path: str, file_id: str, folder_id: str, original_filename: str) -> List[Document]:
        """Process a PDF file from Supabase storage"""
        temp_path = None
        try:
            # Download PDF from Supabase
            temp_path = await self.download_pdf_from_supabase(storage_path)
            
            # Process PDF in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                self.executor,
                self._process_pdf_sync,
                temp_path,
                file_id,
                folder_id,
                original_filename
            )
            
            # Add storage path to all chunks
            for chunk in chunks:
                chunk.metadata["storage_path"] = storage_path
            
            # Log processing statistics
            total_content_length = sum(len(chunk.page_content) for chunk in chunks)
            print(f"PDF Processing Complete:")
            print(f"  - File: {original_filename}")
            print(f"  - Total chunks: {len(chunks)}")
            print(f"  - Total content length: {total_content_length}")
            print(f"  - Average chunk size: {total_content_length / len(chunks) if chunks else 0:.0f}")
            
            return chunks
            
        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def process_multiple_pdfs(self, pdf_files: List[Dict[str, Any]]) -> Dict[str, List[Document]]:
        """Process multiple PDF files concurrently"""
        tasks = []
        for pdf_file in pdf_files:
            task = self.process_pdf(
                pdf_file["storage_path"],
                pdf_file["id"],
                pdf_file["folder_id"],
                pdf_file.get("original_filename", pdf_file.get("filename", "unknown.pdf"))
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_docs = {}
        total_chunks = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing file {pdf_files[i]['id']}: {result}")
                processed_docs[pdf_files[i]["id"]] = []
            else:
                processed_docs[pdf_files[i]["id"]] = result
                total_chunks += len(result)
        
        print(f"Batch processing complete: {len(pdf_files)} files, {total_chunks} total chunks")
        return processed_docs