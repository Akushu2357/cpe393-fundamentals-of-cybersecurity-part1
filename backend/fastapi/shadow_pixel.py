import random
import math
import io
from PIL import Image
import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes

class ShadowCrypto:
    """Layer 1: Authenticated Encryption (AES-256 GCM)"""
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        return scrypt(password.encode(), salt, 32, N=2**14, r=8, p=1)

    @classmethod
    def encrypt(cls, plaintext: str, password: str) -> bytes:
        salt = get_random_bytes(16)
        key = cls.derive_key(password, salt)
        # Explicitly use 12-byte nonce (standard for GCM)
        nonce = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        return salt + nonce + tag + ciphertext

    @classmethod
    def decrypt(cls, encrypted_data: bytes, password: str) -> str:
        try:
            # Slicing based on fixed lengths: 
            # Salt(16) + Nonce(12) + Tag(16) + Ciphertext(rest)
            salt = encrypted_data[:16]
            nonce = encrypted_data[16:28]  # 12 bytes
            tag = encrypted_data[28:44]    # 16 bytes
            ciphertext = encrypted_data[44:]
            
            key = cls.derive_key(password, salt)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted_data.decode('utf-8')
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
    def calculate_psnr(cls, original_img, stego_img):
        arr1 = np.array(original_img.convert('RGB'), dtype=np.float32)
        arr2 = np.array(stego_img.convert('RGB'), dtype=np.float32)
        mse = np.mean((arr1 - arr2) ** 2)
        if mse == 0: return 100.0
        return 20 * math.log10(255.0 / math.sqrt(mse))

    @classmethod
    def embed_to_pil(cls, img, payload, seed_data):
        img = img.convert('RGB') # Force RGB to strip Alpha
        pixels = img.load()
        width, height = img.size
        
        full_payload = cls.MAGIC_BYTES + len(payload).to_bytes(4, 'big') + payload
        total_bits = len(full_payload) * 8
        
        print(f"[DEBUG EMBED] Payload Size: {len(payload)} bytes")
        print(f"[DEBUG EMBED] Total bits (inc. header): {total_bits}")
        print(f"[DEBUG EMBED] Header (6 bytes): {full_payload[:6].hex()}")

        if total_bits > width * height * 3:
            raise ValueError(f"Payload too large! Need {total_bits} bits, have {width*height*3}")

        coords = cls.get_pixel_sequence(width, height, seed_data)
        
        # Log first 3 coordinates for verification
        print(f"[DEBUG EMBED] First 3 coords: {coords[:3]}")

        bit_idx = 0
        for byte in full_payload:
            for i in range(7, -1, -1):
                bit = (byte >> i) & 1
                x, y, channel = coords[bit_idx]
                pixel_list = list(pixels[x, y])
                pixel_list[channel] = (pixel_list[channel] & ~1) | bit
                pixels[x, y] = tuple(pixel_list)
                bit_idx += 1
        
        print(f"[DEBUG EMBED] Last bit_idx used: {bit_idx}")
        return img

    @classmethod
    def extract_from_pil(cls, img, seed_data):
        img = img.convert('RGB')
        pixels = img.load()
        width, height = img.size
        coords = cls.get_pixel_sequence(width, height, seed_data)
        
        print(f"[DEBUG EXTRACT] Image size: {width}x{height}")
        print(f"[DEBUG EXTRACT] First 3 coords: {coords[:3]}")

        def get_bits(start_bit, count):
            bits = []
            for i in range(start_bit, start_bit + count):
                x, y, channel = coords[i]
                bits.append(pixels[x, y][channel] & 1)
            
            byte_list = []
            for i in range(0, len(bits), 8):
                byte = 0
                for bit in bits[i:i+8]:
                    byte = (byte << 1) | bit
                byte_list.append(byte)
            return bytes(byte_list)

        # 1. Read Header (6 bytes = 48 bits)
        header = get_bits(0, 6 * 8)
        print(f"[DEBUG EXTRACT] Extracted Header: {header.hex()}")

        magic = header[:2]
        if magic != cls.MAGIC_BYTES:
            print(f"[DEBUG EXTRACT] MAGIC MISMATCH! Found {magic} expected {cls.MAGIC_BYTES}")
            return None
            
        payload_len = int.from_bytes(header[2:], 'big')
        print(f"[DEBUG EXTRACT] Found Payload Length: {payload_len} bytes")

        # Basic Sanity Check for length
        if payload_len > (width * height * 3) // 8:
            print(f"[DEBUG EXTRACT] CRITICAL: Invalid length detected ({payload_len})")
            return None

        # 2. Read Payload
        payload = get_bits(6 * 8, payload_len * 8)
        print(f"[DEBUG EXTRACT] Extracted Payload (First 16 hex): {payload[:16].hex()}")
        return payload
