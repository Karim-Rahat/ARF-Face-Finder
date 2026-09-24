from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import threading
import time
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_file
from send2trash import send2trash
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parent
DATA = ROOT / ".facefinder"
MODELS = DATA / "models"
UPLOADS = DATA / "uploads"
CACHE = DATA / "cache.sqlite3"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
MODEL_URLS = {
    "face_detection_yunet_2023mar.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
}

app = Flask(__name__, template_folder="facefinder_templates", static_folder="facefinder_static")
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024


@dataclass
class Job:
    id: str
    folder: Path
    reference: Path
    threshold: float
    status: str = "queued"
    total: int = 0
    processed: int = 0
    matches: list[dict] = field(default_factory=list)
    paths: dict[str, Path] = field(default_factory=dict)
    error: str | None = None
    current: str = ""
    started: float = field(default_factory=time.time)


jobs: dict[str, Job] = {}
engine_lock = threading.Lock()


def setup() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(CACHE) as db:
        db.execute("CREATE TABLE IF NOT EXISTS embeddings(path TEXT,size INTEGER,mtime INTEGER,faces TEXT,PRIMARY KEY(path,size,mtime))")


def download_models() -> None:
    for name, url in MODEL_URLS.items():
        target = MODELS / name
        if target.exists() and target.stat().st_size > 100_000:
            continue
        temp = target.with_suffix(".download")
        req = urllib.request.Request(url, headers={"User-Agent": "FaceFinder/1.0"})
        with urllib.request.urlopen(req, timeout=180) as response, temp.open("wb") as output:
            shutil.copyfileobj(response, output)
        if temp.stat().st_size < 100_000:
            temp.unlink(missing_ok=True)
            raise RuntimeError(f"Download of {name} was incomplete.")
        temp.replace(target)


class FaceEngine:
    def __init__(self) -> None:
        self.detector = cv2.FaceDetectorYN.create(str(MODELS / "face_detection_yunet_2023mar.onnx"), "", (320, 320), .78, .3, 5000)
        self.recognizer = cv2.FaceRecognizerSF.create(str(MODELS / "face_recognition_sface_2021dec.onnx"), "")

    def extract(self, path: Path) -> list[dict]:
        try:
            image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            return []
        if image is None or not image.size:
            return []
        height, width = image.shape[:2]
        scale = min(1.0, 1600 / max(height, width))
        work = cv2.resize(image, None, fx=scale, fy=scale) if scale < 1 else image
        wh, ww = work.shape[:2]
        self.detector.setInputSize((ww, wh))
        _, detected = self.detector.detect(work)
        if detected is None:
            return []
        faces = []
        for face in detected:
            # Ignore malformed detector output instead of aborting the scan.
            if face.shape[0] < 14 or not np.isfinite(face).all():
                continue
            feature = self.recognizer.feature(self.recognizer.alignCrop(work, face)).flatten().astype(np.float32)
            norm = float(np.linalg.norm(feature))
            if not norm:
                continue
            feature /= norm
            x, y, w, h = (face[:4] / scale).tolist()
            faces.append({"embedding": feature, "box": [max(0, round(x)), max(0, round(y)), round(w), round(h)], "area": w * h})
        return faces


def cached(path: Path) -> list[dict] | None:
    stat = path.stat()
    with sqlite3.connect(CACHE) as db:
        row = db.execute("SELECT faces FROM embeddings WHERE path=? AND size=? AND mtime=?", (str(path), stat.st_size, stat.st_mtime_ns)).fetchone()
    if not row:
        return None
    return [{"embedding": np.asarray(x["embedding"], dtype=np.float32), "box": x["box"], "area": x["area"]} for x in json.loads(row[0])]


def save_cache(path: Path, faces: list[dict]) -> None:
    stat = path.stat()
    packed = [{"embedding": x["embedding"].tolist(), "box": x["box"], "area": x["area"]} for x in faces]
    with sqlite3.connect(CACHE) as db:
        db.execute("DELETE FROM embeddings WHERE path=?", (str(path),))
        db.execute("INSERT INTO embeddings VALUES(?,?,?,?)", (str(path), stat.st_size, stat.st_mtime_ns, json.dumps(packed)))


def run_scan(job: Job) -> None:
    try:
        job.status = "preparing"
        setup()
        download_models()
        with engine_lock:
            engine = FaceEngine()
            refs = engine.extract(job.reference)
            if not refs:
                raise ValueError("No clear face was found in the reference photo. Try a well-lit, front-facing photo.")
            reference = max(refs, key=lambda item: item["area"])["embedding"]
            images = sorted(p for p in job.folder.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS)
            job.total = len(images)
            if not images:
                raise ValueError("No supported images were found in that folder.")
            job.status = "scanning"
            for index, path in enumerate(images, 1):
                job.current = path.name
                try:
                    faces = cached(path)
                    if faces is None:
                        faces = engine.extract(path)
                        save_cache(path, faces)
                    candidates = [(float(np.dot(reference, f["embedding"])), f["box"]) for f in faces]
                    if candidates:
                        score, box = max(candidates, key=lambda item: item[0])
                        if score >= job.threshold:
                            result_id = hashlib.sha256(f"{job.id}:{path}".encode()).hexdigest()[:20]
                            job.paths[result_id] = path
                            job.matches.append({"id": result_id, "name": path.name, "relative": str(path.relative_to(job.folder)), "score": round(score * 100, 1), "box": box})
                            job.matches.sort(key=lambda item: item["score"], reverse=True)
                except (OSError, ValueError, cv2.error):
                    pass
                job.processed = index
        job.current = ""
        job.status = "complete"
    except Exception as exc:
        job.status = "error"
        job.error = str(exc)


def get_job(job_id: str) -> Job:
    job = jobs.get(job_id)
    if not job:
        abort(404)
    return job


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/scan")
def start_scan():
    folder = Path(request.form.get("folder", "").strip().strip('"')).expanduser().resolve()
    reference = request.files.get("reference")
    try:
        threshold = float(request.form.get("threshold", ".42"))
    except ValueError:
        return jsonify(error="Invalid match strictness."), 400
    if not folder.is_dir():
        return jsonify(error="That photo folder does not exist or cannot be opened."), 400
    if not reference or not reference.filename:
        return jsonify(error="Choose a reference face photo."), 400
    if Path(reference.filename).suffix.lower() not in EXTENSIONS:
        return jsonify(error="Choose a JPG, PNG, WebP, BMP, or TIFF photo."), 400
    if not .25 <= threshold <= .75:
        return jsonify(error="Match strictness must be between 25% and 75%."), 400
    setup()
    job_id = uuid.uuid4().hex
    ref_path = UPLOADS / f"{job_id}-{secure_filename(reference.filename) or 'reference.jpg'}"
    reference.save(ref_path)
    jobs[job_id] = Job(job_id, folder, ref_path, threshold)
    threading.Thread(target=run_scan, args=(jobs[job_id],), daemon=True).start()
    return jsonify(id=job_id)


@app.get("/api/jobs/<job_id>")
def status(job_id: str):
    job = get_job(job_id)
    return jsonify(id=job.id, status=job.status, total=job.total, processed=job.processed, matches=job.matches, error=job.error, current=job.current, elapsed=round(time.time() - job.started, 1))


@app.get("/api/jobs/<job_id>/images/<result_id>")
def image(job_id: str, result_id: str):
    path = get_job(job_id).paths.get(result_id)
    if not path or not path.is_file():
        abort(404)
    return send_file(path, conditional=True, max_age=3600)


@app.post("/api/jobs/<job_id>/copy")
def copy(job_id: str):
    job, payload = get_job(job_id), request.get_json(silent=True) or {}
    destination_text, ids = str(payload.get("destination", "")).strip().strip('"'), payload.get("ids", [])
    if not destination_text or not isinstance(ids, list):
        return jsonify(error="Choose files and enter a destination folder."), 400
    destination = Path(destination_text).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    count = 0
    for result_id in ids:
        source = job.paths.get(str(result_id))
        if not source or not source.is_file():
            continue
        target, suffix = destination / source.name, 1
        while target.exists():
            target = destination / f"{source.stem}_{suffix}{source.suffix}"
            suffix += 1
        shutil.copy2(source, target)
        count += 1
    return jsonify(message=f"Copied {count} photo{'s' if count != 1 else ''}.")


@app.post("/api/jobs/<job_id>/delete")
def delete(job_id: str):
    job, payload = get_job(job_id), request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    if payload.get("confirmation") != "DELETE" or not isinstance(ids, list):
        return jsonify(error="Deletion was not confirmed."), 400
    deleted = []
    for result_id in ids:
        source = job.paths.get(str(result_id))
        if source and source.is_file():
            send2trash(str(source))
            deleted.append(str(result_id))
    return jsonify(message=f"Moved {len(deleted)} photo{'s' if len(deleted) != 1 else ''} to the Recycle Bin.", deleted=deleted)


if __name__ == "__main__":
    setup()
    app.run(host="127.0.0.1", port=5173, debug=False, threaded=True)
