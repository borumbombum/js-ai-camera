import cv2
import numpy as np
from ultralytics import YOLO
from dataclasses import dataclass
from typing import List, Optional

COLORS = {
    'person': (255, 0, 0),
    'car': (0, 255, 0),
    'truck': (0, 255, 0),
    'bus': (0, 255, 0),
    'motorcycle': (0, 255, 0),
    'bicycle': (0, 255, 0),
    'dog': (165, 42, 42),
    'cat': (165, 42, 42),
    'bird': (135, 206, 235),
    'default': (0, 255, 255),
}

@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: tuple

class ObjectDetector:
    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model = YOLO(model_name)
        self.class_names = self.model.names
        
    def detect(self, frame: np.ndarray) -> List[Detection]:
        results = self.model(frame, verbose=False)[0]
        detections = []
        
        for box in results.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            detection = Detection(
                class_name=self.class_names[class_id],
                confidence=confidence,
                bbox=(x1, y1, x2, y2)
            )
            detections.append(detection)
            
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        output = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = COLORS.get(det.class_name.lower(), COLORS['default'])
            
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            label = f"{det.class_name} {det.confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(output, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
            cv2.putText(output, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
        return output
    
    def get_person_detections(self, detections: List[Detection]) -> List[Detection]:
        return [d for d in detections if d.class_name.lower() == 'person']
