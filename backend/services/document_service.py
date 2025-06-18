import requests
import pypdf
from io import BytesIO
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re


class DocumentService:
    """Service for document processing operations"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text to ensure proper spacing"""
        # First, normalize whitespace
        text = ' '.join(text.split())
        
        # Fix common concatenations from PDF extraction
        # Pattern 1: Fix camelCase-like concatenations (lowercase followed by uppercase)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Pattern 2: Fix words ending with common suffixes followed by new words
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ment', 'ness', 'ity', 'ous', 'ive', 'ful', 'less', 'able', 'ible']
        for suffix in suffixes:
            # Match suffix followed by lowercase letter (new word)
            text = re.sub(rf'({suffix})([a-z])', rf'\1 \2', text)
        
        # Pattern 3: Fix common word boundaries
        # Numbers followed by letters
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
        
        # Pattern 4: Fix punctuation spacing
        text = re.sub(r'([.!?;:,])([A-Za-z])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])([.!?;:,])', r'\1\2', text)  # No space before punctuation
        
        # Pattern 5: Fix parentheses and brackets
        text = re.sub(r'\)([A-Za-z])', r') \1', text)
        text = re.sub(r'([A-Za-z])\(', r'\1 (', text)
        text = re.sub(r'\]([A-Za-z])', r'] \1', text)
        text = re.sub(r'([A-Za-z])\[', r'\1 [', text)
        
        # Pattern 6: Fix specific common concatenations in your domain
        common_fixes = {
            r'securitymeasures': 'security measures',
            r'factorauthentication': 'factor authentication',
            r'continuoussecurity': 'continuous security',
            r'securityaudits': 'security audits',
            r'useraccounts': 'user accounts',
            r'hotelowners': 'hotel owners',
            r'foreignkey': 'foreign key',
            r'roomtype': 'room type',
            r'availabilitystatus': 'availability status',
            r'bookinginformation': 'booking information',
            r'bookingstatus': 'booking status',
            r'chatmessages': 'chat messages',
            r'messagecontent': 'message content',
            r'real-time': 'real-time',
            r'chatfunctionality': 'chat functionality',
            r'aredelivered': 'are delivered',
            r'instantlywhen': 'instantly when',
            r'bothparties': 'both parties',
            r'areonline': 'are online',
            r'arestored': 'are stored',
            r'forlater': 'for later',
            r'retrievalwhen': 'retrieval when',
            r'offline': 'offline',
            r'implementingreal': 'implementing real',
            r'timechat': 'time chat',
            r'functionalitybetween': 'functionality between',
            r'wascomplex': 'was complex',
            r'especiallyensuring': 'especially ensuring',
            r'thatmessages': 'that messages',
            r'whenbot': 'when bot',
            r'hpartiesare': 'h parties are',
            r'online': 'online',
            r'storedfor': 'stored for',
            r'laterretrieval': 'later retrieval',
            r'whenoffline': 'when offline',
        }
        
        # Apply common fixes
        for pattern, replacement in common_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Pattern 7: Fix concatenated prepositions and articles
        prepositions = ['about', 'above', 'across', 'after', 'against', 'along', 'among', 'around', 
                       'at', 'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond',
                       'by', 'down', 'during', 'except', 'for', 'from', 'in', 'inside', 'into',
                       'like', 'near', 'of', 'off', 'on', 'since', 'to', 'toward', 'through',
                       'under', 'until', 'up', 'upon', 'with', 'within', 'and', 'or', 'but',
                       'the', 'a', 'an', 'is', 'are', 'was', 'were', 'been', 'being', 'have',
                       'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                       'may', 'might', 'must', 'can', 'that', 'this', 'these', 'those']
        
        for prep in prepositions:
            # Add space after these words if followed by a letter
            text = re.sub(rf'\b({prep})([a-zA-Z])', rf'\1 \2', text)
        
        # Pattern 8: Final cleanup - remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Pattern 9: Ensure sentences have proper spacing after periods
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        return text.strip()
    
    
    def extract_text_from_pdf_url(self, pdf_url: str) -> str:
        """Extract text from PDF URL"""
        try:
            # Download PDF from URL
            pdf_response = requests.get(pdf_url)
            pdf_response.raise_for_status()
            
            # Extract text from PDF
            pdf_reader = pypdf.PdfReader(BytesIO(pdf_response.content))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                # Clean the extracted text to ensure proper spacing
                cleaned_page_text = self.clean_extracted_text(page_text)
                text += cleaned_page_text + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {e}")
    
    def process_files_to_text(self, files: List[dict]) -> Tuple[List[str], List[str]]:
        """Process multiple PDF files and extract text"""
        all_texts = []
        sources = []
        
        for file_info in files:
            try:
                text = self.extract_text_from_pdf_url(file_info["file_url"])
                if text:
                    all_texts.append(text)
                    sources.append(file_info["original_filename"])
            except Exception as e:
                print(f"Error processing file {file_info['filename']}: {e}")
                continue
        
        return all_texts, sources
    
    def split_texts_to_chunks(self, texts: List[str], sources: List[str]) -> Tuple[List[str], List[str]]:
        """Split texts into chunks with source tracking"""
        chunks = []
        chunk_sources = []
        
        for i, text in enumerate(texts):
            text_chunks = self.text_splitter.split_text(text)
            chunks.extend(text_chunks)
            chunk_sources.extend([sources[i]] * len(text_chunks))
        
        return chunks, chunk_sources 