import re
from docx import Document
import fitz
import os
import random

def parse_answers_from_text(text):
    pattern = r"\b(\d+)[\.\)]\s*([ABCD])"
    matches = re.findall(pattern, text)
    sorted_matches = sorted(matches, key=lambda x: int(x[0]))
    return [ans for _, ans in sorted_matches]

def extract_from_docx(path):
    try:
        doc = Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return parse_answers_from_text(text)
    except Exception as e:
        print(f"❌ 读取 DOCX 错误: {e}")
        return []

def extract_from_pdf(path):
    try:
        text = ""
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text()
        return parse_answers_from_text(text)
    except Exception as e:
        print(f"❌ 读取 PDF 错误: {e}")
        return []

def extract_skema(path):
    ext = path.lower()
    if ext.endswith(".pdf"):
        return extract_from_pdf(path)
    elif ext.endswith(".docx"):
        return extract_from_docx(path)
    elif ext.endswith((".jpg", ".jpeg", ".png")):
        print("⚠️ 图片格式暂未集成 OCR，返回 40 题示例答案")
        return [random.choice(['A', 'B', 'C', 'D']) for _ in range(40)]
    else:
        raise ValueError(f"不支持的格式：{os.path.basename(path)}")
