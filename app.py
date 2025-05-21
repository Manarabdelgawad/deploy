from fastapi import FastAPI, File, UploadFile, HTTPException
import cv2
import numpy as np
from ultralytics import YOLO
from io import BytesIO
from PIL import Image
import os
import gdown
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Space Debris Detection API")

# Load the YOLO model
model_path = "train_yolo9_v1/weights/best.pt"  # Updated path with forward slashes
model = None

async def load_model():
    global model
    try:
        # Download model from Google Drive if not present
        if not os.path.exists(model_path):
            logger.info(f"Model not found at {model_path}, attempting to download...")
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            model_url = os.getenv("MODEL_URL")
            if not model_url:
                raise ValueError("MODEL_URL environment variable is not set")
            logger.info(f"Downloading model from {model_url}")
            gdown.download(model_url, model_path, quiet=False)
            
        logger.info(f"Loading model from {model_path}")
        model = YOLO(model_path)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@app.on_event("startup")
async def startup_event():
    await load_model()

@app.post("/detect", summary="Detect space debris in an image and decide satellite movement")
async def detect_objects(file: UploadFile = File(...)):
    try:
        # Check if model is loaded
        if model is None:
            logger.error("Model not loaded")
            raise HTTPException(status_code=500, detail="Model not loaded. Please try again later.")

        # Validate file type
        if not file.content_type.startswith("image/"):
            logger.warning(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image (PNG, JPEG, etc.)")

        # Check file size (limit to 10MB)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB
            logger.warning(f"File too large: {len(contents)} bytes")
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB")

        logger.info("Processing image...")
        image = np.array(Image.open(BytesIO(contents)))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # Convert to BGR for OpenCV

        # Run detection
        logger.info("Running object detection...")
        results = model(image)
        object_info = []

        img_height, img_width = image.shape[:2]
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                width = x2 - x1
                height = y2 - y1
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                # Determine position
                horizontal_dir = "center"
                if center_x < img_width / 3:
                    horizontal_dir = "left"
                elif center_x > 2 * img_width / 3:
                    horizontal_dir = "right"

                vertical_dir = "middle"
                if center_y < img_height / 3:
                    vertical_dir = "top"
                elif center_y > 2 * img_height / 3:
                    vertical_dir = "bottom"

                position = "center" if horizontal_dir == "center" and vertical_dir == "middle" else f"{vertical_dir}-{horizontal_dir}"

                object_info.append({
                    "class_id": int(box.cls),
                    "class_name": model.names[int(box.cls)],
                    "width": width,
                    "height": height,
                    "center_x": center_x,
                    "center_y": center_y,
                    "position": position
                })

        # Decide satellite movement
        def decide_satellite_movement(objects):
            if not objects:
                return "No objects detected, stay in position"
            for obj in objects:
                if "left" in obj['position']:
                    return "Move satellite right"
                elif "right" in obj['position']:
                    return "Move satellite left"
            for obj in objects:
                if obj['position'] == "center":
                    return "Move satellite slightly right"
            return "Stay in position"

        decision = decide_satellite_movement(object_info)

        return {
            "objects": object_info,
            "decision": decision
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/", summary="API root endpoint")
async def root():
    return {"message": "Space Debris Detection API"}