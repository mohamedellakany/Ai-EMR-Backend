# from rest_framework import serializers
# from .models import Chat, Analysis, Transcript

# class ChatSerializer(serializers.ModelSerializer):
#     analysis_id = serializers.SerializerMethodField()

#     class Meta:
#         model = Chat
#         fields = ['id', 'name', 'transcript', 'analysis', 'created_at', 'analysis_id']

#     def get_analysis_id(self, obj):
#         if obj.analysis:
#             return obj.analysis.id
#         return None

# class AnalysisSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Analysis
#         fields = ['id', 'transcript', 'result', 'created_at']

# class TranscriptSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Transcript
#         fields = ['id', 'content', 'created_at']


# backend/med_app/serializers.py

from rest_framework import serializers
from .models import Chat, Analysis, Transcript

class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = ['id', 'content', 'created_at']

class ChatSerializer(serializers.ModelSerializer):
    analysis_id = serializers.SerializerMethodField()
    transcript_content = serializers.CharField(source='transcript.content', read_only=True)  # Add this line

    class Meta:
        model = Chat
        fields = ['id', 'name', 'transcript', 'transcript_content', 'analysis', 'created_at', 'analysis_id']  # Include transcript_content

    def get_analysis_id(self, obj):
        if obj.analysis:
            return obj.analysis.id
        return None

class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ['id', 'transcript', 'result', 'created_at']