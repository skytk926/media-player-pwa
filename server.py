"""
Combined server: PWA + faster-whisper (CTranslate2, int8, low memory).
Usage:
    python3 server.py                      # tiny model (~40MB RAM)
    WHISPER_MODEL=base python3 server.py   # base (~80MB, more accurate)
    WHISPER_MODEL=small python3 server.py  # small (~250MB, best)
Open: http://localhost:8900
"""
import gc
import os
import subprocess
import tempfile
import wave
from urllib.parse import unquote

import numpy as np
from faster_whisper import WhisperModel
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

MODEL_NAME = os.environ.get("WHISPER_MODEL", "tiny")
PORT = int(os.environ.get("PORT", "8900"))
CHUNK_SEC = 30
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Player + Whisper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None


def get_model():
    global model
    if model is None:
        print(f"Loading faster-whisper model: {MODEL_NAME} (int8) ...")
        model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")
        print("Model loaded.")
    return model


@app.post("/transcribe")
async def transcribe(request: Request):
    filename = unquote(request.headers.get("X-Filename", "audio.wav"))
    suffix = os.path.splitext(filename)[1] or ".wav"

    # Stream body directly to temp file
    tmp_fd, src_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            async for chunk in request.stream():
                f.write(chunk)
    except Exception:
        os.unlink(src_path)
        raise

    wav_path = src_path + ".wav"

    try:
        # Convert to 16kHz mono WAV
        subprocess.run(
            ["ffmpeg", "-y", "-i", src_path,
             "-ac", "1", "-ar", "16000", "-f", "wav", wav_path],
            capture_output=True, check=True
        )

        m = get_model()
        all_segments = []

        # faster-whisper handles chunking internally, but we still stream WAV
        # to keep memory low for large files
        with wave.open(wav_path, "rb") as wf:
            sr = wf.getframerate()
            total_frames = wf.getnframes()
            total_sec = total_frames / sr
            chunk_frames = CHUNK_SEC * sr
            n_chunks = max(1, int(np.ceil(total_frames / chunk_frames)))

            for i, start_frame in enumerate(range(0, total_frames, chunk_frames)):
                wf.setpos(start_frame)
                frames_to_read = min(chunk_frames, total_frames - start_frame)
                raw = wf.readframes(frames_to_read)
                audio = (
                    np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                )
                offset_sec = start_frame / sr

                segs, _ = m.transcribe(audio, language="ja", beam_size=1)
                for seg in segs:
                    text = seg.text.strip()
                    if text:
                        all_segments.append({
                            "start": round(offset_sec + seg.start, 2),
                            "end": round(offset_sec + seg.end, 2),
                            "text": text,
                        })

                del audio, segs
                gc.collect()

        return JSONResponse({
            "language": "ja",
            "segments": all_segments,
        })

    finally:
        for p in (src_path, wav_path):
            if os.path.exists(p):
                os.unlink(p)
        gc.collect()


@app.get("/health")
async def health():
    import socket
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model": MODEL_NAME,
        "engine": "faster-whisper (CTranslate2 int8)",
        "ips": ips,
    }


@app.get("/{filename:path}")
async def serve_static(filename: str):
    path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(path):
        return FileResponse(path)
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/")
async def root():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


if __name__ == "__main__":
    print(f"Server :{PORT}  model={MODEL_NAME}  engine=faster-whisper(int8)")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
