from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatViewSet, AnalyzeTranscriptView, CreateChatView, DeleteChatView, ExportWordView,
    SaveTranscriptView, SaveAnalysisView, ListChatsView, ExportTranscriptView, RenameChatView
)

router = DefaultRouter()
router.register(r'chats', ChatViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('analyze-transcript/', AnalyzeTranscriptView.as_view(), name='analyze_transcript'),
    path('chats/create/', CreateChatView.as_view(), name='create_chat'),
    path('chats/delete/<int:chat_id>/', DeleteChatView.as_view(), name='delete_chat'),
    path('export-word/<int:analysis_id>/', ExportWordView.as_view(), name='export_word'),
    path('transcripts/', SaveTranscriptView.as_view(), name='save_transcript'),
    path('analyses/', SaveAnalysisView.as_view(), name='save_analysis'),
    path('chats/', ListChatsView.as_view(), name='list_chats'),
    path('export-transcript/<int:chat_id>/', ExportTranscriptView.as_view(), name='export_transcript'),
    path('chats/rename/<int:chat_id>/', RenameChatView.as_view(), name='rename_chat'),
]