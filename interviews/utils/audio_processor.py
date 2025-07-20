
import os
import subprocess
import time
import requests
from pydub import AudioSegment
from django.conf import settings



def isolate_audio_track(video_path, output_path):
    ffmpeg_cmd = getattr(settings, 'FFMPEG_PATH', 'ffmpeg')

    command = [
        ffmpeg_cmd, "-y", "-i", video_path,
        "-f", "wav", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print("📁 Isolated audio track saved to:", output_path)
        print("📦 Audio file size:", os.path.getsize(output_path), "bytes")
        
        audio = AudioSegment.from_wav(output_path)
        print("📏 Audio duration:", len(audio) / 1000, "seconds")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise FileNotFoundError(f"❌ Audio isolation failed. Output file not found or empty: {output_path}")
        
    except FileNotFoundError:
        raise RuntimeError(f"FFmpeg not found. Ensure '{ffmpeg_cmd}' is in your system's PATH or configured in settings.py.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg command failed: {e.stderr} (stdout: {e.stdout})")
    except Exception as e:
        raise RuntimeError(f"Error during audio isolation: {e}")



def start_assemblyai_transcription(audio_path):
    api_key = settings.ASSEMBLYAI_API_KEY

    if not api_key:
        raise ValueError("ASSEMBLYAI_API_KEY is not set in environment variables or settings.py")

    
    upload_response = None
    audio_url = None
    transcript_response = None
    transcript_json = None

    try:
        print(f"Uploading audio file to AssemblyAI: {audio_path}")
        with open(audio_path, "rb") as f:
            upload_response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": api_key},
                data=f
            )
        upload_response.raise_for_status() 
        audio_url = upload_response.json().get("upload_url")
        print(f"DEBUG: AssemblyAI uploaded audio URL: {audio_url}")

        if not audio_url:
            raise RuntimeError("AssemblyAI did not return an audio upload URL.")

        print("Initiating transcript request from AssemblyAI...")
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={"authorization": api_key},
            json={
                "audio_url": audio_url,
                "sentiment_analysis": True,
                "entity_detection": True,
                "auto_chapters": True,
                "word_boost": ["um", "uh", "like", "you know", "so", "actually", "basically"],
                "disfluencies": True,
                "format_text": True,
                "punctuate": True,
              
                "language_code": "en_us"
            }
        )
        transcript_response.raise_for_status() 
        transcript_json = transcript_response.json()
        transcript_job_id = transcript_json.get("id")

        if not transcript_job_id:
            print("❌ No transcript job ID returned. Full response:", transcript_json)
            raise RuntimeError("AssemblyAI did not return a transcript job ID.")

        print(f"🔁 AssemblyAI transcription job submitted. ID: {transcript_job_id}")
        return transcript_job_id

    except FileNotFoundError:
        raise RuntimeError(f"Audio file not found at {audio_path} for AssemblyAI upload.")
    except requests.exceptions.RequestException as e:
       
        error_msg = f"Network or API communication error with AssemblyAI: {e}"
        
        if upload_response is not None and upload_response.status_code >= 400:
            try:
                aa_error = upload_response.json().get('error')
                if aa_error:
                    error_msg += f" (AssemblyAI Upload Error: {aa_error})"
            except ValueError: pass
        elif transcript_response is not None and transcript_response.status_code >= 400:
            try:
                aa_error = transcript_response.json().get('error')
                if aa_error:
                    error_msg += f" (AssemblyAI Transcript Error: {aa_error})"
            except ValueError: pass 
        
        raise RuntimeError(error_msg)
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred during AssemblyAI processing: {type(e).__name__}: {e}")


def retrieve_assemblyai_transcript(transcript_job_id):
    api_key = settings.ASSEMBLYAI_API_KEY

    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_job_id}"
    headers = {"authorization": api_key}
    
    print(f"Polling AssemblyAI transcript job status for ID: {transcript_job_id}")

    while True:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        status = response_json.get('status')
        
        print(f"Current AssemblyAI job status: {status}")

        if status == 'completed':
            print("AssemblyAI transcription job completed successfully!")
            return _format_assemblyai_output(response_json)
        elif status == 'error':
            error_msg = response_json.get('error', 'Unknown AssemblyAI error.')
            raise RuntimeError(f"AssemblyAI transcription job failed: {error_msg}")
        else:
            time.sleep(2)


def _format_assemblyai_output(raw_api_response):
    full_transcript_text = raw_api_response.get('text', '')
    overall_confidence = raw_api_response.get('confidence')

    filler_words_extracted = []
    all_word_details = []
    
    if 'words' in raw_api_response:
        for word_obj in raw_api_response['words']:
            start_time_sec = word_obj['start'] / 1000
            end_time_sec = word_obj['end'] / 1000

            word_data_item = {
                "word": word_obj['text'],
                "start_time": f"{start_time_sec:.2f}",
                "end_time": f"{end_time_sec:.2f}",
                "confidence": f"{word_obj['confidence']:.2f}"
            }
            all_word_details.append(word_data_item)

            if word_obj.get('disfluency', False):
                filler_words_extracted.append(word_data_item)


    overall_sentiment = "Neutral"
    sentiment_breakdown = {}
    if 'sentiment_analysis' in raw_api_response and isinstance(raw_api_response['sentiment_analysis'], dict):
        if 'chapters' in raw_api_response['sentiment_analysis']:
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            for chapter_sentiment in raw_api_response['sentiment_analysis']['chapters']:
                if chapter_sentiment['sentiment'] == 'POSITIVE': positive_count += 1
                elif chapter_sentiment['sentiment'] == 'NEGATIVE': negative_count += 1
                else: neutral_count += 1
            
            if positive_count > negative_count and positive_count > neutral_count:
                overall_sentiment = "Positive"
            elif negative_count > positive_count and negative_count > neutral_count:
                overall_sentiment = "Negative"
            else:
                overall_sentiment = "Neutral"
            
            sentiment_breakdown = {
                "positive_chapters": positive_count,
                "negative_chapters": negative_count,
                "neutral_chapters": neutral_count
            }
        elif 'results' in raw_api_response['sentiment_analysis']:
            total_positive_score = 0
            total_negative_score = 0
            total_neutral_score = 0
            num_sentences = 0
            for sentence_sentiment in raw_api_response['sentiment_analysis']['results']:
                if sentence_sentiment['sentiment'] == 'POSITIVE': total_positive_score += 1
                elif sentence_sentiment['sentiment'] == 'NEGATIVE': total_negative_score += 1
                else: total_neutral_score += 1
                num_sentences += 1
            
            if num_sentences > 0:
                if total_positive_score > total_negative_score and total_positive_score > total_neutral_score:
                    overall_sentiment = "Positive"
                elif total_negative_score > total_positive_score and total_negative_score > total_neutral_score:
                    overall_sentiment = "Negative"
                else:
                    overall_sentiment = "Neutral"
            
            sentiment_breakdown = {
                "positive_sentences": total_positive_score,
                "negative_sentences": total_negative_score,
                "neutral_sentences": total_neutral_score
            }


    return {
        "transcript": full_transcript_text,
        "overall_confidence": overall_confidence,
        "filler_words": filler_words_extracted,
        "word_level_details": all_word_details,
        "sentiment": overall_sentiment,
        "sentiment_breakdown": sentiment_breakdown,
        "entities": raw_api_response.get('entities', []),
        "chapters": raw_api_response.get('chapters', []),
    }