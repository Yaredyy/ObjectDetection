from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
import cv2
import numpy as np
import uvicorn
import logging
import os
from ultralytics import YOLO
from io import BytesIO

import gdown

app = FastAPI()


model_url = "https://drive.google.com/uc?id=1OUhPbZ8VWLevKmG44F09gQpiQN0F-Pk1"
model_path = 'yolov5su.pt'


def download_model():
    print("Downloading model weights from Google Drive using gdown...")
    gdown.download(model_url, model_path, quiet=False)
    print("Download complete.")

if not os.path.exists(model_path):
    download_model()


# Load the model
try:
    model = YOLO(model_path)
except Exception as e:
    logging.error(f"Error loading YOLOv5 model: {e}")
    model = None 

#objects
class_names = {
    0: "Person",
    1: "Bicycle",
    2: "Car",
    3: "Motorcycle",
    4: "Airplane",
    5: "Bus",
    6: "Train",
    7: "Truck",
    8: "Boat",
    9: "Traffic Light",
    10: "Fire Hydrant",
    11: "Stop Sign",
    12: "Parking Meter",
    13: "Bench",
    14: "Bird",
    15: "Cat",
    16: "Dog",
    17: "Horse",
    18: "Sheep",
    19: "Cow",
    20: "Elephant",
    21: "Bear",
    22: "Zebra",
    23: "Giraffe",
    24: "Backpack",
    25: "Umbrella",
    26: "Handbag",
    27: "Tie",
    28: "Suitcase",
    29: "Frisbee",
    30: "Skis",
    31: "Snowboard",
    32: "Sports Ball",
    33: "Kite",
    34: "Baseball Bat",
    35: "Baseball Glove",
    36: "Skateboard",
    37: "Surfboard",
    38: "Tennis Racket",
    39: "Bottle",
    40: "Wine Glass",
    41: "Cup",
    42: "Fork",
    43: "Knife",
    44: "Spoon",
    45: "Bowl",
    46: "Banana",
    47: "Apple",
    48: "Sandwich",
    49: "Orange",
    50: "Broccoli",
    51: "Carrot",
    52: "Hot Dog",
    53: "Pizza",
    54: "Donut",
    55: "Cake",
    56: "Chair",
    57: "Couch",
    58: "Potted Plant",
    59: "Bed",
    60: "Dining Table",
    61: "Toilet",
    62: "TV",
    63: "Laptop",
    64: "Mouse",
    65: "Remote",
    66: "Keyboard",
    67: "Cell Phone",
    68: "Microwave",
    69: "Oven",
    70: "Toaster",
    71: "Sink",
    72: "Refrigerator",
    73: "Book",
    74: "Clock",
    75: "Vase",
    76: "Scissors",
    77: "Teddy Bear",
    78: "Hair Drier",
    79: "Toothbrush"
}


# Define function to process images and detect objects
def detect_objects(image: np.ndarray):
    if model is None:
        logging.error("Model is not loaded. Cannot perform detection.")
        return []

    results = model(image)  # Automatically handles pre-processing and runs inference

    detected_objects = []
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)

        for box, confidence, class_id in zip(boxes, confidences, class_ids):
            if confidence > 0.5:  # Only consider objects with confidence above 50%
                detected_objects.append({
                    'class_id': int(class_id),
                    'confidence': float(confidence),
                    'box': box.tolist()
                })

    return detected_objects


# Function to draw bounding boxes on the image
def draw_bounding_boxes(image: np.ndarray, detections):
    for detection in detections:
        box = detection['box']
        class_id = detection['class_id']
        class_name = class_names.get(class_id, "Unknown")  # Use the class name or "Unknown"
        label = f"{class_name}: {detection['confidence']:.2f}"
        # Draw rectangle
        cv2.rectangle(image, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)
        # Put label with larger font size
        cv2.putText(image, label, (int(box[0]), int(box[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1, 4, 2)

    return image


# API route to upload an image and get detected objects
@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    detections = detect_objects(image)
    
    output_image = draw_bounding_boxes(image, detections)
    
    _, buffer = cv2.imencode('.jpg', output_image)
    image_stream = BytesIO(buffer)

    return StreamingResponse(image_stream, media_type="image/jpeg")


# Route to serve the HTML file
@app.get("/", response_class=HTMLResponse)
async def get_html():
    with open("index.html", "r") as f:
        return f.read()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
