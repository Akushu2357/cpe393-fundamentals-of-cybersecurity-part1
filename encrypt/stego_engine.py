import random
import math
from PIL import Image
import numpy as np

class ShadowStego:
    """
    Shadow-Pixel Layer 2: Steganography (Randomized LSB)
    - Magic Bytes: "SP" (2 bytes)
    - Length Header: 4 bytes
    - Method: Randomized LSB (PRNG seeded with password/key)
    """
    
    MAGIC_BYTES = b"SP"
    HEADER_SIZE = 6 # 2 (SP) + 4 (Length)

    @staticmethod
    def get_pixel_sequence(width, height, seed_data):
        """
        Create a deterministic random sequence of pixel coordinates 
        based on the provided seed (e.g., hash of the password).
        """
        random.seed(seed_data)
        coords = [(x, y, c) for y in range(height) for x in range(width) for c in range(3)]
        random.shuffle(coords)
        return coords

    @classmethod
    def calculate_psnr(cls, original_path, stego_path):
        """
        Calculate Peak Signal-to-Noise Ratio (PSNR) to measure image quality loss.
        PSNR > 40dB is typically invisible to the human eye.
        """
        img1 = Image.open(original_path).convert('RGB')
        img2 = Image.open(stego_path).convert('RGB')
        
        arr1 = np.array(img1, dtype=np.float32)
        arr2 = np.array(img2, dtype=np.float32)
        
        mse = np.mean((arr1 - arr2) ** 2)
        if mse == 0:
            return 100.0
            
        max_pixel = 255.0
        psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        return psnr

    @classmethod
    def embed(cls, image_path, payload, output_path, seed_data):
        """
        Embeds bytes into a PNG image using Randomized LSB.
        Payload structure: [MAGIC_BYTES] + [LENGTH (4)] + [CRYPT_PAYLOAD]
        """
        img = Image.open(image_path).convert('RGB')
        pixels = img.load()
        width, height = img.size
        
        # Prepare full payload with header
        full_payload = cls.MAGIC_BYTES + len(payload).to_bytes(4, 'big') + payload
        total_bits = len(full_payload) * 8
        
        # Capacity Check
        if total_bits > width * height * 3:
            raise ValueError(f"Payload too large! Need {total_bits} bits, but only {width*height*3} available.")

        # Get randomized coordinates
        coords = cls.get_pixel_sequence(width, height, seed_data)
        
        # Embed bits
        bit_idx = 0
        for byte in full_payload:
            for i in range(7, -1, -1): # MSB to LSB
                bit = (byte >> i) & 1
                x, y, channel = coords[bit_idx]
                
                pixel_list = list(pixels[x, y])
                # Modify the LSB (Least Significant Bit)
                pixel_list[channel] = (pixel_list[channel] & ~1) | bit
                pixels[x, y] = tuple(pixel_list)
                
                bit_idx += 1
        
        img.save(output_path, "PNG")
        return True

    @classmethod
    def extract(cls, image_path, seed_data):
        """
        Extracts bytes from a PNG image using Randomized LSB.
        """
        img = Image.open(image_path).convert('RGB')
        pixels = img.load()
        width, height = img.size
        
        coords = cls.get_pixel_sequence(width, height, seed_data)
        
        def get_bits(start_bit, count):
            bits = []
            for i in range(start_bit, start_bit + count):
                x, y, channel = coords[i]
                bits.append(pixels[x, y][channel] & 1)
            
            # Convert bits to bytes
            byte_list = []
            for i in range(0, len(bits), 8):
                byte = 0
                for bit in bits[i:i+8]:
                    byte = (byte << 1) | bit
                byte_list.append(byte)
            return bytes(byte_list)

        # 1. Read Header (6 bytes = 48 bits)
        header = get_bits(0, cls.HEADER_SIZE * 8)
        magic = header[:2]
        if magic != cls.MAGIC_BYTES:
            return None # Not a Shadow-Pixel file or wrong password (wrong seed)
            
        payload_len = int.from_bytes(header[2:], 'big')
        
        # 2. Read Payload
        payload = get_bits(cls.HEADER_SIZE * 8, payload_len * 8)
        return payload

# --- Demo Layer 2 (Mock Execution) ---
if __name__ == "__main__":
    print("[*] Stego Engine Ready.")
    # In a real run, you would provide a valid PNG and a payload from crypto.py
