import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from docling.chunking import HybridChunker
from langchain_docling import DoclingLoader
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from supabase import Client

from config import config

class DocumentProcessor:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.chunker = HybridChunker(tokenizer=config.EMBEDDING_MODEL)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
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
    
    def _process_pdf_sync(self, pdf_path: str) -> List[Document]:
        """Synchronous PDF processing using docling"""
        # Use docling to load and convert PDF to markdown
        loader = DoclingLoader(
            file_path=[pdf_path],
            export_type="markdown",  # Convert to markdown
            chunker=self.chunker
        )
        
        # Load documents
        docs = loader.load()
        
        # Split markdown documents using headers
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header_1"),
                ("##", "Header_2"),
                ("###", "Header_3"),
            ],
            return_each_line=False,
            strip_headers=False
        )
        
        # Split documents into chunks
        all_splits = []
        for doc in docs:
            splits = splitter.split_text(doc.page_content)
            # Add metadata to each split
            for split in splits:
                split.metadata.update(doc.metadata)
            all_splits.extend(splits)
        
        return all_splits
    
    async def process_pdf(self, storage_path: str, file_id: str, folder_id: str) -> List[Document]:
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
                temp_path
            )
            
            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "file_id": file_id,
                    "folder_id": folder_id,
                    "storage_path": storage_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
            
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
                pdf_file["folder_id"]
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_docs = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error processing file {pdf_files[i]['id']}: {result}")
                processed_docs[pdf_files[i]["id"]] = []
            else:
                processed_docs[pdf_files[i]["id"]] = result
        
        return processed_docs