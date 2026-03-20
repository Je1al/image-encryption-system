# Image Encryption System (IES)

> **Educational cryptographic project** demonstrating image encryption through pixel permutation, chaotic key generation, and XOR ciphering.

---

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
  - [Pixel Permutation](#1-pixel-permutation)
  - [Chaotic Map Key Generation](#2-chaotic-map-key-generation)
  - [XOR Encryption](#3-xor-encryption)
- [Encryption Pipeline](#encryption-pipeline)
- [Decryption Pipeline](#decryption-pipeline)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [Interactive Menu](#interactive-menu)
  - [CLI Scripts](#cli-scripts)
  - [Python API](#python-api)
- [Example Output](#example-output)
- [Security Discussion](#security-discussion)
- [License](#license)

---

## Overview

IES combines three classical cryptographic building blocks to encrypt images so that the encrypted result appears as random noise, while the original can be perfectly reconstructed with the correct key.

```
original.png  ──▶  permute pixels  ──▶  chaotic XOR  ──▶  encrypted.png
                         ▲                    ▲
                         │                    │
                     secret key           secret key
```

---

## How It Works

### 1. Pixel Permutation

**Concept:**  
Rather than processing pixels in order, we shuffle them to a random arrangement before encryption. This destroys spatial correlation—edges, shapes, and colour gradients all disappear.

**Implementation:**
1. Flatten the `(H × W × 3)` image array into a list of `H×W` RGB triples.
2. Use a seeded `numpy.random.default_rng` (PCG64) to generate a permutation `P` of indices `[0, H×W)`.
3. Reorder: `out[i] = in[P[i]]`.
4. Reshape back to `(H, W, 3)`.

**Reversal:**  
Compute the inverse permutation `inv_P` where `inv_P[P[i]] = i`, then apply it to restore the original order.

```
P    = [3, 0, 2, 1]           # shuffle
inv_P = [1, 3, 2, 0]          # inverse: inv_P[P[i]] = i
```

### 2. Chaotic Map Key Generation

**Why chaotic maps?**

Chaotic systems exhibit:
- **Sensitivity to initial conditions** — a difference of `10⁻¹⁵` in the starting value produces a completely different sequence (butterfly effect).
- **Determinism** — given the same parameters, the sequence is exactly reproducible.
- **Pseudo-randomness** — the output passes basic statistical randomness tests.

**The Logistic Map:**

```
x(n+1) = r · x(n) · (1 − x(n))
```

For `r ∈ (3.57, 4.0]` the system enters full chaos: the orbit is aperiodic, dense, and ergodic over `(0, 1)`.

**Key derivation:**
1. Hash the secret key string → two sub-hashes.
2. Map to `x₀ ∈ (0.001, 0.999)` and `r ∈ (3.570, 4.000)`.
3. Discard 1 000 warm-up iterations to escape transient behaviour.
4. Collect `H × W × 3` float values, scale to `[0, 255]`, cast to `uint8`.

### 3. XOR Encryption

**Principle:**

XOR (`⊕`) satisfies:

```
ciphertext = plaintext  ⊕ key
plaintext  = ciphertext ⊕ key   ← same operation!
```

Because XOR is its own inverse, the same function handles both encryption and decryption. Every byte of the permuted image is XOR'd with the corresponding byte from the chaotic key stream.

**Why it works visually:**  
Even a single bit difference in the key byte flips bits in the cipher byte unpredictably. Combined with the chaotic stream, the result is statistically indistinguishable from random noise.

---

## Encryption Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    ENCRYPTION PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  original.png                                               │
│       │                                                     │
│       ▼                                                     │
│  [1] image_loader.load_image()                              │
│       │   → NumPy array (H, W, 3) uint8                     │
│       ▼                                                     │
│  [2] permutation.permute_pixels(image, key)                 │
│       │   → spatial structure destroyed                     │
│       ▼                                                     │
│  [3] chaotic_map.generate_image_key(x₀, r, shape)           │
│       │   → uint8 key array of same shape                   │
│       ▼                                                     │
│  [4] encrypt.xor_encrypt(permuted, key)                     │
│       │   → each byte XOR'd with key byte                   │
│       ▼                                                     │
│  encrypted.png                                              │
└─────────────────────────────────────────────────────────────┘
```

## Decryption Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    DECRYPTION PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  encrypted.png                                              │
│       │                                                     │
│       ▼                                                     │
│  [1] image_loader.load_image()                              │
│       ▼                                                     │
│  [2] chaotic_map.generate_image_key(x₀, r, shape)           │
│       │   ← identical parameters re-generated               │
│       ▼                                                     │
│  [3] encrypt.xor_encrypt(encrypted, key)   ← XOR again      │
│       │   → XOR cancels itself: A⊕K⊕K = A                  │
│       ▼                                                     │
│  [4] permutation.inverse_permute_pixels(result, key)        │
│       │   → pixels restored to original positions           │
│       ▼                                                     │
│  decrypted.png  (pixel-identical to original)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
image-encryption-system/
│
├── image_loader.py     # Load / save images as NumPy arrays
├── chaotic_map.py      # Logistic map + chaotic key generation
├── permutation.py      # Deterministic pixel permutation & inverse
├── encrypt.py          # Full encryption pipeline + CLI
├── decrypt.py          # Full decryption pipeline + CLI + verification
├── example.py          # Interactive menu (main entry point)
│
├── images/
│   ├── original.png    # Source image (example)
│   ├── encrypted.png   # Encrypted output (looks like noise)
│   └── decrypted.png   # Reconstructed image (matches original)
│
└── README.md
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/image-encryption-system.git
cd image-encryption-system

# Install dependencies
pip install numpy pillow
```

No other dependencies required.

---

## Usage

### Interactive Menu

```bash
python example.py
```

```
  ██╗███████╗███████╗
  ██║██╔════╝██╔════╝
  ██║█████╗  ███████╗
  ██║██╔══╝  ╚════██║
  ██║███████╗███████║
  ╚═╝╚══════╝╚══════╝
  Image Encryption System  v1.0
  Pixel Permutation · Chaotic Maps · XOR

  ──────────────────────────────────────────────
  [1]  Encrypt an image
  [2]  Decrypt an image
  [3]  Run full demo  (generate → encrypt → decrypt → verify)
  [4]  Verify reconstruction
  [5]  About / How it works
  [0]  Exit
  ──────────────────────────────────────────────
```

### CLI Scripts

```bash
# Encrypt
python encrypt.py path/to/photo.png images/encrypted.png --key "my-secret-key"

# Decrypt
python decrypt.py images/encrypted.png images/decrypted.png --key "my-secret-key"
```

### Python API

```python
from encrypt import encrypt_image
from decrypt import decrypt_image, verify_reconstruction

# Encrypt
encrypt_image("images/original.png", "images/encrypted.png", secret_key="my-key")

# Decrypt
decrypt_image("images/encrypted.png", "images/decrypted.png", secret_key="my-key")

# Verify
result = verify_reconstruction("images/original.png", "images/decrypted.png")
print(result)
# {'match': True, 'max_difference': 0, 'mse': 0.0, 'psnr_db': inf}
```

---

## Example Output

| Original | Encrypted | Decrypted |
|:--------:|:---------:|:---------:|
| ![original](images/original.png) | ![encrypted](images/encrypted.png) | ![decrypted](images/decrypted.png) |

Encrypted image appears as **random noise** — no structure, shapes, or colours from the original are visible. Decrypted image is **pixel-identical** to the original (PSNR = ∞ dB, MSE = 0).

---

## Security Discussion

### Strengths

| Property | Description |
|---|---|
| **Confusion** | XOR with a chaotic stream obscures byte values |
| **Diffusion** | Pixel permutation spreads spatial information |
| **Key sensitivity** | Logistic map is highly sensitive to x₀ and r |
| **Determinism** | Same key always reconstructs the same image |

### Weaknesses

| Weakness | Explanation |
|---|---|
| **Logistic map is not a CSPRNG** | It has detectable statistical biases and is not cryptographically secure |
| **No authentication** | An attacker can tamper with the encrypted image undetected |
| **Key derivation is weak** | A polynomial hash is not a proper KDF (no salt, no iterations) |
| **Susceptible to chosen-plaintext attacks** | With enough image pairs an attacker can recover key parameters |

### Recommended Improvements for Production

1. **Replace logistic map** with `secrets` module or `os.urandom()` + AES-256 in CTR mode.
2. **Add authentication** using AES-GCM or ChaCha20-Poly1305 (AEAD ciphers).
3. **Use a proper KDF** — PBKDF2-HMAC-SHA256 with salt and ≥ 100 000 iterations.
4. **Implement block cipher modes** — CBC or GCM prevents pattern leakage in uniform regions.

```python
# Production-grade alternative (Python stdlib)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)
aesgcm = AESGCM(key)
ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, associated_data=None)
```

---

## License

MIT License. Free for educational and portfolio use.

---

*Built for educational purposes in applied cryptography.*  
*Do not use this system to protect sensitive data in production.*
