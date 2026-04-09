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

st.set_page_config(page_title="VM Models | Enterprise Pro", layout="wide", initial_sidebar_state="collapsed")

# --- УМНАЯ ЛОГИКА БАЗЫ ДАННЫХ (ИСПРАВЛЯЕТ ОШИБКИ) ---
def load_db():
    default_db = {
        "users": [{"login": "Admin.Maksym", "pass": "Maksym777", "role": "Админ", "session": ADMIN_SESSION, "tg_name": "@Maksym_Admin", "limit": 0}],
        "history": []
    }
    if not os.path.exists(DB_FILE): return default_db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # ФИКС: Если у старых юзеров нет нужных полей, добавляем их прямо сейчас
            for u in data.get("users", []):
                if "limit" not in u: u["limit"] = 0
                if "tg_name" not in u: u["tg_name"] = ""
                if "session" not in u: u["session"] = ""
                if "role" not in u: u["role"] = "Работник"
            return data
    except: return default_db

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

if 'db' not in st.session_state: st.session_state.db = load_db()
if 'auth' not in st.session_state: st.session_state.auth = False

# --- СТИЛИЗАЦИЯ (ПРЕМИУМ ДИЗАЙН) ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    .stApp { background-color: #0d111b; color: #ffffff; }
    .brand-vm { color: #007BFF; font-size: 32px; font-weight: 900; font-family: 'Arial Black'; }
    .brand-models { color: #ffffff; font-size: 32px; font-weight: 900; }
    .status-card { background: #161b2c; border: 1px solid #232d45; border-radius: 12px; padding: 15px; text-align: center; }
    .status-label { color: #8a8d9b; font-size: 11px; text-transform: uppercase; font-weight: bold; }
    .status-on { color: #3fb950; font-weight: bold; }
    .status-off { color: #f85149; font-weight: bold; }
    div.stButton > button { background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%); color: white !important; border-radius: 8px; font-weight: bold; width: 100%; border: none; padding: 12px; }
    .stTabs [aria-selected="true"] { color: #007BFF !important; border-bottom: 3px solid #007BFF !important; }
    .stTextInput input { background-color: #0d111b !important; border: 1px solid #30363d !important; color: white !important; }
    .instr-link { color: #007BFF !important; text-decoration: underline; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ТЕЛЕГРАМ ---
async def start_telegram_logic(api_id, api_hash, phone):
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    sent_code = await client.send_code_request(phone)
    return client, sent_code.phone_code_hash

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

# --- ПРОВЕРКА ВХОДА ---
if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        l_in = st.text_input("Логин")
        p_in = st.text_input("Пароль", type="password")
        if st.button("ENTER"):
            found = next((x for x in st.session_state.db["users"] if x["login"] == l_in and x["pass"] == p_in), None)
            if found:
                st.session_state.auth = True; st.session_state.user = found; st.rerun()
            else: st.error("Неверный доступ")
else:
    u = st.session_state.user
    st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:center; padding:15px; border-bottom:1px solid #232d45; margin-bottom:20px;"><div class="brand-vm">VM <span class="brand-models">Models</span></div><div style="color:#8a8d9b;">{u.get("role", "Скаут")}: <b>{u["login"]}</b></div></div>', unsafe_allow_html=True)

    # ДАШБОРД (ВЕРХНИЕ КАРТОЧКИ)
    tg_name = u.get("tg_name", "")
    tg_status = f'<span class="status-on">ПОДКЛЮЧЕН <br><small>{tg_name}</small></span>' if u.get("session") else '<span class="status-off">НЕ ПОДКЛЮЧЕН</span>'
    
    c_s1, c_s2, c_s3 = st.columns(3)
    c_s1.markdown(f'<div class="status-card"><div class="status-label">Аккаунт</div><div style="font-size:18px; font-weight:bold;">{u["login"]}</div></div>', unsafe_allow_html=True)
    c_s2.markdown(f'<div class="status-card"><div class="status-label">Telegram Status</div><div style="font-size:18px;">{tg_status}</div></div>', unsafe_allow_html=True)
    c_s3.markdown(f'<div class="status-card"><div class="status-label">Лимит (24ч)</div><div style="font-size:18px; font-weight:bold;">{u.get("limit", 0)} / 50</div></div>', unsafe_allow_html=True)

    tabs = st.tabs(["⚡ СБОР", "📱 АККАУНТ", "📜 ИСТОРИЯ", "👥 КОМАНДА", "🚪 ВЫХОД"])

    # ВКЛАДКА: СБОР
    with tabs[0]:
        user_sess = u.get("session", ADMIN_SESSION if u["role"] == "Админ" else "")
        if not user_sess:
            st.warning("⚠️ Перейдите во вкладку АККАУНТ и подключите свой Telegram.")
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
                    if u.get('limit', 0) >= 50: st.error("Дневной лимит исчерпан!")
                    else:
                        ph = st.empty()
                        loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                        data = loop.run_until_complete(run_live_parser(user_sess, target, days_v, method, ph))
                        if data:
                            # Обновляем лимит мгновенно
                            for db_u in st.session_state.db["users"]:
                                if db_u["login"] == u["login"]: 
                                    db_u["limit"] = db_u.get("limit", 0) + 1
                                    st.session_state.user["limit"] = db_u["limit"]
                            st.session_state.db["history"].append({"user": u["login"], "target": target, "count": len(data), "date": datetime.now().strftime("%d.%m %H:%M")})
                            save_db(st.session_state.db)
                            
                            st.write("---")
                            c_d1, c_d2 = st.columns(2)
                            usernames_txt = "\n".join([i['ЮЗЕРНЕЙМ'] for i in data if i['ЮЗЕРНЕЙМ'] != "---"])
                            c_d1.download_button("📥 СКАЧАТЬ В БЛОКНОТ (@)", usernames_txt, "usernames.txt")
                            c_d2.download_button("📥 СКАЧАТЬ CSV (Полный)", pd.DataFrame(data).to_csv(index=False).encode('utf-8'), "vm_scout.csv")
                            st.success("Готово!")
                else: st.warning("Укажите цель!")
            st.markdown('</div>', unsafe_allow_html=True)

    # ВКЛАДКА: АККАУНТ
    with tabs[1]:
        if u["role"] == "Админ": st.success(f"✅ Админ-аккаунт {tg_name} активен.")
        elif u.get("session"):
            st.success(f"✅ Подключено: {u.get('tg_name')}")
            if st.button("Отключить"):
                for db_u in st.session_state.db["users"]:
                    if db_u["login"] == u["login"]: db_u["session"] = ""; db_u["tg_name"] = ""
                save_db(st.session_state.db); st.rerun()
        else:
            st.markdown(f'Инструкция: <a href="https://telegram.org" target="_blank" class="instr-link">my.telegram.org</a>', unsafe_allow_html=True)
            phone = st.text_input("Ваш номер (+...)")
            if st.button("Прислать код"):
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                client, c_h = loop.run_until_complete(start_telegram_logic(API_ID_DEFAULT, API_HASH_DEFAULT, phone))
                st.session_state.temp_client = client; st.session_state.temp_hash = c_h; st.info("Код отправлен!")
            t_code = st.text_input("Код подтверждения")
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

    # ВКЛАДКА: ИСТОРИЯ
    with tabs[2]:
        my_h = [h for h in st.session_state.db["history"] if h["user"] == u["login"]]
        if my_h: st.table(pd.DataFrame(my_h)[::-1])
        else: st.write("История пуста.")

    # ВКЛАДКА: КОМАНДА
    with tabs[3]:
        if u["role"] == "Админ":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Новый скаут")
                nl, np = st.text_input("Логин"), st.text_input("Пароль")
                if st.button("Создать доступ"):
                    st.session_state.db["users"].append({"login": nl, "pass": np, "role": "Работник", "session": "", "tg_name": "", "limit": 0})
                    save_db(st.session_state.db); st.rerun()
            with col2:
                for i, worker in enumerate(st.session_state.db["users"]):
                    if worker["role"] != "Админ":
                        # ФИКС KEYERROR: Используем .get() для безопасности
                        label = f"👤 {worker['login']} ({worker.get('limit', 0)}/50)"
                        with st.expander(label):
                            if st.button("Удалить", key=f"del_{i}"):
                                st.session_state.db["users"].pop(i); save_db(st.session_state.db); st.rerun()
        else: st.info("Только для админа.")

    # ВКЛАДКА: ВЫХОД
    with tabs[4]:
        if st.button("Подтвердить выход"):
            st.session_state.auth = False; st.rerun()
