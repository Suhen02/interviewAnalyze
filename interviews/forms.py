# interviews/forms.py
from django import forms
from .models import InterviewSession

class InterviewUploadForm(forms.ModelForm):
    uploader_name = forms.CharField(max_length=100, required=False, help_text="Your name or identifier (optional)")

    class Meta:
        model = InterviewSession
        fields = ['uploader_name', 'video_file']