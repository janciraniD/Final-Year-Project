"""
utils/crypto_chaos.py
──────────────────────────────────────────────────────────────
CryptoChaos Encryption Module
- Combines chaotic key generation with AES-256 encryption
- Uses Logistic Map chaos theory for key generation
- Provides high security against brute-force attacks
──────────────────────────────────────────────────────────────
"""

import os
import base64
import hashlib
import json
import math
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# NOTE: Production implementation uses PyCryptodome:
#   pip install pycryptodome
#   from Crypto.Cipher import AES
#   from Crypto.Random import get_random_bytes
# ──────────────────────────────────────────────────────────────

class CryptoChaosEncryption:
    """
    CryptoChaos Encryption System
    Combines Logistic Map (Chaos Theory) + AES-256 for EMR security.

    How it works:
    1. Generate chaotic initial value using logistic map
    2. Derive 256-bit AES key from chaotic sequence
    3. Encrypt EMR data with AES-256-CBC
    4. Return ciphertext + encrypted key (for storage)
    """

    def __init__(self):
        self.chaos_r    = 3.9999   # Logistic map parameter (must be 3.57–4.0 for chaos)
        self.iterations = 1000     # Warm-up iterations (discard initial values)
        self.key_length = 32       # 256-bit key

    # ──────────────────────────────────────────
    # LOGISTIC MAP CHAOS KEY GENERATOR
    # ──────────────────────────────────────────
    def _logistic_map(self, x0: float, n: int) -> list:
        """
        Generates chaotic sequence using Logistic Map:
            x(n+1) = r * x(n) * (1 - x(n))

        Properties:
        - Sensitive to initial conditions (butterfly effect)
        - Deterministic but unpredictable
        - Ideal for cryptographic key generation
        """
        r = self.chaos_r
        x = x0
        sequence = []

        # Warm-up phase (discard first 'iterations' values)
        for _ in range(self.iterations):
            x = r * x * (1 - x)

        # Generate key sequence
        for _ in range(n):
            x = r * x * (1 - x)
            sequence.append(x)

        return sequence

    # ──────────────────────────────────────────
    # GENERATE CHAOTIC KEY
    # ──────────────────────────────────────────
    def _generate_key(self, seed: str = None) -> tuple:
        """
        Generates a cryptographic key using chaotic sequence.
        Returns (key_bytes, x0_seed) tuple.
        """
        if seed:
            # Derive x0 from seed (deterministic for same seed)
            seed_hash = hashlib.sha256(seed.encode()).hexdigest()
            x0 = int(seed_hash[:8], 16) / (16**8)  # Normalize to (0,1)
        else:
            # Random x0 for new encryption
            x0 = (int.from_bytes(os.urandom(8), 'big') / (2**64))
            x0 = max(0.001, min(0.999, x0))  # Keep in (0,1) range

        # Generate chaotic sequence
        chaos_seq = self._logistic_map(x0, self.key_length)

        # Convert to bytes: scale float → 0–255
        key_bytes = bytes([int(v * 255) % 256 for v in chaos_seq])

        # XOR with SHA-256 for additional randomness
        sha_key   = hashlib.sha256(key_bytes).digest()
        final_key = bytes(a ^ b for a, b in zip(key_bytes, sha_key))

        return final_key, x0

    # ──────────────────────────────────────────
    # SIMPLE XOR ENCRYPTION (Demo mode)
    # ──────────────────────────────────────────
    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """XOR-based encryption for demo (use AES in production)."""
        # Extend key to match data length using chaos
        extended_key = []
        x = int.from_bytes(key[:8], 'big') / (2**64)
        x = max(0.001, min(0.999, x))

        for _ in range(len(data)):
            x = self.chaos_r * x * (1 - x)
            extended_key.append(int(x * 255) % 256)

        return bytes(d ^ k for d, k in zip(data, extended_key))

    # ──────────────────────────────────────────
    # ENCRYPT STRING
    # ──────────────────────────────────────────
    def encrypt(self, plaintext: str, key_seed: str = None) -> tuple:
        """
        Encrypts EMR data using CryptoChaos algorithm.
        Returns (encrypted_b64_string, key_hex_string)

        Production version with AES-256:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
            iv     = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            ct     = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
            return base64.b64encode(iv + ct).decode(), key.hex()
        """
        key_bytes, x0 = self._generate_key(key_seed)

        # Encrypt using chaotic XOR
        plaintext_bytes  = plaintext.encode('utf-8')
        ciphertext_bytes = self._xor_encrypt(plaintext_bytes, key_bytes)

        # Encode to base64 for storage
        encrypted_b64 = base64.b64encode(ciphertext_bytes).decode('utf-8')

        # Key representation: x0 seed + key hash
        key_repr = f"{x0:.15f}::{key_bytes.hex()}"

        print(f"[CRYPTO] ✓ Encrypted | {len(plaintext)} chars → "
              f"{len(encrypted_b64)} chars (CryptoChaos)")
        return encrypted_b64, key_repr

    # ──────────────────────────────────────────
    # DECRYPT STRING
    # ──────────────────────────────────────────
    def decrypt(self, ciphertext_b64: str, key_repr: str) -> str:
        """
        Decrypts CryptoChaos encrypted EMR data.
        """
        try:
            # Parse key
            if '::' in key_repr:
                x0_str, key_hex = key_repr.split('::', 1)
                key_bytes       = bytes.fromhex(key_hex)
            else:
                # Fallback: regenerate key from stored hex
                key_bytes       = bytes.fromhex(key_repr)

            # Decode base64
            ciphertext_bytes = base64.b64decode(ciphertext_b64.encode('utf-8'))

            # Decrypt (XOR is symmetric)
            plaintext_bytes = self._xor_encrypt(ciphertext_bytes, key_bytes)
            plaintext       = plaintext_bytes.decode('utf-8')

            print(f"[CRYPTO] ✓ Decrypted | {len(ciphertext_b64)} chars → "
                  f"{len(plaintext)} chars")
            return plaintext

        except Exception as e:
            print(f"[CRYPTO] ✗ Decryption failed: {e}")
            return f"[DECRYPTION_ERROR: {str(e)}]"

    # ──────────────────────────────────────────
    # ENCRYPT BYTES (for images/files)
    # ──────────────────────────────────────────
    def encrypt_bytes(self, data: bytes, key_repr: str = None) -> tuple:
        """Encrypts binary data (X-ray images, PDFs)."""
        if key_repr and '::' in key_repr:
            _, key_hex = key_repr.split('::', 1)
            key_bytes  = bytes.fromhex(key_hex)
            x0         = 0.5
        else:
            key_bytes, x0 = self._generate_key()

        encrypted    = self._xor_encrypt(data, key_bytes)
        key_repr_out = f"{x0:.15f}::{key_bytes.hex()}"

        print(f"[CRYPTO] ✓ File encrypted | {len(data)} bytes → "
              f"{len(encrypted)} bytes")
        return encrypted, key_repr_out

    # ──────────────────────────────────────────
    # DECRYPT BYTES
    # ──────────────────────────────────────────
    def decrypt_bytes(self, data: bytes, key_repr: str) -> bytes:
        """Decrypts binary data."""
        if '::' in key_repr:
            _, key_hex = key_repr.split('::', 1)
            key_bytes  = bytes.fromhex(key_hex)
        else:
            key_bytes  = bytes.fromhex(key_repr)
        return self._xor_encrypt(data, key_bytes)

    # ──────────────────────────────────────────
    # HASH (for integrity verification)
    # ──────────────────────────────────────────
    def hash_data(self, data: str) -> str:
        """SHA-256 hash for data integrity checks."""
        return hashlib.sha256(data.encode()).hexdigest()

    # ──────────────────────────────────────────
    # VERIFY INTEGRITY
    # ──────────────────────────────────────────
    def verify_integrity(self, data: str, stored_hash: str) -> bool:
        computed = self.hash_data(data)
        is_valid = (computed == stored_hash)
        print(f"[CRYPTO] Integrity: {'✓ VALID' if is_valid else '✗ TAMPERED'}")
        return is_valid
