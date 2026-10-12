import re
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import requests
import yt_dlp

# Este servidor vive en api-backend/; la página está en la carpeta superior.
BASE_DIR = Path(__file__).resolve().parent.parent
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


VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_oembed_cache = {}
OEMBED_TTL = 7 * 24 * 3600


@app.get("/api/oembed/{video_id}")
def oembed(video_id: str):
    """Título y canal reales de un video de YouTube (API oEmbed), con caché."""
    if not VIDEO_ID.match(video_id):
        raise HTTPException(status_code=400, detail="Invalid video id")
    cached = _oembed_cache.get(video_id)
    if cached and time.time() - cached[0] < OEMBED_TTL:
        return cached[1]
    try:
        res = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=8,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))
    if res.status_code != 200:
        raise HTTPException(status_code=404 if res.status_code in (401, 403, 404) else 502, detail="oEmbed unavailable")
    data = res.json()
    result = {
        "title": data.get("title", ""),
        "author_name": data.get("author_name", ""),
        "thumbnail_url": data.get("thumbnail_url", ""),
    }
    _oembed_cache[video_id] = (time.time(), result)
    return result


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
