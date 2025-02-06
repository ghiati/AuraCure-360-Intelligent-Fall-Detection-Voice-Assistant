import torch
import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
import os
import threading
import requests

# Set environment variable to control OpenCV threading
os.environ["OPENCV_OPENCL_RUNTIME"] = "disabled"

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# Use os.path for platform-independent path handling
model_path = os.path.expanduser('/home/mg/projet_transverseaux/assistant/model.h5')
video_path = os.path.expanduser('/home/mg/projet_transverseaux/assistant/video .avi')

# Load your custom model
try:
    model1 = load_model(model_path)
except Exception as e:
    print(f"Error loading model: {e}")
    exit(1)

# Flask server URL
FLASK_SERVER_URL = "http://127.0.0.1:5000/fall_detected"

# Fall detection flag
fall_detected_flag = False

def smooth_landmarks(new_landmarks, previous_landmarks, alpha):
    if previous_landmarks is None:
        return new_landmarks
    return [
        type(new)(
            x=alpha * new.x + (1 - alpha) * old.x,
            y=alpha * new.y + (1 - alpha) * old.y,
            z=alpha * new.z + (1 - alpha) * old.z,
            visibility=alpha * new.visibility + (1 - alpha) * old.visibility,
        )
        for new, old in zip(new_landmarks, previous_landmarks)
    ]

# Variables for tracking
x_coords = []
y_coords = []
predictions = []
distances = []

bool_flag = False
class_labels = {
    0: {"label": "Personne", "color": (0, 0, 255)},
    1: {"label": "Chute", "color": (255, 0, 0)},
    2: {"label": "Dormir", "color": (0, 255, 255)},
    3: {"label": "Déséquilibre", "color": (255, 255, 0)},
    5: {"label": "Assis", "color": (255, 0, 255)}
}

def calculate_entropy(probabilities):
    probabilities = np.array(probabilities)
    epsilon = 1e-10
    return -np.sum(probabilities * np.log(probabilities + epsilon))

# Initialize video capture with proper settings
cap = cv2.VideoCapture(video_path)

# Check if video opened successfully
if not cap.isOpened():
    print(f"Error: Could not open video file: {video_path}")
    exit(1)

# Set video capture properties
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    min_detection_confidence=0.8,
    min_tracking_confidence=0.1,
    model_complexity=1
)

previous_landmarks = None
alpha = 0.1

# Define mean and scale for normalization (replace with your actual values)
mean = [0, 0, 0, 0]
scale = [1, 1, 1, 1]

# Create a lock for thread-safe operations
frame_lock = threading.Lock()

try:
    while cap.isOpened():
        with frame_lock:
            ret, frame = cap.read()
            if not ret:
                print("End of video stream.")
                break

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Pass the frame through YOLOv5
        results = model(frame_rgb)
        detections = results.pandas().xywh[0]
        threshold = 0.6
        detections = detections[(detections['class'] == 0) & (detections['confidence'] > threshold)]

        # Process detections
        for _, detection in detections.iterrows():
            if detection['class'] == 0:
                x_center = int(detection['xcenter'])
                y_center = int(detection['ycenter'])
                width = int(detection['width'])
                height = int(detection['height'])

                # Process pose
                results = pose.process(frame_rgb)

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    smoothed_landmarks = smooth_landmarks(landmarks, previous_landmarks, alpha)
                    previous_landmarks = smoothed_landmarks

                    # Get hand coordinates
                    left_hand = smoothed_landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
                    right_hand = smoothed_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]

                    left_x, left_y = int(left_hand.x * frame.shape[1]), int(left_hand.y * frame.shape[0])
                    right_x, right_y = int(right_hand.x * frame.shape[1]), int(right_hand.y * frame.shape[0])
                    distance = np.sqrt((right_x - left_x)**2 + (right_y - left_y)**2)

                    # Draw hand landmarks
                    cv2.circle(frame, (left_x, left_y), 10, (0, 255, 0), -1)
                    cv2.circle(frame, (right_x, right_y), 10, (255, 0, 0), -1)

                    xmin = int(x_center - width / 2)
                    ymin = int(y_center - height / 2)
                    x_coords.append(x_center)
                    y_coords.append(y_center)
                    distances.append(distance)

                else:
                    x_coords = []
                    y_coords = []
                    distances = []
                    continue

                # Analyze variance every 30 frames
                if len(x_coords) % 30 == 0 and len(x_coords) > 0:
                    x_variance = np.var(x_coords)
                    y_variance = np.var(y_coords)
                    distance_main_GD_variance = np.var(distances)

                    x_coords = []
                    y_coords = []
                    distances = []

                    liste = [
                        (x_variance - mean[0]) / scale[0],
                        (y_variance - mean[1]) / scale[1],
                        (width / height - mean[2]) / scale[2],
                        (distance_main_GD_variance - mean[3]) / scale[3]
                    ]

                    liste = np.array(liste).reshape(1, -1)
                    prediction = model1.predict(liste)
                    predictions.append(prediction)

                if len(predictions) == 1:
                    entropies = [calculate_entropy(prediction) for prediction in predictions]
                    min_entropy_index = np.argmin(entropies)
                    class_predire = np.argmax(predictions[min_entropy_index])
                    class_info = class_labels.get(class_predire)
                    bool_flag = True
                    predictions = []

                if bool_flag and class_info is not None:
                    cv2.rectangle(frame, (xmin, ymin), (xmin + width, ymin + height), class_info["color"], 2)
                    cv2.putText(frame, class_info["label"], (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, class_info["color"], 2)

                    # If a fall is detected and no message has been sent yet
                    if class_predire == 1 and not fall_detected_flag:  # Fall detected
                        try:
                            response = requests.post(FLASK_SERVER_URL)
                            if response.status_code == 200:
                                print("Fall detected! Alert sent to the assistant.")
                                fall_detected_flag = True  # Set the flag to prevent additional messages
                        except Exception as e:
                            print(f"Error sending fall alert: {e}")
                    elif class_predire != 1:
                        fall_detected_flag = False  # Reset the flag if no fall is detected

        # Display the frame
        cv2.imshow('Fall Detection', frame)

        # Handle window events
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # q or ESC
            break

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Cleanup
    with frame_lock:
        cap.release()
    cv2.destroyAllWindows()
    # Ensure all windows are closed
    for i in range(5):
        cv2.waitKey(1)