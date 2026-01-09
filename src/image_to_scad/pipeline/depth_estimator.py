"""
AI-based depth estimation using Intel DPT-Hybrid-MiDaS model.

This module provides depth estimation from single images using
the Intel DPT (Dense Prediction Transformer) model.
"""

from typing import Optional

import numpy as np

from image_to_scad.exceptions import DepthEstimationError
from image_to_scad.utils.logging import get_logger


# Model configuration
MODEL_ID = "Intel/dpt-hybrid-midas"
MODEL_REVISION = "main"


class DepthEstimator:
    """
    Estimate depth from images using Intel DPT-Hybrid-MiDaS model.

    The model is loaded lazily on first use and cached for subsequent
    calls. Use release() to free memory when done.

    Example:
        >>> estimator = DepthEstimator()
        >>> depth_map = estimator.estimate(image_array)
        >>> print(depth_map.shape)  # Same as input image (H, W)
        >>> estimator.release()  # Free memory
    """

    def __init__(self, device: Optional[str] = None) -> None:
        """
        Initialize the depth estimator.

        Args:
            device: Device to use for inference ("cpu", "cuda", "mps").
                   If None, automatically selects best available device.
        """
        self._logger = get_logger(__name__)
        self._device = device
        self._model = None
        self._processor = None
        self._torch = None

    def _ensure_loaded(self) -> None:
        """
        Ensure the model is loaded (lazy initialization).

        Raises:
            DepthEstimationError: If model loading fails.
        """
        if self._model is not None:
            return

        try:
            import torch
            from transformers import DPTForDepthEstimation, DPTImageProcessor

            self._torch = torch

            # Determine device
            if self._device is None:
                if torch.cuda.is_available():
                    self._device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self._device = "mps"
                else:
                    self._device = "cpu"

            self._logger.info(f"Loading depth estimation model on {self._device}...")

            # Load model and processor
            self._processor = DPTImageProcessor.from_pretrained(MODEL_ID)
            self._model = DPTForDepthEstimation.from_pretrained(MODEL_ID)
            self._model.to(self._device)
            self._model.eval()

            self._logger.info("Depth estimation model loaded successfully")

        except ImportError as e:
            raise DepthEstimationError(
                f"Missing required dependency: {e}. "
                "Install with: pip install torch transformers"
            ) from e
        except Exception as e:
            raise DepthEstimationError(f"Failed to load depth model: {e}") from e

    def estimate(self, image: np.ndarray) -> np.ndarray:
        """
        Estimate depth from an RGB image.

        Args:
            image: RGB image as numpy array with shape (H, W, 3).

        Returns:
            np.ndarray: Depth map as 2D array with shape (H, W).
                       Values are relative depth (higher = closer).

        Raises:
            DepthEstimationError: If depth estimation fails.
            ValueError: If image format is invalid.
        """
        self._validate_image(image)
        self._ensure_loaded()

        try:
            # Preprocess image
            inputs = self._processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Run inference
            with self._torch.no_grad():
                outputs = self._model(**inputs)
                predicted_depth = outputs.predicted_depth

            # Interpolate to original size
            prediction = self._torch.nn.functional.interpolate(
                predicted_depth.unsqueeze(1),
                size=image.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()

            # Convert to numpy
            depth_map = prediction.cpu().numpy()

            self._logger.debug(
                f"Depth estimation complete. "
                f"Shape: {depth_map.shape}, "
                f"Range: [{depth_map.min():.2f}, {depth_map.max():.2f}]"
            )

            return depth_map

        except Exception as e:
            raise DepthEstimationError(f"Depth estimation failed: {e}") from e

    def _validate_image(self, image: np.ndarray) -> None:
        """
        Validate input image format.

        Args:
            image: Image array to validate.

        Raises:
            ValueError: If image format is invalid.
        """
        if not isinstance(image, np.ndarray):
            raise ValueError("Image must be a numpy array")

        if image.ndim != 3:
            raise ValueError(f"Image must be 3D array (H, W, C), got {image.ndim}D")

        if image.shape[2] != 3:
            raise ValueError(f"Image must have 3 channels (RGB), got {image.shape[2]}")

    def release(self) -> None:
        """
        Release the model from memory.

        Call this to free GPU/RAM when the model is no longer needed.
        """
        if self._model is not None:
            del self._model
            self._model = None

        if self._processor is not None:
            del self._processor
            self._processor = None

        # Clear CUDA cache if available
        if self._torch is not None and self._torch.cuda.is_available():
            self._torch.cuda.empty_cache()

        self._logger.debug("Depth estimation model released")

    @property
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded."""
        return self._model is not None

    @property
    def device(self) -> Optional[str]:
        """Get the device being used for inference."""
        return self._device
