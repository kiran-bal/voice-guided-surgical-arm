"""
Camera Service for object detection.
Uses OpenCV to detect objects and returns detection results.
"""

import logging
from typing import Dict, Optional, Any
import cv2
import numpy as np

from ..config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraService:
    """Service for camera-based object detection."""
    
    def __init__(self):
        """Initialize the camera service."""
        self.use_camera = Config.USE_CAMERA
        self.camera_index = 2  # Default camera index from reference code
        
        # Camera detection parameters
        self.detection_distance = Config.CAMERA_DETECTION_DISTANCE
        self.detection_height = Config.CAMERA_DETECTION_HEIGHT
        self.height_tolerance = Config.CAMERA_HEIGHT_TOLERANCE
        self.distance_tolerance = Config.CAMERA_DISTANCE_TOLERANCE
        self.pixels_per_cm = Config.CAMERA_PIXELS_PER_CM
        
        # Color detection parameters
        self.detect_color = Config.CAMERA_DETECT_COLOR
        self.color_lower_hsv = self._parse_hsv_string(Config.CAMERA_COLOR_LOWER_HSV)
        self.color_upper_hsv = self._parse_hsv_string(Config.CAMERA_COLOR_UPPER_HSV)
        
        # Detection mode parameters
        self.detection_mode = Config.CAMERA_DETECTION_MODE
        self.color_only_min_area = Config.CAMERA_COLOR_ONLY_MIN_AREA
        
        if self.use_camera:
            logger.info("✅ Camera Service initialized with camera enabled")
            logger.info(f"   - Detection Distance: {self.detection_distance} cm")
            logger.info(f"   - Detection Height: {self.detection_height} cm")
            logger.info(f"   - Height Tolerance: {self.height_tolerance} cm")
            logger.info(f"   - Distance Tolerance: {self.distance_tolerance} cm")
            logger.info(f"   - Detect Color: {self.detect_color}")
            logger.info(f"   - Color HSV Range: {self.color_lower_hsv} - {self.color_upper_hsv}")
            logger.info(f"   - Detection Mode: {self.detection_mode}")
            if self.detection_mode == 'color_only':
                logger.info(f"   - Color-Only Min Area: {self.color_only_min_area}")
        else:
            logger.info("✅ Camera Service initialized in test mode (camera disabled)")
    
    def detect_object(self, pixels_per_cm: Optional[float] = None) -> Dict[str, Any]:
        """
        Detect objects using camera or return dummy data.
        Checks for green objects at specified distance and height.
        
        Args:
            pixels_per_cm: Optional calibration factor for height measurement
            
        Returns:
            Dictionary containing detection results with distance and height validation
        """
        if not self.use_camera:
            logger.info("📷 Camera disabled - returning dummy detection data")
            return {
                "object_detected": False,
                "height": None,
                "distance": None,
                "height_match": False,
                "distance_match": False,
                "mode": "test"
            }
        
        try:
            logger.info("📷 Starting object detection...")
            
            # Initialize camera
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                logger.error(f"❌ Could not open camera at index {self.camera_index}")
                return {
                    "object_detected": False,
                    "height": None,
                    "error": f"Could not open camera at index {self.camera_index}"
                }
            
            # Capture frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error("❌ Failed to capture image from camera")
                return {
                    "object_detected": False,
                    "height": None,
                    "error": "Failed to capture image from camera"
                }
            
            # Process frame for object detection
            result = self._process_frame(frame, pixels_per_cm)
            
            # Validate based on detection mode
            if self.detection_mode == 'color_only':
                result = self._validate_color_only_detection(result)
            else:
                result = self._validate_detection(result)
            
            logger.info(f"✅ Object detection completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Camera detection error: {e}")
            return {
                "object_detected": False,
                "height": None,
                "error": f"Camera detection error: {str(e)}"
            }
    
    def _process_frame(self, frame: np.ndarray, pixels_per_cm: Optional[float] = None) -> Dict[str, Any]:
        """
        Process camera frame for object detection.
        
        Args:
            frame: Camera frame as numpy array
            pixels_per_cm: Optional calibration factor
            
        Returns:
            Detection results dictionary
        """
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Use configurable color range
            mask = cv2.inRange(hsv, self.color_lower_hsv, self.color_upper_hsv)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Initialize result
            result = {
                "object_detected": False,
                "height": None,
                "contour_count": len(contours)
            }
            
            # Process contours if any found
            if contours:
                # Find largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                contour_area = cv2.contourArea(largest_contour)
                
                logger.info(f"📊 Largest contour area: {contour_area}")
                
                # Check if contour is large enough to be considered an object
                if contour_area > 1000:  # Threshold from reference code
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    
                    result["object_detected"] = True
                    result["contour_area"] = contour_area
                    result["bounding_box"] = {"x": x, "y": y, "width": w, "height": h}
                    
                    # Calculate height if calibration factor provided
                    if pixels_per_cm:
                        height_cm = round(h / pixels_per_cm, 2)
                        result["height"] = height_cm
                        logger.info(f"📏 Object height: {height_cm} cm")
                    else:
                        result["height"] = h  # Height in pixels
                        logger.info(f"📏 Object height: {h} pixels")
                    
                    logger.info(f"🎯 Object detected: {result}")
                else:
                    logger.info(f"📊 Contour too small (area: {contour_area})")
            else:
                logger.info("📊 No contours found")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Frame processing error: {e}")
            return {
                "object_detected": False,
                "height": None,
                "distance": None,
                "height_match": False,
                "distance_match": False,
                "error": f"Frame processing error: {str(e)}"
            }
    
    def _validate_detection(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate detection results against configured distance and height parameters.
        
        Args:
            result: Detection result from frame processing
            
        Returns:
            Updated result with validation flags
        """
        if not result.get("object_detected", False):
            result.update({
                "distance": None,
                "height_match": False,
                "distance_match": False
            })
            return result
        
        # Get detected height and calculate distance
        detected_height = result.get("height")
        if detected_height is None:
            result.update({
                "distance": None,
                "height_match": False,
                "distance_match": False
            })
            return result
        
        # Calculate distance based on height (assuming perspective projection)
        # This is a simplified calculation - in practice, you'd need proper camera calibration
        calculated_distance = self._calculate_distance_from_height(detected_height)
        result["distance"] = calculated_distance
        
        # Check if height matches expected range
        height_min = self.detection_height - self.height_tolerance
        height_max = self.detection_height + self.height_tolerance
        height_match = height_min <= detected_height <= height_max
        result["height_match"] = height_match
        
        # Check if distance matches expected range
        distance_min = self.detection_distance - self.distance_tolerance
        distance_max = self.detection_distance + self.distance_tolerance
        distance_match = distance_min <= calculated_distance <= distance_max
        result["distance_match"] = distance_match
        
        logger.info(f"📏 Validation - Height: {detected_height}cm (target: {self.detection_height}±{self.height_tolerance}cm, match: {height_match})")
        logger.info(f"📏 Validation - Distance: {calculated_distance}cm (target: {self.detection_distance}±{self.distance_tolerance}cm, match: {distance_match})")
        
        return result
    
    def _calculate_distance_from_height(self, height_cm: float) -> float:
        """
        Calculate distance from camera based on object height.
        This is a simplified calculation - proper implementation would use camera calibration.
        
        Args:
            height_cm: Height of detected object in cm
            
        Returns:
            Estimated distance in cm
        """
        # Simplified distance calculation based on perspective projection
        # In a real implementation, you'd use proper camera calibration parameters
        # This assumes the camera is positioned at a known height and angle
        
        # For now, using a simple inverse relationship
        # You may need to adjust this based on your specific camera setup
        base_distance = 50.0  # Base distance for reference height
        reference_height = 10.0  # Reference height at base distance
        
        if height_cm <= 0:
            return float('inf')
        
        # Calculate distance using inverse square relationship
        distance = base_distance * (reference_height / height_cm)
        
        return round(distance, 2)
    
    def _validate_color_only_detection(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate detection results for color-only mode.
        Only checks if object of specified color exists in field of view.
        
        Args:
            result: Detection result from frame processing
            
        Returns:
            Updated result with color-only validation
        """
        if not result.get("object_detected", False):
            result.update({
                "distance": None,
                "height": None,
                "height_match": False,
                "distance_match": False,
                "color_only_detected": False
            })
            return result
        
        # Get contour area to check if it meets minimum size
        contour_area = result.get("contour_area", 0)
        color_detected = contour_area >= self.color_only_min_area
        
        result["color_only_detected"] = color_detected
        result["height_match"] = True  # Always true in color-only mode
        result["distance_match"] = True  # Always true in color-only mode
        
        logger.info(f"🎨 Color-only validation - Area: {contour_area} (min: {self.color_only_min_area}), Detected: {color_detected}")
        
        return result
    
    def _parse_hsv_string(self, hsv_string: str) -> np.ndarray:
        """
        Parse HSV string from environment variable to numpy array.
        
        Args:
            hsv_string: Comma-separated HSV values (e.g., "35,40,40")
            
        Returns:
            Numpy array with HSV values
        """
        try:
            h, s, v = map(int, hsv_string.split(','))
            return np.array([h, s, v])
        except (ValueError, AttributeError) as e:
            logger.warning(f"⚠️ Invalid HSV string '{hsv_string}', using default green values: {e}")
            return np.array([35, 40, 40])  # Default green values
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current camera detection configuration.
        
        Returns:
            Dictionary containing current configuration parameters
        """
        return {
            "detection_distance": self.detection_distance,
            "detection_height": self.detection_height,
            "height_tolerance": self.height_tolerance,
            "distance_tolerance": self.distance_tolerance,
            "pixels_per_cm": self.pixels_per_cm,
            "detect_color": self.detect_color,
            "color_lower_hsv": self.color_lower_hsv.tolist(),
            "color_upper_hsv": self.color_upper_hsv.tolist(),
            "detection_mode": self.detection_mode,
            "color_only_min_area": self.color_only_min_area,
            "camera_enabled": self.use_camera
        }
    
    def get_test_detection(self) -> Dict[str, Any]:
        """
        Get test detection data for development/testing.
        
        Returns:
            Dictionary with test detection data including distance and height validation
        """
        logger.info("🧪 Returning test detection data")
        
        if self.detection_mode == 'color_only':
            # Color-only mode test data
            return {
                "object_detected": True,
                "height": None,
                "distance": None,
                "height_match": True,
                "distance_match": True,
                "color_only_detected": True,
                "contour_area": self.color_only_min_area + 100,
                "mode": "test",
                "test_data": True
            }
        else:
            # Full mode test data
            test_height = self.detection_height
            test_distance = self._calculate_distance_from_height(test_height)
            
            # Check if test data matches configured parameters
            height_match = abs(test_height - self.detection_height) <= self.height_tolerance
            distance_match = abs(test_distance - self.detection_distance) <= self.distance_tolerance
            
            return {
                "object_detected": True,
                "height": test_height,
                "distance": test_distance,
                "height_match": height_match,
                "distance_match": distance_match,
                "mode": "test",
                "test_data": True
            }
