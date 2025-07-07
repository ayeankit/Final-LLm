from django.urls import path
from .views import DocumentUploadView, AskQuestionView, QALogListView

urlpatterns = [
    path('upload-document/', DocumentUploadView.as_view(), name='upload-document'),
    path('ask-question/', AskQuestionView.as_view(), name='ask-question'),
    path('logs/', QALogListView.as_view(), name='qa-logs'),
] 