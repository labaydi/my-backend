from flask import Flask, request
from flask_cors import CORS  # NEU
import os
import shutil
import zipfile
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()

EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

app = Flask(__name__)
CORS(app)  # NEU

UPLOAD_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert():
    shutil.rmtree(UPLOAD_FOLDER, ignore_errors=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    files = request.files.getlist('files')
    from_format = request.form.get('from_format')
    to_format = request.form.get('to_format')
    empfaenger_email = request.form.get('email')

    if not empfaenger_email or not from_format or not to_format or from_format == to_format:
        return "Ungültige Eingaben", 400

    converted = 0

    for file in files:
        if not file.filename.endswith(from_format):
            continue
        try:
            content = file.read().decode('utf-8', errors='ignore')
            base = os.path.splitext(file.filename)[0]
            new_filename = base + to_format
            new_path = os.path.join(UPLOAD_FOLDER, new_filename)

            with open(new_path, "w", encoding="utf-8") as out_file:
                out_file.write(content)
            converted += 1
        except Exception as e:
            print(f"Fehler: {e}")

    if converted == 0:
        return "Keine gültigen Dateien gefunden.", 400

    # ZIP-Datei erstellen
    zip_path = "output.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            zipf.write(filepath, arcname=filename)

    # E-Mail versenden
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Ihre konvertierten Dateien'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = empfaenger_email
        msg.set_content('Hier sind Ihre konvertierten Dateien im Anhang.')

        with open(zip_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='zip', filename='konvertierte_dateien.zip')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        return f"Erfolg: Dateien wurden an {empfaenger_email} gesendet.", 200

    except Exception as e:
        print(f"E-Mail-Fehler: {e}")
        return f"Dateien konvertiert, aber E-Mail-Versand fehlgeschlagen: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
