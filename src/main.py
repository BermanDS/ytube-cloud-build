import os
import glob
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)


@app.post("/subtitles")
def subtitles():
    payload = request.get_json(silent=True) or {}

    url = payload.get("url")
    lang = payload.get("lang", "en")

    if not url:
        return jsonify({"error": "url is required"}), 400

    workdir = "/tmp/subtitles"
    os.makedirs(workdir, exist_ok=True)

    output_template = os.path.join(
        workdir,
        "%(id)s.%(ext)s",
    )

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [lang],
        "subtitlesformat": "vtt",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        video_id = info.get("id")

        # yt-dlp typically writes something like:
        # /tmp/subtitles/VIDEO_ID.en.vtt
        matches = glob.glob(
            os.path.join(workdir, f"{video_id}.{lang}*.vtt")
        )

        if not matches:
            return jsonify({
                "error": "No subtitles found",
                "video_id": video_id,
                "available_manual": list(
                    (info.get("subtitles") or {}).keys()
                ),
                "available_auto": list(
                    (info.get("automatic_captions") or {}).keys()
                ),
            }), 404

        subtitle_path = matches[0]

        with open(subtitle_path, "r", encoding="utf-8") as f:
            subtitle_text = f.read()

        return jsonify({
            "video_id": video_id,
            "title": info.get("title"),
            "language": lang,
            "subtitles": subtitle_text,
        })

    except Exception as exc:
        return jsonify({
            "error": str(exc),
        }), 500


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
    )
