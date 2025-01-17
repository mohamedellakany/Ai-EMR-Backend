from django.db import models

class Chat(models.Model):
    name = models.CharField(max_length=255, default="Untitled Chat")
    transcript = models.TextField(blank=True, null=True)
    analysis = models.ForeignKey('Analysis', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Analysis(models.Model):
    transcript = models.TextField()
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.transcript[:50]}..."

class Transcript(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transcript {self.id}"