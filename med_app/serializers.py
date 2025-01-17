from rest_framework import serializers
from .models import Chat, Analysis

class ChatSerializer(serializers.ModelSerializer):
    analysis_id = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'name', 'transcript', 'analysis', 'created_at', 'analysis_id']

    def get_analysis_id(self, obj):
        if obj.analysis:
            return obj.analysis.id
        return None

class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ['id', 'transcript', 'result', 'created_at']