# Smart Voting System

A secure face recognition-based voting system built with Python Flask and OpenCV.

## Features

- Face recognition-based voter registration
- Secure voting process with face verification
- Real-time video feed for registration and voting
- User-friendly interface
- Vote tracking and duplicate vote prevention

## Prerequisites

- Python 3.8 or higher
- Webcam
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/adarshyadav0906/SmartVotingSystem.git
cd SmartVotingSystem
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create necessary directories:
```bash
mkdir data
```

## Usage

1. Start the server:
```bash
python app.py
```

2. Open a web browser and navigate to:
```
http://localhost:5000
```

3. Register as a voter:
   - Click on "Register" in the navigation
   - Enter your 12-digit Aadhar number
   - Look at the camera and follow the instructions
   - Wait for registration confirmation

4. Cast your vote:
   - Click on "Vote" in the navigation
   - Look at the camera for verification
   - Press the number key (1-4) corresponding to your choice
   - Wait for vote confirmation

## Security Features

- Face recognition for voter verification
- One vote per registered voter
- Secure storage of voter data
- Real-time face detection and verification

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
