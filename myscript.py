import streamlit as st
import asyncio
import pandas as pd
from telethon import TelegramClient
from datetime import datetime, timedelta, timezone

# Твои ключи
api_id = 34321415 
api_hash = 'a858399e90e04f5992a97096b614f31e'

st.set_page_config(page_title="TG Parser Web", layout="wide")
st.title("🌐 Telegram Web Parser")

# Настройки в боковой панели
with st.sidebar:
    st.header("Настройки")
    target_url = st.text_input("Ссылка на группу (без @)", "nadiyno_perevozumo")
    days_to_check = st.selectbox("Период активности (дней):", [5, 10, 30])
    msg_limit = st.number_input("Лимит проверки сообщений", 100, 10000, 1000)

if st.button("🚀 Запустить поиск активных пользователей"):
    async def run_parser():
        client = TelegramClient('final_session', api_id, api_hash)
        await client.start()
        
        limit_date = datetime.now(timezone.utc) - timedelta(days=days_to_check)
        active_users = {}

        st.info(f"Анализируем сообщения за последние {days_to_check} дней...")
        
        async for message in client.iter_messages(target_url, limit=msg_limit):
            if message.date < limit_date: break
            
            if message.sender_id and message.sender_id not in active_users:
                sender = await message.get_sender()
                if sender and not getattr(sender, 'bot', False):
                    username = getattr(sender, 'username', None)
                    link = f"https://t.me{username}" if username else "Нет ника"
                    active_users[message.sender_id] = {
                        "Имя": getattr(sender, 'first_name', 'Скрыто'),
                        "Юзернейм": f"@{username}" if username else "---",
                        "Ссылка на профиль": link,
                        "Последняя активность": message.date.strftime('%Y-%m-%d %H:%M')
                    }
        
        await client.disconnect()
        return list(active_users.values())

    results = asyncio.run(run_parser())
    
    if results:
        df = pd.DataFrame(results)
        st.success(f"Найдено активных: {len(df)}")
        # Делаем колонку со ссылками кликабельной
        st.dataframe(df, column_config={"Ссылка на профиль": st.column_config.LinkColumn()})
        st.download_button("Скачать результат Excel", df.to_csv(index=False).encode('utf-16'), "active_users.csv")
    else:
        st.warning("Активных пользователей не найдено.")
