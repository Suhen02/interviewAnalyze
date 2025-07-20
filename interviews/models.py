
from django.db import models



class InterviewSession(models.Model):
    uploader_name = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="Name or identifier provided by the uploader (string)")

    video_file = models.FileField(upload_to='interview_videos/',
                                  help_text="Uploaded interview video file.")
    uploaded_at = models.DateTimeField(auto_now_add=True,
                                       help_text="Timestamp of video upload.")

    # --- NEW FIELD ---
    assemblyai_job_id_field = models.CharField(max_length=100, blank=True, null=True, unique=True,
                                               help_text="ID of the AssemblyAI transcription job.")
    # --- END NEW FIELD ---

    transcript = models.TextField(blank=True, null=True, help_text="Full transcription of the interview.")
    filler_words_data = models.JSONField(blank=True, null=True, help_text="JSON array of detected filler words with details.")
    word_confidences_data = models.JSONField(blank=True, null=True, help_text="JSON array of all words with their confidence scores.")
    overall_clarity_confidence = models.FloatField(blank=True, null=True, help_text="Overall confidence score of the transcription (0.0-1.0).")
    sentiment_data = models.JSONField(blank=True, null=True, help_text="JSON object summarizing sentiment analysis.")
    pose_data = models.JSONField(blank=True, null=True, help_text="JSON array of pose analysis results per sampled frame.")
    entities_data = models.JSONField(blank=True, null=True, help_text="JSON array of named entities detected.")
    chapters_data = models.JSONField(blank=True, null=True, help_text="JSON array of auto-generated chapters.")

    STATUS_CHOICES = [
        ('Uploaded', 'Uploaded'),
        ('Processing', 'Processing'),
        ('Analyzed', 'Analyzed'),
        ('Failed', 'Failed'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Uploaded', help_text="Current status of the video analysis.")
    error_message = models.TextField(blank=True, null=True, help_text="Details if the analysis failed.")


    def __str__(self):
        return f"Session {self.id} - {self.uploader_name or 'Anonymous'} - {self.status}"

    class Meta:
        verbose_name = "Interview Session"
        verbose_name_plural = "Interview Sessions"