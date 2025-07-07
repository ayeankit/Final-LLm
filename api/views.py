from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Document, Chunk, QALog
from .serializers import DocumentSerializer
import os
from . import utils
import numpy as np
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class DocumentUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        name = file_obj.name
        document = Document.objects.create(name=name, file=file_obj)
        file_path = document.file.path
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            text, page_map = utils.parse_pdf(file_path)
        elif ext in ['.md', '.markdown']:
            text, page_map = utils.parse_markdown(file_path)
        elif ext in ['.txt']:
            text, page_map = utils.parse_text(file_path)
        else:
            return Response({'error': 'Unsupported file type.'}, status=status.HTTP_400_BAD_REQUEST)
        chunks = utils.chunk_text(text)
        embeddings = []
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            emb = utils.get_embedding(chunk)
            embeddings.append(emb)
            page_number = 1
            Chunk.objects.create(
                document=document,
                text=chunk,
                embedding=emb.tobytes(),
                page_number=page_number,
                chunk_index=idx
            )
        # TODO: Build and persist FAISS index for this document
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)

def build_faiss_index_from_db():
    chunks = Chunk.objects.all()
    embeddings = []
    chunk_refs = []
    for chunk in chunks:
        emb = np.frombuffer(chunk.embedding, dtype=np.float32)
        embeddings.append(emb)
        chunk_refs.append(chunk)
    if not embeddings:
        return None, []
    index = utils.build_faiss_index(embeddings)
    return index, chunk_refs

class AskQuestionView(APIView):
    authentication_classes = [TokenAuthentication]
    def post(self, request, format=None):
        question = request.data.get('question')
        if not question:
            return Response({'success': False, 'data': None, 'error': 'No question provided.'}, status=status.HTTP_400_BAD_REQUEST)
        # 1. Embed question
        q_emb = utils.get_embedding(question)
        # 2. Build FAISS index from DB
        index, chunk_refs = build_faiss_index_from_db()
        if index is None:
            return Response({'success': False, 'data': None, 'error': 'No knowledge base available.'}, status=status.HTTP_400_BAD_REQUEST)
        # 3. Search top chunks
        top_k = 5
        top_indices = utils.search_faiss_index(index, q_emb, top_k=top_k)
        top_chunks = [chunk_refs[i] for i in top_indices if i < len(chunk_refs)]
        # 4. Deduplicate and select the most relevant chunk
        seen = set()
        unique_chunks = []
        for c in top_chunks:
            if c.text not in seen:
                unique_chunks.append(c)
                seen.add(c.text)
        if not unique_chunks:
            return Response({'success': True, 'data': {'answer': "I don't know.", 'sources': []}, 'error': None})
        best_chunk = unique_chunks[0]
        answer = best_chunk.text
        # 5. Format sources as 'DocumentName - Page X' if page_number is available
        if best_chunk.page_number:
            source = f"{best_chunk.document.name} - Page {best_chunk.page_number}"
        else:
            source = f"{best_chunk.document.name}"
        sources = [source]
        # 6. Log Q&A
        QALog.objects.create(
            question=question,
            answer=answer,
            user=str(request.user) if request.user.is_authenticated else None,
            sources=", ".join(sources)
        )
        return Response({'answer': answer, 'sources': sources})

class QALogListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        logs = QALog.objects.all().order_by('-created_at')[:100]
        data = [
            {
                'question': log.question,
                'answer': log.answer,
                'sources': log.sources,
                'created_at': log.created_at,
                'user': log.user
            }
            for log in logs
        ]
        return Response({'success': True, 'data': data, 'error': None})
