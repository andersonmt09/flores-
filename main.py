from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import requests
import yt_dlp

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"

# Solo se sirve lo que la página necesita: nunca el código del servidor ni .git.
PUBLIC_FILES = {"index.html", "musica.html", "playlist_generated.js"}
PUBLIC_DIRS = {"assets"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
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
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    results = []
    for entry in info.get('entries') or []:
        thumbnails = entry.get('thumbnails') or [{}]
        results.append({
            'title': entry.get('title'),
            'id': entry.get('id'),
            'thumbnail': thumbnails[0].get('url', ''),
            'duration': entry.get('duration')
        })
    return {"results": results}


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
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    url = info.get('url')
    if not url:
        raise HTTPException(status_code=404, detail="Stream not found")

    upstream = requests.get(url, stream=True, timeout=(10, 60))
    if not upstream.ok:
        upstream.close()
        raise HTTPException(status_code=502, detail="Upstream stream failed")

    def iterfile():
        with upstream:
            for chunk in upstream.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

    media_type = upstream.headers.get("Content-Type", "audio/mp4")
    return StreamingResponse(iterfile(), media_type=media_type)


def no_cache_index():
    return FileResponse(
        INDEX_FILE,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"},
    )


@app.get("/")
def serve_root():
    return no_cache_index()


@app.get("/{full_path:path}")
def serve_static(full_path: str):
    target = (BASE_DIR / full_path).resolve()
    try:
        relative = target.relative_to(BASE_DIR)
    except ValueError:
        raise HTTPException(status_code=404)

    parts = relative.parts
    allowed = (len(parts) == 1 and parts[0] in PUBLIC_FILES) or (len(parts) > 1 and parts[0] in PUBLIC_DIRS)
    if allowed and target.is_file():
        return FileResponse(target)
    if allowed:
        raise HTTPException(status_code=404)
    return no_cache_index()
