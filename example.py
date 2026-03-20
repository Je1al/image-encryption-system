"""
example.py
───────────────────────────────────────────────────────────────────────────────
Interactive CLI menu for the Image Encryption System (IES).

Usage:
    python example.py

Menu options
    1. Encrypt an image
    2. Decrypt an image
    3. Run full demo  (generate test image → encrypt → decrypt → verify)
    4. Verify reconstruction
    5. About / How it works
    0. Exit
───────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── Local modules ─────────────────────────────────────────────────────────────
from image_loader import load_image, save_image
from encrypt      import encrypt_image
from decrypt      import decrypt_image, verify_reconstruction
from chaotic_map  import derive_x0_r, logistic_map


# ─── ANSI colours ─────────────────────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    WHITE  = "\033[97m"


def clr(text: str, colour: str) -> str:
    return f"{colour}{text}{C.RESET}"


# ─── Banner ───────────────────────────────────────────────────────────────────

BANNER = f"""
{C.CYAN}{C.BOLD}
  ██╗███████╗███████╗
  ██║██╔════╝██╔════╝
  ██║█████╗  ███████╗
  ██║██╔══╝  ╚════██║
  ██║███████╗███████║
  ╚═╝╚══════╝╚══════╝
{C.RESET}{C.WHITE}  Image Encryption System  v1.0{C.RESET}
{C.DIM}  Pixel Permutation · Chaotic Maps · XOR{C.RESET}
"""

MENU = f"""
{C.BOLD}{'─'*46}{C.RESET}
{C.CYAN}  [1]{C.RESET}  Encrypt an image
{C.CYAN}  [2]{C.RESET}  Decrypt an image
{C.GREEN}  [3]{C.RESET}  Run full demo  (generate → encrypt → decrypt → verify)
{C.YELLOW}  [4]{C.RESET}  Verify reconstruction
{C.MAGENTA}  [5]{C.RESET}  About / How it works
{C.RED}  [0]{C.RESET}  Exit
{C.BOLD}{'─'*46}{C.RESET}
"""


# ─── Demo image generator ────────────────────────────────────────────────────

def _create_demo_image(path: str, size: int = 256) -> None:
    """
    Create a colourful synthetic test image so the demo works without
    requiring the user to provide their own file.
    """
    img = Image.new("RGB", (size, size), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background gradient – manual pixel painting
    pixels = img.load()
    for y in range(size):
        for x in range(size):
            r = int(255 * x / size)
            g = int(255 * y / size)
            b = int(255 * (1 - x / size) * (1 - y / size))
            pixels[x, y] = (r, g, b)

    # Geometric shapes
    draw.rectangle([20, 20, 100, 100], fill=(255, 80,  80))
    draw.ellipse(  [130, 20, 230, 120],fill=(80, 200, 120))
    draw.polygon(  [(128, 140), (80, 220), (176, 220)], fill=(80, 120, 255))
    draw.rectangle([160, 160, 240, 240], fill=(255, 220, 50))
    draw.ellipse(  [20, 140, 110, 230],  fill=(220, 80, 220))

    # Label
    try:
        draw.text((60, 110), "IES Demo", fill=(255, 255, 255))
    except Exception:
        pass   # font unavailable – skip text

    img.save(path)


# ─── Menu actions ─────────────────────────────────────────────────────────────

def action_encrypt() -> None:
    print(f"\n{clr('ENCRYPT IMAGE', C.CYAN)}")
    inp = input("  Input image path  : ").strip()
    if not os.path.isfile(inp):
        print(clr(f"  ✗  File not found: {inp}", C.RED))
        return
    out = input("  Output image path : ").strip() or "images/encrypted.png"
    key = input("  Secret key        : ").strip()
    if not key:
        print(clr("  ✗  Key cannot be empty.", C.RED))
        return
    print()
    encrypt_image(inp, out, key)


def action_decrypt() -> None:
    print(f"\n{clr('DECRYPT IMAGE', C.CYAN)}")
    inp = input("  Encrypted image path : ").strip()
    if not os.path.isfile(inp):
        print(clr(f"  ✗  File not found: {inp}", C.RED))
        return
    out = input("  Output image path    : ").strip() or "images/decrypted.png"
    key = input("  Secret key           : ").strip()
    if not key:
        print(clr("  ✗  Key cannot be empty.", C.RED))
        return
    print()
    decrypt_image(inp, out, key)


def action_full_demo() -> None:
    """
    End-to-end demo:
      1. Generate a synthetic test image  → images/original.png
      2. Encrypt it                       → images/encrypted.png
      3. Decrypt it                       → images/decrypted.png
      4. Verify pixel-perfect reconstruction
    """
    print(f"\n{clr('FULL DEMO', C.GREEN)}")
    key = input("  Secret key (or press Enter for 'ies-demo-key'): ").strip()
    key = key or "ies-demo-key"

    os.makedirs("images", exist_ok=True)
    orig_path = "images/original.png"
    enc_path  = "images/encrypted.png"
    dec_path  = "images/decrypted.png"

    print(f"\n  {clr('▶', C.GREEN)} Generating synthetic test image …")
    _create_demo_image(orig_path, size=256)
    print(f"     Saved → {orig_path}")

    print(f"\n  {clr('▶', C.YELLOW)} Encrypting …")
    encrypt_image(orig_path, enc_path, key, verbose=True)

    print(f"\n  {clr('▶', C.CYAN)} Decrypting …")
    decrypt_image(enc_path, dec_path, key, verbose=True)

    print(f"\n  {clr('▶', C.MAGENTA)} Verifying reconstruction …")
    result = verify_reconstruction(orig_path, dec_path)
    _print_verification(result)

    print(f"\n  {clr('✓ Demo complete.', C.GREEN)}  Check the images/ folder.")


def action_verify() -> None:
    print(f"\n{clr('VERIFY RECONSTRUCTION', C.YELLOW)}")
    orig = input("  Original  image path : ").strip()
    dec  = input("  Decrypted image path : ").strip()
    for p in (orig, dec):
        if not os.path.isfile(p):
            print(clr(f"  ✗  File not found: {p}", C.RED))
            return
    result = verify_reconstruction(orig, dec)
    _print_verification(result)


def _print_verification(result: dict) -> None:
    if "error" in result:
        print(clr(f"  ✗  {result['error']}", C.RED))
        return
    tick = clr("✓", C.GREEN) if result["match"] else clr("✗", C.RED)
    print(f"\n     Match          : {tick}  {result['match']}")
    print(f"     Max Δ pixel    :    {result['max_difference']}")
    print(f"     MSE            :    {result['mse']}")
    psnr = result['psnr_db']
    psnr_str = "∞ dB  (perfect)" if psnr == float("inf") else f"{psnr} dB"
    print(f"     PSNR           :    {psnr_str}")


def action_about() -> None:
    print(f"""
{clr('HOW IT WORKS', C.MAGENTA)}
{'─' * 60}
{clr('1. Pixel Permutation', C.CYAN)}
   The image is flattened into a list of RGB triples. A Fisher–Yates
   shuffle driven by a seeded PRNG rearranges pixel positions, completely
   destroying spatial structure (edges, shapes, colour gradients).
   The permutation is reversible: we simply apply the inverse mapping.

{clr('2. Chaotic Key Generation', C.CYAN)}
   A Logistic Map iterator generates the key stream:
     x(n+1) = r · x(n) · (1 − x(n))   with r ∈ (3.57, 4.0]
   This system is deterministic yet exhibits extreme sensitivity to
   initial conditions (x₀, r) — a hallmark of chaos.  Float values are
   scaled to [0, 255] to produce byte-sized key material.

{clr('3. XOR Encryption', C.CYAN)}
   Every byte of the permuted image array is XOR'd with the corresponding
   key byte.  XOR is its own inverse:  (A ⊕ K) ⊕ K = A.  This means
   the same operation is used for both encryption and decryption.

{clr('Decryption Order', C.YELLOW)}
   encrypted → XOR (same key) → inverse permutation → original

{clr('Security Notes', C.RED)}
   • Educational grade — NOT production-safe.
   • Logistic map is not a CSPRNG; it has detectable statistical biases.
   • A production system would use AES-256-GCM or ChaCha20-Poly1305.
{'─' * 60}
""")


# ─── Main loop ────────────────────────────────────────────────────────────────

def main() -> None:
    print(BANNER)

    actions = {
        "1": action_encrypt,
        "2": action_decrypt,
        "3": action_full_demo,
        "4": action_verify,
        "5": action_about,
    }

    while True:
        print(MENU)
        choice = input(f"  {clr('Select option', C.BOLD)} › ").strip()

        if choice == "0":
            print(f"\n  {clr('Goodbye!', C.DIM)}\n")
            sys.exit(0)

        handler = actions.get(choice)
        if handler:
            handler()
        else:
            print(clr(f"\n  Unknown option: '{choice}'", C.RED))

        input(f"\n  {clr('Press Enter to continue …', C.DIM)}")


if __name__ == "__main__":
    main()
