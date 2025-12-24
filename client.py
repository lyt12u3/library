# client.py
import requests
import json

# Єдина точка входу для всієї системи (Вимога ПЗ №4) 
GATEWAY_URL = "http://127.0.0.1:8080"

class LibraryClient:
    """
    Клас-клієнт, що інкапсулює логіку взаємодії з API Gateway.
    Маршрутизація до конкретних мікросервісів виконується шлюзом динамічно.
    """

    # --- 1-4. CATALOG SERVICE (Через Gateway) ---
    @staticmethod
    def get_all_books():
        try:
            return requests.get(f"{GATEWAY_URL}/catalog/books").json()
        except Exception as e: return f"Помилка з'єднання: {e}"

    @staticmethod
    def get_book_by_id(book_id):
        resp = requests.get(f"{GATEWAY_URL}/catalog/books/{book_id}")
        return resp.json() if resp.status_code == 200 else resp.json().get('detail', "Помилка")

    @staticmethod
    def search_by_author(author):
        return requests.get(f"{GATEWAY_URL}/catalog/books/search/{author}").json()

    @staticmethod
    def add_book(book_id, title, author, desc):
        payload = {"id": book_id, "title": title, "author": author, "description": desc}
        resp = requests.post(f"{GATEWAY_URL}/catalog/books", json=payload)
        return resp.json()

    # --- 5-8. READER SERVICE (Через Gateway) ---
    @staticmethod
    def get_all_readers():
        # Додаємо слеш в кінці для коректної обробки Gateway
        return requests.get(f"{GATEWAY_URL}/readers/").json()

    @staticmethod
    def get_reader_by_id(reader_id):
        """Виправлено: Метод тепер існує для запобігання AttributeError"""
        resp = requests.get(f"{GATEWAY_URL}/readers/{reader_id}")
        return resp.json() if resp.status_code == 200 else resp.json().get('detail', "Помилка")

    @staticmethod
    def register_reader(reader_id, name):
        payload = {"id": reader_id, "name": name}
        resp = requests.post(f"{GATEWAY_URL}/readers/", json=payload)
        return resp.json()

    @staticmethod
    def update_reader_status(reader_id, status):
        resp = requests.put(f"{GATEWAY_URL}/readers/{reader_id}/status", params={"status": status})
        return resp.json()

    # --- 9-12. LOAN SERVICE (Через Gateway) ---
    @staticmethod
    def create_loan(book_id, reader_id):
        payload = {"bookId": book_id, "readerId": reader_id}
        resp = requests.post(f"{GATEWAY_URL}/loans/", json=payload)
        if resp.status_code == 201:
            return f"Успіх: {resp.json()}"
        return f"Відмова: {resp.json().get('detail', resp.text)}"

    @staticmethod
    def return_book(loan_id):
        resp = requests.put(f"{GATEWAY_URL}/loans/{loan_id}/return")
        return resp.json().get("message", resp.text)

    @staticmethod
    def get_reader_history(reader_id):
        return requests.get(f"{GATEWAY_URL}/loans/history/{reader_id}").json()

    @staticmethod
    def get_active_loans():
        return requests.get(f"{GATEWAY_URL}/loans/active").json()

def main():
    client = LibraryClient()
    while True:
        print("\n" + "="*45)
        print("    LIBRARY MANAGEMENT SYSTEM (PZ4)    ")
        print("    CONNECTED VIA API GATEWAY (8080)   ")
        print("="*45)
        print("1. [Catalog] Показати всі книги")
        print("2. [Catalog] Пошук за ID книги")
        print("3. [Catalog] Пошук за автором")
        print("4. [Catalog] Додати нову книгу")
        print("-" * 25)
        print("5. [Reader]  Список всіх читачів")
        print("6. [Reader]  Дані читача за ID")
        print("7. [Reader]  Реєстрація читача")
        print("8. [Reader]  Змінити статус читача")
        print("-" * 25)
        print("9. [Loan]    Оформити видачу книги")
        print("10. [Loan]   Повернути книгу")
        print("11. [Loan]   Історія запозичень читача")
        print("12. [Loan]   Список книг на руках (активні)")
        print("0. Вихід")
        
        choice = input("\nВаш вибір: ")

        try:
            if choice == "1": print(client.get_all_books())
            elif choice == "2": print(client.get_book_by_id(int(input("ID книги: "))))
            elif choice == "3": print(client.search_by_author(input("Автор: ")))
            elif choice == "4": print(client.add_book(int(input("ID: ")), input("Назва: "), input("Автор: "), input("Опис: ")))
            
            elif choice == "5": print(client.get_all_readers())
            elif choice == "6": print(client.get_reader_by_id(int(input("ID читача: "))))
            elif choice == "7": print(client.register_reader(int(input("ID читача: ")), input("Ім'я: ")))
            elif choice == "8": print(client.update_reader_status(int(input("ID читача: ")), input("Статус (active/blocked): ")))
            
            elif choice == "9": print(client.create_loan(int(input("ID книги: ")), int(input("ID читача: "))))
            elif choice == "10": print(client.return_book(int(input("ID Loan ID: "))))
            elif choice == "11": print(client.get_reader_history(int(input("ID читача: "))))
            elif choice == "12": print(client.get_active_loans())
            
            elif choice == "0": break
            else: print("Невідома команда!")
        except ValueError:
            print("Помилка: введіть коректне числове значення ID.")
        except Exception as e:
            print(f"Виникла помилка: {e}")

if __name__ == "__main__":
    main()