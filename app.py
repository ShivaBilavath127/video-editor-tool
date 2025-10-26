from flask import Flask, render_template, request, send_file, jsonify
import os, datetime, subprocess, tempfile

app = Flask(__name__)

# Temporary directories (Render doesn't persist files)
UPLOAD_FOLDER = tempfile.mkdtemp()
OUTPUT_FOLDER = tempfile.mkdtemp()

# FFmpeg path (Render automatically includes ffmpeg in environment)
FFMPEG_PATH = "ffmpeg"  # Updated with better error handling

@app.route("/")
def home():
    return render_template("index.html")

# ---------- VIDEO CUT ----------
@app.route("/cut", methods=["POST"])
def cut():
    try:
        file = request.files["video"]
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        # Start and End times
        start_h = int(request.form.get("start_h", 0))
        start_m = int(request.form.get("start_m", 0))
        start_s = int(request.form.get("start_s", 0))
        end_h = int(request.form.get("end_h", 0))
        end_m = int(request.form.get("end_m", 0))
        end_s = int(request.form.get("end_s", 0))

        start_time = f"{start_h:02d}:{start_m:02d}:{start_s:02d}"
        end_time = f"{end_h:02d}:{end_m:02d}:{end_s:02d}"

        in_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(in_path)

        out_name = f"clip_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)

        # FFmpeg command
        command = [
            FFMPEG_PATH, "-y",
            "-ss", start_time,
            "-to", end_time,
            "-i", in_path,
            "-c", "copy",
            out_path
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(out_path):
            return jsonify({"error": "Video processing failed"}), 500

        return send_file(out_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- MERGE VIDEOS ----------
@app.route("/merge", methods=["POST"])
def merge():
    try:
        video1 = request.files["video1"]
        video2 = request.files["video2"]

        path1 = os.path.join(UPLOAD_FOLDER, video1.filename)
        path2 = os.path.join(UPLOAD_FOLDER, video2.filename)
        video1.save(path1)
        video2.save(path2)

        out_name = f"merged_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)

        command = [
            FFMPEG_PATH, "-y",
            "-i", path1,
            "-i", path2,
            "-filter_complex",
            "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            out_path
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(out_path):
            return jsonify({"error": "Merge failed"}), 500

        return send_file(out_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)