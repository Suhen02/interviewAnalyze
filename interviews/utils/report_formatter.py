

def compile_feedback_report(transcript_analysis_data, body_pose_data, total_analyzed_frames_count):
    """
    Compiles a detailed feedback report from various analysis data points.
    Args:
        transcript_analysis_data (dict): Pre-processed data from AssemblyAI.
        body_pose_data (list): List of pose analysis results for each sampled frame.
        total_analyzed_frames_count (int): The actual number of frames that underwent pose analysis.
    Returns:
        dict: A comprehensive feedback report.
    """
    issues_identified = []
    actionable_tips = []


    overall_confidence = transcript_analysis_data.get("overall_confidence")
    clarity_level = "N/A"
    if overall_confidence is not None:
        clarity_level = (
            "Excellent" if overall_confidence >= 0.90 else
            "Good" if overall_confidence >= 0.80 else
            "Moderate" if overall_confidence >= 0.70 else
            "Needs Improvement"
        )
    
    
    detected_filler_words = transcript_analysis_data.get("filler_words", [])
    if detected_filler_words:
        for word_info in detected_filler_words:
            issues_identified.append({
                "type": "filler_word",
                "word": word_info.get("word"),
                "time": word_info.get("start_time"),
                "confidence": word_info.get("confidence")
            })

  
    all_word_confidences = transcript_analysis_data.get("word_level_details", [])
    words_with_low_clarity = [
        word for word in all_word_confidences
        if word.get("confidence") and float(word["confidence"]) < 0.70 
    ]
    if words_with_low_clarity:
        issues_identified.append({
            "type": "low_clarity_words",
            "count": len(words_with_low_clarity),
            "words": words_with_low_clarity[:5],
            "message": f"Detected {len(words_with_low_clarity)} words with low clarity. Examples include: " + 
                       ", ".join([f"'{w['word']}' at {w['start_time']}s" for w in words_with_low_clarity[:3]]) + "."
        })


   
    frames_with_slouched_posture = []
    if body_pose_data:
        for pose_result in body_pose_data:
            if pose_result.get("posture") == "slouched":
                frames_with_slouched_posture.append(pose_result.get("frame"))


  
    overall_sentiment_summary = transcript_analysis_data.get("sentiment", "N/A")
    sentiment_detailed_breakdown = transcript_analysis_data.get("sentiment_breakdown", {})
    
    
    summary_sentences = []
    if overall_confidence is not None:
        summary_sentences.append(f"Your overall speech clarity was {overall_confidence:.2f} ({clarity_level}).")
    else:
        summary_sentences.append("Overall speech clarity could not be determined.")

    if detected_filler_words:
        summary_sentences.append(f"You used {len(detected_filler_words)} filler word{'s' if len(detected_filler_words) != 1 else ''}.")
    else:
        summary_sentences.append("No filler words were detected.")
    
    if words_with_low_clarity:
        summary_sentences.append(f"Detected {len(words_with_low_clarity)} words with low clarity.")

    if frames_with_slouched_posture:
        summary_sentences.append(f"Slouched posture was observed in {len(frames_with_slouched_posture)} out of {total_analyzed_frames_count} analyzed frames.")
    else:
        summary_sentences.append("Your posture was generally balanced throughout the analyzed frames.")
    
    summary_sentences.append(f"Overall sentiment of your speech was: {overall_sentiment_summary}.")

    final_summary_text = " ".join(summary_sentences)

   
    if detected_filler_words:
        actionable_tips.append("Practice intentional pauses to reduce filler word usage. Record short mock answers and identify when you use fillers.")
        actionable_tips.append("Focus on structuring your thoughts before speaking to minimize hesitation.")
    
    if overall_confidence is not None and overall_confidence < 0.80:
        if clarity_level == "Needs Improvement":
            actionable_tips.append("Focus on pacing and articulation. Speak clearly and concisely. Practice enunciating each word.")
        else: 
            actionable_tips.append("Speak a bit slower and ensure your enunciation is clear, especially on complex words.")
    
    if words_with_low_clarity:
        actionable_tips.append("Review the sections where specific words had low clarity. Practice pronouncing those words or phrases clearly.")
        actionable_tips.append("Ensure you are speaking directly into the microphone and there isn't excessive background noise.")

    if frames_with_slouched_posture:
        actionable_tips.append("Maintain an upright posture with shoulders back and relaxed. This conveys confidence and professionalism.")
        actionable_tips.append("Sit comfortably but alert. Practice in front of a mirror or camera to self-correct your posture.")
    
    if overall_sentiment_summary == "Negative" or (sentiment_detailed_breakdown and sentiment_detailed_breakdown.get("negative_chapters", 0) > sentiment_detailed_breakdown.get("positive_chapters", 0)):
        actionable_tips.append("Be mindful of your vocal tone and word choice to convey a positive and enthusiastic attitude.")
        actionable_tips.append("Frame answers positively, even when discussing challenges. Focus on solutions and learnings.")

    if not actionable_tips:
        actionable_tips.append("Great job – no major issues detected across the analyzed metrics! Keep up the confident and clear delivery!")

    body_language_performance_score = None
    if total_analyzed_frames_count and total_analyzed_frames_count > 0:
        balanced_frames_count = total_analyzed_frames_count - len(frames_with_slouched_posture)
        body_language_performance_score = round(100 * (balanced_frames_count / total_analyzed_frames_count), 2)
    
    performance_metrics = {
        "overall_speech_clarity_percent": round(overall_confidence * 100, 2) if overall_confidence is not None else None,
        "clarity_level": clarity_level,
        "filler_word_count": len(detected_filler_words),
        "low_clarity_word_count": len(words_with_low_clarity),
        "body_language_score_percent": body_language_performance_score,
        "overall_sentiment": overall_sentiment_summary,
        "sentiment_breakdown": sentiment_detailed_breakdown
    }

   
    entities_for_report = transcript_analysis_data.get('entities')
    if not isinstance(entities_for_report, list): 
        entities_for_report = [] 

    chapters_for_report = transcript_analysis_data.get('chapters')
    if not isinstance(chapters_for_report, list): 
        chapters_for_report = []
   

    return {
        "summary": final_summary_text,
        "metrics": performance_metrics,
        "issues": issues_identified,
        "tips": actionable_tips,
        "overall_confidence": overall_confidence,
        "clarity_level": clarity_level,
    
        "entities": entities_for_report,
        "chapters": chapters_for_report,
    }