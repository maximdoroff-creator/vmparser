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
ADMIN_SESSION = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='

st.set_page_config(page_title="VM Models | Stable Scout", layout="wide")

# --- БАЗА ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "api_id": API_ID_DEFAULT, "api_hash": API_HASH_DEFAULT}],
            "history": []
        }
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

if 'db' not in st.session_state: st.session_state.db = load_db()

# --- СТИЛИЗАЦИЯ ---
st.markdown("""
    <style>
    .stApp { background-color: #0d111b; color: #ffffff; }
    .vm-blue { color: #007BFF; font-weight: 900; font-size: 32px; font-family: 'Arial Black'; }
    .models-white { color: #ffffff; font-weight: 900; font-size: 32px; }
    .card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 25px; margin-bottom: 20px; }
    .instr-link { color: #007BFF !important; text-decoration: underline; font-weight: bold; }
    div.stButton > button { background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%); color: white !important; border-radius: 8px; font-weight: bold; width: 100%; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ТЕЛЕГРАМ ---
async def start_telegram(api_id, api_hash, phone):
    # Создаем именованную сессию, чтобы она хранилась в файле и не вылетала
    session_name = f"user_{phone}"
    client = TelegramClient(session_name, api_id, api_hash)
    await client.connect()
    sent_code = await client.send_code_request(phone)
    return client, sent_code.phone_code_hash

async def run_live_parser(session_str, api_id, api_hash, target, days, method, placeholder):
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    results, seen = [], set()
    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        un = u.username or ""
        results.append({"Имя": f"{u.first_name or ''} {u.last_name or ''}".strip(), "Юзернейм": f"@{un}" if un else "---", "Чат": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"})
        placeholder.dataframe(pd.DataFrame(results), column_config={"Чат": st.column_config.LinkColumn("Написать")}, use_container_width=True, hide_index=True)
    
    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz0123456789":
                res = await client(functions.channels.GetParticipantsRequest(channel=target, filter=types.ChannelParticipantsSearch(char), offset=0, limit=1000, hash=0))
                for u in res.users: await process(u)
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=2000):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="vm-blue">VM</span><span class="models-white"> MODELS</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        l_in = st.text_input("Логин")
        p_in = st.text_input("Пароль", type="password")
        if st.button("LOGIN"):
            found = next((x for x in st.session_state.db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if found:
                st.session_state.auth = True; st.session_state.user = found; st.rerun()
            else: st.error("Доступ закрыт")
else:
    u = st.session_state.user
    st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; padding:15px; border-bottom:1px solid #232d45;"><div class="brand"><span class="vm-blue">VM</span> <span class="models-white">Models</span></div><div style="color:#8a8d9b;">{u["role"]}: {u["login"]} | <a href="/" style="color:#ff4b4b; text-decoration:none;">Выход</a></div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА"])

    with tabs[0]: # СБОР
        user_sess = u.get("session") if u["role"] != "Админ" else ADMIN_SESSION
        if not user_sess:
            st.warning("⚠️ Сначала активируйте аккаунт во вкладке АККАУНТ")
        else:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            targ = st.text_input("Группа (Username или t.me)")
            meth = st.selectbox("Метод:", ["Активные за период", "Все участники"])
            days_v = 0
            if "Активные" in meth:
                per = st.select_slider("Срок:", options=["3 дня", "7 дней", "Месяц", "3 месяца"])
                days_v = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}[per]
            
            if st.button("🚀 ЗАПУСТИТЬ ПАРСИНГ"):
                if targ:
                    ph = st.empty()
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    data = loop.run_until_complete(run_live_parser(user_sess, u.get("api_id", API_ID_DEFAULT), u.get("api_hash", API_HASH_DEFAULT), targ, days_v, meth, ph))
                    if data:
                        st.session_state.db["history"].append({"user": u["login"], "target": targ, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")})
                        save_db(st.session_state.db); st.success("Готово!")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]: # АККАУНТ (ИНСТРУКЦИЯ КАК НА СКРИНЕ)
        st.subheader("Авторизация Telegram аккаунта")
        if u["role"] == "Админ": st.success("✅ Ваш аккаунт Администратора активен постоянно.")
        elif u.get("session"): st.success("✅ Ваш аккаунт успешно подключен и сохранен.")
        else:
            st.markdown(f"""
            <div class="card">
                <b style="font-size:18px;">Где взять данные?</b><br><br>
                1. Перейди на <a href="https://telegram.org" target="_blank" class="instr-link">my.telegram.org</a><br>
                2. Авторизуйся и выбери <b>API development tools</b><br>
                3. Создай приложение (любое имя) и скопируй ключи API ID и API Hash.
            </div>
            """, unsafe_allow_html=True)
            
            c_a, c_b = st.columns(2)
            with c_a:
                aid = st.number_input("API ID", value=API_ID_DEFAULT)
                ahash = st.text_input("API HASH", value=API_HASH_DEFAULT)
                phone = st.text_input("Номер телефона (+...)")
                if st.button("Прислать код подтверждения"):
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    client, c_h = loop.run_until_complete(start_telegram(aid, ahash, phone))
                    st.session_state.temp_client = client; st.session_state.temp_hash = c_h
                    st.session_state.temp_creds = {"id": aid, "hash": ahash}
                    st.info("Код отправлен!")
            with c_b:
                t_code = st.text_input("Код из Telegram")
                if st.button("ПОДТВЕРДИТЬ И СОХРАНИТЬ"):
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    loop.run_until_complete(st.session_state.temp_client.sign_in(phone, t_code, phone_code_hash=st.session_state.temp_hash))
                    s_str = st.session_state.temp_client.session.save()
                    for user in st.session_state.db["users"]:
                        if user["login"] == u["login"]:
                            user["session"] = s_str; user["api_id"] = st.session_state.temp_creds["id"]; user["api_hash"] = st.session_state.temp_creds["hash"]
                    save_db(st.session_state.db); st.success("Аккаунт привязан навсегда!"); st.rerun()

    with tabs[3]: # КОМАНДА
        if u["role"] == "Админ":
            st.subheader("Управление командой")
            col_l, col_r = st.columns(2)
            with col_l:
                new_login = st.text_input("Логин сотрудника")
                new_pass = st.text_input("Пароль сотрудника")
                if st.button("Добавить в базу"):
                    st.session_state.db["users"].append({"login": new_login, "pass": new_pass, "role": "Работник", "session": "", "api_id": "", "api_hash": ""})
                    save_db(st.session_state.db); st.rerun()
            with col_r:
                for i, worker in enumerate(st.session_state.db["users"]):
                    if worker["role"] != "Админ":
                        c1, c2 = st.columns([3,1])
                        c1.write(f"👤 {worker['login']}")
                        if c2.button("Удалить", key=f"del_{i}"):
                            st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()

