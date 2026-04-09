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

st.set_page_config(page_title="VM Models Pro", layout="wide", initial_sidebar_state="collapsed")

# --- БАЗА ДАННЫХ ---
def load_db():
    default_db = {
        "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}],
        "history": []
    }
    if not os.path.exists(DB_FILE): return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for u in data.get("users", []):
                if "limit" not in u: u["limit"] = 0
                if "tg_name" not in u: u["tg_name"] = ""
            return data
    except: return default_db

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# Принудительная загрузка базы при каждом запуске скрипта
st.session_state.db = load_db()

# --- ПРОВЕРКА СЕССИИ (Анти-вылет) ---
if 'auth' not in st.session_state:
    stored_user = st.query_params.get("u")
    if stored_user:
        user_match = next((x for x in st.session_state.db["users"] if x["login"] == stored_user), None)
        if user_match:
            st.session_state.auth = True
            st.session_state.user = user_match
        else: st.session_state.auth = False
    else: st.session_state.auth = False

# --- ДИЗАЙН (VM MODELS BLUE PREMIUM) ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    .stApp { background-color: #0d111b; color: #ffffff !important; }
    
    /* Текст */
    label, p, span, .stMarkdown { color: #ffffff !important; font-weight: 500 !important; }
    .brand-vm { color: #007BFF; font-size: 36px; font-weight: 900; font-family: 'Arial Black'; }
    .brand-models { color: #ffffff; font-size: 36px; font-weight: 900; }
    
    /* Карточки */
    .status-card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 15px; text-align: center; }
    .status-label { color: #8a8d9b; font-size: 11px; text-transform: uppercase; font-weight: bold; }
    .status-on { color: #3fb950; font-weight: bold; }
    
    /* ГАРАНТИРОВАННО СИНЯЯ КНОПКА (Все виды) */
    button[kind="primary"], button[kind="secondary"], .stDownloadButton > button, .stButton > button {
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important; border-radius: 10px !important; border: none !important;
        padding: 12px 24px !important; font-weight: bold !important; width: 100% !important;
        transition: 0.3s !important;
    }
    button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,123,255,0.4); }

    /* Поля ввода */
    .stTextInput input { background-color: #1a1a1a !important; border: 1px solid #333 !important; color: white !important; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ТЕЛЕГРАМ ---
async def run_live_parser(session_str, target, days, method, placeholder):
    client = TelegramClient(StringSession(session_str), API_ID_DEFAULT, API_HASH_DEFAULT)
    await client.connect()
    results, seen = [], set()
    async def process(u_obj):
        if not u_obj or u_obj.id in seen or getattr(u_obj, 'bot', False): return
        seen.add(u_obj.id)
        un = u_obj.username or ""
        results.append({"ИМЯ": f"{u_obj.first_name or ''} {u_obj.last_name or ''}".strip(), "ЮЗЕРНЕЙМ": f"@{un}" if un else "---", "СВЯЗЬ": f"tg://resolve?domain={un}" if un else f"tg://user?id={u_obj.id}"})
        placeholder.dataframe(pd.DataFrame(results), column_config={"СВЯЗЬ": st.column_config.LinkColumn("ЧАТ 🔵")}, use_container_width=True, hide_index=True)
    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz0123456789":
                res = await client(functions.channels.GetParticipantsRequest(channel=target, filter=types.ChannelParticipantsSearch(char), offset=0, limit=1000, hash=0))
                for p in res.users: await process(p)
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
        l_in = st.text_input("Логин").strip()
        p_in = st.text_input("Пароль", type="password").strip()
        if st.button("ENTER"):
            # Принудительно читаем базу перед проверкой
            st.session_state.db = load_db()
            user = next((x for x in st.session_state.db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if user:
                st.session_state.auth = True
                st.session_state.user = user
                st.query_params["u"] = l_in # Сохраняем в URL для анти-вылета
                st.rerun()
            else: st.error("Неверный доступ")
else:
    u = st.session_state.user
    st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; padding:15px; border-bottom:1px solid #232d45; margin-bottom:20px;"><div class="brand-vm">VM <span class="brand-models">Models</span></div><div style="color:#8a8d9b;">{u.get("role", "Скаут")}: <b>{u["login"]}</b></div></div>', unsafe_allow_html=True)

    # ДАШБОРД СТАТУСОВ
    tg_name = u.get("tg_name", "")
    tg_status = f'<span class="status-on">ПОДКЛЮЧЕН <br><small>{tg_name}</small></span>' if u.get("session") else '<span style="color:#f85149; font-weight:bold;">НЕ ПОДКЛЮЧЕН</span>'
    
    cs1, cs2, cs3 = st.columns(3)
    cs1.markdown(f'<div class="status-card"><div class="status-label">Аккаунт</div><div style="font-size:18px; font-weight:bold;">{u["login"]}</div></div>', unsafe_allow_html=True)
    cs2.markdown(f'<div class="status-card"><div class="status-label">Telegram Status</div><div style="font-size:18px;">{tg_status}</div></div>', unsafe_allow_html=True)
    cs3.markdown(f'<div class="status-card"><div class="status-label">Лимит (24ч)</div><div style="font-size:18px; font-weight:bold;">{u.get("limit", 0)} / 50</div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА", "🚪 ВЫХОД"])

    with tabs: # СБОР
        sess = u.get("session", ADMIN_SESSION if u["role"] == "Админ" else "")
        if not sess: st.warning("⚠️ Сначала подключите Telegram во вкладке АККАУНТ")
        else:
            st.markdown('<div style="background:#161b2c; padding:25px; border-radius:12px; border:1px solid #232d45;">', unsafe_allow_html=True)
            target = st.text_input("Username группы или ссылка")
            method = st.radio("Метод:", ["Все участники (Deep)", "Активные за период"], horizontal=True)
            days_v = 0
            if "Активные" in method:
                per = st.selectbox("Период:", ["3 дня", "7 дней", "Месяц", "3 месяца"])
                days_v = {"3 дня": 3, "7 дней": 7, "Месяц": 30, "3 месяца": 90}[per]
            
            if st.button("🚀 ЗАПУСТИТЬ ПРОЦЕСС"):
                if target:
                    if u.get('limit', 0) >= 50: st.error("Лимит исчерпан!")
                    else:
                        ph = st.empty()
                        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                        data = loop.run_until_complete(run_live_parser(sess, target, days_v, method, ph))
                        if data:
                            for db_u in st.session_state.db["users"]:
                                if db_u["login"] == u["login"]: 
                                    db_u["limit"] = db_u.get("limit", 0) + 1
                                    st.session_state.user["limit"] = db_u["limit"]
                            st.session_state.db["history"].append({"user": u["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")})
                            save_db(st.session_state.db)
                            st.write("---")
                            # КНОПКА СКАЧИВАНИЯ (СИНЯЯ)
                            txt_data = "\n".join([i['ЮЗЕРНЕЙМ'] for i in data if i['ЮЗЕРНЕЙМ'] != "---"])
                            st.download_button("📥 СКАЧАТЬ В БЛОКНОТ (@)", txt_data, "usernames.txt")
                            st.success("Готово! Лимит обновлен.")
                else: st.warning("Укажите цель!")
            st.markdown('</div>', unsafe_allow_html=True)

    with tabs: # АККАУНТ
        st.subheader("Управление Telegram")
        if u["role"] == "Админ": st.success(f"✅ Админ-аккаунт активен: {u.get('tg_name')}")
        elif u.get("session"):
            st.success(f"✅ Подключено: {u.get('tg_name')}")
            if st.button("Сбросить"):
                for db_u in st.session_state.db["users"]:
                    if db_u["login"] == u["login"]: db_u["session"] = ""; db_u["tg_name"] = ""
                save_db(st.session_state.db); st.rerun()
        else:
            phone = st.text_input("Ваш номер телефона (+...)")
            if st.button("Прислать код"):
                async def get_c():
                    c = TelegramClient(StringSession(), API_ID_DEFAULT, API_HASH_DEFAULT); await c.connect()
                    res = await c.send_code_request(phone); return c, res.phone_code_hash
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                st.session_state.temp_client, st.session_state.temp_hash = loop.run_until_complete(get_c())
                st.info("Код отправлен!")
            
            t_code = st.text_input("Код из сообщения")
            if st.button("АКТИВИРОВАТЬ"):
                async def finish():
                    await st.session_state.temp_client.sign_in(phone, t_code, phone_code_hash=st.session_state.temp_hash)
                    me = await st.session_state.temp_client.get_me()
                    s_str = st.session_state.temp_client.session.save()
                    uname = f"@{me.username}" if me.username else f"{me.first_name}"
                    for db_u in st.session_state.db["users"]:
                        if db_u["login"] == u["login"]: db_u["session"] = s_str; db_u["tg_name"] = uname
                    save_db(st.session_state.db)
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                loop.run_until_complete(finish()); st.rerun()

    with tabs: # ИСТОРИЯ
        my_h = [h for h in st.session_state.db["history"] if h["user"] == u["login"]]
        if my_h: st.table(pd.DataFrame(my_h)[::-1])
        else: st.write("Пусто.")

    with tabs: # КОМАНДА
        if u["role"] == "Админ":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Новый скаут")
                nl, np = st.text_input("Логин"), st.text_input("Пароль")
                if st.button("Создать"):
                    st.session_state.db["users"].append({"login": nl, "pass": np, "role": "Работник", "session": "", "tg_name": "", "limit": 0})
                    save_db(st.session_state.db); st.success(f"Скаут {nl} добавлен!"); st.rerun()
            with col2:
                for i, worker in enumerate(st.session_state.db["users"]):
                    if worker["role"] != "Админ":
                        with st.expander(f"👤 {worker['login']} ({worker.get('limit',0)}/50)"):
                            if st.button("Удалить", key=f"del_{i}"):
                                st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()
        else: st.info("Только для админа.")

    with tabs: # ВЫХОД
        if st.button("ПОДТВЕРДИТЬ ВЫХОД"):
            st.query_params.clear(); st.session_state.clear(); st.rerun()
