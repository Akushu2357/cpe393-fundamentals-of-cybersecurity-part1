# Frontend

React + Vite frontend for the Watermark Studio UI.

Requirements
- Node.js 16+ and npm or yarn

Install and run (development)
```bash
cd frontend
npm install
npm run dev
```

Build for production
```bash
npm run build
```

After running `npm run dev`, Vite will print the local dev URL (usually http://localhost:5173).

API configuration
The frontend client uses `VITE_API_BASE` (environment variable) or the default value in `frontend/src/api.js` to determine the backend base URL. Set `VITE_API_BASE` to `http://localhost:4001` to use the FastAPI backend shipped in this repo.

Key directories
- `src/` — main React source
- `src/components/` — UI components (e.g. `ShadowPixelForm.jsx`, `WatermarkForm.jsx`)
- `index.html`, `vite.config.js` — Vite config and entry

If you want more detailed usage examples for the components or the API client, I can add them.