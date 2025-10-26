from flask import Flask, render_template, request, send_file
import os, datetime, subprocess

app = Flask(__name__)
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Set your FFmpeg path here
FFMPEG_PATH = "ffmpeg"  # Change to your ffmpeg.exe path

@app.route("/")
def home():
    return render_template("index.html")

# Video Cutter
@app.route("/cut", methods=["POST"])
def cut():
    file = request.files["video"]

    # Get hours, minutes, seconds for start and end
    start_h = int(request.form["start_h"])
    start_m = int(request.form["start_m"])
    start_s = int(request.form["start_s"])
    end_h = int(request.form["end_h"])
    end_m = int(request.form["end_m"])
    end_s = int(request.form["end_s"])

    # Convert to HH:MM:SS format (FFmpeg-friendly)
    start_time = f"{start_h:02d}:{start_m:02d}:{start_s:02d}"
    end_time = f"{end_h:02d}:{end_m:02d}:{end_s:02d}"

    in_path = os.path.join("uploads", file.filename)
    file.save(in_path)

    out_name = f"clip_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    out_path = os.path.join("outputs", out_name)

    # FFmpeg command for precise cutting
    command = [
        FFMPEG_PATH, "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", in_path,
        "-c", "copy",
        out_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return send_file(out_path, as_attachment=True)

# Merge Videos 
@app.route("/merge", methods=["POST"])
def merge():
    video1 = request.files["video1"]
    video2 = request.files["video2"]

    path1 = os.path.join("uploads", video1.filename)
    path2 = os.path.join("uploads", video2.filename)
    video1.save(path1)
    video2.save(path2)

    out_name = f"merged_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    out_path = os.path.join("outputs", out_name)

    # FFmpeg merge using filter_complex (safe for all videos)
    command = [
        FFMPEG_PATH, "-y",
        "-i", path1,
        "-i", path2,
        "-filter_complex", "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-strict", "experimental",
        out_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return send_file(out_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
