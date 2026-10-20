"""
Multi-Threaded Camera Capture Stream.
Eliminates OpenCV frame buffering latency and provides fallback synthetic field frames
when running without a physical webcam connected.
"""

import time
import threading
from typing import Union, Tuple, Optional
import cv2
import numpy as np

from ..core.logger import get_rover_logger

logger = get_rover_logger("CAMERA")

class ThreadedCamera:
    def __init__(self, source: Union[int, str] = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_synthetic = False
        self.running = False
        self._lock = threading.Lock()
        self._frame: Optional[np.ndarray] = None
        self._thread: Optional[threading.Thread] = None
        self._frame_count = 0

    def start(self) -> bool:
        """Initializes the capture stream and launches background worker thread."""
        logger.info(f"Opening camera source: {self.source} ({self.width}x{self.height} @ {self.fps}fps)")
        
        # Try opening physical camera
        try:
            if isinstance(self.source, int):
                # On Windows, cv2.CAP_DSHOW can prevent long timeouts
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(self.source)
            else:
                self.cap = cv2.VideoCapture(self.source)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                # Test read
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self._frame = frame
                    self.is_synthetic = False
                    logger.info("Physical camera stream successfully opened.")
                else:
                    self._fallback_to_synthetic("Camera opened but failed to capture initial frame.")
            else:
                self._fallback_to_synthetic(f"Failed to open camera source '{self.source}'.")
        except Exception as e:
            self._fallback_to_synthetic(f"Camera initialization exception: {e}")

        self.running = True
        self._thread = threading.Thread(target=self._capture_worker, daemon=True, name="CameraCaptureThread")
        self._thread.start()
        return True

    def _fallback_to_synthetic(self, reason: str):
        """Falls back to simulated crop-field video generation for PC testing."""
        logger.warning(f"{reason} Activating SYNTHETIC camera simulation mode.")
        self.is_synthetic = True
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Generates a synthetic agricultural field scene with ground, crop rows, and simulated leaves."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self._frame_count += 1
        
        # 1. Sky / Horizon (Top 40%)
        frame[0:int(self.height * 0.4), :] = [210, 180, 140] # Light blue/haze sky (BGR)
        
        # 2. Agricultural Soil Bed (Bottom 60%)
        frame[int(self.height * 0.4):, :] = [45, 75, 105] # Brown earth soil (BGR)
        
        # 3. Crop Rows (Green foliage along sides)
        # Left crop row
        pts_left = np.array([
            [0, int(self.height * 0.4)],
            [int(self.width * 0.25), int(self.height * 0.4)],
            [int(self.width * 0.35), self.height],
            [0, self.height]
        ], np.int32)
        cv2.fillPoly(frame, [pts_left], (35, 120, 35))

        # Right crop row
        pts_right = np.array([
            [int(self.width * 0.75), int(self.height * 0.4)],
            [self.width, int(self.height * 0.4)],
            [self.width, self.height],
            [int(self.width * 0.65), self.height]
        ], np.int32)
        cv2.fillPoly(frame, [pts_right], (35, 120, 35))

        # 4. Periodic simulated leaf with disease spot on the right side
        sim_cycle = (self._frame_count // 30) % 4
        if sim_cycle in [1, 2]:
            leaf_center = (int(self.width * 0.72), int(self.height * 0.65))
            # Healthy leaf
            cv2.ellipse(frame, leaf_center, (55, 30), 25, 0, 360, (40, 160, 40), -1)
            # Diseased necrotic spot (brown / yellow lesion)
            cv2.circle(frame, (leaf_center[0] - 8, leaf_center[1] + 5), 12, (20, 75, 140), -1)
            cv2.putText(frame, "[SIMULATED INFECTED LEAF]", (leaf_center[0] - 90, leaf_center[1] - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        # 5. Timestamp and overlay
        cv2.putText(frame, "VIRTUAL AGRI-FIELD CAMERA FEED", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return frame

    def _capture_worker(self):
        """Continuously pulls latest frame without accumulating latency."""
        frame_interval = 1.0 / self.fps
        while self.running:
            start_t = time.time()
            if not self.is_synthetic and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    with self._lock:
                        self._frame = frame
                else:
                    time.sleep(0.01)
            else:
                synth = self._generate_synthetic_frame()
                with self._lock:
                    self._frame = synth

            elapsed = time.time() - start_t
            sleep_t = max(0.001, frame_interval - elapsed)
            time.sleep(sleep_t)

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Returns the most recent captured frame."""
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def stop(self):
        """Releases camera resources."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        logger.info("Camera stream stopped.")
