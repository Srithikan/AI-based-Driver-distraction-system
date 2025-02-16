import cv2
import dlib
import numpy as np
import pyttsx3
import csv
import time
from datetime import datetime
from scipy.spatial import distance
from ultralytics import YOLO
from twilio.rest import Client
import requests 


engine = pyttsx3.init()


TWILIO_ACCOUNT_SID = 'ACc9b45ba4ed0a682fd30806fd152ad425'
TWILIO_AUTH_TOKEN = '1ec609e47e7a468a471c5898dff167aa'
TWILIO_PHONE_NUMBER = '+16205632285'
RECIPIENT_PHONE_NUMBER = '+91 6381920315'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def get_location():
    try:
        ip_response = requests.get('https://api.ipify.org?format=json')
        ip_address = ip_response.json()['ip']
        location_response = requests.get(f'https://ipapi.co/{ip_address}/json/')
        location_data = location_response.json()
        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')
        city = location_data.get('city', 'Unknown City')
        region = location_data.get('region', 'Unknown Region')
        country = location_data.get('country_name', 'Unknown Country')
        return latitude, longitude, f"{city}, {region}, {country}"
    except Exception as e:
        print(f"Error getting location: {e}")
        return None, None, "Location unavailable"


EAR_THRESHOLD = 0.25
DROWSY_ALERT_INTERVAL = 5
DROWSY_DETECTION_TIME = 60
HEAD_TURN_THRESHOLD = 100
PHONE_CONFIDENCE_THRESHOLD = 0.5

face_cascade_path = "haarcascade_frontalface_default.xml"
landmarks_path = "shape_predictor_68_face_landmarks.dat"

face_cascade = cv2.CascadeClassifier(face_cascade_path)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(landmarks_path)

model = YOLO("yolov8n.pt")

LEFT_EYE_POINTS = list(range(36, 42))
RIGHT_EYE_POINTS = list(range(42, 48))

csv_file_path = "driver_monitoring_log.csv"
header = ['Timestamp', 'Activity', 'Details']
try:
    with open(csv_file_path, 'x', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
except FileExistsError:
    pass

cap = cv2.VideoCapture(0)
drowsy_start_time = None
last_alert_time = None
phone_detection_time = None
head_turn_time = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    face_rects = face_cascade.detectMultiScale(gray, 1.1, 4)

    results = model(frame)
    current_time = time.time()
    
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if (confidence > PHONE_CONFIDENCE_THRESHOLD and 
                model.names[class_id] == "cell phone"):
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, "Phone Detected", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)


                if phone_detection_time is None or current_time - phone_detection_time > 10:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(csv_file_path, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([timestamp, "Phone Usage", "Driver distracted by phone"])

                    engine.say("Driver distraction by phone")
                    engine.runAndWait()
                    phone_detection_time = current_time


    for face in faces:
        landmarks = predictor(gray, face)
        left_eye = np.array([[landmarks.part(n).x, landmarks.part(n).y] for n in LEFT_EYE_POINTS])
        right_eye = np.array([[landmarks.part(n).x, landmarks.part(n).y] for n in RIGHT_EYE_POINTS])

        avg_ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0


        for (x, y, w, h) in face_rects:
            face_center = (x + w // 2, y + h // 2)
            frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)

            if abs(face_center[0] - frame_center[0]) > HEAD_TURN_THRESHOLD:
                if head_turn_time is None or current_time - head_turn_time > 10:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(csv_file_path, 'a', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([timestamp, "Head Turned Away", "Driver looking away"])

                    engine.say("Driver distraction by looking away")
                    engine.runAndWait()
                    head_turn_time = current_time

        if avg_ear < EAR_THRESHOLD:
            if drowsy_start_time is None:
                drowsy_start_time = current_time
                last_alert_time = current_time

            if current_time - last_alert_time >= DROWSY_ALERT_INTERVAL:
                engine.say("Driver drowsy, wake up!")
                engine.runAndWait()
                last_alert_time = current_time

            if current_time - drowsy_start_time >= DROWSY_DETECTION_TIME:
                latitude, longitude, location = get_location()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(csv_file_path, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([timestamp, "Drowsiness", "Driver drowsy for more than 1 minute"])


                call = client.calls.create(
                    twiml='<Response><Say>Attention! The driver of the vehicle appears to be drowsy and unresponsive.</Say></Response>',
                    to=RECIPIENT_PHONE_NUMBER,
                    from_=TWILIO_PHONE_NUMBER
                )
                print(f"Call initiated: {call.sid}")

                if latitude and longitude:
                    google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                    message_body = f"Driver is drowsy for more than 1 minute. Location: {location}. Google Maps: {google_maps_link}"
                else:
                    message_body = f"Driver is drowsy for more than 1 minute. Location: {location}"

                message = client.messages.create(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=RECIPIENT_PHONE_NUMBER
                )
                print(f"SMS sent: {message.sid}")

                drowsy_start_time = None
                last_alert_time = None
        else:

            drowsy_start_time = None
            last_alert_time = None

    cv2.imshow("Driver Monitoring System", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
