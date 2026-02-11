from flask import Flask, render_template, request, send_file
import json
import regex as re
from docx import Document

app = Flask(__name__)

# ---------- LOAD & NORMALIZE DICTIONARY ----------

def normalize(s):
    return re.sub(r'\s+', ' ', s.lower().strip())

with open("abbreviations.json", encoding="utf-8") as f:
    raw = json.load(f)

# convert all keys to lowercase
ABBR = {normalize(k): v for k, v in raw.items()}

print("Loaded abbreviations:", len(ABBR))


# ---------- TEXT CONVERSION ENGINE ----------

def convert_text(text):

    working = text

    # longest phrases first
    sorted_abbr = sorted(ABBR.items(), key=lambda x: len(x[0]), reverse=True)

    for phrase, abbr in sorted_abbr:

        # allow optional "the" at beginning
        pattern = r'\b(the\s+)?' + re.escape(phrase) + r'\b'

        working = re.sub(pattern, abbr, working, flags=re.IGNORECASE)

    return working


# ---------- DOCX PROCESSOR (PRESERVE FORMATTING) ----------

def process_docx(input_path, output_path):

    doc = Document(input_path)

    for paragraph in doc.paragraphs:

        if not paragraph.text.strip():
            continue

        # join full paragraph text
        full_text = "".join(run.text for run in paragraph.runs)

        converted = convert_text(full_text)

        # clear runs but keep formatting
        for run in paragraph.runs:
            run.text = ""

        # write back converted text in first run
        if paragraph.runs:
            paragraph.runs[0].text = converted

    doc.save(output_path)


# ---------- WEB ROUTE ----------

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        file = request.files["file"]

        input_path = "uploads/input.docx"
        output_path = "outputs/output.docx"

        file.save(input_path)

        process_docx(input_path, output_path)

        return send_file(output_path, as_attachment=True)

    return render_template("index.html")


# ---------- RUN SERVER ----------

if __name__ == "__main__":
    app.run(debug=True)
