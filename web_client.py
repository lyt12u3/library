import streamlit as st
import requests
import pandas as pd
import time

# --- КОНФІГУРАЦІЯ ---
# Клієнт звертається ТІЛЬКИ до Gateway
GATEWAY_URL = "http://127.0.0.1:8080"

# Налаштування сторінки
st.set_page_config(
    page_title="Library Microservices System",
    page_icon="📚",
    layout="wide"
)

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def api_request(method, endpoint, json=None, params=None):
    """Обгортка для запитів з обробкою помилок (UX)"""
    url = f"{GATEWAY_URL}/{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, params=params)
        elif method == "POST":
            resp = requests.post(url, json=json)
        elif method == "PUT":
            resp = requests.put(url, json=json, params=params)
        
        # Обробка помилок 4xx/5xx
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except:
                detail = resp.text
            st.error(f"❌ Помилка API ({resp.status_code}): {detail}")
            return None
        
        return resp.json()
    except Exception as e:
        st.error(f"⚠️ Не вдалося з'єднатися з Gateway: {e}")
        return None

# --- БІЧНА ПАНЕЛЬ (НАВІГАЦІЯ) ---
st.sidebar.title("📚 Library System")
st.sidebar.info("Connected via API Gateway (8080)")
page = st.sidebar.radio("Навігація", ["Каталог книг", "Читачі", "Видача (Loans)"])

# --- СТОРІНКА 1: КАТАЛОГ (CATALOG SERVICE) ---
if page == "Каталог книг":
    st.header("📖 Каталог Книг")
    
    # 1. READ: Таблиця книг
    st.subheader("Список доступних книг")
    if st.button("🔄 Оновити список"):
        st.rerun()
        
    books = api_request("GET", "catalog/books")
    if books:
        df = pd.DataFrame(books)
        # Прикрашаємо таблицю: Available -> ✅/❌
        df["available"] = df["available"].apply(lambda x: "✅ Так" if x else "❌ Ні")
        st.dataframe(df, use_container_width=True)

    # 2. CREATE: Додавання книги
    st.divider()
    st.subheader("➕ Додати нову книгу")
    with st.form("add_book_form"):
        col1, col2 = st.columns(2)
        new_id = col1.number_input("ID Книги", min_value=1, step=1)
        new_title = col2.text_input("Назва книги")
        new_author = col1.text_input("Автор")
        new_desc = col2.text_input("Опис")
        
        submitted = st.form_submit_button("Створити книгу")
        if submitted:
            if new_title and new_author:
                payload = {"id": new_id, "title": new_title, "author": new_author, "description": new_desc}
                res = api_request("POST", "catalog/books", json=payload)
                if res:
                    st.success(f"Книгу '{new_title}' успішно додано!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Будь ласка, заповніть назву та автора.")

# --- СТОРІНКА 2: ЧИТАЧІ (READER SERVICE) ---
elif page == "Читачі":
    st.header("busts_in_silhouette: Управління Читачами")

    # 1. READ: Список читачів
    readers = api_request("GET", "readers/") # Слеш важливий для Gateway
    if readers:
        df_r = pd.DataFrame(readers)
        st.dataframe(df_r, use_container_width=True)

    col_l, col_r = st.columns(2)
    
    # 2. CREATE: Реєстрація
    with col_l:
        st.subheader("➕ Реєстрація читача")
        with st.form("add_reader"):
            r_id = st.number_input("ID Читача", min_value=1, step=1)
            r_name = st.text_input("ПІБ")
            if st.form_submit_button("Зареєструвати"):
                res = api_request("POST", "readers/", json={"id": r_id, "name": r_name})
                if res:
                    st.success("Читача зареєстровано!")
                    time.sleep(1)
                    st.rerun()

    # 3. UPDATE: Зміна статусу
    with col_r:
        st.subheader("🔧 Зміна статусу")
        if readers:
            # Вибір читача зі списку (Aggregation & UX)
            reader_ids = [r['id'] for r in readers]
            selected_id = st.selectbox("Оберіть ID читача", reader_ids)
            new_status = st.radio("Новий статус:", ["active", "blocked"], horizontal=True)
            
            if st.button("Оновити статус"):
                res = api_request("PUT", f"readers/{selected_id}/status", params={"status": new_status})
                if res:
                    st.success(f"Статус читача {selected_id} змінено на {new_status}")
                    time.sleep(1)
                    st.rerun()

# --- СТОРІНКА 3: ВИДАЧА (LOAN ORCHESTRATOR) ---
elif page == "Видача (Loans)":
    st.header("🔄 Оркестрація Видачі (Loans)")
    
    # Складна агрегація: показуємо і книги, і читачів для зручності
    col1, col2 = st.columns(2)
    with col1:
        st.info("Активні читачі")
        readers = api_request("GET", "readers/")
        if readers: st.dataframe(pd.DataFrame(readers)[['id', 'name', 'status']], height=150)
    
    with col2:
        st.info("Доступні книги")
        books = api_request("GET", "catalog/books")
        if books: 
            df_b = pd.DataFrame(books)
            # Фільтруємо тільки доступні книги (Business Logic)
            st.dataframe(df_b[df_b['available'] == True][['id', 'title']], height=150)

    st.divider()

    # 1. CREATE: Оформлення видачі (Inter-service communication)
    st.subheader("📝 Оформити видачу")
    with st.form("loan_form"):
        c1, c2 = st.columns(2)
        lid_book = c1.number_input("ID Книги", min_value=1)
        lid_reader = c2.number_input("ID Читача", min_value=1)
        
        if st.form_submit_button("Видати книгу"):
            # Цей запит пройде через Gateway -> Loan Service -> (Catalog + Reader)
            res = api_request("POST", "loans/", json={"bookId": lid_book, "readerId": lid_reader})
            if res:
                st.success(f"Успіх! Запис видачі створено: {res}")
                time.sleep(2)
                st.rerun()

    # 2. READ: Активні позики
    st.divider()
    st.subheader("📂 Активні позики на руках")
    loans = api_request("GET", "loans/active")
    if loans:
        st.dataframe(pd.DataFrame(loans), use_container_width=True)
    else:
        st.info("Немає активних позик.")

    # 3. UPDATE: Повернення книги
    st.subheader("🔙 Повернення книги")
    ret_id = st.number_input("Введіть ID запису видачі (Loan ID)", min_value=1)
    if st.button("Повернути книгу"):
        res = api_request("PUT", f"loans/{ret_id}/return")
        if res:
            st.success("Книгу повернуто! Каталог оновлено.")
            time.sleep(2)
            st.rerun()