"""
image_loader.py
───────────────────────────────────────────────────────────────────────────────
Handles loading images from disk and converting them to NumPy arrays,
and saving NumPy arrays back as image files.

All images are treated as RGB arrays of shape (H, W, 3) with dtype uint8.
───────────────────────────────────────────────────────────────────────────────
"""

import numpy as np
from PIL import Image
import os


def load_image(path: str) -> np.ndarray:
    """
    Load an image file (PNG / JPG / BMP …) and return it as a NumPy array.

    Parameters
    ----------
    path : str
        Absolute or relative path to the image file.

    Returns
    -------
    np.ndarray
        Shape (H, W, 3), dtype uint8, channel order RGB.

    Raises
    ------
    FileNotFoundError
        If the file does not exist at the given path.
    ValueError
        If the file cannot be decoded as an image.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image not found: {path}")

    try:
        img = Image.open(path).convert("RGB")   # normalise to RGB always
    except Exception as exc:
        raise ValueError(f"Cannot open image '{path}': {exc}") from exc

    return np.array(img, dtype=np.uint8)


def save_image(array: np.ndarray, path: str) -> None:
    """
    Save a NumPy array as an image file.

    Parameters
    ----------
    array : np.ndarray
        Shape (H, W, 3), dtype uint8.
    path : str
        Destination file path.  The format is inferred from the extension
        (e.g. '.png', '.jpg').

    Raises
    ------
    ValueError
        If the array does not have the expected shape or dtype.
    """
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError(
            f"Expected array of shape (H, W, 3), got {array.shape}"
        )

    if array.dtype != np.uint8:
        # Clip and cast – useful when the caller forgot to convert
        array = np.clip(array, 0, 255).astype(np.uint8)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    Image.fromarray(array, mode="RGB").save(path)


def image_info(array: np.ndarray) -> dict:
    """
    Return a dictionary with basic metadata about an image array.

    Parameters
    ----------
    array : np.ndarray
        Shape (H, W, 3), dtype uint8.

    Returns
    -------
    dict
        Keys: height, width, channels, total_pixels, dtype.
    """
    h, w, c = array.shape
    return {
        "height":       h,
        "width":        w,
        "channels":     c,
        "total_pixels": h * w,
        "dtype":        str(array.dtype),
    }
