from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
from shadow_pixel import ShadowCrypto, ShadowStego
import base64
import struct

app = FastAPI(title="Watermark Mock (FastAPI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-PSNR"],
)


def _image_from_bytes(b: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(b))
    return img.convert("RGBA")


def _compose_text_watermark(base: Image.Image, text: str, pos: str, opacity: float) -> Image.Image:
    w, h = base.size
    layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)
    # choose a reasonable font size
    try:
        font_size = max(20, w // 15)
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    # textbbox returns (left, top, right, bottom)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_w = right - left
    text_h = bottom - top
    
    if pos == "top-left":
        x, y = 24, 24
    elif pos == "bottom-right":
        x, y = w - text_w - 24, h - text_h - 24
    else:
        x, y = (w - text_w) // 2, (h - text_h) // 2

    alpha = int(255 * max(0, min(1, opacity)))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))

    return Image.alpha_composite(base, layer)


def _compose_image_watermark(base: Image.Image, logo_bytes: bytes, pos: str, opacity: float) -> Image.Image:
    w, h = base.size
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    # resize logo to ~22% of width
    lw = int(w * 0.22)
    ratio = logo.height / logo.width if logo.width else 1
    lh = int(lw * ratio)
    logo = logo.resize((lw, lh), Image.LANCZOS)

    # apply opacity to logo
    if opacity < 1.0:
        alpha = logo.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        logo.putalpha(alpha)

    if pos == "top-left":
        lx, ly = 24, 24
    elif pos == "bottom-right":
        lx, ly = w - lw - 24, h - lh - 24
    else:
        lx, ly = (w - lw) // 2, (h - lh) // 2

    base.paste(logo, (lx, ly), logo)
    return base


@app.get("/")
async def root():
    return {"ok": True, "msg": "Watermark mock (FastAPI)"}


@app.post("/api/watermark/create")
async def create_watermark(
    file: UploadFile = File(...),
    type: Optional[str] = Form("text"),
    text: Optional[str] = Form("SAMPLE"),
    pos: Optional[str] = Form("center"),
    opacity: Optional[float] = Form(0.4),
    logo: Optional[UploadFile] = File(None),
):
    try:
        contents = await file.read()
        mime = file.content_type or "application/octet-stream"

        # handle images
        if mime.startswith("image/"):
            img = _image_from_bytes(contents)
            if type == "text":
                out = _compose_text_watermark(img, text or "SAMPLE", pos or "center", float(opacity))
            else:
                if not logo:
                    return JSONResponse(status_code=400, content={"error": "logo required for image watermark type"})
                logo_bytes = await logo.read()
                out = _compose_image_watermark(img, logo_bytes, pos or "center", float(opacity))

            buf = io.BytesIO()
            out = out.convert("RGB")
            out.save(buf, format="JPEG")
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/jpeg", headers={"Content-Disposition": f"attachment; filename=watermarked-{file.filename}"})

        # fallback / mock for PDFs and others: echo back
        buf = io.BytesIO(contents)
        buf.seek(0)
        return StreamingResponse(buf, media_type=mime, headers={"Content-Disposition": f"attachment; filename=watermarked-{file.filename}"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/watermark/remove")
async def remove_watermark(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        buf = io.BytesIO(contents)
        buf.seek(0)
        return StreamingResponse(buf, media_type=file.content_type or "application/octet-stream", headers={"Content-Disposition": f"attachment; filename=removed-{file.filename}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/stego/hide")
async def stego_hide(
    file: UploadFile = File(...),
    message: Optional[str] = Form(None),
    password: str = Form(...),
    embed_image: Optional[UploadFile] = File(None),
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # Build payload: support only main message (type 1) and optional image (type 2)
        def _build_payload(message_bytes: bytes | None, embed_image_bytes: bytes | None, embed_image_mime: str | None) -> bytes:
            parts = []
            if message_bytes:
                parts.append(b"\x01" + len(message_bytes).to_bytes(4, 'big') + message_bytes)
            if embed_image_bytes is not None:
                mime_b = (embed_image_mime or "application/octet-stream").encode('utf-8')
                parts.append(b"\x02" + len(mime_b).to_bytes(1, 'big') + mime_b + len(embed_image_bytes).to_bytes(4, 'big') + embed_image_bytes)
            return b"".join(parts)

        message_bytes = message.encode('utf-8') if message else None
        embed_img_bytes = None
        embed_img_mime = None
        if embed_image:
            embed_img_bytes = await embed_image.read()
            embed_img_mime = embed_image.content_type or 'application/octet-stream'

        payload_bytes = _build_payload(message_bytes, embed_img_bytes, embed_img_mime)

        # 1. Encrypt (pass raw bytes)
        payload = ShadowCrypto.encrypt(payload_bytes, password)

        # 2. Embed (RLSB using password as seed)
        stego_img = ShadowStego.embed_to_pil(img, payload, password)

        # 3. Calculate PSNR (Optional but good for quality check)
        psnr = ShadowStego.calculate_psnr(img, stego_img)

        buf = io.BytesIO()
        stego_img.save(buf, format="PNG", optimize=False, compress_level=0)
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=shadow-{file.filename}",
                "X-PSNR": f"{psnr:.2f}"
            }
        )
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post("/api/stego/extract")
async def stego_extract(
    file: UploadFile = File(...),
    password: str = Form(...)
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # 1. Extract payload
        payload = ShadowStego.extract_from_pil(img, password)
        if not payload:
            return JSONResponse(status_code=400, content={"error": "No hidden data found or wrong password."})

        # 2. Decrypt (returns raw bytes)
        decrypted_bytes = ShadowCrypto.decrypt(payload, password)
        if decrypted_bytes is None:
            return JSONResponse(status_code=400, content={"error": "Decryption failed (Integrity check failed)."})

        # 3. Parse TLV (type 1=text, type 2=image)
        i = 0
        result = {"ok": True}
        try:
            while i < len(decrypted_bytes):
                t = decrypted_bytes[i]
                i += 1
                if t == 1:
                    length = int.from_bytes(decrypted_bytes[i:i+4], 'big')
                    i += 4
                    text = decrypted_bytes[i:i+length].decode('utf-8')
                    i += length
                    if 'message' not in result:
                        result['message'] = text
                    else:
                        result.setdefault('extra_text', []).append(text)
                elif t == 2:
                    mime_len = decrypted_bytes[i]
                    i += 1
                    mime = decrypted_bytes[i:i+mime_len].decode('utf-8')
                    i += mime_len
                    length = int.from_bytes(decrypted_bytes[i:i+4], 'big')
                    i += 4
                    img_bytes = decrypted_bytes[i:i+length]
                    i += length
                    b64 = base64.b64encode(img_bytes).decode('ascii')
                    result['embedded_image'] = f"data:{mime};base64,{b64}"
                else:
                    break
        except Exception:
            try:
                result = {"ok": True, "message": decrypted_bytes.decode('utf-8')}
            except Exception:
                result = {"ok": True, "raw_bytes": base64.b64encode(decrypted_bytes).decode('ascii')}

        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4001)
