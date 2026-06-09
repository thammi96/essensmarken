import os
import base64
import time
import logging
import uuid
from threading import Thread
from functools import wraps
from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, jsonify
from weasyprint import HTML

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-for-ticket-gen")

# Simple Auth Credentials
USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "admin")

# Global dict to store background task state and output buffers
# Format: { task_id: { 'status': 'rendering'|'done'|'error', 'step': str, 'page': int, 'pdf_bytes': bytes, 'error': str } }
pdf_tasks = {}

class WeasyPrintProgressHandler(logging.Handler):
    """
    Custom logging handler that intercepts WeasyPrint's internal logger
    and parses page compilation progress in real-time.
    """
    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id
        
    def emit(self, record):
        msg = record.getMessage()
        task = pdf_tasks.get(self.task_id)
        if not task:
            return
            
        if "Step 1" in msg:
            task['step'] = "HTML wird eingelesen"
        elif "Step 2" in msg:
            task['step'] = "CSS wird analysiert"
        elif "Step 3" in msg:
            task['step'] = "CSS wird angewendet"
        elif "Step 4" in msg:
            task['step'] = "Layoutstruktur wird erstellt"
        elif "Creating layout - Page" in msg:
            try:
                # Extract page number from log string, e.g. "Step 5 - Creating layout - Page 3"
                parts = msg.split("Page ")
                if len(parts) > 1:
                    page_num = int(parts[1])
                    task['page'] = page_num
                    task['step'] = f"Erstelle Layout für Seite {page_num}"
            except Exception:
                pass

@app.before_request
def require_login():
    # Allow login route and static assets
    if request.endpoint in ('login', 'static') or not request.endpoint:
        return
    if not session.get("logged_in"):
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for('index'))
        
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if user == USERNAME and pw == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for('index'))
        else:
            flash("Ungültige Anmeldedaten. Bitte versuche es erneut.", "error")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for('login'))

def partition_value(total_value):
    cents = int(round(total_value * 100))
    if cents % 50 != 0:
        cents = (cents // 50) * 50
        
    c50 = 0
    c100 = 0
    c200 = 0
    
    remaining = cents
    
    if remaining >= 100:
        c50 = 2
        remaining -= 100
    elif remaining >= 50:
        c50 = 1
        remaining -= 50
        
    if remaining >= 200:
        c100 = 2
        remaining -= 200
    elif remaining >= 100:
        c100 = 1
        remaining -= 100
        
    c200 = remaining // 200
    remaining = remaining % 200
    
    if remaining >= 100:
        c100 += 1
        remaining -= 100
    if remaining >= 50:
        c50 += 1
        remaining -= 50
        
    boxes = [2.00] * c200 + [1.00] * c100 + [0.50] * c50
    return boxes

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

def async_pdf_generator(task_id, rendered_html):
    """Worker thread that executes WeasyPrint and logs its updates."""
    try:
        # Attach progress tracking logger
        handler = WeasyPrintProgressHandler(task_id)
        wp_logger = logging.getLogger('weasyprint')
        wp_logger.addHandler(handler)
        
        # Compile PDF
        html_doc = HTML(string=rendered_html)
        pdf_bytes = html_doc.write_pdf()
        
        # Save output and mark complete
        pdf_tasks[task_id]['pdf_bytes'] = pdf_bytes
        pdf_tasks[task_id]['status'] = 'done'
        pdf_tasks[task_id]['step'] = 'Generierung abgeschlossen'
        
        # Remove logging handler
        wp_logger.removeHandler(handler)
    except Exception as e:
        logger.exception("Error in async PDF generator thread")
        pdf_tasks[task_id]['status'] = 'error'
        pdf_tasks[task_id]['error'] = str(e)
        pdf_tasks[task_id]['step'] = 'Fehler aufgetreten'

@app.route("/generate", methods=["POST"])
def generate_pdf_async():
    title = request.form.get("title", "Vereinsfest 2026")
    event_date = request.form.get("event_date", "")
    total_value_str = request.form.get("total_value", "10.00")
    ticket_count_str = request.form.get("ticket_count", "4")
    layout_format = request.form.get("layout_format", "portrait")
    grid_layout = request.form.get("grid_layout", "2x2")
    
    try:
        total_value = float(total_value_str)
    except ValueError:
        total_value = 10.00
        
    try:
        ticket_count = int(ticket_count_str)
    except ValueError:
        ticket_count = 4

    custom_boxes = request.form.getlist("custom_box_values")
    if custom_boxes:
        try:
            boxes = [float(val) for val in custom_boxes]
            total_value = sum(boxes)
        except ValueError:
            boxes = partition_value(total_value)
    else:
        boxes = partition_value(total_value)

    logo_file = request.files.get("logo")
    logo_base64 = None
    if logo_file and logo_file.filename != '':
        file_content = logo_file.read()
        mime_type = logo_file.content_type or "image/png"
        encoded = base64.b64encode(file_content).decode("utf-8")
        logo_base64 = f"data:{mime_type};base64,{encoded}"
        
    rendered_html = render_template(
        "pdf_template.html",
        title=title,
        event_date=event_date,
        total_value=total_value,
        ticket_count=ticket_count,
        boxes=boxes,
        logo_base64=logo_base64,
        layout_format=layout_format,
        grid_layout=grid_layout
    )
    
    # Initialize background task state
    task_id = str(uuid.uuid4())
    pdf_tasks[task_id] = {
        'status': 'rendering',
        'step': 'Initialisierung',
        'page': 0,
        'pdf_bytes': None,
        'error': None,
        'title': title
    }
    
    # Spawn background worker thread
    thread = Thread(target=async_pdf_generator, args=(task_id, rendered_html))
    thread.start()
    
    return jsonify({"task_id": task_id, "status": "rendering"})

@app.route("/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    task = pdf_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    return jsonify({
        "status": task['status'],
        "step": task['step'],
        "page": task['page'],
        "error": task['error']
    })

@app.route("/download/<task_id>", methods=["GET"])
def download_pdf(task_id):
    task = pdf_tasks.get(task_id)
    if not task or task['status'] != 'done':
        return "Datei noch nicht bereit oder existiert nicht", 400
        
    pdf_bytes = task['pdf_bytes']
    title = task.get('title', 'verzehrkarten')
    filename = f"verzehrkarten_{title.lower().replace(' ', '_')}.pdf"
    
    # Remove from memory once fetched to save space
    pdf_tasks.pop(task_id, None)
    
    from io import BytesIO
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, debug=True)
