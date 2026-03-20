"""
permutation.py
───────────────────────────────────────────────────────────────────────────────
Deterministic pixel-level permutation for images.

What is pixel permutation?
  Instead of keeping pixels in their original spatial positions, we shuffle
  them according to a secret permutation vector.  When the permutation is
  applied, the spatial structure (edges, colours, shapes) of the image is
  completely destroyed, making statistical attacks harder.

How it works
  1. Flatten the (H, W, 3) array into a 1-D sequence of pixel triples.
  2. Generate a permutation index array P using a seeded RNG derived from
     the secret key.
  3. Reorder pixels: out[i] = in[P[i]] for all i.
  4. Reshape back to (H, W, 3).

Reversibility
  To recover the original order we compute the inverse permutation:
    inv_P[P[i]] = i
  Then: original[i] = shuffled[inv_P[i]]
───────────────────────────────────────────────────────────────────────────────
"""

import numpy as np


# ─── Seed derivation ──────────────────────────────────────────────────────────

def _key_to_seed(secret_key: str) -> int:
    """
    Convert a secret key string to an integer seed for NumPy's RNG.

    We use a djb2-style hash so that even single-character differences in
    the key produce completely different permutations.

    Parameters
    ----------
    secret_key : str

    Returns
    -------
    int
        A non-negative integer suitable for np.random.default_rng().
    """
    h = 5381
    for byte in secret_key.encode("utf-8"):
        h = ((h << 5) + h + byte) & 0xFFFFFFFFFFFFFFFF   # 64-bit
    return h


# ─── Permutation ─────────────────────────────────────────────────────────────

def permute_pixels(image: np.ndarray, secret_key: str) -> np.ndarray:
    """
    Shuffle the pixel positions of *image* using *secret_key*.

    Parameters
    ----------
    image      : np.ndarray  Shape (H, W, 3), dtype uint8.
    secret_key : str         Shared secret used to reproduce the same shuffle.

    Returns
    -------
    np.ndarray
        Pixel-shuffled array of the same shape as *image*.
    """
    h, w, c = image.shape
    n_pixels = h * w

    # Flatten to (n_pixels, 3) so we permute whole RGB triples
    flat = image.reshape(n_pixels, c)

    # Build the permutation vector
    perm = _build_permutation(n_pixels, secret_key)

    # Apply permutation
    shuffled = flat[perm]

    return shuffled.reshape(h, w, c)


def inverse_permute_pixels(image: np.ndarray, secret_key: str) -> np.ndarray:
    """
    Reverse the pixel shuffle produced by :func:`permute_pixels`.

    Parameters
    ----------
    image      : np.ndarray  Shape (H, W, 3), dtype uint8.
    secret_key : str         Same key used during encryption.

    Returns
    -------
    np.ndarray
        Pixel array restored to the original spatial arrangement.
    """
    h, w, c = image.shape
    n_pixels = h * w

    flat = image.reshape(n_pixels, c)

    perm = _build_permutation(n_pixels, secret_key)

    # Compute the inverse permutation: inv_perm[perm[i]] = i
    inv_perm = np.empty_like(perm)
    inv_perm[perm] = np.arange(n_pixels, dtype=perm.dtype)

    # Restore original order
    restored = flat[inv_perm]

    return restored.reshape(h, w, c)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _build_permutation(n: int, secret_key: str) -> np.ndarray:
    """
    Generate a reproducible permutation of indices [0, n).

    Uses NumPy's PCG64 generator seeded from the secret key.
    Same key + same n will always produce the same permutation.

    Parameters
    ----------
    n          : int   Number of elements to permute.
    secret_key : str   Seed source.

    Returns
    -------
    np.ndarray
        1-D int64 array of shape (n,) — a permutation of [0, n).
    """
    seed = _key_to_seed(secret_key)
    rng = np.random.default_rng(seed)
    # rng.permutation returns a NEW shuffled index array without modifying input
    return rng.permutation(n)
