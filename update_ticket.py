import requests
from bs4 import BeautifulSoup
import base64
import re
import time
import json
from datetime import datetime, timedelta

# URL страницы с билетом
TICKET_URL = "https://deticket.online/ticket.html?key=ticket_1761955942491"

def update_ticket_data():
    """
    Функция для скачивания и извлечения данных билета с обработкой base64 QR-кода
    """
    try:
        print("Скачиваю страницу с билетом...")
        
        # Заголовки для имитации браузера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        # Попытка загрузки с повторными попытками
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = requests.get(TICKET_URL, headers=headers, timeout=15)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                print(f"Попытка {attempt + 1} не удалась: {e}")
                if attempt == max_attempts - 1:
                    raise
                time.sleep(2)  # Пауза перед следующей попыткой
        
        print("Страница загружена. Извлекаю данные...")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлекаем номер билета
        ticket_number_element = soup.find(id="ticketNumber")
        if not ticket_number_element:
            raise ValueError("Не удалось найти элемент с id='ticketNumber'")
        ticket_number = ticket_number_element.get_text(strip=True)
        print(f"Найден номер билета: {ticket_number}")

        # Извлекаем QR-код (base64)
        qr_img_element = soup.find(class_="ticket-qr").find("img")
        if not qr_img_element:
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
        valid_from = soup.find(id="validFrom").get_text(strip=True)
        valid_until = soup.find(id="validUntil").get_text(strip=True)
        region = soup.find(id="region").get_text(strip=True)
        ticket_class = soup.find(id="class").get_text(strip=True)
        
        # Формируем данные билета
        ticket_data = {
            "ticket_number": ticket_number,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "region": region,
            "class": ticket_class,
            "price_level": "deutschlandweit",
            "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
        
        # Сохраняем данные билета в JSON
        with open("ticket_data.json", "w") as f:
            json.dump(ticket_data, f, ensure_ascii=False, indent=2)
        print("Данные билета сохранены в ticket_data.json")

        return ticket_data

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        # При ошибке используем данные из последнего успешного обновления
        try:
            with open("ticket_data.json", "r") as f:
                return json.load(f)
        except:
            print("Не удалось загрузить резервные данные")
            return None

if __name__ == "__main__":
    update_ticket_data()
