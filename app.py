from flask import Flask, render_template, send_from_directory, request, session, redirect, url_for
import os, fitz
from uuid import uuid4

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

UPLOAD_FOLDER = 'uploads'
MERGED_FOLDER = 'static/merged'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MERGED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MERGED_FOLDER'] = MERGED_FOLDER

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/merge', methods=['GET', 'POST'])
def upload_pdf():
    if request.method == 'POST':
        files = request.files.getlist('pdfs')
        saved_files = []
        for f in files:
            if f.filename.endswith('.pdf'):
                filename = f"{uuid4().hex}_{f.filename}"
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                saved_files.append(filename)
        session['pdf_files'] = saved_files
        return redirect('/preview')
    return render_template('upload.html')

@app.route('/preview', methods=['GET', 'POST'])
def preview():
    files = session.get('pdf_files', [])
    if request.method == 'POST':
        order = request.form.get('order')
        watermark = request.form.get('watermark', '').strip()
        if order:
            order = eval(order)
            session['ordered_files'] = order
        else:
            session['ordered_files'] = files
        session['watermark'] = watermark
        return redirect(url_for('merging'))
    return render_template('preview.html', files=files)

@app.route('/merging', methods=['POST', 'GET'])
def merging():
    files = session.get('ordered_files', [])
    watermark = session.get('watermark', '')

    merged_pdf = fitz.open()

    for filename in files:
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            pdf = fitz.open(path)
            merged_pdf.insert_pdf(pdf)
            pdf.close()

    if watermark:
        for page in merged_pdf:
            rect = page.rect
            page.insert_text(
                rect.tl + (50, 50),
                watermark,
                fontsize=36,
                color=(1, 0, 0),
                fill_opacity=0.15,
                rotate=45,
            )

    output_filename = f"merged_{uuid4().hex}.pdf"
    output_path = os.path.join(app.config['MERGED_FOLDER'], output_filename)
    merged_pdf.save(output_path)
    merged_pdf.close()

    session['merged_filename'] = output_filename
    return render_template('merging.html')

@app.route('/download')
def download():
    filename = session.get('merged_filename')
    if not filename:
        return redirect(url_for('upload_pdf'))
    return render_template('download.html', filename=filename)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
