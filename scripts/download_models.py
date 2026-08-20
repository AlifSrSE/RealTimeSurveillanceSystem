import os
import urllib.request

MODELS_DIR = "models"

MODELS = {
    "MobileNetSSD_deploy.prototxt": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
    "MobileNetSSD_deploy.caffemodel": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
    "age_deploy.prototxt": "https://github.com/opencv/opencv_3rdparty/raw/age_gender_models/age_deploy.prototxt",
    "age_net.caffemodel": "https://github.com/opencv/opencv_3rdparty/raw/age_gender_models/age_net.caffemodel",
    "gender_deploy.prototxt": "https://github.com/opencv/opencv_3rdparty/raw/age_gender_models/gender_deploy.prototxt",
    "gender_net.caffemodel": "https://github.com/opencv/opencv_3rdparty/raw/age_gender_models/gender_net.caffemodel",
}

def download_models():
    os.makedirs(MODELS_DIR, exist_ok=True)
    for filename, url in MODELS.items():
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            print(f"[skip] {filename} already exists")
            continue
        print(f"[download] {filename} from {url}")
        try:
            urllib.request.urlretrieve(url, path)
            print(f"[ok] saved to {path}")
        except Exception as e:
            print(f"[error] failed to download {filename}: {e}")
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    download_models()
