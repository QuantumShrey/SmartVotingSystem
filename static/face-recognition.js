let isModelLoaded = false;
let faceDescriptors = [];

// Load face-api models
async function loadModels() {
    try {
        await Promise.all([
            faceapi.nets.ssdMobilenetv1.loadFromUri('/static/models'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/static/models')
        ]);
        isModelLoaded = true;
        console.log('Face detection models loaded');
    } catch (error) {
        console.error('Error loading models:', error);
    }
}

// Start webcam
async function startWebcam(videoElement) {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoElement.srcObject = stream;
        return true;
    } catch (error) {
        console.error('Error accessing webcam:', error);
        return false;
    }
}

// Detect faces in video stream
async function detectFaces(videoElement, canvasElement, statusElement) {
    if (!isModelLoaded) {
        statusElement.textContent = 'Loading face detection models...';
        return;
    }

    const displaySize = { width: videoElement.width, height: videoElement.height };
    faceapi.matchDimensions(canvasElement, displaySize);

    setInterval(async () => {
        const detections = await faceapi.detectAllFaces(videoElement)
            .withFaceLandmarks()
            .withFaceDescriptors();

        const resizedDetections = faceapi.resizeResults(detections, displaySize);
        canvasElement.getContext('2d').clearRect(0, 0, canvasElement.width, canvasElement.height);

        if (resizedDetections.length > 0) {
            faceapi.draw.drawDetections(canvasElement, resizedDetections);
            statusElement.textContent = 'Face detected';
        } else {
            statusElement.textContent = 'No face detected';
        }
    }, 100);
}

// Register new face
async function registerFace(videoElement, aadharNumber) {
    if (!isModelLoaded) return null;

    const detection = await faceapi.detectSingleFace(videoElement)
        .withFaceLandmarks()
        .withFaceDescriptor();

    if (detection) {
        const faceData = {
            descriptor: Array.from(detection.descriptor),
            aadharNumber: aadharNumber
        };

        // Send to server
        const response = await fetch('/register_face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(faceData)
        });

        return response.ok;
    }

    return false;
}

// Verify face for voting
async function verifyFace(videoElement) {
    if (!isModelLoaded) return null;

    const detection = await faceapi.detectSingleFace(videoElement)
        .withFaceLandmarks()
        .withFaceDescriptor();

    if (detection) {
        const faceDescriptor = Array.from(detection.descriptor);
        
        // Send to server for verification
        const response = await fetch('/verify_face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ descriptor: faceDescriptor })
        });

        return await response.json();
    }

    return null;
}

// Initialize face recognition
document.addEventListener('DOMContentLoaded', async () => {
    await loadModels();

    // Setup voting video
    const voteVideo = document.getElementById('video-feed');
    const voteCanvas = document.getElementById('face-overlay');
    const voteStatus = document.getElementById('webcam-status');
    if (voteVideo) {
        await startWebcam(voteVideo);
        detectFaces(voteVideo, voteCanvas, voteStatus);
    }

    // Setup registration video
    const regVideo = document.getElementById('reg-video-feed');
    const regCanvas = document.getElementById('reg-face-overlay');
    const regStatus = document.getElementById('reg-webcam-status');
    if (regVideo) {
        await startWebcam(regVideo);
        detectFaces(regVideo, regCanvas, regStatus);
    }
});
