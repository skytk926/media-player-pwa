#!/usr/bin/env python3
"""
Mac上で音声/動画を文字起こし → VTT字幕ファイル出力
使い方: python3 transcribe.py ファイル名.mp3
出力: ファイル名.vtt
"""
import sys, os, subprocess, tempfile, wave, gc
import numpy as np
from faster_whisper import WhisperModel

MODEL_NAME = os.environ.get("WHISPER_MODEL", "tiny")
CHUNK_SEC = 30

def main(input_file):
    if not os.path.exists(input_file):
        print(f"ファイルが見つかりません: {input_file}")
        sys.exit(1)

    print(f"モデル読込中: {MODEL_NAME} ...")
    model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")

    # Convert to 16kHz mono WAV
    print("音声変換中...")
    tmp_wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_file, "-ac", "1", "-ar", "16000", "-f", "wav", tmp_wav],
        capture_output=True, check=True
    )

    # Chunked transcription
    all_segments = []
    with wave.open(tmp_wav, "rb") as wf:
        sr = wf.getframerate()
        total_frames = wf.getnframes()
        total_sec = total_frames / sr
        chunk_frames = CHUNK_SEC * sr
        n_chunks = max(1, int(np.ceil(total_frames / chunk_frames)))

        for i, start_frame in enumerate(range(0, total_frames, chunk_frames)):
            wf.setpos(start_frame)
            frames_to_read = min(chunk_frames, total_frames - start_frame)
            raw = wf.readframes(frames_to_read)
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            offset_sec = start_frame / sr

            print(f"認識中 {i+1}/{n_chunks} ...")
            segs, _ = model.transcribe(audio, language="ja", beam_size=1)
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

    os.unlink(tmp_wav)

    if not all_segments:
        print("字幕なし（音声認識結果が空）")
        sys.exit(0)

    # Generate VTT
    output = os.path.splitext(input_file)[0] + ".vtt"
    with open(output, "w") as f:
        f.write("WEBVTT\n\n")
        for seg in all_segments:
            def ts(s):
                h = int(s // 3600)
                m = int((s % 3600) // 60)
                sec = int(s % 60)
                ms = int((s - int(s)) * 1000)
                return f"{h:02d}:{m:02d}:{sec:02d}.{ms:03d}"
            f.write(f"{ts(seg['start'])} --> {ts(seg['end'])}\n")
            f.write(f"{seg['text']}\n\n")

    print(f"完了: {output} ({len(all_segments)}件)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python3 transcribe.py <ファイル名>")
        sys.exit(1)
    main(sys.argv[1])
