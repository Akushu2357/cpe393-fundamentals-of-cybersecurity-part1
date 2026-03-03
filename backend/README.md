# Mock Backend for Watermark App

This is a small Express mock server implementing two endpoints used by the frontend during development:

- `POST /api/watermark/create` — multipart/form-data: `file` (required), `type` (`text` or `image`), `text`, `pos` (`top-left`|`center`|`bottom-right`), `opacity` (0-1), optional `logo` for image watermark. For images the server applies a simple watermark using `jimp` and returns the processed image. For PDFs the server echoes the uploaded PDF back (mock behavior).
- `POST /api/watermark/remove` — multipart/form-data: `file` (required). Mock: returns the original file as `removed-<name>`.

Quick start:

```bash
cd backend
npm install
npm start
```

The server runs on port `4000` by default. CORS is enabled for local development.
