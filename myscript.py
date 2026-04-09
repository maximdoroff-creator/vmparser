import streamlit as st
import asyncio
import pandas as pd
import os
from telethon import TelegramClient, functions, types
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
api_id = 34321415 
api_hash = 'a858399e90e04f5992a97096b614f31e'
AVATAR_DIR = "avatars"
if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

# Настройка страницы
st.set_page_config(page_title="VM Models | Scout", layout="wide")

# --- КАСТОМНЫЙ ДИЗАЙН (CSS) ---
st.markdown("""
    <style>
    /* Общий фон и цвет текста */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* Стилизация логотипа */
    .logo-text {
        font-size: 45px !important;
        font-weight: 800 !important;
        text-align: center;
        padding-bottom: 20px;
        font-family: 'Arial Black', sans-serif;
    }
    .vm-blue { color: #007BFF; }
    .models-white { color: #FFFFFF; }
    
    /* Синие кнопки и элементы */
    div.stButton > button {
        background-color: #007BFF;
        color: white;
        border-radius: 8px;
        border: none;
        width: 100%;
        font-weight: bold;
    }
    div.stButton > button:hover { background-color: #0056b3; border: none; color: white; }
    
    /* Поля ввода */
    .stTextInput input, .stSelectbox div {
        background-color: #111111 !important;
        color: white !important;
        border: 1px solid #333 !important;
    }
    
    /* Стиль табов */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111111;
        border: 1px solid #333;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Функция для вывода логотипа
def draw_logo():
    st.markdown('<div class="logo-text"><span class="vm-blue">VM</span> <span class="models-white">Models</span></div>', unsafe_allow_html=True)

# Инициализация сессии
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
    session_name = f"session_{st.session_state.user_data['login']}"
    client = TelegramClient(session_name, api_id, api_hash)
    await client.connect()
    
    results = []
    seen_ids = set()

    async def process_user(u):
        if not u or u.id in seen_ids or getattr(u, 'bot', False): return
        seen_ids.add(u.id)
        avatar_path = "https://flaticon.com"
        if u.photo:
            p_name = f"{u.id}.jpg"
            l_path = os.path.join(AVATAR_DIR, p_name)
            if not os.path.exists(l_path):
                try: await client.download_profile_photo(u, file=l_path)
                except: pass
            avatar_path = l_path if os.path.exists(l_path) else avatar_path
        
        un = u.username if u.username else ""
        results.append({
            "Фото": avatar_path,
            "Имя": f"{u.first_name or ''} {u.last_name or ''}".strip() or "Скрыт",
            "Username": f"@{un}" if un else "---",
            "Ссылка": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"
        })

    try:
        if "Все" in method:
            alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
            p_bar = st.progress(0)
            for i, char in enumerate(alphabet):
                p_bar.progress((i + 1) / len(alphabet))
                try:
                    participants = await client(functions.channels.GetParticipantsRequest(
                        channel=target, filter=types.ChannelParticipantsSearch(char),
                        offset=0, limit=1000, hash=0
                    ))
                    for u in participants.users: await process_user(u)
                except: continue
            p_bar.empty()
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=limit):
                if m.date < limit_date: break
                if m.sender_id: await process_user(await m.get_sender())
    finally:
        await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if not st.session_state.auth:
    # Страница входа с логотипом
    st.markdown("<br><br>", unsafe_allow_html=True)
    draw_logo()
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            l = st.text_input("ЛОГИН")
            p = st.text_input("ПАРОЛЬ", type="password")
            if st.button("ВХОД В СИСТЕМУ"):
                user = next((u for u in st.session_state.users_db if u["login"] == l and u["pass"] == p), None)
                if user:
                    st.session_state.auth = True
                    st.session_state.user_data = user
                    st.rerun()
                else:
                    st.error("Ошибка доступа")
else:
    # Главная страница
    draw_logo()
    tabs = st.tabs(["⚡️ СБОР КОНТАКТОВ", "📂 ИСТОРИЯ", "👥 КОМАНДА"])

    with tabs[0]:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            method = st.radio("Режим работы:", ["Все участники", "Активные за период"], key="m_r")
            target = st.text_input("Группа для парсинга (напр. poehalisnami_de)", key="t_i")
        with col2:
            if "Активные" in method:
                period = st.selectbox("Период:", ["3 дня", "Неделя", "Месяц", "3 месяца"], key="p_s")
                p_map = {"3 дня": 3, "Неделя": 7, "Месяц": 30, "3 месяца": 90}
                days_val = p_map[period]
                limit_msg = st.number_input("Лимит сообщений", 100, 50000, 2000)
            else:
                days_val, limit_msg = 0, 0
        
        if st.button("🚀 ЗАПУСТИТЬ ПАРСИНГ", key="s_b"):
            if not target: st.warning("Укажите цель")
            else:
                with st.spinner('VM Models Scout работает...'):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    data = loop.run_until_complete(run_parser(target, days_val, limit_msg, method))
                    if data:
                        df = pd.DataFrame(data)
                        st.success(f"Найдено: {len(df)}")
                        st.dataframe(df, column_config={
                            "Фото": st.column_config.ImageColumn("Аватар"),
                            "Ссылка": st.column_config.LinkColumn("Telegram")
                        }, use_container_width=True)
                        st.download_button("📥 Скачать CSV", df.to_csv(index=False).encode('utf-8'), "scout_data.csv")

    with st.sidebar:
        st.markdown('<div style="color:#007BFF; font-weight:bold;">VM Models Admin</div>', unsafe_allow_html=True)
        st.write(f"Пользователь: {st.session_state.user_data['login']}")
        if st.button("Выйти"):
            st.session_state.auth = False
            st.rerun()
