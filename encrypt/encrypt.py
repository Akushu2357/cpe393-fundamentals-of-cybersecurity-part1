from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
import os

class ShadowCrypto:
    """
    Shadow-Pixel Layer 1: Cryptography (Authenticated Encryption)
    Uses AES-256 GCM for both confidentiality and integrity.
    """
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        # Scrypt is a memory-hard KDF, resistant to GPU brute-forcing.
        return scrypt(password.encode(), salt, 32, N=2**14, r=8, p=1)

    @classmethod
    def encrypt(cls, plaintext: str, password: str) -> bytes:
        """
        Input: Plaintext string, Password string
        Output: [Salt(16)] + [Nonce(12)] + [Tag(16)] + [Ciphertext]
        """
        salt = get_random_bytes(16)
        key = cls.derive_key(password, salt)
        
        # GCM mode uses a Nonce (Number used once) instead of an IV.
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        # Salt + Nonce + Tag + Ciphertext is all we need to decrypt.
        return salt + cipher.nonce + tag + ciphertext

    @classmethod
    def decrypt(cls, encrypted_data: bytes, password: str) -> str:
        """
        Input: Encrypted bytes, Password string
        Output: Plaintext string (if password is correct)
        """
        try:
            # Extract components (Fixed byte lengths)
            salt = encrypted_data[:16]
            nonce = encrypted_data[16:28]  # AES-GCM default nonce is 12 bytes
            tag = encrypted_data[28:44]    # Tag is 16 bytes
            ciphertext = encrypted_data[44:]
            
            key = cls.derive_key(password, salt)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            
            # Decrypt and verify tag simultaneously
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted_data.decode('utf-8')
            
        except (ValueError, KeyError, IndexError):
            # ValueError: Tag verification failed (Wrong password or tampered data)
            # KeyError: Missing key parts
            return None

# --- Testing Layer 1 ---
if __name__ == "__main__":
    msg = "You Never Walk Alone"
    pwd = "key"
    
    # Encrypt
    secret_payload = ShadowCrypto.encrypt(msg, pwd)
    print(f"[*] ข้อความต้นฉบับ: {msg}")
    print(f"[*] ขนาดข้อมูลที่ได้: {len(secret_payload)} bytes")
    print(f"[*] ข้อมูลแบบ Hex (สำหรับส่งต่อ): {secret_payload.hex()[:64]}...")

    # Decrypt (Success Case)
    decrypted = ShadowCrypto.decrypt(secret_payload, pwd)
    print(f"[+] Decrypted (Correct Password): {decrypted}")

    # Decrypt (Fail Case)
    failed = ShadowCrypto.decrypt(secret_payload, "wrong_password")
    print(f"[-] Decrypted (Wrong Password): {failed if failed else 'DECRYPTION FAILED'}")
