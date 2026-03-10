from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
from shadow_pixel import ShadowCrypto, ShadowStego

app = FastAPI(title="Watermark Mock (FastAPI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    message: str = Form(...),
    password: str = Form(...)
):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        # 1. Encrypt
        payload = ShadowCrypto.encrypt(message, password)
        
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
            
        # 2. Decrypt
        decrypted = ShadowCrypto.decrypt(payload, password)
        if not decrypted:
            return JSONResponse(status_code=400, content={"error": "Decryption failed (Integrity check failed)."})
            
        return {"ok": True, "message": decrypted}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4001)
