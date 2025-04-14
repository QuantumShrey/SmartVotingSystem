from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import pickle
import os
import time
import csv
from datetime import datetime
from dotenv import load_dotenv
from flask_cors import CORS
import sys
import logging

# Load environment variables
load_dotenv()

# Environment configuration
ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = ENV == 'development'
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)

# Configure database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATABASE_PATH):
    os.makedirs(DATABASE_PATH)

# Initialize video capture
video = None

def get_video_capture():
    global video
    if video is None:
        try:
            video = cv2.VideoCapture(0)
            if not video.isOpened():
                print("Failed to open camera 0, trying camera 1")
                video.release()
                video = cv2.VideoCapture(1)
                
            if not video.isOpened():
                print("Error: Could not open any camera")
                return None
                
            # Set smaller resolution for better performance
            video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            print("Successfully opened camera")
        except Exception as e:
            print(f"Error initializing camera: {str(e)}")
            if video is not None:
                video.release()
                video = None
            return None
    return video

def release_video():
    global video
    if video:
        video.release()
        video = None

def generate_frames():
    # Load the pre-trained face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    while True:
        video = get_video_capture()
        if not video:
            break
            
        success, frame = video.read()
        if not success:
            break
        else:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Convert frame to jpg
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/start-registration', methods=['POST'])
def start_registration():
    try:
        data = request.json
        if not data or 'aadhar' not in data:
            return jsonify({'error': 'Aadhar number is required'}), 400

        aadhar = data.get('aadhar')
        if not aadhar or len(str(aadhar)) != 12:
            return jsonify({'error': 'Invalid Aadhar number'}), 400

        # Create data directory if it doesn't exist
        if not os.path.exists('data/'):
            os.makedirs('data/')

        # Get video capture
        video = get_video_capture()
        if video is None:
            return jsonify({'error': 'Could not access camera'}), 500

        try:
            facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces_data = []
            i = 0
            framesTotal = 10  # Reduced number of frames for faster registration
            attempts = 0
            max_attempts = 50  # Maximum attempts to capture all frames

            while len(faces_data) < framesTotal and attempts < max_attempts:
                ret, frame = video.read()
                if not ret:
                    return jsonify({'error': 'Could not read from camera'}), 500

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = facedetect.detectMultiScale(gray, 1.3, 5)

                if len(faces) > 0:
                    x, y, w, h = faces[0]  # Take the first detected face
                    crop_img = frame[y:y+h, x:x+w]
                    resized_img = cv2.resize(crop_img, (50, 50))
                    faces_data.append(resized_img)
                    i += 1
                attempts += 1

            if len(faces_data) < framesTotal:
                return jsonify({'error': 'Could not capture enough face images. Please ensure your face is clearly visible.'}), 400

            faces_data = np.asarray(faces_data)
            faces_data = faces_data.reshape((len(faces_data), -1))

            # Save the face data
            if 'names.pkl' not in os.listdir('data/'):
                names = [aadhar] * len(faces_data)
                with open('data/names.pkl', 'wb') as f:
                    pickle.dump(names, f)
            else:
                with open('data/names.pkl', 'rb') as f:
                    names = pickle.load(f)
                names = names + [aadhar] * len(faces_data)
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

            return jsonify({'success': True, 'message': 'Registration successful'})

        finally:
            if video is not None:
                video.release()

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    return jsonify({"status": "success", "message": "Registration completed successfully"})

@app.route('/api/verify-and-vote', methods=['POST'])
def verify_and_vote():
    try:
        data = request.json
        if not data or 'vote' not in data:
            return jsonify({"error": "Vote choice is required"}), 400
        
        vote = data.get('vote')
        
        # Check if data files exist
        if not os.path.exists('data/names.pkl') or not os.path.exists('data/faces_data.pkl'):
            return jsonify({"error": "No registered voters found. Please register first."}), 400

        # Initialize video capture
        video = get_video_capture()
        if video is None:
            return jsonify({"error": "Could not access camera"}), 500

        try:
            # Load face detection model
            facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Load training data
            with open('data/names.pkl', 'rb') as f:
                LABELS = pickle.load(f)
            
            with open('data/faces_data.pkl', 'rb') as f:
                FACES = pickle.load(f)
            
            # Initialize and train KNN classifier
            from sklearn.neighbors import KNeighborsClassifier
            knn = KNeighborsClassifier(n_neighbors=5)
            knn.fit(FACES, LABELS)
            
            # Capture and process frame
            ret, frame = video.read()
            if not ret:
                return jsonify({"error": "Could not capture image from camera"}), 500
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = facedetect.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return jsonify({"error": "No face detected. Please look at the camera."}), 400
            
            # Process the detected face
            x, y, w, h = faces[0]
            crop_img = frame[y:y+h, x:x+w]
            resized_img = cv2.resize(crop_img, (50, 50)).flatten().reshape(1, -1)
            
            # Predict identity
            output = knn.predict(resized_img)
            
            # Check if already voted
            if check_if_exists(output[0]):
                return jsonify({"error": "You have already voted"}), 400
            
            # Record the vote
            try:
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
                
                return jsonify({"success": True, "message": f"Vote recorded successfully for {vote}"})
            
            except Exception as e:
                print(f"Error recording vote: {str(e)}")
                return jsonify({"error": "Error recording vote"}), 500
                
        finally:
            if video is not None:
                video.release()
                
    except Exception as e:
        print(f"Error in verify_and_vote: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
        global video
        try:
            # Initialize camera
            video = get_video_capture()
            if video is None:
                print("Could not initialize camera")
                return

            while True:
                ret, frame = video.read()
                if not ret:
                    print("Error: Could not read frame")
                    break

                try:
                    # Draw face detection rectangle
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    faces = facedetect.detectMultiScale(gray, 1.3, 5)
                    
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Convert frame to JPEG
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if not ret:
                        print("Error: Could not encode frame")
                        break
                        
                    frame_bytes = jpeg.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except Exception as e:
                    print(f"Error processing frame: {str(e)}")
                    break

        except Exception as e:
            print(f"Error in video feed: {str(e)}")
        finally:
            if video is not None:
                video.release()
                video = None

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    release_video()
    return jsonify({"status": "success"})

@app.route('/register_face', methods=['POST'])
def register_face():
    data = request.json
    if not data or 'aadharNumber' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        video = get_video_capture()
        if not video:
            return jsonify({'error': 'Camera not available'}), 500

        # Load face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Capture frame and detect face
        ret, frame = video.read()
        if not ret:
            return jsonify({'error': 'Failed to capture image'}), 500

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return jsonify({'error': 'No face detected'}), 400

        # Get the first face
        x, y, w, h = faces[0]
        face_img = gray[y:y+h, x:x+w]
        
        # Resize face image to standard size
        face_img = cv2.resize(face_img, (100, 100))
        
        # Save face image and Aadhar number
        face_data = {
            'face_features': face_img.flatten().tolist(),
            'aadhar_number': data['aadharNumber']
        }
        
        # Save to pickle file
        faces_file = os.path.join(DATABASE_PATH, 'faces_data.pkl')
        faces = []
        if os.path.exists(faces_file):
            with open(faces_file, 'rb') as f:
                faces = pickle.load(f)
        
        faces.append(face_data)
        with open(faces_file, 'wb') as f:
            pickle.dump(faces, f)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify_face', methods=['POST'])
def verify_face():
    try:
        video = get_video_capture()
        if not video:
            return jsonify({'error': 'Camera not available'}), 500

        # Load face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # Capture frame and detect face
        ret, frame = video.read()
        if not ret:
            return jsonify({'error': 'Failed to capture image'}), 500

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return jsonify({'error': 'No face detected'}), 400

        # Get the first face
        x, y, w, h = faces[0]
        face_img = gray[y:y+h, x:x+w]
        
        # Resize face image to standard size
        face_img = cv2.resize(face_img, (100, 100))
        current_features = face_img.flatten()

        # Load saved face data
        faces_file = os.path.join(DATABASE_PATH, 'faces_data.pkl')
        if not os.path.exists(faces_file):
            return jsonify({'error': 'No registered faces found'}), 404

        with open(faces_file, 'rb') as f:
            faces = pickle.load(f)

        # Compare with saved faces using simple Euclidean distance
        min_distance = float('inf')
        matched_aadhar = None

        for face in faces:
            saved_features = np.array(face['face_features'])
            distance = np.linalg.norm(current_features - saved_features)
            
            if distance < min_distance:
                min_distance = distance
                matched_aadhar = face['aadhar_number']

        # If the minimum distance is below threshold, consider it a match
        if min_distance < 5000:  # Adjust this threshold as needed
            return jsonify({
                'success': True,
                'aadhar_number': matched_aadhar
            })

        return jsonify({'success': False, 'error': 'No matching face found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
