import random
import math
from PIL import Image
import io
import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
import zlib
import hashlib

class ShadowCrypto:
    """Layer 1: Authenticated Encryption (AES-256 GCM)"""
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        return scrypt(password.encode(), salt, 32, N=2**14, r=8, p=1)

    @classmethod
    def encrypt(cls, data, password: str) -> bytes:
        """Encrypt raw bytes or text using AES-256-GCM.

        `data` may be `str` or `bytes`. Returns: salt(16)|nonce(12)|tag(16)|ciphertext
        """
        # ensure we have bytes
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = bytes(data)

        # 1) create salt and derive an AES-256 key from the password
        salt = get_random_bytes(16)
        key = cls.derive_key(password, salt)

        # 2) use a 12-byte nonce for GCM (recommended size)
        nonce = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        # 3) compress the bytes to reduce size before encryption
        compressed = zlib.compress(data_bytes, level=9)

        # 4) encrypt and return the concatenated blob
        ciphertext, tag = cipher.encrypt_and_digest(compressed)
        return salt + nonce + tag + ciphertext

    @classmethod
    def decrypt(cls, encrypted_data: bytes, password: str) -> bytes:
        try:
            # Slicing based on fixed lengths: 
            # Salt(16) + Nonce(12) + Tag(16) + Ciphertext(rest)
            salt = encrypted_data[:16]
            nonce = encrypted_data[16:28]  # 12 bytes
            tag = encrypted_data[28:44]    # 16 bytes
            ciphertext = encrypted_data[44:]
            
            # 1) derive the same key from the stored salt and provided password
            key = cls.derive_key(password, salt)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

            # 2) decrypt and verify the GCM tag (raises on integrity failure)
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

            # 3) try to decompress; if decompression fails, fall back to raw
            try:
                decompressed = zlib.decompress(decrypted_data)
            except zlib.error:
                decompressed = decrypted_data

            # 4) return raw bytes (caller decides how to interpret)
            return decompressed
        except Exception as e:
            print(f"[DEBUG CRYPTO] Decryption Error: {str(e)}")
            return None

class ShadowStego:
    """Layer 2: Randomized LSB Steganography (Debug Mode)"""
    MAGIC_BYTES = b"SP"

    @staticmethod
    def get_pixel_sequence(width, height, seed_data):
        # Use a local RNG to ensure deterministic behavior across threads
        rng = random.Random(seed_data)
        coords = [(x, y, c) for y in range(height) for x in range(width) for c in range(3)]
        rng.shuffle(coords)
        return coords
    
    @classmethod
    def calculate_psnr(cls, original_path, stego_path):
        """
        Calculate Peak Signal-to-Noise Ratio (PSNR) to measure image quality loss.
        PSNR > 40dB is typically invisible to the human eye.
        """
        # Accept either file paths, raw bytes, or PIL Image objects
        def _to_image(obj):
            if isinstance(obj, Image.Image):
                return obj.convert('RGB')
            if isinstance(obj, (bytes, bytearray)):
                return Image.open(io.BytesIO(obj)).convert('RGB')
            # assume path-like
            return Image.open(obj).convert('RGB')

        # convert inputs to PIL Image if needed
        img1 = _to_image(original_path)
        img2 = _to_image(stego_path)
        
        arr1 = np.array(img1, dtype=np.float32)
        arr2 = np.array(img2, dtype=np.float32)
        
        mse = np.mean((arr1 - arr2) ** 2)
        if mse == 0:
            return 100.0
            
        max_pixel = 255.0
        psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        return psnr

    @classmethod
    def embed_to_pil(cls, img, payload, seed_data):
        # 1) normalize image to RGB and get dimensions
        img = img.convert('RGB')  # Force RGB to strip Alpha
        width, height = img.size

        # 2) build payload with a small header: MAGIC(2) + length(4) + data
        full_payload = cls.MAGIC_BYTES + len(payload).to_bytes(4, 'big') + payload
        total_bits = len(full_payload) * 8

        print(f"[DEBUG EMBED] Payload Size: {len(payload)} bytes")
        print(f"[DEBUG EMBED] Total bits (inc. header): {total_bits}")
        print(f"[DEBUG EMBED] Header (6 bytes): {full_payload[:6].hex()}")

        # 3) quick capacity check (3 channels per pixel)
        capacity = width * height * 3
        if total_bits > capacity:
            raise ValueError(f"Payload too large! Need {total_bits} bits, have {capacity}")

        # 4) convert image into a flat uint8 array for fast vector operations
        arr = np.array(img, dtype=np.uint8)
        flat = arr.reshape(-1)

        # 5) derive a deterministic permutation from the seed (password).
        #    We hash the seed and use a reproducible RNG so extract can rebuild it.
        seed_bytes = hashlib.sha256(str(seed_data).encode('utf-8')).digest()
        seed_int = int.from_bytes(seed_bytes[:8], 'big')
        rng = np.random.default_rng(seed_int)
        perm = rng.permutation(flat.size)

        # 6) convert payload bytes into an array of bits (MSB-first)
        bits = np.unpackbits(np.frombuffer(full_payload, dtype=np.uint8)).astype(np.uint8)

        # 7) write bits to the least-significant-bit of selected positions
        #    Use numpy masks to ensure operations stay in uint8 and avoid
        #    Python-negative-int issues when using bitwise not (~1).
        targets = perm[:bits.size]
        mask = np.uint8(0xFE)  # 11111110 to clear LSB
        vals = np.bitwise_and(flat[targets].astype(np.uint8), mask)
        flat[targets] = np.bitwise_or(vals, bits).astype(np.uint8)

        # 8) reshape array back to image and return
        arr2 = flat.reshape((height, width, 3))
        return Image.fromarray(arr2, 'RGB')

    @classmethod
    def extract_from_pil(cls, img, seed_data):
        # 1) normalize image and prepare flat array
        img = img.convert('RGB')
        width, height = img.size

        print(f"[DEBUG EXTRACT] Image size: {width}x{height}")

        arr = np.array(img, dtype=np.uint8)
        flat = arr.reshape(-1)

        # 2) recreate the exact same permutation using the provided seed
        seed_bytes = hashlib.sha256(str(seed_data).encode('utf-8')).digest()
        seed_int = int.from_bytes(seed_bytes[:8], 'big')
        rng = np.random.default_rng(seed_int)
        perm = rng.permutation(flat.size)

        # helper: read `count` bits starting at `start_bit` by selecting
        # the same permuted indices and masking LSB
        def read_bits(start_bit, count):
            indices = perm[start_bit:start_bit+count]
            return flat[indices] & 1

        # 3) read and decode header (6 bytes = 48 bits)
        header_bits = read_bits(0, 6 * 8)
        header_bytes = np.packbits(header_bits)
        header = bytes(header_bytes.tolist())
        print(f"[DEBUG EXTRACT] Extracted Header: {header.hex()}")

        # 4) basic header validation
        magic = header[:2]
        if magic != cls.MAGIC_BYTES:
            print(f"[DEBUG EXTRACT] MAGIC MISMATCH! Found {magic} expected {cls.MAGIC_BYTES}")
            return None

        payload_len = int.from_bytes(header[2:], 'big')
        print(f"[DEBUG EXTRACT] Found Payload Length: {payload_len} bytes")

        # 5) sanity check length against image capacity
        if payload_len > (width * height * 3) // 8:
            print(f"[DEBUG EXTRACT] CRITICAL: Invalid length detected ({payload_len})")
            return None

        # 6) read payload bits, pack back into bytes and return
        payload_bits = read_bits(6 * 8, payload_len * 8)
        payload_bytes = np.packbits(payload_bits)
        payload = bytes(payload_bytes.tolist())
        print(f"[DEBUG EXTRACT] Extracted Payload (First 16 hex): {payload[:16].hex()}")
        return payload
