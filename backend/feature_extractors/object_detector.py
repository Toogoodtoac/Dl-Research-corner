"""
Object detection for video frames
"""

from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()


class ObjectDetector:
    """Object detection using OpenCV DNN or lightweight alternatives"""

    def __init__(self, model_type: str = "opencv", confidence_threshold: float = 0.5):
        self.model_type = model_type
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.class_names = []

        # COCO class names (simplified)
        self.coco_classes = [
            "person",
            "bicycle",
            "car",
            "motorcycle",
            "airplane",
            "bus",
            "train",
            "truck",
            "boat",
            "traffic light",
            "fire hydrant",
            "stop sign",
            "parking meter",
            "bench",
            "bird",
            "cat",
            "dog",
            "horse",
            "sheep",
            "cow",
            "elephant",
            "bear",
            "zebra",
            "giraffe",
            "backpack",
            "umbrella",
            "handbag",
            "tie",
            "suitcase",
            "frisbee",
            "skis",
            "snowboard",
            "sports ball",
            "kite",
            "baseball bat",
            "baseball glove",
            "skateboard",
            "surfboard",
            "tennis racket",
            "bottle",
            "wine glass",
            "cup",
            "fork",
            "knife",
            "spoon",
            "bowl",
            "banana",
            "apple",
            "sandwich",
            "orange",
            "broccoli",
            "carrot",
            "hot dog",
            "pizza",
            "donut",
            "cake",
            "chair",
            "couch",
            "potted plant",
            "bed",
            "dining table",
            "toilet",
            "tv",
            "laptop",
            "mouse",
            "remote",
            "keyboard",
            "cell phone",
            "microwave",
            "oven",
            "toaster",
            "sink",
            "refrigerator",
            "book",
            "clock",
            "vase",
            "scissors",
            "teddy bear",
            "hair drier",
            "toothbrush",
        ]

        self._load_model()

    def _load_model(self):
        """Load object detection model"""
        try:
            if self.model_type == "opencv":
                # Try to load OpenCV DNN model
                model_path = "models/yolov4.weights"
                config_path = "models/yolov4.cfg"

                if not (
                    cv2.os.path.exists(model_path) and cv2.os.path.exists(config_path)
                ):
                    logger.warning("YOLO model files not found, using mock detection")
                    self.model = "mock"
                else:
                    self.model = cv2.dnn.readNetFromDarknet(config_path, model_path)
                    self.class_names = self.coco_classes
                    logger.info("Loaded YOLO model for object detection")
            else:
                self.model = "mock"
                logger.info("Using mock object detection")

        except Exception as e:
            logger.warning(f"Failed to load object detection model: {e}")
            self.model = "mock"

    def detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """Detect objects in a frame"""
        if self.model == "mock":
            return self._mock_detection(frame)
        elif self.model_type == "opencv":
            return self._opencv_detection(frame)
        else:
            return []

    def _mock_detection(self, frame: np.ndarray) -> List[Dict]:
        """Mock object detection for testing"""
        height, width = frame.shape[:2]

        # Generate some mock detections
        mock_objects = []

        # Mock person detection
        if np.random.random() > 0.3:
            mock_objects.append(
                {
                    "bbox": [width * 0.1, height * 0.2, width * 0.3, height * 0.8],
                    "class_id": 0,
                    "class_name": "person",
                    "confidence": 0.85,
                }
            )

        # Mock car detection
        if np.random.random() > 0.5:
            mock_objects.append(
                {
                    "bbox": [width * 0.6, height * 0.6, width * 0.9, height * 0.9],
                    "class_id": 2,
                    "class_name": "car",
                    "confidence": 0.78,
                }
            )

        # Mock chair detection
        if np.random.random() > 0.7:
            mock_objects.append(
                {
                    "bbox": [width * 0.4, height * 0.5, width * 0.6, height * 0.7],
                    "class_id": 56,
                    "class_name": "chair",
                    "confidence": 0.72,
                }
            )

        return mock_objects

    def _opencv_detection(self, frame: np.ndarray) -> List[Dict]:
        """OpenCV DNN object detection"""
        if self.model is None:
            return []

        height, width = frame.shape[:2]

        # Prepare input blob
        blob = cv2.dnn.blobFromImage(
            frame, 1 / 255.0, (416, 416), swapRB=True, crop=False
        )
        self.model.setInput(blob)

        # Get detections
        layer_names = self.model.getLayerNames()
        output_layers = [
            layer_names[i - 1] for i in self.model.getUnconnectedOutLayers()
        ]
        outputs = self.model.forward(output_layers)

        # Process outputs
        boxes = []
        confidences = []
        class_ids = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > self.confidence_threshold:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # Apply non-maximum suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, 0.4)

        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                results.append(
                    {
                        "bbox": [x, y, x + w, y + h],  # [x1, y1, x2, y2]
                        "class_id": class_ids[i],
                        "class_name": (
                            self.class_names[class_ids[i]]
                            if class_ids[i] < len(self.class_names)
                            else f"class_{class_ids[i]}"
                        ),
                        "confidence": confidences[i],
                    }
                )

        return results

    def get_dominant_objects(
        self, frame: np.ndarray, max_objects: int = 5
    ) -> List[Dict]:
        """Get dominant objects in frame (highest confidence)"""
        detections = self.detect_objects(frame)

        # Sort by confidence and limit results
        detections.sort(key=lambda x: x["confidence"], reverse=True)
        return detections[:max_objects]

    def filter_by_class(
        self, detections: List[Dict], class_names: List[str]
    ) -> List[Dict]:
        """Filter detections by class names"""
        return [d for d in detections if d["class_name"] in class_names]

    def get_bbox_center(self, bbox: List[float]) -> Tuple[float, float]:
        """Get center point of bounding box"""
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return center_x, center_y

    def get_bbox_area(self, bbox: List[float]) -> float:
        """Get area of bounding box"""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
