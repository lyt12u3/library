import requests
import json
from config import CATALOG_SERVICE_URL, READER_SERVICE_URL, LOAN_SERVICE_URL

class LibraryClient:
    """
    Клас-клієнт для взаємодії з розподіленою системою.
    Інкапсулює логіку викликів API трьох мікросервісів.
    """

    # --- 1-4. ВЗАЄМОДІЯ З CATALOG SERVICE (Порт 8001) ---
    @staticmethod
    def get_all_books():
        try:
            return requests.get(f"{CATALOG_SERVICE_URL}/catalog/books").json()
        except Exception as e: return f"Помилка Catalog Service: {e}"

    @staticmethod
    def get_book_by_id(book_id):
        try:
            resp = requests.get(f"{CATALOG_SERVICE_URL}/catalog/books/{book_id}")
            return resp.json() if resp.status_code == 200 else resp.json().get('detail')
        except Exception as e: return f"Помилка: {e}"

    @staticmethod
    def search_by_author(author):
        try:
            return requests.get(f"{CATALOG_SERVICE_URL}/catalog/books/search/{author}").json()
        except Exception as e: return f"Помилка: {e}"

    @staticmethod
    def add_book(book_id, title, author, desc):
        payload = {"id": book_id, "title": title, "author": author, "description": desc}
        try:
            resp = requests.post(f"{CATALOG_SERVICE_URL}/catalog/books", json=payload)
            return resp.json() if resp.status_code == 200 else resp.json().get('detail')
        except Exception as e: return f"Помилка: {e}"

    # --- 5-8. ВЗАЄМОДІЯ З READER SERVICE (Порт 8002) ---
    @staticmethod
    def get_all_readers():
        try:
            return requests.get(f"{READER_SERVICE_URL}/readers").json()
        except Exception as e: return f"Помилка Reader Service: {e}"

    @staticmethod
    def get_reader_by_id(reader_id):
        try:
            resp = requests.get(f"{READER_SERVICE_URL}/readers/{reader_id}")
            return resp.json() if resp.status_code == 200 else resp.json().get('detail')
        except Exception as e: return f"Помилка: {e}"

    @staticmethod
    def register_reader(reader_id, name):
        payload = {"id": reader_id, "name": name}
        try:
            resp = requests.post(f"{READER_SERVICE_URL}/readers", json=payload)
            return resp.json() if resp.status_code == 200 else resp.json().get('detail')
        except Exception as e: return f"Помилка: {e}"

    @staticmethod
    def update_reader_status(reader_id, status):
        try:
            resp = requests.put(f"{READER_SERVICE_URL}/readers/{reader_id}/status", params={"status": status})
            return resp.json() if resp.status_code == 200 else resp.json().get('detail')
        except Exception as e: return f"Помилка: {e}"

    # --- 9-12. ВЗАЄМОДІЯ З LOAN SERVICE (Оркестратор, Порт 8003) ---
    @staticmethod
    def create_loan(book_id, reader_id):
        payload = {"bookId": book_id, "readerId": reader_id}
        try:
            resp = requests.post(f"{LOAN_SERVICE_URL}/loans", json=payload)
            return resp.json() if resp.status_code == 201 else f"Відмова: {resp.json().get('detail')}"
        except Exception as e: return f"Помилка Loan Service: {e}"

    @staticmethod
    def return_book(loan_id):
        try:
            resp = requests.put(f"{LOAN_SERVICE_URL}/loans/{loan_id}/return")
            return resp.json().get("message", resp.text)
        except Exception as e: return f"Помилка: {e}"

    @staticmethod
    def get_reader_history(reader_id):
        try:
            return requests.get(f"{LOAN_SERVICE_URL}/loans/history/{reader_id}").json()
        except Exception as e: return f"Помилка: {e}"

    @staticmethod
    def get_active_loans():
        try:
            return requests.get(f"{LOAN_SERVICE_URL}/loans/active").json()
        except Exception as e: return f"Помилка: {e}"

def main():
    client = LibraryClient()
    while True:
        print("\n" + "="*35)
        print("    LIBRARY MANAGEMENT SYSTEM (PZ3)    ")
        print("="*35)
        print("1. [Catalog] Показати всі книги")
        print("2. [Catalog] Пошук за ID книги")
        print("3. [Catalog] Пошук за автором")
        print("4. [Catalog] Додати нову книгу")
        print("-" * 20)
        print("5. [Reader]  Список всіх читачів")
        print("6. [Reader]  Дані читача за ID")
        print("7. [Reader]  Реєстрація читача")
        print("8. [Reader]  Змінити статус читача")
        print("-" * 20)
        print("9. [Loan]    Оформити видачу книги")
        print("10. [Loan]   Повернути книгу")
        print("11. [Loan]   Історія запозичень читача")
        print("12. [Loan]   Список книг на руках (активні)")
        print("0. Вихід")
        
        choice = input("\nВаш вибір: ")

        if choice == "1": print(client.get_all_books())
        elif choice == "2": print(client.get_book_by_id(int(input("ID книги: "))))
        elif choice == "3": print(client.search_by_author(input("Автор: ")))
        elif choice == "4": print(client.add_book(int(input("ID: ")), input("Назва: "), input("Автор: "), input("Опис: ")))
        
        elif choice == "5": print(client.get_all_readers())
        elif choice == "6": print(client.get_reader_by_id(int(input("ID читача: "))))
        elif choice == "7": print(client.register_reader(int(input("ID читача: ")), input("Ім'я: ")))
        elif choice == "8": print(client.update_reader_status(int(input("ID читача: ")), input("Статус (active/blocked): ")))
        
        elif choice == "9": print(client.create_loan(int(input("ID книги: ")), int(input("ID читача: "))))
        elif choice == "10": print(client.return_book(int(input("ID видачі (Loan ID): "))))
        elif choice == "11": print(client.get_reader_history(int(input("ID читача: "))))
        elif choice == "12": print(client.get_active_loans())
        
        elif choice == "0": break
        else: print("Невідома команда!")

if __name__ == "__main__":
    main()