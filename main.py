"""Driver Drowsiness & Distraction Detection System - Main Application.

Usage:
    python main.py              - Start with default webcam
    python main.py --camera 1   - Use camera index 1

Controls:
    Q / ESC  - Quit
    L        - Toggle landmark display
    M        - Toggle metrics display
    R        - Reset all detectors
"""

import sys
import time
import cv2
import numpy as np

import config
from detector.face_mesh import FaceMeshDetector
from detector.drowsiness import DrowsinessDetector
from detector.distraction import DistractionDetector
from detector.phone_detector import PhoneDetector
from alerts.alert_manager import AlertManager


def draw_no_face_warning(frame):
    """Draw a warning when no face is detected."""
    h, w = frame.shape[:2]

    # Dark overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (30, 30, 30), -1)
    frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)

    # Warning icon and text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = "NO FACE DETECTED"
    text_size = cv2.getTextSize(text, font, 1.0, 2)[0]
    text_x = (w - text_size[0]) // 2
    text_y = h // 2
    cv2.putText(frame, text, (text_x, text_y), font, 1.0,
                (0, 60, 255), 2, cv2.LINE_AA)

    sub_text = "Please face the camera"
    sub_size = cv2.getTextSize(sub_text, font, 0.6, 1)[0]
    sub_x = (w - sub_size[0]) // 2
    cv2.putText(frame, sub_text, (sub_x, text_y + 35), font, 0.6,
                (180, 180, 180), 1, cv2.LINE_AA)

    return frame


def main():
    """Main application loop."""
    # Parse command line arguments
    camera_index = config.CAMERA_INDEX
    if len(sys.argv) > 1:
        if sys.argv[1] == "--camera" and len(sys.argv) > 2:
            camera_index = int(sys.argv[2])

    # Initialize components
    print("[INFO] Initializing Driver Drowsiness & Distraction Detection System...")
    face_detector = FaceMeshDetector(
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    drowsiness_detector = DrowsinessDetector()
    distraction_detector = DistractionDetector()
    phone_detector = PhoneDetector()
    alert_manager = AlertManager()

    # Initialize video capture with retry
    print(f"[INFO] Opening camera {camera_index}...")
    cap = None
    max_retries = 3
    for attempt in range(max_retries):
        # Try DirectShow backend first (more reliable on Windows)
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Fallback to default backend
            cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        if cap.isOpened():
            # Try reading a test frame
            ret, _ = cap.read()
            if ret:
                print(f"[INFO] Camera {camera_index} opened successfully.")
                break
            else:
                print(f"[WARNING] Camera opened but failed to read frame. Retrying ({attempt+1}/{max_retries})...")
                cap.release()
                time.sleep(2)
        else:
            print(f"[WARNING] Cannot open camera {camera_index}. Retrying ({attempt+1}/{max_retries})...")
            time.sleep(2)
    else:
        print(f"[ERROR] Cannot open camera {camera_index} after {max_retries} attempts.")
        print("        Make sure a webcam is connected and not in use by another app.")
        print("        You can specify a different camera with: python main.py --camera <index>")
        sys.exit(1)

    # Display settings
    show_landmarks = config.SHOW_LANDMARKS
    show_metrics = config.SHOW_METRICS

    # FPS tracking
    fps_start_time = time.time()
    frame_count = 0
    fps = 0.0

    # No-face frame counter (to avoid flickering)
    no_face_frames = 0
    # Camera read failure counter
    fail_count = 0

    print("[INFO] System ready. Press Q or ESC to quit.")
    print("[INFO] Controls: L=landmarks, M=metrics, R=reset")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                fail_count += 1
                if fail_count == 1:
                    print("[WARNING] Failed to read frame from camera. Reconnecting...")
                if fail_count > 30:
                    # Try to reconnect
                    cap.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        cap = cv2.VideoCapture(camera_index)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
                    fail_count = 0
                    if cap.isOpened():
                        print("[INFO] Camera reconnected.")
                continue
            fail_count = 0

            frame_h, frame_w = frame.shape[:2]

            # Run phone object detection (YOLO) on every 3rd frame for performance
            phone_result = None
            if frame_count % 3 == 0:
                phone_result = phone_detector.detect(frame)
            elif hasattr(phone_detector, '_phone_detected'):
                phone_result = {'phone_detected': phone_detector._phone_detected,
                                'phone_box': phone_detector._phone_box}
            else:
                phone_result = {'phone_detected': False, 'phone_box': None}

            # Draw phone bounding box if detected
            frame = phone_detector.draw_phone_box(frame, phone_result)

            # Process frame with face mesh
            faces = face_detector.process(frame)

            if faces is not None and len(faces) > 0:
                no_face_frames = 0
                landmarks = faces[0]  # Flat list of NormalizedLandmark objects

                # Update drowsiness detector
                drowsiness_result = drowsiness_detector.update(
                    landmarks, frame_w, frame_h
                )

                # Update distraction detector (pass EAR + phone detection)
                distraction_result = distraction_detector.update(
                    landmarks, frame_w, frame_h,
                    ear=drowsiness_result['ear'],
                    phone_in_frame=phone_result['phone_detected'],
                )

                # Draw landmarks if enabled
                if show_landmarks:
                    frame = face_detector.draw_landmarks(frame, landmarks)

                # Trigger alerts
                if drowsiness_result['is_drowsy']:
                    alert_manager.trigger_drowsy_alert()
                    frame = alert_manager.draw_alert_overlay(
                        frame, 'drowsy', True
                    )

                if drowsiness_result['is_yawning']:
                    alert_manager.trigger_yawn_alert()
                    frame = alert_manager.draw_alert_overlay(
                        frame, 'yawning',
                        not drowsiness_result['is_drowsy']
                    )

                if distraction_result['is_phone_usage']:
                    alert_manager.trigger_phone_alert()
                    frame = alert_manager.draw_alert_overlay(
                        frame, 'phone',
                        not drowsiness_result['is_drowsy']
                        and not drowsiness_result['is_yawning']
                    )

                if distraction_result['is_distracted']:
                    alert_manager.trigger_distraction_alert()
                    frame = alert_manager.draw_alert_overlay(
                        frame, 'distracted',
                        not drowsiness_result['is_drowsy']
                        and not drowsiness_result['is_yawning']
                        and not distraction_result['is_phone_usage']
                    )

                # Draw dashboard UI with metrics
                if show_metrics:
                    frame = alert_manager.draw_dashboard(
                        frame, drowsiness_result, distraction_result, fps
                    )
            else:
                # No face detected
                no_face_frames += 1
                if no_face_frames > 5:
                    frame = draw_no_face_warning(frame)
                # Reset detectors when face is lost
                drowsiness_detector.reset()
                distraction_detector.reset()

            # Calculate FPS
            frame_count += 1
            elapsed = time.time() - fps_start_time
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                fps_start_time = time.time()

            # Show the frame
            cv2.imshow("Driver Drowsiness & Distraction Detection", frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # Q or ESC
                break
            elif key == ord('l'):
                show_landmarks = not show_landmarks
                print(f"[INFO] Landmarks: {'ON' if show_landmarks else 'OFF'}")
            elif key == ord('m'):
                show_metrics = not show_metrics
                print(f"[INFO] Metrics: {'ON' if show_metrics else 'OFF'}")
            elif key == ord('r'):
                drowsiness_detector.reset()
                distraction_detector.reset()
                print("[INFO] Detectors reset.")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")

    finally:
        # Cleanup
        print("[INFO] Cleaning up...")
        cap.release()
        cv2.destroyAllWindows()
        face_detector.release()
        alert_manager.release()
        print("[INFO] System stopped.")


if __name__ == "__main__":
    main()
