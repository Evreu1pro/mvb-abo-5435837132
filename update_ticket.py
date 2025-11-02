import requests
from bs4 import BeautifulSoup
import base64
import re

# URL страницы с билетом
TICKET_URL = "https://deticket.online/ticket.html?key=ticket_1761955942491"

def update_ticket_data():
    """
    Основная функция для скачивания и извлечения данных.
    """
    try:
        print("Скачиваю страницу с билетом...")
        response = requests.get(TICKET_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  

        print("Извлекаю данные...")
        soup = BeautifulSoup(response.text, 'html.parser')

        ticket_number_element = soup.find(id="ticketNumber")
        if not ticket_number_element:
            raise ValueError("Не удалось найти элемент с id='ticketNumber'")
        new_ticket_number = ticket_number_element.get_text(strip=True)
        print(f"Найден номер билета: {new_ticket_number}")

        qr_img_element = soup.find(id="qrCodeImage")
        if not qr_img_element:
            raise ValueError("Не удалось найти элемент с id='qrCodeImage'")
        
        qr_data_uri = qr_img_element['src']
        
        base64_string = re.sub(r'^data:image/[^;]+;base64,', '', qr_data_uri)
        
        qr_image_data = base64.b64decode(base64_string)
        print("QR-код успешно декодирован.")

        with open("qr-code.png", "wb") as f:
            f.write(qr_image_data)
        print("Файл qr-code.png обновлен.")

        with open("ticket_number.txt", "w") as f:
            f.write(new_ticket_number)
        print(f"Файл ticket_number.txt обновлен значением: {new_ticket_number}")

        return new_ticket_number

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании страницы: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Ошибка при парсинге данных: {e}")
        return None
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return None

if __name__ == "__main__":
    update_ticket_data()
