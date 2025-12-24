import requests

BASE_URL = "http://127.0.0.1:8000"

class LibraryClient:
    # --- CATALOG SERVICE METHODS --- [cite: 929-985]
    @staticmethod
    def get_all_books():
        return requests.get(f"{BASE_URL}/catalog/books").json()

    @staticmethod
    def get_book_by_id(book_id):
        response = requests.get(f"{BASE_URL}/catalog/books/{book_id}")
        return response.json() if response.status_code == 200 else response.text

    @staticmethod
    def search_by_author(author):
        return requests.get(f"{BASE_URL}/catalog/books/search/{author}").json()

    @staticmethod
    def add_new_book(title, author, desc):
        payload = {"id": int(input("Введіть новий ID для книги: ")), "title": title, "author": author, "description": desc}
        return requests.post(f"{BASE_URL}/catalog/books", json=payload).json()

    # --- READER SERVICE METHODS --- [cite: 1039-1088]
    @staticmethod
    def list_readers():
        return requests.get(f"{BASE_URL}/readers").json()

    @staticmethod
    def get_reader(reader_id):
        return requests.get(f"{BASE_URL}/readers/{reader_id}").json()

    @staticmethod
    def register_reader(name):
        new_id = int(input("Введіть ID для нового читача: "))
        payload = {"id": new_id, "name": name}
        return requests.post(f"{BASE_URL}/readers", json=payload).json()

    @staticmethod
    def update_reader_status(reader_id, status):
        return requests.put(f"{BASE_URL}/readers/{reader_id}/status", params={"status": status}).json()

    # --- LOAN SERVICE METHODS --- [cite: 988-1036]
    @staticmethod
    def create_loan(book_id, reader_id):
        # Виклик з параметрами запиту [cite: 700, 1009]
        response = requests.post(f"{BASE_URL}/loans", params={"bookId": book_id, "readerId": reader_id})
        if response.status_code == 200:
            return f"Успіх: {response.json()}"
        return f"Помилка: {response.json().get('detail')}"

    @staticmethod
    def return_book(loan_id):
        return requests.put(f"{BASE_URL}/loans/{loan_id}/return").json()

    @staticmethod
    def get_reader_history(reader_id):
        return requests.get(f"{BASE_URL}/loans/history/{reader_id}").json()

    @staticmethod
    def get_active_loans():
        return requests.get(f"{BASE_URL}/loans/active").json()

# --- ТЕРМІНАЛЬНИЙ ІНТЕРФЕЙС --- [cite: 1166-1243]
def main():
    client = LibraryClient()
    while True:
        print("\n" + "="*30)
        print(" LIBRARY MANAGEMENT SYSTEM ")
        print("="*30)
        print("1. [Catalog] Показати всі книги")
        print("2. [Catalog] Пошук за ID книги")
        print("3. [Catalog] Пошук за автором")
        print("4. [Catalog] Додати нову книгу")
        print("-" * 15)
        print("5. [Reader] Список всіх читачів")
        print("6. [Reader] Дані читача за ID")
        print("7. [Reader] Реєстрація читача")
        print("8. [Reader] Змінити статус читача")
        print("-" * 15)
        print("9. [Loan] Оформити видачу книги")
        print("10. [Loan] Повернути книгу")
        print("11. [Loan] Історія запозичень читача")
        print("12. [Loan] Список книг на руках (активні)")
        print("0. Вихід")
        
        choice = input("\nВаш вибір: ")

        if choice == "1": print(client.get_all_books())
        elif choice == "2": print(client.get_book_by_id(input("ID книги: ")))
        elif choice == "3": print(client.search_by_author(input("Автор: ")))
        elif choice == "4": print(client.add_new_book(input("Назва: "), input("Автор: "), input("Опис: ")))
        
        elif choice == "5": print(client.list_readers())
        elif choice == "6": print(client.get_reader(input("ID читача: ")))
        elif choice == "7": print(client.register_reader(input("Ім'я читача: ")))
        elif choice == "8": print(client.update_reader_status(input("ID читача: "), input("Новий статус (active/blocked): ")))
        
        elif choice == "9": print(client.create_loan(input("ID книги: "), input("ID читача: ")))
        elif choice == "10": print(client.return_book(input("ID запису видачі (Loan ID): ")))
        elif choice == "11": print(client.get_reader_history(input("ID читача: ")))
        elif choice == "12": print(client.get_active_loans())
        
        elif choice == "0": break
        else: print("Невідома команда!")

if __name__ == "__main__":
    main()