import sys
import os
from encrypt import ShadowCrypto
from stego_engine import ShadowStego

def shadow_pixel_app():
    print("\n" + "="*40)
    print("   SHADOW-PIXEL: STEGO-CRYPTO ENGINE")
    print("="*40)
    
    choice = input("[1] Hide Data (Embed)\n[2] Extract Data (Recover)\n[>] Choice: ")

    if choice == "1":
        # Inputs
        image_path = input("[?] Enter Path to Original PNG: ")
        message = input("[?] Message to hide: ")
        password = input("[?] Password: ")
        output_path = "stego_output.png"
        
        # 1. Encryption
        print("\n[*] Layer 1: Encrypting message...")
        payload = ShadowCrypto.encrypt(message, password)
        print(f"[+] Encrypted payload size: {len(payload)} bytes")
        
        # 2. Steganography (Embed)
        print("[*] Layer 2: Embedding into image (RLSB)...")
        try:
            # We use the password (or a derivative) as the seed for RLSB
            seed = password 
            ShadowStego.embed(image_path, payload, output_path, seed)
            print(f"[+] Success! Output saved as: {output_path}")
            
            # 3. Quality Check (PSNR)
            psnr = ShadowStego.calculate_psnr(image_path, output_path)
            print(f"[*] Visual Fidelity (PSNR): {psnr:.2f} dB")
            if psnr > 40:
                print("[!] Result: High Quality (Invisible to human eye)")
            else:
                print("[!] Warning: Image degradation detected.")
                
        except Exception as e:
            print(f"[!] Error: {str(e)}")

    elif choice == "2":
        # Inputs
        stego_path = input("[?] Enter Path to Stego PNG: ")
        password = input("[?] Password: ")
        
        print("\n[*] Layer 2: Attempting extraction (RLSB)...")
        seed = password
        extract_payload = ShadowStego.extract(stego_path, seed)
        
        if extract_payload is None:
            print("[!] Critical: Magic Bytes not found. Incorrect Password or Invalid File.")
            return

        print("[*] Layer 1: Decrypting payload (AES-GCM)...")
        decrypted_msg = ShadowCrypto.decrypt(extract_payload, password)
        
        if decrypted_msg:
            print(f"\n[SUCCESS] Decrypted Message: {decrypted_msg}")
        else:
            print("[!] Decryption Failed (Integrity check failed).")

if __name__ == "__main__":
    shadow_pixel_app()
