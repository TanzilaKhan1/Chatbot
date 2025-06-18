# AI Chat PDF

An interactive web application that allows users to upload PDF documents, organize them into folders, and have AI-powered conversations with the document contents using a Retrieval Augmented Generation (RAG) system.

## Overview

AI Chat PDF combines a modern Next.js frontend with a FastAPI backend to provide an intuitive interface for document management and AI-assisted information retrieval. 

## Features

- **Document Management**: Upload, organize and manage PDF files in a folder structure
- **AI Chat Interface**: Converse with your documents using natural language
- **RAG-based Responses**: Get accurate answers with relevant sources from your documents
- **Session Management**: Save and continue conversations across multiple sessions
- **Responsive UI**: Modern, responsive interface built with Next.js and TailwindCSS

## Tech Stack

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **UI Components**: Radix UI with custom TailwindCSS styling
- **State Management**: React hooks
- **HTTP Client**: Axios
- **Styling**: TailwindCSS with animations
- **Markdown Rendering**: react-markdown with remark-gfm

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **AI/ML**:
  - LangChain for RAG pipeline
  - OpenAI API integration
  - Sentence transformers for embeddings
- **PDF Processing**:
  - PyPDF
  - PDFPlumber
  - PyMuPDF
- **Vector Database**: Qdrant for document embeddings
- **Database**: Supabase

## Architecture

The application follows a client-server architecture:

1. **Frontend**: Next.js application that provides the user interface for document management and chat
2. **Backend API**: FastAPI server that handles document processing, vector search, and AI integration
3. **Vector Store**: Qdrant database that stores document chunks and embeddings
4. **LLM Service**: Integration with OpenAI's models for generating responses

## Setup and Installation

### Prerequisites
- Node.js 18+
- Python 3.10+
- OpenAI API key

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (create a `.env` file):
   ```
   OPENAI_API_KEY=your_openai_api_key
   LLM_MODEL=gpt-4-turbo
   ```

4. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000`

## Usage

1. Create folders to organize your documents
2. Upload PDF files to your folders
3. Navigate to the chat interface
4. Ask questions about your documents


## License

[MIT License](LICENSE)
