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

# Отключаем сайдбар программно
st.set_page_config(page_title="VM Models | Premium Scout", layout="wide", initial_sidebar_state="collapsed")

# --- БАЗА ДАННЫХ ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}],
            "history": []
        }
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {"users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}], "history": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(db, f, indent=4, ensure_ascii=False)

if 'db' not in st.session_state: st.session_state.db = load_db()
if 'auth' not in st.session_state: st.session_state.auth = False

# --- СТИЛИЗАЦИЯ (БЕЗ САЙДБАРА) ---
st.markdown("""
    <style>
    /* Прячем кнопку сайдбара совсем */
    [data-testid="collapsedControl"] { display: none; }
    
    .stApp { background-color: #0d111b; color: #ffffff; }
    
    /* Шапка VM Models */
    .top-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; border-bottom: 1px solid #232d45; margin-bottom: 25px; }
    .brand-vm { color: #007BFF; font-size: 28px; font-weight: 900; font-family: 'Arial Black'; }
    .brand-models { color: #ffffff; font-size: 28px; font-weight: 900; }
    
    /* Дашборд карточки */
    .status-container { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 30px; }
    .status-card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 20px; flex: 1; text-align: center; }
    .status-label { color: #8a8d9b; font-size: 11px; text-transform: uppercase; font-weight: bold; margin-bottom: 8px; }
    .status-value { font-size: 18px; font-weight: bold; }
    .status-on { color: #3fb950; }
    .status-off { color: #f85149; }
    
    /* Кнопки */
    div.stButton > button { background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%); color: white !important; border-radius: 8px; font-weight: bold; border: none; padding: 12px; transition: 0.3s; }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,123,255,0.4); }
    
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ---
async def run_live_parser(session_str, target, days, method, placeholder):
    client = TelegramClient(StringSession(session_str), API_ID_DEFAULT, API_HASH_DEFAULT)
    await client.connect()
    results, seen = [], set()
    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        un = u.username or ""
        results.append({"ИМЯ": f"{u.first_name or ''} {u.last_name or ''}".strip(), "ЮЗЕРНЕЙМ": f"@{un}" if un else "---", "ЧАТ": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"})
        placeholder.dataframe(pd.DataFrame(results), column_config={"ЧАТ": st.column_config.LinkColumn("ЧАТ 🔵")}, use_container_width=True, hide_index=True)
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
if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u_in = st.text_input("Логин")
        p_in = st.text_input("Пароль", type="password")
        if st.button("ВОЙТИ"):
            user = next((x for x in st.session_state.db["users"] if x["login"] == u_in and x["pass"] == p_in), None)
            if user:
                st.session_state.auth = True; st.session_state.user = user; st.rerun()
            else: st.error("Неверный доступ")
else:
    u = st.session_state.user
    
    # ХЕДЕР ВНУТРИ (Вместо сайдбара)
    st.markdown(f"""
    <div class="top-header">
        <div class="brand"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div>
        <div style="display:flex; align-items:center; gap:20px;">
            <span style="color:#8a8d9b;">{u['role']}: <b>{u['login']}</b></span>
            <a href="/" style="background:#ff4b4b; color:white; padding:5px 15px; border-radius:5px; text-decoration:none; font-weight:bold; font-size:12px;">ВЫХОД</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ДАШБОРД СТАТУСОВ
    tg_name = u.get("tg_name", "@Maksym_Admin") if u['role'] == "Админ" else u.get("tg_name", "")
    tg_status = f'<span class="status-on">ПОДКЛЮЧЕН <br><small>{tg_name}</small></span>' if u.get("session") else '<span class="status-off">НЕ ПОДКЛЮЧЕН</span>'
    
    st.markdown(f"""
    <div class="status-container">
        <div class="status-card"><div class="status-label">Аккаунт</div><div class="status-value">{u['login']}</div></div>
        <div class="status-card"><div class="status-label">Telegram Status</div><div class="status-value">{tg_status}</div></div>
        <div class="status-card"><div class="status-label">Лимит (24ч)</div><div class="status-value">{u.get('limit', 0)} / 50</div></div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА", "❓ ПОМОЩЬ"])

    with tabs[0]: # СБОР
        if not u.get("session"):
            st.warning("⚠️ Подключите Telegram во вкладке АККАУНТ")
        else:
            st.markdown('<div style="background:#161b2c; padding:25px; border-radius:12px; border:1px solid #232d45;">', unsafe_allow_html=True)
            targ = st.text_input("Ссылка на группу", placeholder="nakordoni_poland")
            meth = st.radio("Метод:", ["Все участники (Deep)", "Активные за период"], horizontal=True)
            days_v = 0
            if "Активные" in meth:
                per = st.selectbox("Срок активности:", ["3 дня", "7 дней", "Месяц", "3 месяца"])
                days_v = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}[per]
            
            if st.button("🚀 ЗАПУСТИТЬ ПРОЦЕСС"):
                if targ:
                    ph = st.empty()
                    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                    data = loop.run_until_complete(run_live_parser(u["session"], targ, days_v, meth, ph))
                    if data:
                        for user_db in st.session_state.db["users"]:
                            if user_db["login"] == u["login"]: user_db["limit"] += 1
                        st.session_state.db["history"].append({"user": u["login"], "target": targ, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")})
                        save_db(st.session_state.db); st.success("Готово!"); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]: # АККАУНТ
        st.subheader("Авторизация Telegram")
        if u["role"] == "Админ":
            st.success(f"✅ Ваш ТГ аккаунт Администратора {tg_name} подключен.")
        elif u.get("session"):
            st.success(f"✅ Подключен аккаунт: {u.get('tg_name')}")
            if st.button("Сбросить сессию"):
                for user_db in st.session_state.db["users"]:
                    if user_db["login"] == u["login"]: user_db["session"] = ""; user_db["tg_name"] = ""
                save_db(st.session_state.db); st.rerun()
        else:
            phone = st.text_input("Номер телефона (+...)")
            if st.button("Прислать код"):
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                client = TelegramClient(StringSession(), API_ID_DEFAULT, API_HASH_DEFAULT)
                await client.connect()
                res = await client.send_code_request(phone)
                st.session_state.temp_client = client; st.session_state.temp_hash = res.phone_code_hash
                st.info("Код отправлен!")
            
            t_code = st.text_input("Код из ТГ")
            if st.button("Активировать"):
                async def finish_auth():
                    await st.session_state.temp_client.sign_in(phone, t_code, phone_code_hash=st.session_state.temp_hash)
                    me = await st.session_state.temp_client.get_me()
                    s_str = st.session_state.temp_client.session.save()
                    tg_uname = f"@{me.username}" if me.username else f"{me.first_name}"
                    for user_db in st.session_state.db["users"]:
                        if user_db["login"] == u["login"]:
                            user_db["session"] = s_str; user_db["tg_name"] = tg_uname
                    save_db(st.session_state.db)
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                loop.run_until_complete(finish_auth()); st.rerun()

    with tabs[3]: # КОМАНДА
        if u["role"] == "Админ":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Новый скаут")
                nl, np = st.text_input("Логин"), st.text_input("Пароль")
                if st.button("Создать доступ"):
                    st.session_state.db["users"].append({"login": nl, "pass": np, "role": "Работник", "session": "", "tg_name": "", "limit": 0})
                    save_db(st.session_state.db); st.rerun()
            with col2:
                st.subheader("Мониторинг")
                for i, worker in enumerate(st.session_state.db["users"]):
                    if worker["role"] != "Админ":
                        with st.expander(f"👤 {worker['login']} | ТГ: {worker.get('tg_name', '❌')}"):
                            w_h = [h for h in st.session_state.db["history"] if h["user"] == worker["login"]]
                            if w_h: st.table(pd.DataFrame(w_h))
                            if st.button("Удалить доступ", key=f"del_{i}"):
                                st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()

