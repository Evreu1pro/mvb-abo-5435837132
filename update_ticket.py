import os
from flask import Flask, render_template, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import base64
import re
import threading
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'

# URL страницы с билетом
TICKET_URL = "https://deticket.online/ticket.html?key=ticket_1761955942491"

# Папка для хранения данных
DATA_FOLDER = "ticket_data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def update_ticket_data():
    """
    Функция для скачивания и извлечения данных билета.
    """
    try:
        print("Скачиваю страницу с билетом...")
        response = requests.get(TICKET_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  

        print("Извлекаю данные...")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлекаем номер билета
        ticket_number_element = soup.find(id="ticketNumber")
        if not ticket_number_element:
            raise ValueError("Не удалось найти элемент с id='ticketNumber'")
        new_ticket_number = ticket_number_element.get_text(strip=True)
        print(f"Найден номер билета: {new_ticket_number}")

        # Извлекаем QR-код
        qr_img_element = soup.find(id="qrCodeImage")
        if not qr_img_element:
            raise ValueError("Не удалось найти элемент с id='qrCodeImage'")
        
        qr_data_uri = qr_img_element['src']
        
        # Извлекаем base64 данные из URI
        base64_string = re.sub(r'^data:image/[^;]+;base64,', '', qr_data_uri)
        
        # Декодируем изображение
        qr_image_data = base64.b64decode(base64_string)
        print("QR-код успешно декодирован.")

        # Сохраняем QR-код
        qr_path = os.path.join(DATA_FOLDER, "qr-code.png")
        with open(qr_path, "wb") as f:
            f.write(qr_image_data)
        print("QR-код обновлен.")

        # Сохраняем номер билета и даты
        ticket_path = os.path.join(DATA_FOLDER, "ticket_data.json")
        
        # Рассчитываем даты валидности (текущий месяц)
        today = datetime.now()
        valid_from = datetime(today.year, today.month, 1)
        valid_to = datetime(today.year, today.month + 1, 1, 3, 0, 0) if today.month < 12 else datetime(today.year + 1, 1, 1, 3, 0, 0)
        
        import json
        ticket_data = {
            "ticket_number": new_ticket_number,
            "valid_from": valid_from.strftime("%d.%m.%Y %H:%M"),
            "valid_to": valid_to.strftime("%d.%m.%Y %H:%M"),
            "name": "Yehor Antoniuk",
            "birthdate": "31.05.2004",
            "last_updated": datetime.now().isoformat()
        }
        
        with open(ticket_path, "w") as f:
            json.dump(ticket_data, f, ensure_ascii=False, indent=2)
        print("Данные билета обновлены.")

        return True

    except Exception as e:
        print(f"Ошибка при обновлении данных билета: {e}")
        return False

def background_updater():
    """Фоновый процесс для автоматического обновления данных каждые 24 часа"""
    while True:
        print("Запуск автоматического обновления билета...")
        update_ticket_data()
        # Ждем 24 часа перед следующим обновлением
        time.sleep(24 * 60 * 60)

@app.route('/')
def ticket_page():
    """Основная страница с билетом"""
    return render_template('ticket.html')

@app.route('/api/ticket-data')
def get_ticket_data():
    """API для получения данных билета"""
    import json
    ticket_path = os.path.join(DATA_FOLDER, "ticket_data.json")
    qr_exists = os.path.exists(os.path.join(DATA_FOLDER, "qr-code.png"))
    
    if not os.path.exists(ticket_path) or not qr_exists:
        # Если данных нет, обновляем их
        if not update_ticket_data():
            return jsonify({"error": "Не удалось загрузить данные билета"}), 500
    
    with open(ticket_path, 'r') as f:
        ticket_data = json.load(f)
    
    # Добавляем URL для QR-кода
    ticket_data['qr_code_url'] = '/static/qr-code.png'
    
    return jsonify(ticket_data)

@app.route('/api/update-ticket', methods=['POST'])
def trigger_update():
    """API для ручного обновления данных билета"""
    success = update_ticket_data()
    return jsonify({"success": success, "message": "Данные билета успешно обновлены" if success else "Ошибка при обновлении данных"})

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Сервер статических файлов"""
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

if __name__ == "__main__":
    # Запускаем фоновый процесс обновления в отдельном потоке
    updater_thread = threading.Thread(target=background_updater, daemon=True)
    updater_thread.start()
    
    # Первое обновление при запуске
    update_ticket_data()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
