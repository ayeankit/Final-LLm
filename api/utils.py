import os
import PyPDF2
import markdown
from docx import Document as DocxDocument
import numpy as np
import faiss
import requests
import json
import re

from django.conf import settings
from sentence_transformers import SentenceTransformer

# --- Config ---
HF_API_KEY = os.getenv('HF_API_KEY')
HF_MODEL = "tiiuae/falcon-rw-1b"  # You can change this to any supported hosted model
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Load sentence transformer model (for embeddings)
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- File Parsing ---
def parse_pdf(file_path):
    text = ""
    page_map = []
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
                page_map.append((i+1, page_text))
    return text, page_map

def parse_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    html = markdown.markdown(text)
    return text, [(1, text)]

def parse_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return text, [(1, text)]

# --- Chunking ---
def chunk_text(text, chunk_size=None, overlap=None):
    # Simple regex-based sentence splitter (handles ., !, ?)
    sentence_endings = re.compile(r'(?<=[.!?]) +')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]

# --- Embedding ---
def get_embedding(text):
    embedding = model.encode([text])[0]
    return np.array(embedding, dtype=np.float32)

# --- LLM Completion ---
def query_llm(prompt):
    # LLM call is disabled. Just return the context as the answer.
    # To re-enable, restore the Hugging Face API call below.
    return prompt

# --- FAISS Index Management ---
def build_faiss_index(embeddings):
    dim = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dim)
    index.add(np.stack(embeddings))
    return index

def search_faiss_index(index, query_embedding, top_k=5):
    D, I = index.search(np.array([query_embedding]), top_k)
    return I[0] 
