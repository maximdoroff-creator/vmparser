import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
api_id = 34321415 
api_hash = 'a858399e90e04f5992a97096b614f31e'

# Эта строка заставляет Streamlit обновиться
st.cache_data.clear()

st.set_page_config(page_title="TG Scout Admin Panel", layout="wide")

# --- БАЗА ПОЛЬЗОВАТЕЛЕЙ ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = [
        {"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ"},
        {"login": "Sophia_Tabachenko", "pass": "work123", "role": "Работник"}
    ]

if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user_data = None

# --- СТИЛИЗАЦИЯ ПОД ВАШИ СКРИНШОТЫ ---
st.markdown("""
    <style>
    .stApp { background-color: #0f111a; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #1a1c24; border-radius: 10px 10px 0 0; color: white; padding: 0 30px; }
    .stButton>button { border-radius: 8px; font-weight: bold; background-color: #ff4b91; color: white; border: none; width: 100%; height: 3.5em; }
    .stButton>button:hover { background-color: #ff85b3; color: white; }
    .user-card { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #2d2f39; margin-bottom: 10px; }
    div[data-testid="stMetric"] { background-color: #1a1c24; border-radius: 15px; padding: 15px; border: 1px solid #2d2f39; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ВХОДА ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>Вход в систему</h1>", unsafe_allow_html=True)
        l = st.text_input("ЛОГИН")
        p = st.text_input("ПАРОЛЬ", type="password")
        if st.button("ВОЙТИ"):
            user = next((u for u in st.session_state.users_db if u["login"] == l and u["pass"] == p), None)
            if user:
                st.session_state.auth = True
                st.session_state.user_data = user
                st.rerun()
            else:
                st.error("Неверные данные доступа")
else:
    # --- ВЕРХНЯЯ ПАНЕЛЬ СТАТИСТИКИ ---
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Пользователь", st.session_state.user_data['login'])
    with c2: st.metric("Статус Telegram", "Подключен ✅")
    with c3: st.metric("Роль", st.session_state.user_data['role'])

    # --- ВКЛАДКИ ---
    t_list = ["ИНСТРУКЦИЯ", "⚡️ СБОР", "📂 ИСТОРИЯ"]
    if st.session_state.user_data["role"] == "Админ":
        t_list.append("👥 КОМАНДА")
    
    tabs = st.tabs(t_list)

    # Вкладка КОМАНДА
    if st.session_state.user_data["role"] == "Админ":
        with tabs[-1]:
            cl, cr = st.columns([1, 2])
            with cl:
                st.subheader("+ Добавить")
                nl = st.text_input("НОВЫЙ ЛОГИН")
                np = st.text_input("НОВЫЙ ПАРОЛЬ")
                nr = st.selectbox("РОЛЬ", ["Работник", "Админ"])
                if st.button("Создать аккаунт"):
                    st.session_state.users_db.append({"login": nl, "pass": np, "role": nr})
                    st.success("Добавлен!")
                    st.rerun()
            with cr:
                st.subheader("Структура команды")
                for u in st.session_state.users_db:
                    st.markdown(f'<div class="user-card"><b>{u["login"]}</b> — {u["role"]}</div>', unsafe_allow_html=True)

    # Вкладка СБОР
    with tabs[1]:
        st.subheader("Настройки парсинга")
        target = st.text_input("Ссылка на группу")
        if st.button("ЗАПУСТИТЬ ПРОЦЕСС"):
            st.info("Парсинг запущен от имени " + st.session_state.user_data['login'])

    with st.sidebar:
        if st.button("Выйти"):
            st.session_state.auth = False
            st.rerun()
