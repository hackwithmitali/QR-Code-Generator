from flask import Flask, render_template, request, send_file, redirect, url_for
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image
import os
import time
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "static/logos"
app.config['QR_FOLDER'] = "static/qrcodes"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# Make sure qrcodes folder exists
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

latest_qr_path = None  # store last generated QR


@app.route("/")
def index():
    return render_template("index.html", qr=None)


@app.route("/generate", methods=["POST"])
def generate():
    global latest_qr_path

    # Get form data
    data = request.form.get("data", "").strip()
    hex_color = request.form.get("color", "#000000")
    size = request.form.get("size", "300")
    logo_choice = request.form.get("logo_choice")
    uploaded_logo = request.files.get("logo_file")

    # Validation: check if text is entered
    if not data:
        return render_template("index.html", 
                               qr=None, 
                               error="⚠️ Please enter some text or URL!",
                               data=data, color=hex_color, size=size, logo_choice=logo_choice)

    # Convert hex to RGB
    color = hex_to_rgb(hex_color)
    size = int(size)

    # Create basic QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(front_color=color, back_color=(255, 255, 255))
    )

    img = img.resize((size, size))

    # Handle logo (preset or uploaded)
    logo = None

    if logo_choice != "none":
        logo_path = f"static/logos/{logo_choice}.png"
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)

    if uploaded_logo and uploaded_logo.filename != "":
        try:
            logo = Image.open(uploaded_logo)
        except:
            pass  # in case user uploads invalid format

    if logo:
        logo = logo.resize((size // 4, size // 4))
        img.paste(logo, ((size - logo.size[0]) // 2, (size - logo.size[1]) // 2), mask=logo)

    # Save generated QR with unique filename
    timestamp = str(int(time.time()))
    file_path = f"{app.config['QR_FOLDER']}/qr_{timestamp}.png"
    img.save(file_path)
    latest_qr_path = file_path

    # Full QR URL for sharing (local URL)
    qr_url = f"http://127.0.0.1:5000/{file_path}"
    
    
    

    return render_template(
    "index.html",
    qr="/" + file_path,
    qr_url=qr_url,
    data=data,
    color=hex_color,
    size=size,
    logo_choice=logo_choice,
    success="QR Code generated successfully!"
)

@app.route("/download_pdf")
def download_pdf():
    global latest_qr_path
    if not latest_qr_path:
        return redirect(url_for("index"))

    pdf_path = "static/qrcodes/qr.pdf"
    c = canvas.Canvas(pdf_path)
    c.drawImage(latest_qr_path, 100, 500, width=300, height=300)
    c.save()
    return send_file(pdf_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

