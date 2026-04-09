import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
api_id = 34321415 
api_hash = 'a858399e90e04f5992a97096b614f31e'

st.set_page_config(page_title="TG Scout Admin Panel", layout="wide")

# --- БАЗА ПОЛЬЗОВАТЕЛЕЙ (В памяти сессии) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = [
        {"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ"},
        {"login": "Sophia_Tabachenko", "pass": "work123", "role": "Работник"},
        {"login": "Rusya_Golik", "pass": "work456", "role": "Работник"}
    ]

if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user_data = None

# --- СТИЛИЗАЦИЯ (Цвета со скрина) ---
st.markdown("""
    <style>
    .stApp { background-color: #0f111a; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .pink-button>button { background-color: #ff4b91 !important; color: white !important; height: 3em; width: 100%; border: none; }
    .delete-button>button { background-color: transparent !important; color: #ff4b4b !important; border: none !important; text-align: right; }
    .user-card { background-color: #1a1c24; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #2d2f39; }
    .sidebar-card { background-color: #161922; padding: 20px; border-radius: 15px; border: 1px solid #2d2f39; }
    input { background-color: #1a1c24 !important; color: white !important; border: 1px solid #2d2f39 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЭКРАН ВХОДА ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div style="text-align:center; margin-top:100px;">', unsafe_allow_html=True)
        st.title("Вход в систему")
        l = st.text_input("ЛОГИН")
        p = st.text_input("ПАРОЛЬ", type="password")
        if st.button("ВОЙТИ", key="login_btn"):
            user = next((u for u in st.session_state.users_db if u["login"] == l and u["pass"] == p), None)
            if user:
                st.session_state.auth = True
                st.session_state.user_data = user
                st.rerun()
            else:
                st.error("Ошибка доступа")
        st.markdown('</div>', unsafe_allow_html=True)

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ---
else:
    # Верхнее меню как на скрине
    tabs_list = ["ИНСТРУКЦИЯ", "🔐 МОИ ЧАТЫ", "📊 СБОР", "📂 ИСТОРИЯ"]
    if st.session_state.user_data["role"] == "Админ":
        tabs_list.append("👥 КОМАНДА")
    
    tabs = st.tabs(tabs_list)

    # --- ВКЛАДКА КОМАНДА (ТОЛЬКО АДМИН) ---
    if st.session_state.user_data["role"] == "Админ":
        with tabs[-1]:
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown("### + Добавить")
                with st.container():
                    new_login = st.text_input("ЛОГИН", key="new_l")
                    new_pass = st.text_input("ПАРОЛЬ", key="new_p")
                    new_role = st.selectbox("РОЛЬ", ["Работник", "Админ"])
                    st.markdown('<div class="pink-button">', unsafe_allow_html=True)
                    if st.button("Создать"):
                        if new_login and new_pass:
                            st.session_state.users_db.append({"login": new_login, "pass": new_pass, "role": new_role})
                            st.success("Добавлен!")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            with col_right:
                st.markdown("### Структура команды")
                for i, user in enumerate(st.session_state.users_db):
                    c_user, c_del = st.columns([3, 1])
                    with c_user:
                        st.markdown(f"""
                        <div class="user-card">
                            <b style="font-size:18px;">{user['login']}</b><br>
                            <span style="color:gray; font-size:12px;">{user['role'].lower()}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_del:
                        st.markdown('<div class="delete-button">', unsafe_allow_html=True)
                        if st.button("Удалить", key=f"del_{i}"):
                            st.session_state.users_db.pop(i)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- ВКЛАДКА СБОР (РАБОЧАЯ) ---
    with tabs[2]:
        st.markdown("### Сбор аудитории")
        target = st.text_input("Ссылка на чат")
        if st.button("ЗАПУСТИТЬ", key="run_btn"):
            st.info("Парсинг запущен...")
            # Твоя логика Telethon здесь...

    with st.sidebar:
        st.write(f"Вы вошли как: **{st.session_state.user_data['login']}**")
        if st.button("Выйти"):
            st.session_state.auth = False
            st.rerun()
