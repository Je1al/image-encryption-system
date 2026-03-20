"""
decrypt.py
───────────────────────────────────────────────────────────────────────────────
Full decryption pipeline (exact mirror of encrypt.py, applied in reverse):

  encrypted image
       │
       ▼
  [Step 1] Load encrypted image  →  NumPy array (H, W, 3) uint8
       │
       ▼
  [Step 2] Chaotic key re-generation  →  same key as used during encryption
       │
       ▼
  [Step 3] XOR decryption  →  reverses the XOR (XOR is self-inverse)
       │
       ▼
  [Step 4] Inverse pixel permutation  →  restores original spatial layout
       │
       ▼
  decrypted image  →  should match original pixel-for-pixel
───────────────────────────────────────────────────────────────────────────────
"""

import numpy as np
import time

from image_loader import load_image, save_image, image_info
from permutation  import inverse_permute_pixels
from chaotic_map  import derive_x0_r, generate_image_key
from encrypt      import xor_encrypt          # XOR is self-inverse; reuse it


# ─── Core decrypt function ────────────────────────────────────────────────────

def decrypt_image(
    input_path:  str,
    output_path: str,
    secret_key:  str,
    verbose:     bool = True,
) -> dict:
    """
    Decrypt an image file that was encrypted with :func:`encrypt.encrypt_image`.

    Parameters
    ----------
    input_path  : str   Path to the encrypted image.
    output_path : str   Where to save the decrypted result.
    secret_key  : str   Must be identical to the key used during encryption.
    verbose     : bool  Print progress information.

    Returns
    -------
    dict
        Metadata: {input_path, output_path, image_shape, duration_sec}.
    """
    t_start = time.perf_counter()

    # ── Step 1: Load encrypted image ──────────────────────────────────────────
    if verbose:
        _log("Step 1/4", "Loading encrypted image …")
    image = load_image(input_path)
    info  = image_info(image)
    if verbose:
        _log("        ", f"  Shape : {image.shape}  |  "
                         f"Pixels : {info['total_pixels']:,}")

    # ── Step 2: Re-generate the same chaotic key ───────────────────────────────
    if verbose:
        _log("Step 2/4", "Re-generating chaotic key stream …")
    x0, r = derive_x0_r(secret_key)
    key   = generate_image_key(x0, r, image.shape)
    if verbose:
        _log("        ", f"  x₀ = {x0:.6f}   r = {r:.6f}")

    # ── Step 3: XOR decryption ────────────────────────────────────────────────
    # XOR is its own inverse: data ⊕ key ⊕ key = data
    if verbose:
        _log("Step 3/4", "XOR decryption …")
    xor_decrypted = xor_encrypt(image, key)

    # ── Step 4: Inverse pixel permutation ─────────────────────────────────────
    if verbose:
        _log("Step 4/4", "Reversing pixel permutation …")
    decrypted = inverse_permute_pixels(xor_decrypted, secret_key)

    # ── Save result ───────────────────────────────────────────────────────────
    save_image(decrypted, output_path)

    duration = time.perf_counter() - t_start
    if verbose:
        _log("Done    ", f"Decrypted image saved → {output_path}")
        _log("        ", f"  Total time : {duration:.3f}s")

    return {
        "input_path":   input_path,
        "output_path":  output_path,
        "image_shape":  image.shape,
        "duration_sec": round(duration, 4),
    }


# ─── Verification helper ──────────────────────────────────────────────────────

def verify_reconstruction(
    original_path:  str,
    decrypted_path: str,
) -> dict:
    """
    Compare the original and decrypted images pixel-by-pixel.

    Parameters
    ----------
    original_path  : str
    decrypted_path : str

    Returns
    -------
    dict
        {
          match          : bool   – True if images are identical,
          max_difference : int    – maximum per-channel per-pixel delta,
          mse            : float  – mean squared error (0.0 = perfect match),
          psnr_db        : float  – peak signal-to-noise ratio in dB
                                    (inf = perfect match),
        }
    """
    original  = load_image(original_path).astype(np.int32)
    decrypted = load_image(decrypted_path).astype(np.int32)

    if original.shape != decrypted.shape:
        return {
            "match": False,
            "error": f"Shape mismatch: {original.shape} vs {decrypted.shape}",
        }

    diff    = original - decrypted
    max_diff = int(np.abs(diff).max())
    mse     = float(np.mean(diff ** 2))
    psnr    = float("inf") if mse == 0.0 else 10 * np.log10(255 ** 2 / mse)

    return {
        "match":          max_diff == 0,
        "max_difference": max_diff,
        "mse":            round(mse, 6),
        "psnr_db":        round(psnr, 2),
    }


# ─── CLI helpers ──────────────────────────────────────────────────────────────

def _log(stage: str, message: str) -> None:
    print(f"  [{stage}] {message}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Image Encryption System – decrypt an image"
    )
    parser.add_argument("input",   help="Path to encrypted image")
    parser.add_argument("output",  help="Path for decrypted output")
    parser.add_argument("--key",   required=True, help="Secret key string")
    args = parser.parse_args()

    result = decrypt_image(args.input, args.output, args.key)
