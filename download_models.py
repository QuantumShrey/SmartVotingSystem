import os
import requests

MODEL_URLS = {
    'ssd_mobilenetv1_model-weights_manifest.json': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/ssd_mobilenetv1_model-weights_manifest.json',
    'ssd_mobilenetv1_model-shard1': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/ssd_mobilenetv1_model-shard1',
    'face_landmark_68_model-weights_manifest.json': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-weights_manifest.json',
    'face_landmark_68_model-shard1': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_landmark_68_model-shard1',
    'face_recognition_model-weights_manifest.json': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-weights_manifest.json',
    'face_recognition_model-shard1': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-shard1',
    'face_recognition_model-shard2': 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/face_recognition_model-shard2'
}

def download_models():
    models_dir = os.path.join('static', 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    for filename, url in MODEL_URLS.items():
        print(f'Downloading {filename}...')
        response = requests.get(url)
        with open(os.path.join(models_dir, filename), 'wb') as f:
            f.write(response.content)
        print(f'Downloaded {filename}')

if __name__ == '__main__':
    download_models()
