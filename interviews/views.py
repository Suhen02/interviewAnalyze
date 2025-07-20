
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
import os
import shutil

from .models import InterviewSession # Make sure this is imported
from .forms import InterviewUploadForm

from .utils.video_processor import capture_video_frames
from .utils.audio_processor import isolate_audio_track, start_assemblyai_transcription, retrieve_assemblyai_transcript
from .utils.body_language_analyzer import process_all_frame_poses

from .utils.report_formatter import compile_feedback_report

def index(request):
    form = InterviewUploadForm()
    return render(request, 'index.html', )

def upload(request):
    form = InterviewUploadForm()
    return render(request, 'analyse.html')
def form(request):
    form = InterviewUploadForm()
    return render(request, 'form.html',{'form': form})

def initiate_analysis(request):
    print("Request method:", request.method)

    if request.method == 'POST':
        print("Received POST request.")
        print("Request.FILES:", request.FILES)

        form = InterviewUploadForm(request.POST, request.FILES)
        
        print("Form is_bound:", form.is_bound)
        print("Form data (request.POST):", request.POST)

        if form.is_valid():
            print("Form is valid.")
            print("Form cleaned_data:", form.cleaned_data)

            uploader_name_from_form = form.cleaned_data.get('uploader_name') 
            video_file = form.cleaned_data['video_file']
            
            if video_file:
                print(f"Video file received: {video_file.name}, size: {video_file.size} bytes")
            else:
                print("No video file found in form.cleaned_data['video_file']. This is unexpected if form.is_valid().")

            if not video_file.name.lower().endswith('.mp4'):
                error_message = "Only .mp4 files are allowed."
                return render(request, 'upload_error.html', {'error_message': error_message})
            if video_file.size > 50 * 1024 * 1024:
                error_message = "File size exceeds 50MB limit."
                return render(request, 'upload_error.html', {'error_message': error_message})

            # Create the InterviewSession instance
            session = InterviewSession.objects.create(
                uploader_name=uploader_name_from_form,
                video_file=video_file,
                status='Processing'
            )

            session_media_dir = os.path.join(settings.MEDIA_ROOT, 'sessions', str(session.id))
            os.makedirs(session_media_dir, exist_ok=True)

            video_path = session.video_file.path
            audio_output_path = os.path.join(session_media_dir, f'session_{session.id}.wav')
            frames_output_dir = os.path.join(session_media_dir, 'frames')
            
            try:
                print(f"Starting audio isolation for session {session.id}...")
                isolate_audio_track(video_path, audio_output_path)
                print("Audio isolation complete.")

                print(f"Starting frame capture for session {session.id}...")
                total_captured_frames = capture_video_frames(video_path, frames_output_dir, frame_interval=15)
                print(f"Captured {total_captured_frames} sampled frames.")

                print(f"Processing poses for session {session.id}...")
                pose_analysis_results = process_all_frame_poses(frames_output_dir)
                print("Pose analysis complete.")

                print(f"Initiating AssemblyAI transcription for session {session.id}...")
                assemblyai_job_id = start_assemblyai_transcription(audio_output_path)
                print(f"AssemblyAI transcription job started. ID: {assemblyai_job_id}")

                # --- STORE JOB ID IN MODEL, NOT JUST SESSION ---
                session.assemblyai_job_id_field = assemblyai_job_id
                session.save(update_fields=['assemblyai_job_id_field']) # Save immediately
                # --- END STORE JOB ID ---

                # Store other data in session for immediate use by polling.
                # This will be replaced by retrieving from model later, but useful for initial poll.
                request.session['current_session_id'] = session.id
                request.session['pose_analysis_results'] = pose_analysis_results
                request.session['total_sampled_frames_count'] = total_captured_frames

                session.status = 'Processing'
                session.save() # This save might update status and other fields

                return redirect('display_processing_screen')

            except Exception as e:
                print(f"🛑 Error during initial analysis initiation for session {session.id}: {e}")
                session.status = 'Failed'
                session.error_message = str(e)
                session.save()
                if os.path.exists(session_media_dir):
                     shutil.rmtree(session_media_dir)
                return render(request, 'upload_error.html', {'error_message': str(e)})
        else:
            print("Form is NOT valid.")
            print("Form errors:", form.errors)
            error_message = "Invalid form submission. Please check your file."
            return render(request, 'upload_error.html', {'error_message': error_message, 'form_errors': form.errors})
    else:
        form = InterviewUploadForm()
        return render(request, 'analyse.html', {'form': form})


def display_processing_screen(request):
    session_id = request.session.get('current_session_id')
    if not session_id:
        return redirect('index')
    
    return render(request, 'processing.html', {'session_id': session_id})


def check_analysis_status(request):
    # Retrieve session ID from the request session, then get the InterviewSession object
    session_id = request.session.get("current_session_id")
    if not session_id:
        return JsonResponse({"status": "missing_data", "message": "Session ID missing."}, status=200)

    try:
        session = get_object_or_404(InterviewSession, id=session_id)
        
        # --- RETRIEVE JOB ID FROM MODEL, NOT SESSION ---
        assemblyai_job_id = session.assemblyai_job_id_field
        if not assemblyai_job_id:
            # If job ID is somehow missing from DB (shouldn't happen after first save)
            raise RuntimeError("AssemblyAI job ID is missing from the database for this session.")
        # --- END RETRIEVE JOB ID ---

        # Poll AssemblyAI (this will block until complete or error)
        formatted_transcript_data = retrieve_assemblyai_transcript(assemblyai_job_id)
        
        # --- Update Django Model with Results ---
        session.transcript = formatted_transcript_data.get('transcript')
        session.filler_words_data = formatted_transcript_data.get('filler_words')
        session.word_confidences_data = formatted_transcript_data.get('word_level_details')
        session.overall_clarity_confidence = formatted_transcript_data.get('overall_confidence')

        sentiment_data_temp = {
            'overall_sentiment': formatted_transcript_data.get('sentiment', 'N/A'),
            'breakdown': formatted_transcript_data.get('sentiment_breakdown', {})
        }
        session.sentiment_data = sentiment_data_temp

        entities_data_to_save = formatted_transcript_data.get('entities')
        if entities_data_to_save is None or not isinstance(entities_data_to_save, list):
            entities_data_to_save = []

        chapters_data_to_save = formatted_transcript_data.get('chapters')
        if chapters_data_to_save is None or not isinstance(chapters_data_to_save, list):
            chapters_data_to_save = []

        session.entities_data = entities_data_to_save
        session.chapters_data = chapters_data_to_save
        
        pose_data_to_save = request.session.get('pose_analysis_results') # Still from session for first fetch
        if pose_data_to_save is None or not isinstance(pose_data_to_save, list):
            pose_data_to_save = []
        session.pose_data = pose_data_to_save # Save to DB

        session.status = 'Analyzed'
        session.save() # This save saves all updated fields.

        # Clean up session data once analysis is complete and saved
        if 'current_session_id' in request.session: del request.session['current_session_id']
        if 'pose_analysis_results' in request.session: del request.session['pose_analysis_results']
        if 'total_sampled_frames_count' in request.session: del request.session['total_sampled_frames_count']
        # The assemblyai_job_id is now in the DB, so no need to delete from session anymore if we only get it from DB.
        # But if you stored it in session initially, it can be deleted:
        if 'assemblyai_job_id' in request.session: del request.session['assemblyai_job_id']


        session_media_dir = os.path.join(settings.MEDIA_ROOT, 'sessions', str(session.id))
        if os.path.exists(session_media_dir):
            shutil.rmtree(session_media_dir)
            print(f"Cleaned up temporary media directory: {session_media_dir}")


        return JsonResponse({"status": "completed", "redirect_url": redirect('show_results_report', session_id=session.id).url})

    except Exception as e:
        print(f"🛑 Error checking analysis status or processing results for session {session_id}: {e}")
        # Ensure session object is fetched/re-fetched if error occurred early
        try:
            session = get_object_or_404(InterviewSession, id=session_id)
            session.status = 'Failed'
            session.error_message = str(e)
            session.save()
        except Exception as update_e:
            print(f"Failed to update session status after error: {update_e}")

        session_media_dir = os.path.join(settings.MEDIA_ROOT, 'sessions', str(session.id))
        if os.path.exists(session_media_dir):
            shutil.rmtree(session_media_dir)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def show_results_report(request, session_id):
    """
    Displays the final analysis report for a given session.
    """
    interview_session = get_object_or_404(InterviewSession, id=session_id)

    if interview_session.status != 'Analyzed':
        return redirect('display_processing_screen')

    transcript_data_for_report = {
        "transcript": interview_session.transcript,
        "overall_confidence": interview_session.overall_clarity_confidence,
        "filler_words": interview_session.filler_words_data,
        "word_level_details": interview_session.word_confidences_data,
        "sentiment": interview_session.sentiment_data.get('overall_sentiment') if interview_session.sentiment_data else 'N/A',
        "sentiment_breakdown": interview_session.sentiment_data.get('breakdown') if interview_session.sentiment_data else {},
        
        # Ensure these are lists when retrieved from JSONField, as they might be None
        "entities": interview_session.entities_data or [],
        "chapters": interview_session.chapters_data or [],
    }

    # Ensure pose_data_for_report is also an empty list if None
    body_pose_data_for_report = interview_session.pose_data or [] 
    total_analyzed_frames_count = len(body_pose_data_for_report) if body_pose_data_for_report else 0

    feedback_report = compile_feedback_report(
        transcript_data_for_report,
        body_pose_data_for_report,
        total_analyzed_frames_count
    )
    
    context = {
        'interview_session': interview_session,
        'feedback': feedback_report,
    }
    return render(request, "results.html", context)

def show_upload_error(request):
    """
    A simple error page for upload issues.
    """
    error_message = request.GET.get('error_message', 'An unknown error occurred during upload or analysis.')
    form_errors = request.GET.get('form_errors', None)
    return render(request, 'upload_error.html', {'error_message': error_message, 'form_errors': form_errors})