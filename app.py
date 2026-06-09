import os
import base64
from functools import wraps
from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash
from weasyprint import HTML

app = Flask(__name__)
# Secure secret key from environment or fallback
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-for-ticket-gen")

# Simple Auth Credentials
USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "admin")

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
    """
    Partitions a total value (e.g. 10.00) into denominations of 2.00, 1.00, and 0.50
    to create a user-friendly and aesthetically pleasing layout of ticket boxes.
    """
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

@app.route("/generate", methods=["POST"])
def generate_pdf():
    title = request.form.get("title", "Vereinsfest 2026")
    event_date = request.form.get("event_date", "")
    total_value_str = request.form.get("total_value", "10.00")
    ticket_count_str = request.form.get("ticket_count", "4")
    layout_format = request.form.get("layout_format", "portrait") # portrait or landscape
    grid_layout = request.form.get("grid_layout", "2x2") # 2x2, 4x4, 4x6
    
    try:
        total_value = float(total_value_str)
    except ValueError:
        total_value = 10.00
        
    try:
        ticket_count = int(ticket_count_str)
    except ValueError:
        ticket_count = 4

    # Check if user customized the boxes
    custom_boxes = request.form.getlist("custom_box_values")
    if custom_boxes:
        try:
            boxes = [float(val) for val in custom_boxes]
            total_value = sum(boxes)
        except ValueError:
            boxes = partition_value(total_value)
    else:
        boxes = partition_value(total_value)

    # Handle logo upload
    logo_file = request.files.get("logo")
    logo_base64 = None
    if logo_file and logo_file.filename != '':
        file_content = logo_file.read()
        mime_type = logo_file.content_type or "image/png"
        encoded = base64.b64encode(file_content).decode("utf-8")
        logo_base64 = f"data:{mime_type};base64,{encoded}"
        
    # Render PDF template using Flask templates
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
    
    # Generate PDF via WeasyPrint
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    
    filename = f"verzehrkarten_{title.lower().replace(' ', '_')}.pdf"
    
    from io import BytesIO
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, debug=True)
