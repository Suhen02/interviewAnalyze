
import os
import mediapipe as mp
import cv2

mp_pose = mp.solutions.pose

def detect_single_frame_pose(image_path):
    """
    Detects human pose and estimates posture from a single image.
    Args:
        image_path (str): Path to the image file.
    Returns:
        dict: Analysis results including posture and 3D pose landmarks.
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Image not found or could not be loaded: {image_path}")
        return {"posture": "unknown", "pose_3d_landmarks": None, "error": "Image not found or could not be loaded"}

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
         
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            shoulder_drop = abs(left_shoulder.y - right_shoulder.y)

        
            pose_3d_landmarks_data = []
            if results.pose_world_landmarks:
                pose_3d_landmarks_data = [{
                    "x": lm.x,
                    "y": lm.y,
                    "z": lm.z,
                    "visibility": lm.visibility
                } for lm in results.pose_world_landmarks.landmark]
            else:
                print(f"Warning: No 3D pose world landmarks detected for {os.path.basename(image_path)}")

            return {
                "posture": "slouched" if shoulder_drop > 0.1 else "balanced",
                "pose_3d_landmarks": pose_3d_landmarks_data # Renamed key
            }
        
        return {"posture": "unknown", "pose_3d_landmarks": None, "message": "No pose landmarks detected"}

    
def process_all_frame_poses(frame_dir):
    """
    Processes all sampled frames in a directory for body pose.
    Args:
        frame_dir (str): Directory containing image frames.
    Returns:
        list: A list of dictionaries, each containing analysis results for a frame.
    """
    results = []
    frame_files = sorted([f for f  in os.listdir(frame_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    for frame_file in frame_files:
        frame_path = os.path.join(frame_dir, frame_file)
        result = detect_single_frame_pose(frame_path)
        
        results.append({
            "frame": frame_file,
            "posture": result.get("posture", "unknown"),
            "pose_3d_landmarks": result.get("pose_3d_landmarks")
        })
    print(f"🧍‍♂️ Processed {len(results)} poses from {frame_dir}")
    return results