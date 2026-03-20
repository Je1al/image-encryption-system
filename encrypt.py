"""
encrypt.py
───────────────────────────────────────────────────────────────────────────────
Full encryption pipeline:

  original image
       │
       ▼
  [Step 1] Load image  →  NumPy array (H, W, 3) uint8
       │
       ▼
  [Step 2] Pixel permutation  →  spatial structure destroyed
       │
       ▼
  [Step 3] Chaotic key generation  →  key array matching image shape
       │
       ▼
  [Step 4] XOR encryption  →  each byte XOR'd with key byte
       │
       ▼
  encrypted image  →  saved to disk

Both pixel permutation and XOR encryption are keyed with the same
secret_key string; the chaotic initial conditions are derived from it.
───────────────────────────────────────────────────────────────────────────────
"""

import numpy as np
import time

from image_loader import load_image, save_image, image_info
from permutation import permute_pixels
from chaotic_map  import derive_x0_r, generate_image_key


# ─── Core encrypt function ────────────────────────────────────────────────────

def encrypt_image(
    input_path:  str,
    output_path: str,
    secret_key:  str,
    verbose:     bool = True,
) -> dict:
    """
    Encrypt an image file using pixel permutation + chaotic XOR.

    Parameters
    ----------
    input_path  : str   Path to the plaintext image.
    output_path : str   Where to save the encrypted image.
    secret_key  : str   Passphrase / key string chosen by the user.
    verbose     : bool  Print progress information.

    Returns
    -------
    dict
        Metadata about the encryption run:
        {input_path, output_path, secret_key_hint,
         image_shape, duration_sec}.
    """
    t_start = time.perf_counter()

    # ── Step 1: Load image ────────────────────────────────────────────────────
    if verbose:
        _log("Step 1/4", "Loading image …")
    image = load_image(input_path)
    info  = image_info(image)
    if verbose:
        _log("        ", f"  Shape : {image.shape}  |  "
                         f"Pixels : {info['total_pixels']:,}")

    # ── Step 2: Pixel permutation ─────────────────────────────────────────────
    if verbose:
        _log("Step 2/4", "Applying pixel permutation …")
    permuted = permute_pixels(image, secret_key)

    # ── Step 3: Chaotic key generation ────────────────────────────────────────
    if verbose:
        _log("Step 3/4", "Generating chaotic key stream …")
    x0, r = derive_x0_r(secret_key)
    key   = generate_image_key(x0, r, image.shape)
    if verbose:
        _log("        ", f"  x₀ = {x0:.6f}   r = {r:.6f}")

    # ── Step 4: XOR encryption ────────────────────────────────────────────────
    if verbose:
        _log("Step 4/4", "XOR encryption …")
    encrypted = xor_encrypt(permuted, key)

    # ── Save result ───────────────────────────────────────────────────────────
    save_image(encrypted, output_path)

    duration = time.perf_counter() - t_start
    if verbose:
        _log("Done    ", f"Encrypted image saved → {output_path}")
        _log("        ", f"  Total time : {duration:.3f}s")

    return {
        "input_path":      input_path,
        "output_path":     output_path,
        "secret_key_hint": secret_key[:2] + "…" * (len(secret_key) > 2),
        "image_shape":     image.shape,
        "duration_sec":    round(duration, 4),
    }


# ─── XOR helper ──────────────────────────────────────────────────────────────

def xor_encrypt(data: np.ndarray, key: np.ndarray) -> np.ndarray:
    """
    XOR every byte of *data* with the corresponding byte of *key*.

    Parameters
    ----------
    data : np.ndarray  uint8 array of any shape.
    key  : np.ndarray  uint8 array of the same shape as *data*.

    Returns
    -------
    np.ndarray
        XOR result, uint8, same shape as inputs.

    Note
    ----
    XOR is its own inverse: XOR(XOR(data, key), key) == data.
    This is the fundamental reason the same function is used for both
    encryption and decryption.
    """
    if data.shape != key.shape:
        raise ValueError(
            f"Data shape {data.shape} != key shape {key.shape}"
        )
    return np.bitwise_xor(data, key)


# ─── CLI entry point ──────────────────────────────────────────────────────────

def _log(stage: str, message: str) -> None:
    print(f"  [{stage}] {message}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Image Encryption System – encrypt an image"
    )
    parser.add_argument("input",   help="Path to plaintext image")
    parser.add_argument("output",  help="Path for encrypted output")
    parser.add_argument("--key",   required=True, help="Secret key string")
    args = parser.parse_args()

    result = encrypt_image(args.input, args.output, args.key)
