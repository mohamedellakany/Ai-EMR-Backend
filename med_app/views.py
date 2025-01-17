from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import openai
import json
from io import BytesIO
from docx import Document
from .models import Chat, Analysis
from .serializers import ChatSerializer
from rest_framework import status

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all().order_by('-created_at')
    serializer_class = ChatSerializer

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        Chat.objects.all().delete()
        return Response({'message': 'All chats cleared successfully.'})

class CreateChatView(APIView):
    def post(self, request):
        name = request.data.get('name', 'Untitled Chat')
        chat = Chat.objects.create(name=name)
        return Response({"id": chat.id, "name": chat.name})

class DeleteChatView(APIView):
    def delete(self, request, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            chat.delete()
            return Response({"message": "Chat deleted successfully."})
        except Chat.DoesNotExist:
            return Response({"error": "Chat not found."}, status=404)

class ListChatsView(APIView):
    def get(self, request):
        chats = Chat.objects.all().order_by('-created_at')
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)


class ExportWordView(APIView):
    def get(self, request, analysis_id):
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            chat = Chat.objects.filter(analysis=analysis).first()
            if not chat:
                return Response({"error": "Chat not found for this analysis."}, status=404)

            doc = Document()
            doc.add_paragraph(analysis.result)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            # Use the chat name as the file name
            file_name = f"{chat.name}.docx"
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            return response
        except Analysis.DoesNotExist:
            return Response({"error": "Analysis not found."}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class SaveTranscriptView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            content = data.get('content')
            if not content:
                return JsonResponse({"error": "No transcript content provided"}, status=400)

            # Check if a chat with this transcript already exists
            existing_chat = Chat.objects.filter(transcript=content).first()
            if existing_chat:
                return JsonResponse({"id": existing_chat.id, "content": existing_chat.transcript})

            # Save the transcript as a new chat
            chat = Chat.objects.create(transcript=content, name="Transcript Chat")
            return JsonResponse({"id": chat.id, "content": chat.transcript})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeTranscriptView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            transcript = data.get('transcript')
            if not transcript:
                return JsonResponse({"error": "No transcript provided"}, status=400)

            # Initialize the OpenAI client
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            # Use the new API format
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes medical transcripts."},
                    {"role": "user", "content": f"Analyze the following medical transcript and provide insights:\n\n{transcript}"}
                ],
                max_tokens=500,
            )

            # Extract the analysis result
            analysis_result = response.choices[0].message.content

            # Check if a chat with this analysis already exists
            existing_chat = Chat.objects.filter(analysis__result=analysis_result).first()
            if existing_chat:
                return JsonResponse({
                    "analysis": analysis_result,
                    "analysis_id": existing_chat.analysis.id,
                    "chat_id": existing_chat.id
                })

            # Save the analysis to the database
            analysis = Analysis.objects.create(
                transcript=transcript,
                result=analysis_result
            )

            # Create a chat associated with this analysis
            chat = Chat.objects.create(analysis=analysis, name="Analysis Chat")

            return JsonResponse({
                "analysis": analysis_result,
                "analysis_id": analysis.id,  # Return the ID for future reference
                "chat_id": chat.id  # Return the chat ID as well
            })

        except Exception as e:
            # Log any exceptions
            print(f"Unexpected error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SaveAnalysisView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            result = data.get('result')
            if not result:
                return JsonResponse({"error": "No analysis result provided"}, status=400)

            # Check if a chat with this analysis already exists
            existing_chat = Chat.objects.filter(analysis__result=result).first()
            if existing_chat:
                return JsonResponse({
                    "id": existing_chat.id,
                    "result": existing_chat.analysis.result,
                    "analysis_id": existing_chat.analysis.id
                })

            # Save the analysis as an Analysis object
            analysis = Analysis.objects.create(result=result)
            chat = Chat.objects.create(analysis=analysis, name="Analysis Chat")
            return JsonResponse({"id": chat.id, "result": chat.analysis.result, "analysis_id": analysis.id})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

class ExportTranscriptView(APIView):
    def get(self, request, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            if not chat.transcript:
                return Response({"error": "No transcript found for this chat."}, status=404)

            doc = Document()
            doc.add_paragraph(chat.transcript)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            # Use the chat name as the file name
            file_name = f"{chat.name}.docx".replace(" ", "_")  # Replace spaces with underscores for file names
            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            return response
        except Chat.DoesNotExist:
            return Response({"error": "Chat not found."}, status=404)

class RenameChatView(APIView):
    def post(self, request, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            new_name = request.data.get('name')
            if not new_name:
                return Response({"error": "New name is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            chat.name = new_name
            chat.save()
            return Response({"message": "Chat renamed successfully.", "name": chat.name})
        except Chat.DoesNotExist:
            return Response({"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND)