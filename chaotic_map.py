"""
chaotic_map.py
───────────────────────────────────────────────────────────────────────────────
Chaotic key-stream generation based on the Logistic Map.

  x(n+1) = r · x(n) · (1 − x(n))

Why chaotic maps for cryptography?
  • Extreme sensitivity to initial conditions (butterfly effect):
    a change of 10⁻¹⁵ in x₀ produces a completely different sequence.
  • Deterministic yet unpredictable without knowing the exact parameters.
  • Uniform-looking output that passes basic randomness tests.
  • Cheap to compute – no expensive modular arithmetic required.

Security note
  The logistic map alone is NOT cryptographically secure.  It is used here
  for educational purposes.  A production system would replace this module
  with a CSPRNG (e.g. ChaCha20) or a block cipher in CTR mode.
───────────────────────────────────────────────────────────────────────────────
"""

import numpy as np


# ─── Constants ────────────────────────────────────────────────────────────────

# r must be in (3.57, 4.0] for fully chaotic behaviour.
# r = 3.9999 gives a dense, aperiodic orbit covering (0, 1) almost uniformly.
DEFAULT_R = 3.9999

# Number of warm-up iterations discarded to escape transient behaviour.
WARMUP_ITERATIONS = 1_000


# ─── Core generator ───────────────────────────────────────────────────────────

def logistic_map(x0: float, r: float = DEFAULT_R, n: int = 1) -> np.ndarray:
    """
    Iterate the logistic map and return *n* values after warm-up.

    Parameters
    ----------
    x0 : float
        Initial condition.  Must be in (0, 1) exclusive.
    r  : float
        Growth parameter.  Chaotic regime: 3.57 < r ≤ 4.0.
    n  : int
        Number of output values required.

    Returns
    -------
    np.ndarray
        1-D array of *n* floats in (0, 1).

    Raises
    ------
    ValueError
        If x0 is not in (0, 1) or r is outside the chaotic regime.
    """
    if not (0.0 < x0 < 1.0):
        raise ValueError(f"x0 must be strictly in (0, 1); got {x0}")
    if not (3.57 < r <= 4.0):
        raise ValueError(f"r must be in (3.57, 4.0] for chaotic behaviour; got {r}")

    x = float(x0)

    # Discard warm-up iterations to avoid transient behaviour
    for _ in range(WARMUP_ITERATIONS):
        x = r * x * (1.0 - x)

    # Collect n values
    values = np.empty(n, dtype=np.float64)
    for i in range(n):
        x = r * x * (1.0 - x)
        values[i] = x

    return values


# ─── Key-stream builders ──────────────────────────────────────────────────────

def generate_key_stream(x0: float, r: float, length: int) -> np.ndarray:
    """
    Generate a byte-valued key stream of the requested length.

    The raw float sequence is converted to uint8 by:
      1. Multiplying each value by 256 (maps (0,1) → (0, 256)).
      2. Taking the floor (integer part) and casting to uint8.

    This distributes values roughly uniformly across 0–255.

    Parameters
    ----------
    x0     : float   Initial condition (secret key component 1).
    r      : float   Logistic parameter (secret key component 2).
    length : int     Number of bytes required.

    Returns
    -------
    np.ndarray
        1-D uint8 array of shape (length,).
    """
    floats = logistic_map(x0, r, length)
    # Scale to [0, 255] and convert to bytes
    key_bytes = (floats * 256).astype(np.uint8)
    return key_bytes


def generate_image_key(x0: float, r: float, shape: tuple) -> np.ndarray:
    """
    Generate a key array that matches the shape of an image pixel array.

    Parameters
    ----------
    x0    : float   Initial condition.
    r     : float   Logistic parameter.
    shape : tuple   (H, W, 3) – shape of the target image array.

    Returns
    -------
    np.ndarray
        uint8 array of the same shape as the image.
    """
    h, w, c = shape
    total = h * w * c                         # total number of bytes needed
    flat_key = generate_key_stream(x0, r, total)
    return flat_key.reshape(shape)            # match image dimensions


# ─── Key derivation helper ────────────────────────────────────────────────────

def derive_x0_r(secret_key: str) -> tuple[float, float]:
    """
    Derive (x0, r) from a human-readable secret key string.

    Method
    ------
    1. Hash the UTF-8 bytes of the key with a simple rolling polynomial.
    2. Map the hash to x0 ∈ (0.001, 0.999) and r ∈ (3.57, 4.00).

    This is deterministic: same key always gives same (x0, r).

    Parameters
    ----------
    secret_key : str
        Any non-empty string chosen by the user.

    Returns
    -------
    tuple[float, float]
        (x0, r) ready to feed into the logistic map.
    """
    if not secret_key:
        raise ValueError("Secret key must be a non-empty string.")

    # Rolling-polynomial hash (similar to Java's String.hashCode)
    h = 0
    for ch in secret_key.encode("utf-8"):
        h = (h * 31 + ch) & 0xFFFFFFFF        # keep it 32-bit

    # Spread the 32-bit hash across two independent sub-keys
    h1 = h & 0xFFFF                            # lower 16 bits
    h2 = (h >> 16) & 0xFFFF                   # upper 16 bits

    # Normalise to the required ranges
    x0 = 0.001 + (h1 / 0xFFFF) * 0.998        # → (0.001, 0.999)
    r  = 3.570 + (h2 / 0xFFFF) * 0.430        # → (3.570, 4.000)

    return x0, r
