from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
def search(q: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_flat': True,
        'default_search': 'ytsearch10',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(q, download=False)
            entries = info.get('entries', [])
            results = []
            for entry in entries:
                results.append({
                    'title': entry.get('title'),
                    'id': entry.get('id'),
                    'thumbnail': entry.get('thumbnails', [{}])[0].get('url', ''),
                    'duration': entry.get('duration')
                })
            return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream/{video_id}")
def stream(video_id: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extractor_args': {'youtube': {'client': ['android', 'ios']}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            url = info.get('url')
            if not url:
                raise HTTPException(status_code=404, detail="Stream not found")
            
            def iterfile():
                with requests.get(url, stream=True) as r:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk

            return StreamingResponse(iterfile(), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug_source")
def debug_source():
    with open(__file__, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f"<pre>{f.read()}</pre>")

@app.get("/")
def serve_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"})

@app.get("/{full_path:path}")
def serve_static(full_path: str):
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    return FileResponse("index.html")
