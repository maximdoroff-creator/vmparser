import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
api_id = 34321415 
api_hash = 'a858399e90e04f5992a97096b614f31e'

st.set_page_config(page_title="TG Scout Admin", layout="wide")

# Инициализация базы пользователей в памяти
if 'users_db' not in st.session_state:
    st.session_state.users_db = [
        {"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ"},
        {"login": "Worker1", "pass": "123", "role": "Работник"}
    ]

if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user_data = None

# --- ЛОГИКА ПАРСЕРА ---
async def run_parser(target, days, limit, method):
    client = TelegramClient('final_session', api_id, api_hash)
    await client.start()
    results = []
    
    if "Все" in method:
        participants = await client.get_participants(target)
        for u in participants:
            results.append({"Имя": u.first_name, "Username": f"@{u.username}" if u.username else "---", "Ссылка": f"https://t.me{u.username}" if u.username else ""})
    else:
        limit_date = datetime.now(timezone.utc) - timedelta(days=days)
        seen = set()
        async for m in client.iter_messages(target, limit=limit):
            if m.date < limit_date: break
            if m.sender_id and m.sender_id not in seen:
                s = await m.get_sender()
                if s and not getattr(s, 'bot', False):
                    seen.add(m.sender_id)
                    un = getattr(s, 'username', None)
                    results.append({"Имя": getattr(s, 'first_name', 'Скрыт'), "Username": f"@{un}" if un else "---", "Ссылка": f"https://t.me{un}" if un else ""})
    
    await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if not st.session_state.auth:
    st.title("Вход в систему")
    l = st.text_input("ЛОГИН")
    p = st.text_input("ПАРОЛЬ", type="password")
    if st.button("ВОЙТИ"):
        user = next((u for u in st.session_state.users_db if u["login"] == l and u["pass"] == p), None)
        if user:
            st.session_state.auth = True
            st.session_state.user_data = user
            st.rerun()
        else:
            st.error("Ошибка доступа")
else:
    # Меню вкладок
    t_list = ["ИНСТРУКЦИЯ", "⚡️ СБОР", "📂 ИСТОРИЯ"]
    if st.session_state.user_data["role"] == "Админ":
        t_list.append("👥 КОМАНДА")
    
    tabs = st.tabs(t_list)

    # Вкладка СБОР
    with tabs[1]:
        st.subheader("Настройки парсинга")
        method = st.radio("Метод:", ["Все участники", "Активные"], horizontal=True)
        target = st.text_input("Ссылка на группу")
        days = st.slider("Дней активности", 1, 30, 5) if "Активные" in method else 0
        
        if st.button("ЗАПУСТИТЬ ПРОЦЕСС"):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            data = loop.run_until_complete(run_parser(target, days, 1000, method))
            if data:
                df = pd.DataFrame(data)
                st.success(f"Найдено: {len(df)}")
                st.dataframe(df, column_config={"Ссылка": st.column_config.LinkColumn()})
            else:
                st.warning("Никого не нашли.")

    # Вкладка КОМАНДА
    if st.session_state.user_data["role"] == "Админ":
        with tabs[-1]:
            cl, cr = st.columns([1, 2])
            with cl:
                st.subheader("+ Добавить")
                nl, np = st.text_input("ЛОГИН "), st.text_input("ПАРОЛЬ ")
                nr = st.selectbox("РОЛЬ", ["Работник", "Админ"])
                if st.button("Создать"):
                    st.session_state.users_db.append({"login": nl, "pass": np, "role": nr})
                    st.success("Добавлен!")
                    st.rerun()
            with cr:
                st.subheader("Структура команды")
                for u in st.session_state.users_db:
                    st.write(f"👤 **{u['login']}** ({u['role']})")

    with st.sidebar:
        st.write(f"Вы: {st.session_state.user_data['login']}")
        if st.button("Выйти"):
            st.session_state.auth = False
            st.rerun()

