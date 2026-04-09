import streamlit as st
import asyncio
import pandas as pd
import os
import json
from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
API_ID = 34321415 
API_HASH = 'a858399e90e04f5992a97096b614f31e'
MY_SESSION_STRING = '1ApWapzMBu6a2yrYGwEl4SmIajfYwWFcdt93DPZJADeUU4mA61FcGqC9v_PqjQZm0zMQC3OZFXKLQzM_3_D15YlGyk4Z4s64oPq_dF2FXIW67-dTreso3mfFl2v3BILmO_PKoR_iBMZ5aYCUM_DY9rJcWA2_xhQ1RSmUc1HxzD9L1aDF7fiHAWcLiduwJFSOYDSuWTINIXPIIMsmqtxGxeNFM2sbgWJIFkBhGe0I4g_YaSlcV342H53kS0JUJrS2IGaTI6KgqQ6XymA9MdtjjjHRWiqb4xLRTBqyXgDvAFnnsnbegH8nMEkwudAyEa-Y-O5oCP4WJfS220InB3tNJFe8u9_qXbJw='

AVATAR_DIR = "avatars"
if not os.path.exists(AVATAR_DIR): os.makedirs(AVATAR_DIR)

st.set_page_config(page_title="VM Models | Blue Edition", layout="wide")

# --- СТИЛИЗАЦИЯ VM MODELS BLUE ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #080a12; color: #ffffff; }}
    [data-testid="stDataFrame"] {{ background: #080a12; border: none; }}
    div.stButton > button {{
        background: linear-gradient(90deg, #007BFF 0%, #0056b3 100%) !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
        padding: 10px 25px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
        transition: 0.3s;
    }}
    div.stButton > button:hover {{ 
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 123, 255, 0.5);
        color: white !important;
    }}
    .stTabs [aria-selected="true"] {{ color: #007BFF !important; border-bottom-color: #007BFF !important; }}
    .brand-vm {{ color: #007BFF; font-size: 32px; font-weight: 900; font-family: 'Arial Black'; }}
    .brand-models {{ color: #ffffff; font-size: 32px; font-weight: 900; }}
    .info-card {{
        background: #101425;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #1c223a;
        margin-bottom: 15px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГИКА ПАРСЕРА ---
async def run_live_parser(target, days, limit, method, placeholder):
    client = TelegramClient(StringSession(MY_SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    results, seen = [], set()

    async def process(u):
        if not u or u.id in seen or getattr(u, 'bot', False): return
        seen.add(u.id)
        ava = "https://flaticon.com"
        if u.photo:
            p_path = f"{AVATAR_DIR}/{u.id}.jpg"
            if not os.path.exists(p_path):
                try: await client.download_profile_photo(u, file=p_path)
                except: pass
            if os.path.exists(p_path): ava = p_path
        un = u.username or ""
        results.append({
            "АВА": ava,
            "ИМЯ": f"{u.first_name or ''} {u.last_name or ''}".strip() or "User",
            "ЮЗЕРНЕЙМ": f"@{un}" if un else "---",
            "СВЯЗЬ": f"tg://resolve?domain={un}" if un else f"tg://user?id={u.id}"
        })
        placeholder.dataframe(
            pd.DataFrame(results), 
            column_config={
                "АВА": st.column_config.ImageColumn("АВА"),
                "СВЯЗЬ": st.column_config.LinkColumn("НАПИСАТЬ 🔵")
            }, 
            use_container_width=True, hide_index=True
        )

    try:
        if "Все" in method:
            for char in "abcdefghijklmnopqrstuvwxyz":
                res = await client(functions.channels.GetParticipantsRequest(
                    channel=target, filter=types.ChannelParticipantsSearch(char),
                    offset=0, limit=1000, hash=0
                ))
                for u in res.users: await process(u)
        else:
            limit_date = datetime.now(timezone.utc) - timedelta(days=days)
            async for m in client.iter_messages(target, limit=limit):
                if m.date < limit_date: break
                if m.sender_id: await process(await m.get_sender())
    finally: await client.disconnect()
    return results

# --- ИНТЕРФЕЙС ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div style="text-align:center; padding-top:100px;"><span class="brand-vm">VM</span> <span class="brand-models">Models</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ENTER"):
            if u == "Admin.Maksym" and p == "Maksym777":
                st.session_state.auth = True; st.session_state.user_data = {"login": u, "role": "Админ"}
                st.rerun()
            else: st.error("Ошибка доступа")
else:
    st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #1c223a; margin-bottom:20px;"><div class="brand-vm">VM <span class="brand-models">Models</span></div><div style="color:#58a6ff; font-weight:bold;">Premium Blue Edition</div></div>', unsafe_allow_html=True)
    tabs = st.tabs(["📖 ИНСТРУКЦИЯ", "📦 СБОР", "👥 КОМАНДА"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="info-card"><b style="color:#007BFF;">📱 Статус</b><br>Система авторизована. Канал связи стабилен.</div>', unsafe_allow_html=True)
            st.markdown('<div class="info-card"><b style="color:#007BFF;">🛡 Приватность</b><br>Все выгрузки защищены VM Models.</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="info-card"><b style="color:#007BFF;">🔍 Сбор</b><br>Используйте Глубокий поиск для больших чатов.</div>', unsafe_allow_html=True)
            st.markdown('<div class="info-card"><b style="color:#007BFF;">📥 Выгрузка</b><br>После сбора доступен экспорт в CSV.</div>', unsafe_allow_html=True)
        if st.button("ПОГНАЛИ СОБИРАТЬ! 🚀"): st.info("Перейдите во вкладку СБОР")

    with tabs[1]:
        st.markdown('<div style="background:#101425; padding:25px; border-radius:15px; border:1px solid #1c223a; margin-bottom:20px;">', unsafe_allow_html=True)
        target = st.text_input("Ссылка на группу", placeholder="nakordoni_poland")
        method = st.radio("Алгоритм:", ["Активные (неделя)", "Все участники"], horizontal=True)
        if st.button("🚀 ЗАПУСТИТЬ ПАРСИНГ"):
            if target:
                table_placeholder = st.empty()
                loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
                final_data = loop.run_until_complete(run_live_parser(target, 7, 2000, method, table_placeholder))
                if final_data:
                    csv = pd.DataFrame(final_data).to_csv(index=False).encode('utf-8')
                    st.download_button("📥 СКАЧАТЬ CSV", csv, "scout_data.csv")
            else: st.warning("Введите цель!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        if st.session_state.user_data["role"] == "Админ":
            st.write("👤 Admin.Maksym — **Online** 🔵")
            st.write("👤 Worker1 — **Active** ⚪")

