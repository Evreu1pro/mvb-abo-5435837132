import requests
from bs4 import BeautifulSoup
import base64
import re
import json
from datetime import datetime
import os

# URL страницы с билетом
TICKET_URL = "https://deticket.online/ticket.html?key=ticket_1761955942491"

def get_backup_data():
    """Возвращает резервные данные на случай ошибки"""
    return {
        "ticket_number": "RESERVE-123456",
        "valid_from": "01.11.2025 - 00:00",
        "valid_until": "01.12.2025 - 03:00",
        "region": "Deutschlandweit",
        "class": "2. Klasse",
        "price_level": "deutschlandweit",
        "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "update_status": "Fehler beim Abrufen - Reservdaten verwendet"
    }

def update_ticket_data():
    """
    Функция для скачивания и извлечения данных билета с обработкой ошибок
    """
    try:
        print("Скачиваю страницу с билетом...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(TICKET_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        print("Страница загружена. Извлекаю данные...")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлекаем номер билета
        ticket_number_element = soup.find(id="ticketNumber")
        if not ticket_number_element:
            raise ValueError("Не удалось найти элемент с id='ticketNumber'")
        ticket_number = ticket_number_element.get_text(strip=True)
        print(f"Найден номер билета: {ticket_number}")

        # Извлекаем QR-код
        qr_img_element = soup.find(class_="ticket-qr").find("img")
        if not qr_img_element or 'src' not in qr_img_element.attrs:
            raise ValueError("Не удалось найти QR-код")
        
        qr_data_uri = qr_img_element['src']
        
        # Извлекаем base64 данные
        base64_match = re.search(r'data:image/[a-zA-Z]+;base64,(.+)', qr_data_uri)
        if not base64_match:
            raise ValueError("Не удалось найти base64 данные в QR-коде")
        
        base64_string = base64_match.group(1)
        qr_image_data = base64.b64decode(base64_string)
        print("QR-код успешно декодирован.")

        # Сохраняем QR-код
        with open("qr-code.png", "wb") as f:
            f.write(qr_image_data)
        print("Файл qr-code.png обновлен.")

        # Извлекаем детали билета
        valid_from = soup.find(id="validFrom").get_text(strip=True) if soup.find(id="validFrom") else "01.11.2025 - 00:00"
        valid_until = soup.find(id="validUntil").get_text(strip=True) if soup.find(id="validUntil") else "01.12.2025 - 03:00"
        region = soup.find(id="region").get_text(strip=True) if soup.find(id="region") else "Deutschlandweit"
        ticket_class = soup.find(id="class").get_text(strip=True) if soup.find(id="class") else "2. Klasse"
        
        # Формируем данные билета
        ticket_data = {
            "ticket_number": ticket_number,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "region": region,
            "class": ticket_class,
            "price_level": "deutschlandweit",
            "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "update_status": "Erfolgreich aktualisiert"
        }
        
        # Сохраняем данные билета
        with open("ticket_data.json", "w") as f:
            json.dump(ticket_data, f, ensure_ascii=False, indent=2)
        print("Данные билета сохранены в ticket_data.json")

        return ticket_data

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        
        # Используем резервные данные
        backup_data = get_backup_data()
        
        # Сохраняем резервные данные
        with open("ticket_data.json", "w") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        print("Резервные данные сохранены в ticket_data.json")
        
        # Пытаемся сохранить placeholder QR-код, если основной не загрузился
        if not os.path.exists("qr-code.png"):
            try:
                with open("qr-code.png", "wb") as f:
                    # Минимальный placeholder PNG
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0eIDAT\x18\x95c\x90\xfb\x1f\x00\x02\xf8\x01\xff\xaf\xb1\xa1\x1c\x00\x00\x00\x00IEND\xaeB`\x82')
                print("Создан placeholder QR-код")
            except Exception as img_error:
                print(f"Не удалось создать placeholder QR-код: {img_error}")
        
        return backup_data

if __name__ == "__main__":
    update_ticket_data()
