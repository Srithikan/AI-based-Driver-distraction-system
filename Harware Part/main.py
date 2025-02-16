import cv2
import mediapipe as mp
import numpy as np
import time
import serial  
import pyttsx3 

# Initialize Serial Communication (Change COM port accordingly)
try:
    arduino = serial.Serial('COM5', 9600, timeout=1)  
    time.sleep(2)  # Wait for Arduino to initialize
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()
engine.setProperty('rate', 150) 
engine.setProperty('volume', 1.0)  

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Define facial landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH = [78, 191, 308, 14]  # Upper lip, lower lip

# Function to calculate aspect ratio
def aspect_ratio(landmarks, img_w, img_h):
    """Calculates the aspect ratio of eyes or mouth"""
    try:
        a = np.linalg.norm(np.array([landmarks[1].x * img_w, landmarks[1].y * img_h]) - 
                           np.array([landmarks[-2].x * img_w, landmarks[-2].y * img_h]))
        b = np.linalg.norm(np.array([landmarks[2].x * img_w, landmarks[2].y * img_h]) - 
                           np.array([landmarks[-3].x * img_w, landmarks[-3].y * img_h]))
        c = np.linalg.norm(np.array([landmarks[0].x * img_w, landmarks[0].y * img_h]) - 
                           np.array([landmarks[-1].x * img_w, landmarks[-1].y * img_h]))
        return (a + b) / (2.0 * c)
    except IndexError:
        return 1

# Variables for drowsiness and distraction detection
drowsy_start_time = None
DROWSY_THRESHOLD = 10  
last_sent_signal = None  
last_alert_time = 0  
ALERT_COOLDOWN = 5

# Open Laptop Webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip and Convert to RGB
    frame = cv2.flip(frame, 1)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_h, img_w, _ = frame.shape

    # Process Frame with MediaPipe
    results = face_mesh.process(img_rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # Calculate Eye Aspect Ratio (EAR)
            left_eye_ar = aspect_ratio([face_landmarks.landmark[i] for i in LEFT_EYE], img_w, img_h)
            right_eye_ar = aspect_ratio([face_landmarks.landmark[i] for i in RIGHT_EYE], img_w, img_h)
            avg_eye_ar = (left_eye_ar + right_eye_ar) / 2.0

            # Calculate Mouth Aspect Ratio (MAR) for yawning
            mouth_ar = aspect_ratio([face_landmarks.landmark[i] for i in MOUTH], img_w, img_h)

            # Drowsiness detection logic
            if avg_eye_ar < 0.22 or mouth_ar > 0.6:
                if drowsy_start_time is None:
                    drowsy_start_time = time.time()
                elif time.time() - drowsy_start_time > DROWSY_THRESHOLD:
                    if last_sent_signal != '1':
                        print("Drowsy! Sending signal to Arduino...")
                        arduino.write(b'1')  # Send '1' to Arduino to stop the motor
                        last_sent_signal = '1'
            else:
                drowsy_start_time = None
                if last_sent_signal != '0':
                    arduino.write(b'0')  # Send '0' to Arduino to resume normal operation
                    last_sent_signal = '0'

            # Distraction detection logic
            if time.time() - last_alert_time > ALERT_COOLDOWN:
                if not results.multi_face_landmarks:
                    print("Driver Distraction by using phone")
                    engine.say("Driver Distraction by using phone")
                    engine.runAndWait()
                    last_alert_time = time.time()

                # For simplicity, assume looking away if face landmarks are not centered
                face_center_x = np.mean([landmark.x for landmark in face_landmarks.landmark])
                if face_center_x < 0.3 or face_center_x > 0.7: 
                    print("Driver Distraction by looking away")
                    engine.say("Driver Distraction by looking away")
                    engine.runAndWait()
                    last_alert_time = time.time()

 
    cv2.imshow("Drowsiness and Distraction Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
arduino.close()
