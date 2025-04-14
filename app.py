from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import face_recognition
import pickle
import os
from datetime import datetime
from dotenv import load_dotenv
from win32com.client import Dispatch
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Environment configuration
ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = ENV == 'development'
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///votes.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Configure database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATABASE_PATH):
    os.makedirs(DATABASE_PATH)
CORS(app)

# Initialize video capture
video = None

def get_video_capture():
    if ENV == 'production':
        # Return a mock camera in production
        return None
    global video
    if video is None:
        video = cv2.VideoCapture(0)
    return video

def release_video():
    global video
    if video is not None:
        video.release()
        video = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/start-registration', methods=['POST'])
def start_registration():
    data = request.json
    aadhar = data.get('aadhar')
    
    if not os.path.exists('data/'):
        os.makedirs('data/')
    
    video = get_video_capture()
    facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces_data = []
    i = 0
    framesTotal = 51
    captureAfterFrame = 2
    
    while len(faces_data) < framesTotal:
        ret, frame = video.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facedetect.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            crop_img = frame[y:y+h, x:x+w]
            resized_img = cv2.resize(crop_img, (50, 50))
            if len(faces_data) <= framesTotal and i % captureAfterFrame == 0:
                faces_data.append(resized_img)
            i += 1
    
    faces_data = np.asarray(faces_data)
    faces_data = faces_data.reshape((framesTotal, -1))
    
    # Save the face data
    if 'names.pkl' not in os.listdir('data/'):
        names = [aadhar] * framesTotal
        with open('data/names.pkl', 'wb') as f:
            pickle.dump(names, f)
    else:
        with open('data/names.pkl', 'rb') as f:
            names = pickle.load(f)
        names = names + [aadhar] * framesTotal
        with open('data/names.pkl', 'wb') as f:
            pickle.dump(names, f)
    
    if 'faces_data.pkl' not in os.listdir('data/'):
        with open('data/faces_data.pkl', 'wb') as f:
            pickle.dump(faces_data, f)
    else:
        with open('data/faces_data.pkl', 'rb') as f:
            faces = pickle.load(f)
        faces = np.append(faces, faces_data, axis=0)
        with open('data/faces_data.pkl', 'wb') as f:
            pickle.dump(faces, f)
    
    return jsonify({"status": "success", "message": "Registration completed successfully"})

@app.route('/api/verify-and-vote', methods=['POST'])
def verify_and_vote():
    data = request.json
    vote = data.get('vote')
    
    video = get_video_capture()
    facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    with open('data/names.pkl', 'rb') as f:
        LABELS = pickle.load(f)
    
    with open('data/faces_data.pkl', 'rb') as f:
        FACES = pickle.load(f)
    
    from sklearn.neighbors import KNeighborsClassifier
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(FACES, LABELS)
    
    ret, frame = video.read()
    if not ret:
        return jsonify({"status": "error", "message": "Could not capture image"})
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)
    
    if len(faces) == 0:
        return jsonify({"status": "error", "message": "No face detected"})
    
    x, y, w, h = faces[0]
    crop_img = frame[y:y+h, x:x+w]
    resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
    output = knn.predict(resized_img)
    
    # Check if already voted
    if check_if_exists(output[0]):
        return jsonify({"status": "error", "message": "You have already voted"})
    
    # Record the vote
    ts = time.time()
    date = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
    timestamp = datetime.fromtimestamp(ts).strftime("%H:%M-%S")
    
    exist = os.path.isfile("Votes.csv")
    if exist:
        with open("Votes.csv", "a") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([output[0], vote, date, timestamp])
    else:
        with open("Votes.csv", "a") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['NAME', 'VOTE', 'DATE', 'TIME'])
            writer.writerow([output[0], vote, date, timestamp])
    
    return jsonify({"status": "success", "message": f"Vote recorded successfully for {vote}"})

def check_if_exists(value):
    try:
        with open("Votes.csv", "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row and row[0] == value:
                    return True
    except FileNotFoundError:
        return False
    return False

@app.route('/video_feed')
def video_feed():
    def generate():
        video = get_video_capture()
        while True:
            ret, frame = video.read()
            if not ret:
                break
            # Draw face detection rectangle
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = facedetect.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Convert frame to JPEG
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    release_video()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
