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
from datetime import datetime
from io import BytesIO
from docx import Document
from .models import Chat, Analysis, Transcript
from .serializers import ChatSerializer, AnalysisSerializer, TranscriptSerializer
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
        search_query = request.query_params.get('q', '')
        chats = Chat.objects.all().order_by('-created_at')
        if search_query:
            chats = chats.filter(name__icontains=search_query)
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

            # Generate a name with the current date and time
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            chat_name = f"Transcript_{current_time}"  # Format: Transcript_YYYY-MM-DD_HH-MM-SS

            # Create a new Transcript object
            transcript = Transcript.objects.create(content=content)

            # Create a new Chat object linked to the transcript
            chat = Chat.objects.create(transcript=transcript, name=chat_name)

            return JsonResponse({"id": chat.id, "content": chat.transcript.content, "name": chat.name})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SaveAnalysisView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
            result = data.get('result')
            if not result:
                return JsonResponse({"error": "No analysis result provided"}, status=400)

            # Check if an analysis with the same result already exists
            existing_analysis = Analysis.objects.filter(result=result).first()
            if (existing_analysis):
                # If the analysis already exists, return the associated chat
                existing_chat = Chat.objects.filter(analysis=existing_analysis).first()
                if existing_chat:
                    return JsonResponse({"id": existing_chat.id, "result": existing_chat.analysis.result, "name": existing_chat.name})

            # Generate a name with the current date and time
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            chat_name = f"Analysis_{current_time}"  # Format: Analysis_YYYY-MM-DD_HH-MM-SS

            # Create a new Analysis object
            analysis = Analysis.objects.create(result=result)

            # Create a new Chat object linked to the analysis
            chat = Chat.objects.create(analysis=analysis, name=chat_name)

            return JsonResponse({
                "id": chat.id,
                "result": chat.analysis.result,
                "name": chat.name
            })

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

            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes medical transcripts."},
                    {"role": "user", "content": f"Analyze the following medical transcript and provide insights:\n\n{transcript}"}
                ],
                max_tokens=500,
            )

            analysis_result = response.choices[0].message.content

            existing_chat = Chat.objects.filter(analysis__result=analysis_result).first()
            if existing_chat:
                return JsonResponse({
                    "analysis": analysis_result,
                    "analysis_id": existing_chat.analysis.id,
                    "chat_id": existing_chat.id
                })

            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            chat_name = f"Analysis_{current_time}"

            analysis = Analysis.objects.create(transcript=transcript, result=analysis_result)
            chat = Chat.objects.create(analysis=analysis, name=chat_name)

            return JsonResponse({
                "analysis": analysis_result,
                "analysis_id": analysis.id,
                "chat_id": chat.id
            })

        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

class ExportTranscriptView(APIView):
    def get(self, request, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            if not chat.transcript:
                return Response({"error": "No transcript found for this chat."}, status=404)

            doc = Document()
            doc.add_paragraph(chat.transcript.content)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            file_name = f"{chat.name}.docx".replace(" ", "_")
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

class AllChatsView(APIView):
    def get(self, request):
        chats = Chat.objects.all().order_by('-created_at')
        chat_serializer = ChatSerializer(chats, many=True)

        analyses = Analysis.objects.all().order_by('-created_at')
        analysis_serializer = AnalysisSerializer(analyses, many=True)

        transcripts = Transcript.objects.all().order_by('-created_at')
        transcript_serializer = TranscriptSerializer(transcripts, many=True)

        return Response({
            'chats': chat_serializer.data,
            'analyses': analysis_serializer.data,
            'transcripts': transcript_serializer.data,
        })

class DownloadTranscriptView(APIView):
    def get(self, request, transcript_id):
        try:
            transcript = Transcript.objects.get(id=transcript_id)
            doc = Document()
            doc.add_paragraph(transcript.content)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"Transcript_{current_time}.docx"

            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            return response
        except Transcript.DoesNotExist:
            return Response({"error": "Transcript not found."}, status=404)

class DownloadAnalysisView(APIView):
    def get(self, request, analysis_id):
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            doc = Document()
            doc.add_paragraph(analysis.result)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"Analysis_{current_time}.docx"

            response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            response['Content-Disposition'] = f'attachment; filename={file_name}'
            return response
        except Analysis.DoesNotExist:
            return Response({"error": "Analysis not found."}, status=404)

class DeleteAnalysisView(APIView):
    def delete(self, request, analysis_id):
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            analysis.delete()
            return Response({"message": "Analysis deleted successfully."}, status=status.HTTP_200_OK)
        except Analysis.DoesNotExist:
            return Response({"error": "Analysis not found."}, status=status.HTTP_404_NOT_FOUND)

class DeleteTranscriptView(APIView):
    def delete(self, request, transcript_id):
        try:
            transcript = Transcript.objects.get(id=transcript_id)
            transcript.delete()
            return Response({"message": "Transcript deleted successfully."}, status=status.HTTP_200_OK)
        except Transcript.DoesNotExist:
            return Response({"error": "Transcript not found."}, status=status.HTTP_404_NOT_FOUND)

# from rest_framework import viewsets
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from django.http import JsonResponse, HttpResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from django.conf import settings
# import openai
# import json
# from datetime import datetime
# from io import BytesIO
# from docx import Document
# from .models import Chat, Analysis, Transcript
# from .serializers import ChatSerializer, AnalysisSerializer, TranscriptSerializer
# from rest_framework import status

# class ChatViewSet(viewsets.ModelViewSet):
#     queryset = Chat.objects.all().order_by('-created_at')
#     serializer_class = ChatSerializer

#     @action(detail=False, methods=['delete'])
#     def clear_all(self, request):
#         Chat.objects.all().delete()
#         return Response({'message': 'All chats cleared successfully.'})

# class CreateChatView(APIView):
#     def post(self, request):
#         name = request.data.get('name', 'Untitled Chat')
#         chat = Chat.objects.create(name=name)
#         return Response({"id": chat.id, "name": chat.name})

# class DeleteChatView(APIView):
#     def delete(self, request, chat_id):
#         try:
#             chat = Chat.objects.get(id=chat_id)
#             chat.delete()
#             return Response({"message": "Chat deleted successfully."})
#         except Chat.DoesNotExist:
#             return Response({"error": "Chat not found."}, status=404)

# class ListChatsView(APIView):
#     def get(self, request):
#         search_query = request.query_params.get('q', '')
#         chats = Chat.objects.all().order_by('-created_at')
#         if search_query:
#             chats = chats.filter(name__icontains=search_query)
#         serializer = ChatSerializer(chats, many=True)
#         return Response(serializer.data)
    
# class ExportWordView(APIView):
#     def get(self, request, analysis_id):
#         try:
#             analysis = Analysis.objects.get(id=analysis_id)
#             chat = Chat.objects.filter(analysis=analysis).first()
#             if not chat:
#                 return Response({"error": "Chat not found for this analysis."}, status=404)

#             doc = Document()
#             doc.add_paragraph(analysis.result)

#             buffer = BytesIO()
#             doc.save(buffer)
#             buffer.seek(0)

#             file_name = f"{chat.name}.docx"
#             response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#             response['Content-Disposition'] = f'attachment; filename={file_name}'
#             return response
#         except Analysis.DoesNotExist:
#             return Response({"error": "Analysis not found."}, status=404)

# @method_decorator(csrf_exempt, name='dispatch')
# class SaveTranscriptView(APIView):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             content = data.get('content')
#             if not content:
#                 return JsonResponse({"error": "No transcript content provided"}, status=400)

#             # Generate a name with the current date and time
#             current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#             chat_name = f"Transcript_{current_time}"  # Format: Transcript_YYYY-MM-DD_HH-MM-SS

#             # Create a new Transcript object
#             transcript = Transcript.objects.create(content=content)

#             # Create a new Chat object linked to the transcript
#             chat = Chat.objects.create(transcript=transcript, name=chat_name)

#             return JsonResponse({"id": chat.id, "content": chat.transcript.content, "name": chat.name})

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)

# @method_decorator(csrf_exempt, name='dispatch')
# class SaveAnalysisView(APIView):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             result = data.get('result')
#             if not result:
#                 return JsonResponse({"error": "No analysis result provided"}, status=400)

#             # Check if an analysis with the same result already exists
#             existing_analysis = Analysis.objects.filter(result=result).first()
#             if existing_analysis:
#                 # If the analysis already exists, return the associated chat
#                 existing_chat = Chat.objects.filter(analysis=existing_analysis).first()
#                 if existing_chat:
#                     return JsonResponse({"id": existing_chat.id, "result": existing_chat.analysis.result, "name": existing_chat.name})

#             # Generate a name with the current date and time
#             current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#             chat_name = f"Analysis_{current_time}"  # Format: Analysis_YYYY-MM-DD_HH-MM-SS

#             # Create a new Analysis object
#             analysis = Analysis.objects.create(result=result)

#             # Create a new Chat object linked to the analysis
#             chat = Chat.objects.create(analysis=analysis, name=chat_name)

#             return JsonResponse({
#                 "id": chat.id,
#                 "result": chat.analysis.result,
#                 "name": chat.name
#             })

#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
        
# @method_decorator(csrf_exempt, name='dispatch')
# class AnalyzeTranscriptView(APIView):
#     def post(self, request):
#         try:
#             data = json.loads(request.body)
#             transcript = data.get('transcript')
#             if not transcript:
#                 return JsonResponse({"error": "No transcript provided"}, status=400)

#             client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {"role": "system", "content": "You are a helpful assistant that analyzes medical transcripts."},
#                     {"role": "user", "content": f"Analyze the following medical transcript and provide insights:\n\n{transcript}"}
#                 ],
#                 max_tokens=500,
#             )

#             analysis_result = response.choices[0].message.content

#             existing_chat = Chat.objects.filter(analysis__result=analysis_result).first()
#             if existing_chat:
#                 return JsonResponse({
#                     "analysis": analysis_result,
#                     "analysis_id": existing_chat.analysis.id,
#                     "chat_id": existing_chat.id
#                 })

#             current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#             chat_name = f"Analysis_{current_time}"

#             analysis = Analysis.objects.create(transcript=transcript, result=analysis_result)
#             chat = Chat.objects.create(analysis=analysis, name=chat_name)

#             return JsonResponse({
#                 "analysis": analysis_result,
#                 "analysis_id": analysis.id,
#                 "chat_id": chat.id
#             })

#         except Exception as e:
#             print(f"Unexpected error: {e}")
#             return JsonResponse({"error": str(e)}, status=500)

# class ExportTranscriptView(APIView):
#     def get(self, request, chat_id):
#         try:
#             chat = Chat.objects.get(id=chat_id)
#             if not chat.transcript:
#                 return Response({"error": "No transcript found for this chat."}, status=404)

#             doc = Document()
#             doc.add_paragraph(chat.transcript)

#             buffer = BytesIO()
#             doc.save(buffer)
#             buffer.seek(0)

#             file_name = f"{chat.name}.docx".replace(" ", "_")
#             response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#             response['Content-Disposition'] = f'attachment; filename={file_name}'
#             return response
#         except Chat.DoesNotExist:
#             return Response({"error": "Chat not found."}, status=404)

# class RenameChatView(APIView):
#     def post(self, request, chat_id):
#         try:
#             chat = Chat.objects.get(id=chat_id)
#             new_name = request.data.get('name')
#             if not new_name:
#                 return Response({"error": "New name is required."}, status=status.HTTP_400_BAD_REQUEST)
            
#             chat.name = new_name
#             chat.save()
#             return Response({"message": "Chat renamed successfully.", "name": chat.name})
#         except Chat.DoesNotExist:
#             return Response({"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND)

# class AllChatsView(APIView):
#     def get(self, request):
#         chats = Chat.objects.all().order_by('-created_at')
#         chat_serializer = ChatSerializer(chats, many=True)

#         analyses = Analysis.objects.all().order_by('-created_at')
#         analysis_serializer = AnalysisSerializer(analyses, many=True)

#         transcripts = Transcript.objects.all().order_by('-created_at')
#         transcript_serializer = TranscriptSerializer(transcripts, many=True)

#         return Response({
#             'chats': chat_serializer.data,
#             'analyses': analysis_serializer.data,
#             'transcripts': transcript_serializer.data,
#         })

# class DownloadTranscriptView(APIView):
#     def get(self, request, transcript_id):
#         try:
#             transcript = Transcript.objects.get(id=transcript_id)
#             doc = Document()
#             doc.add_paragraph(transcript.content)

#             buffer = BytesIO()
#             doc.save(buffer)
#             buffer.seek(0)

#             current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#             file_name = f"Transcript_{current_time}.docx"

#             response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#             response['Content-Disposition'] = f'attachment; filename={file_name}'
#             return response
#         except Transcript.DoesNotExist:
#             return Response({"error": "Transcript not found."}, status=404)

# class DownloadAnalysisView(APIView):
#     def get(self, request, analysis_id):
#         try:
#             analysis = Analysis.objects.get(id=analysis_id)
#             doc = Document()
#             doc.add_paragraph(analysis.result)

#             buffer = BytesIO()
#             doc.save(buffer)
#             buffer.seek(0)

#             current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#             file_name = f"Analysis_{current_time}.docx"

#             response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#             response['Content-Disposition'] = f'attachment; filename={file_name}'
#             return response
#         except Analysis.DoesNotExist:
#             return Response({"error": "Analysis not found."}, status=404)

# class DeleteAnalysisView(APIView):
#     def delete(self, request, analysis_id):
#         try:
#             analysis = Analysis.objects.get(id=analysis_id)
#             analysis.delete()
#             return Response({"message": "Analysis deleted successfully."}, status=status.HTTP_200_OK)
#         except Analysis.DoesNotExist:
#             return Response({"error": "Analysis not found."}, status=status.HTTP_404_NOT_FOUND)

# class DeleteTranscriptView(APIView):
#     def delete(self, request, transcript_id):
#         try:
#             transcript = Transcript.objects.get(id=transcript_id)
#             transcript.delete()
#             return Response({"message": "Transcript deleted successfully."}, status=status.HTTP_200_OK)
#         except Transcript.DoesNotExist:
#             return Response({"error": "Transcript not found."}, status=status.HTTP_404_NOT_FOUND)