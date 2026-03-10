from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Protocol.KDF import scrypt
import os

def encrypt_message(plaintext, password):
    """
    ฟังก์ชันสำหรับการเข้ารหัสข้อความ (AES-256) 
    Output:จะเป็นก้อนข้อมูล bytes (Salt + IV + Ciphertext) เพื่อใช้นำไปฝังในภาพ
    """
    # 1 สร้างค่ามาสุ่มใส่ password เพื่อให้เดาไม่ได้
    salt = os.urandom(16)
    # 2 สร้าง Key จาก Password
    key = scrypt(password, salt, 32, N=2**14, r=8, p=1)
    # 3 สร้าง IV (16 bytes)
    iv = os.urandom(16)
    # 4 เข้ารหัส AES-256 แบบ CBC Mode
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
    ciphertext = cipher.encrypt(padded_data)
    return salt + iv + ciphertext

# --- ตัวอย่างการใช้งาน ---
if __name__ == "__main__":
    msg = "You Never Walk Alone"
    pwd = "key"
    
    result = encrypt_message(msg, pwd)
    
    print(f"ข้อความต้นฉบับ: {msg}")
    print(f"ขนาดข้อมูลที่ได้: {len(result)} bytes")
    print(f"ข้อมูลแบบ Hex (สำหรับส่งต่อ): {result.hex()}")
