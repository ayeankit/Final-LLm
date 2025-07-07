from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from . import utils
import os
import numpy as np
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path

# Create your models here.

class Document(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Chunk(models.Model):
    document = models.ForeignKey(Document, related_name='chunks', on_delete=models.CASCADE)
    text = models.TextField()
    embedding = models.BinaryField()  # Store numpy array as bytes
    page_number = models.IntegerField(null=True, blank=True)
    chunk_index = models.IntegerField()

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.name}"

class QALog(models.Model):
    question = models.TextField()
    answer = models.TextField()
    user = models.CharField(max_length=255, null=True, blank=True)  # For token-based auth, can be username or token
    created_at = models.DateTimeField(auto_now_add=True)
    sources = models.TextField(null=True, blank=True)  # Store as comma-separated or JSON string

    def __str__(self):
        return f"Q: {self.question[:30]}... | {self.created_at}"

@receiver(post_save, sender=Document)
def create_chunks_and_embeddings(sender, instance, created, **kwargs):
    if created:
        print(f"Signal triggered for document: {instance.name}")
        # Only process new documents
        file_path = instance.file.path
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            text, page_map = utils.parse_pdf(file_path)
        elif ext == '.md':
            text, page_map = utils.parse_markdown(file_path)
        elif ext == '.txt':
            text, page_map = utils.parse_text(file_path)
        else:
            return  # unsupported file type
        chunks = utils.chunk_text(text)
        for idx, chunk in enumerate(chunks):
            embedding = utils.get_embedding(chunk)
            # Store numpy array as bytes
            embedding_bytes = embedding.tobytes()
            Chunk.objects.create(
                document=instance,
                text=chunk,
                embedding=embedding_bytes,
                page_number=None,
                chunk_index=idx
            )
