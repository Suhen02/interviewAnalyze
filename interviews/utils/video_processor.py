
import cv2
import os

def capture_video_frames(video_path, output_dir, frame_interval=15):
    """
    Captures frames from a video at a specified interval for analysis.
    Args:
        video_path (str): Path to the input video file.
        output_dir (str): Directory where frames will be saved.
        frame_interval (int): Capture every Nth frame. (e.g., 15 for every 15th frame)
    Returns:
        int: Total number of frames captured.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file for frame capture: {video_path}")

    frame_count = 0
    captured_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_filename = os.path.join(output_dir, f'frame_{captured_count:05d}.jpg')
            cv2.imwrite(frame_filename, frame)
            captured_count += 1
        
        frame_count += 1

    cap.release()
    print(f"🖼️ Captured {captured_count} frames from {video_path} into {output_dir}")
    return captured_count