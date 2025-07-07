# Knowledge Assistant API

A Django-based backend system that powers a Knowledge Assistant API using OpenAI LLM and FAISS for retrieval-augmented generation (RAG) from PDF, Markdown, or Text knowledge bases.

## Features
- Upload and ingest knowledge base documents (PDF, Markdown, Text)
- Parse, chunk, and embed content using OpenAI
- Store embeddings in FAISS for semantic search
- Ask questions via API, with answers grounded in uploaded knowledge
- Admin interface for document management

## Tech Stack
- Python 3.x
- Django + Django REST Framework
- OpenAI API (for embeddings and LLM)
- FAISS (vector search)
- PyPDF2, python-docx, markdown (parsing)

## Setup
1. **Clone and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Set OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY=your-openai-key
   ```
3. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
4. **Create superuser (for admin):**
   ```bash
   python manage.py createsuperuser
   ```
5. **Run the server:**
   ```bash
   python manage.py runserver
   ```

## API Endpoints
### 1. Upload Document
- **POST** `/api/upload-document/`
- **Form Data:** `file` (PDF, .md, .txt)
- **Response:** Document metadata

### 2. Ask Question
- **POST** `/api/ask-question/`
- **JSON:** `{ "question": "What is the use of mitochondria?" }`
- **Response:**
  ```json
  {
    "answer": "The mitochondria is known as the powerhouse of the cell...",
    "sources": ["Document.pdf - Chunk 3"]
  }
  ```

## Admin
- Visit `/admin/` to manage documents and chunks.

## Notes
- Only context from uploaded documents is used to answer questions (RAG).
- Caching and advanced prompt engineering can be added for optimization.

## Example Knowledge Base
- Upload a Science Class IX PDF or Markdown file to test. # Final-LLm
# Final-LLm
# Final-LLm
