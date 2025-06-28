from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
from utils import extract_student_name, extract_student_answers
from skema_parser import extract_skema
import tempfile

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "/tmp"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
results_cache = []

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/grade", methods=["POST"])
def grade():
    skema_file = request.files.get("skema")
    student_file = request.files.get("student")
    school = request.form.get("school", "SJKC")

    if not skema_file or not student_file:
        return jsonify({"error": "缺少 skema 或 student 文件"}), 400

    if not allowed_file(skema_file.filename) or not allowed_file(student_file.filename):
        return jsonify({"error": "上传的文件类型不被允许"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=secure_filename(skema_file.filename)) as skema_temp:
        skema_file.save(skema_temp.name)
        skema_path = skema_temp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=secure_filename(student_file.filename)) as student_temp:
        student_file.save(student_temp.name)
        student_path = student_temp.name

    skema_answers = extract_skema(skema_path)
    total_questions = len(skema_answers)
    if total_questions == 0:
        return jsonify({"error": "Skema 读取失败"}), 400

    student_answers = extract_student_answers(student_path, total_questions)
    student_name = extract_student_name(student_path, school)

    correct = [i + 1 for i, (a, b) in enumerate(zip(skema_answers, student_answers)) if a == b]
    incorrect = [i + 1 for i in range(total_questions) if i + 1 not in correct]

    result = {
        "name": student_name,
        "score": len(correct),
        "total": total_questions,
        "correct": correct,
        "incorrect": incorrect
    }

    results_cache.append(result)
    return jsonify(result)

@app.route("/export-excel", methods=["GET"])
def export_excel():
    if not results_cache:
        return jsonify({"error": "暂无成绩可导出"}), 400

    df = pd.DataFrame(results_cache)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"/tmp/成绩表_{now}.xlsx"
    df.to_excel(file_path, index=False)

    if not os.path.exists(file_path):
        return jsonify({"error": "生成失败"}), 500

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

