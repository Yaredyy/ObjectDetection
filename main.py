# FastAPI main.py
from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
from io import BytesIO
import torch
import uvicorn
import logging

app = FastAPI()

# Load model safely
MODEL_PATH = "yolov5su.pt"
try:
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=MODEL_PATH)
except Exception as e:
    model = None
    print(f"Error loading model: {e}")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded correctly."}
    
    contents = await file.read()
    image = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    
    results = model(image)
    results.render()
    
    _, encoded_img = cv2.imencode('.jpg', image)
    return {"message": "Success", "image": encoded_img.tobytes()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)