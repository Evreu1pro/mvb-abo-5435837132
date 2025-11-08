from flask import Flask, render_template, jsonify
import threading
import time
import os
import requests
from bs4 import BeautifulSoup
import base64
import re
from datetime import datetime

app = Flask(__name__)

# URL der Ticket-Seite
TICKET_URL = "https://deticket.online/ticket.html?key=ticket_1761955942491"
REFRESH_INTERVAL = 30  # Sekunden für automatische Aktualisierung

# Speicherordner für Ticket-Daten
DATA_FOLDER = "ticket_data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Ticket-Daten (wird beim Start und bei Aktualisierungen gefüllt)
ticket_data = {
    "ticket_number": "Wird geladen...",
    "qr_code_path": "/static/placeholder_qr.png",
    "valid_from": "01.08.2025 00:00",
    "valid_to": "01.09.2025 03:00",
    "name": "Yehor Antoniuk",
    "birthdate": "31.05.2004",
    "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    "update_status": "Warte auf erste Aktualisierung..."
}

def download_and_process_ticket():
    """Lädt Ticket-Daten von der externen Quelle und verarbeitet sie"""
    global ticket_data
    
    try:
        print("Aktualisiere Ticket-Daten...")
        ticket_data["update_status"] = "Aktualisierung läuft..."
        
        # Herunterladen der Seite
        response = requests.get(TICKET_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Verarbeiten mit BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ticket-Nummer extrahieren
        ticket_number_element = soup.find(id="ticketNumber")
        if ticket_number_element:
            ticket_data["ticket_number"] = ticket_number_element.get_text(strip=True)
            print(f"Ticket-Nummer: {ticket_data['ticket_number']}")
        
        # QR-Code extrahieren und speichern
        qr_img_element = soup.find(id="qrCodeImage")
        if qr_img_element and 'src' in qr_img_element.attrs:
            qr_data_uri = qr_img_element['src']
            base64_string = re.sub(r'^data:image/[^;]+;base64,', '', qr_data_uri)
            qr_image_data = base64.b64decode(base64_string)
            
            # QR-Code speichern
            qr_path = os.path.join(DATA_FOLDER, "qr-code.png")
            with open(qr_path, "wb") as f:
                f.write(qr_image_data)
            
            ticket_data["qr_code_path"] = "/static/qr-code.png"
            print("QR-Code erfolgreich gespeichert.")
        
        # Aktualisierungszeit setzen
        ticket_data["last_updated"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        ticket_data["update_status"] = "Aktualisierung erfolgreich!"
        print("Ticket-Daten erfolgreich aktualisiert.")
        
        return True
    except Exception as e:
        print(f"Fehler bei der Aktualisierung: {e}")
        ticket_data["update_status"] = f"Fehler: {str(e)}"
        return False

def auto_refresh_thread():
    """Hintergrund-Thread für automatische Aktualisierung"""
    while True:
        download_and_process_ticket()
        time.sleep(REFRESH_INTERVAL)

@app.route('/')
def index():
    """Hauptseite mit dem Ticket"""
    return render_template('ticket.html', ticket=ticket_data)

@app.route('/api/ticket-data')
def get_ticket_data():
    """API zum Abrufen der aktuellen Ticket-Daten"""
    return jsonify(ticket_data)

@app.route('/api/force-update', methods=['POST'])
def force_update():
    """API zum manuellen Auslösen einer Aktualisierung"""
    success = download_and_process_ticket()
    return jsonify({
        "success": success,
        "message": "Aktualisierung erfolgreich!" if success else "Fehler bei der Aktualisierung",
        "ticket_data": ticket_data
    })

# Hintergrund-Thread für automatische Aktualisierung starten
refresh_thread = threading.Thread(target=auto_refresh_thread, daemon=True)
refresh_thread.start()

# Erstmalige Daten beim Start laden
download_and_process_ticket()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
