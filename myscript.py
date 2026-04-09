import streamlit as st
import asyncio
import pandas as pd
import os
import json
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
API_ID_DEFAULT = 34321415 
API_HASH_DEFAULT = 'a858399e90e04f5992a97096b614f31e'
DB_FILE = "vm_database.json"

st.set_page_config(page_title="VM Models | Enterprise", layout="wide")

# --- БАЗА ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": "", "api_id": "", "api_hash": ""}],
            "history": []
        }
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- СТИЛЬ (VM MODELS PREMIUM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d111b; color: #ffffff; }
    /* Хедер */
    .vm-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 30px; border-bottom: 1px solid #1f2937; margin-bottom: 20px; }
    .brand { font-size: 28px; font-weight: 900; font-family: 'Arial Black'; }
    .vm-blue { color: #007BFF; }
    /* Карточки */
    .card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .stat-label { color: #8a8d9b; font-size: 12px; text-transform: uppercase; font-weight: bold; }
    /* Кнопки */
    div.stButton > button { background: #007BFF; color: white !important; border-radius: 8px; font-weight: bold; border: none; width: 100%; padding: 10px; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 2px solid #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ТЕЛЕГРАМ ---
async def start_telegram(api_id, api_hash, phone):
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    sent_code = await client.send_code_request(phone)
    return client, sent_code.phone_code_hash

async def run_parser(session_str, api_id, api_hash, target, method, placeholder):
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    results, seen = [], set()
    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        un = u.username or ""
        results.append({"Имя": f"{u.first_name or ''} {u.last_name or ''}".strip(), "Юзернейм": f"@{un}" if un else "---", "Ссылка": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"})
        placeholder.dataframe(pd.DataFrame(results), column_config={"Ссылка": st.column_config.LinkColumn("Чат")}, use_container_width=True)
    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz":
                res = await client(functions.channels.GetParticipantsRequest(channel=target, filter=types.ChannelParticipantsSearch(char), offset=0, limit=1000, hash=0))
                for u in res.users: await process(u)
        else:
            async for m in client.iter_messages(target, limit=1500):
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- АВТОРИЗАЦИЯ ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="brand"><span class="vm-blue">VM</span> MODELS</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u = st.text_input("Логин")
        p = st.text_input("Пароль", type="password")
        if st.button("ВОЙТИ"):
            user = next((x for x in st.session_state.db["users"] if x["login"] == u and x["pass"] == p), None)
            if user:
                st.session_state.auth = True; st.session_state.user = user; st.rerun()
            else: st.error("Доступ закрыт")
else:
    # ХЕДЕР
    st.markdown(f'<div class="vm-header"><div class="brand"><span class="vm-blue">VM</span> MODELS</div><div style="color:#8a8d9b;">{st.session_state.user["role"]}: {st.session_state.user["login"]} | <a href="/" style="color:#ff4b4b; text-decoration:none;">Выход</a></div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА"])

    # --- ВКЛАДКА 1: СБОР ---
    with tabs[0]:
        if not st.session_state.user.get("session"):
            st.warning("⚠️ Сначала подключите Telegram во вкладке 'АККАУНТ'")
        else:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            target = st.text_input("Ссылка на группу (напр. nakordoni_poland)")
            method = st.radio("Метод:", ["Все участники", "Активные"], horizontal=True)
            if st.button("🚀 ЗАПУСТИТЬ"):
                placeholder = st.empty()
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                data = loop.run_until_complete(run_parser(st.session_state.user["session"], st.session_state.user["api_id"], st.session_state.user["api_hash"], target, method, placeholder))
                if data:
                    # Сохраняем в историю
                    entry = {"user": st.session_state.user["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")}
                    st.session_state.db["history"].append(entry); save_db(st.session_state.db)
                    st.success("Парсинг завершен!")

    # --- ВКЛАДКА 2: АККАУНТ (ПОДКЛЮЧЕНИЕ ТГ) ---
    with tabs[1]:
        st.subheader("Подключение Telegram")
        if st.session_state.user.get("session"):
            st.success("✅ Ваш аккаунт подключен и готов к работе.")
            if st.button("Отключить и сбросить"):
                st.session_state.user["session"] = ""; save_db(st.session_state.db); st.rerun()
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                api_id = st.number_input("API ID", value=API_ID_DEFAULT)
                api_hash = st.text_input("API HASH", value=API_HASH_DEFAULT)
                phone = st.text_input("Номер телефона (+7...)")
                if st.button("Получить код"):
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    client, code_hash = loop.run_until_complete(start_telegram(api_id, api_hash, phone))
                    st.session_state.temp_client = client; st.session_state.temp_hash = code_hash
                    st.session_state.temp_data = {"id": api_id, "hash": api_hash}
                    st.info("Код отправлен в Telegram!")
            with col_b:
                code = st.text_input("Код из сообщения")
                if st.button("Подтвердить вход"):
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    loop.run_until_complete(st.session_state.temp_client.sign_in(phone, code, phone_code_hash=st.session_state.temp_hash))
                    session_str = st.session_state.temp_client.session.save()
                    # Сохраняем юзеру
                    for u in st.session_state.db["users"]:
                        if u["login"] == st.session_state.user["login"]:
                            u["session"] = session_str; u["api_id"] = st.session_state.temp_data["id"]; u["api_hash"] = st.session_state.temp_data["hash"]
                    save_db(st.session_state.db); st.success("Успешно подключено!"); st.rerun()

    # --- ВКЛАДКА 3: ИСТОРИЯ ---
    with tabs[2]:
        st.subheader("Ваши последние выгрузки")
        my_hist = [h for h in st.session_state.db["history"] if h["user"] == st.session_state.user["login"]]
        if my_hist:
            st.table(pd.DataFrame(my_hist)[::-1])
        else: st.write("Вы еще ничего не парсили.")

    # --- ВКЛАДКА 4: КОМАНДА (АДМИН) ---
    with tabs[3]:
        if st.session_state.user["role"] == "Админ":
            col_1, col_2 = st.columns([1, 2])
            with col_1:
                st.subheader("Добавить скаута")
                new_l = st.text_input("Новый логин")
                new_p = st.text_input("Новый пароль")
                if st.button("Создать"):
                    st.session_state.db["users"].append({"login": new_l, "pass": new_p, "role": "Работник", "session": "", "api_id": "", "api_hash": ""})
                    save_db(st.session_state.db); st.success("Сотрудник добавлен!"); st.rerun()
            with col_2:
                st.subheader("Мониторинг команды")
                for i, u in enumerate(st.session_state.db["users"]):
                    if u["role"] != "Админ":
                        with st.expander(f"👤 {u['login']} (Нажми, чтобы увидеть историю)"):
                            u_hist = [h for h in st.session_state.db["history"] if h["user"] == u["login"]]
                            if u_hist: st.table(pd.DataFrame(u_hist))
                            else: st.write("Сотрудник еще не работал.")
                            if st.button("Удалить сотрудника", key=f"del_{i}"):
                                st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()
        else: st.info("Этот раздел доступен только администратору.")

