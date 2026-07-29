import asyncio
import os
import time
import random
import urllib.parse
import aiohttp
import requests
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import yt_dlp
from gtts import gTTS
import qrcode
from bs4 import BeautifulSoup

TOKEN = "8521430059:AAGfd5eMdZaatX79rHp3UCXCiIlwwhtutck"
bot = AsyncTeleBot(TOKEN, parse_mode="Markdown")

# Vaqtinchalik saqlash uchun lug'at (State uchun)
user_states = {}

# --- YOUTUBE / MEDIA YUKLASH ---
async def download_media_async(url, output_path, is_audio=False):
    loop = asyncio.get_running_loop()
    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True, 'no_warnings': True, 'default_search': 'ytsearch1:'
        }
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path, 'quiet': True, 'no_warnings': True,
        }
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    await loop.run_in_executor(None, download)
    return output_path + ".mp3" if is_audio else output_path

async def ask_ai(prompt):
    try:
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
    except Exception:
        pass
    return "Kechirasiz, sun'iy intellekt javob berishda xatolik yuz berdi."

# --- ASOSIY MENYU ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("1. 📥 Video Yuklagich", callback_data="menu_video"),
        types.InlineKeyboardButton("2. 📱 QR Kod Yaratish", callback_data="menu_qr"),
        types.InlineKeyboardButton("3. 🎙 Matnni Ovozga Aylantirish", callback_data="menu_tts"),
        types.InlineKeyboardButton("4. 💱 Valyuta Kurslari", callback_data="menu_currency"),
        types.InlineKeyboardButton("5. 🌤 Ob-Havo", callback_data="menu_weather"),
        types.InlineKeyboardButton("6. 🆔 Mening Profilim", callback_data="menu_profile"),
        types.InlineKeyboardButton("7. 🔑 Parol Yaratish", callback_data="menu_password"),
        types.InlineKeyboardButton("8. 🎲 Tanga / Tasodifiy", callback_data="menu_dice"),
        types.InlineKeyboardButton("9. 🔄 Lotin -> Kirill", callback_data="menu_to_cyrillic"),
        types.InlineKeyboardButton("10. 🔄 Kirill -> Lotin", callback_data="menu_to_latin"),
        types.InlineKeyboardButton("11. ⏱ Hozirgi Vaqt", callback_data="menu_time"),
        types.InlineKeyboardButton("12. 📝 Matn Uzunligi", callback_data="menu_length"),
        types.InlineKeyboardButton("13. 🔠 KATTA HARFLarga", callback_data="menu_upper"),
        types.InlineKeyboardButton("14. 🔡 kichik harflarga", callback_data="menu_lower"),
        types.InlineKeyboardButton("15. 🔍 Google Qidiruv Linki", callback_data="menu_google"),
        types.InlineKeyboardButton("16. 🌐 IP-Manzil Ma'lumoti", callback_data="menu_ip"),
        types.InlineKeyboardButton("17. 🧮 Kalkulyator", callback_data="menu_calc"),
        types.InlineKeyboardButton("18. 📊 Bot Holati", callback_data="menu_status"),
        types.InlineKeyboardButton("19. 💡 Motivation Sitatalar", callback_data="menu_quote"),
        types.InlineKeyboardButton("20. ℹ️ Yordam / Qo'llanma", callback_data="menu_help")
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    text = (
        f"🚀 *20-in-1 Mega Botga xush kelibsiz!*\n\n"
        f"Menga Instagram, YouTube, TikTok linkini yuboring yoki quyidagi 20 xil funksiyadan birini tanlang:"
    )
    await bot.send_message(message.chat.id, text, reply_markup=get_main_menu())

# --- INLINE TUGMALAR BILAN ISHLASH ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
async def callback_menus(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    action = call.data.replace("menu_", "")

    if action == "video":
        user_states[user_id] = "wait_video"
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, "📥 *Video yuklash uchun Instagram, TikTok yoki YouTube havolasini yuboring:*")
    
    elif action == "qr":
        user_states[user_id] = "wait_qr"
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, "📱 *QR kod yaratish uchun matn yoki havola yuboring:*")

    elif action == "tts":
        user_states[user_id] = "wait_tts"
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, "🎙 *Matnni ovozga aylantirish uchun istalgan matn yuboring:*")

    elif action == "currency":
        try:
            r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
            rates = f"💱 *Markaziy Bank valyuta kurslari:*\n\n"
            for item in r:
                if item['Code'] in ['USD', 'EUR', 'RUB']:
                    rates += f"🇺🇸/🇪🇺/🇷🇺 *{item['Cty_uz']} ({item['Code']}):* {item['Rate']} so'm\n"
            await bot.answer_callback_query(call.id)
            await bot.send_message(chat_id, rates)
        except Exception:
            await bot.answer_callback_query(call.id, "Valyuta kurslarini olishda xatolik!")

    elif action == "weather":
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, "🌤 Hozircha ob-havo avtomatik Farg'ona bo'yicha: *+32°C, Ochiq havo* ☀️")

    elif action == "profile":
        user = call.from_user
        info = (
            f"🆔 *Sizning profilingiz:*\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"📛 Familiya: {user.last_name or 'Mavjud emas'}\n"
            f"🔗 Username: @{user.username or 'Mavjud emas'}\n"
            f"🆔 ID: `{user.id}`"
        )
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, info)

    elif action == "password":
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        pwd = "".join(random.choice(chars) for _ in range(12))
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, f"🔑 *Yangi xavfsiz parol:*\n`{pwd}`")

    elif action == "dice":
        await bot.answer_callback_query(call.id)
        await bot.send_dice(chat_id, emoji='🎲')

    elif action == "time":
        t_now = time.strftime("%H:%M:%S | %d-%m-%Y", time.localtime())
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, f"⏱ *Hozirgi vaqt:* `{t_now}`")

    elif action == "quote":
        quotes = [
            "💡 \"Hech qachon taslim bo'lma! G'alaba oxirgi qadamda bo'lishi mumkin.\"",
            "💡 \"Bugungi qilgan harakatingiz — ertangi kelajakongiz poydevori.\"",
            "💡 \"Vaqt bu eng qimmatbaho boylik, uni behuda sarflamang.\""
        ]
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, random.choice(quotes))

    elif action == "status":
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, "📊 *Bot holati:* 🟢 Ishlayapti (24/7 Render.com serverida)")

    elif action == "help":
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, "ℹ️ *Qo'llanma:* Istalgan tugmani bosing yoki to'g'ridan-to'g'ri matn/link yuboring!")

    else:
        user_states[user_id] = f"wait_{action}"
        await bot.answer_callback_query(call.id)
        await bot.send_message(chat_id, f"✍️ Ushbu funksiya uchun kerakli matn yoki sonni yuboring:")

# --- MATN VA LINKLARNI QAYTA ISHLASH ---
@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    text = message.text.strip()
    user_id = message.from_user.id
    state = user_states.get(user_id)

    # Agar maxsus holatda bo'lsa
    if state == "wait_video" or text.startswith("http://") or text.startswith("https://"):
        user_states.pop(user_id, None)
        wait_msg = await bot.reply_to(message, "⏳ *Video yuklanmoqda...*")
        video_path = f"vid_{user_id}_{int(time.time())}.mp4"
        try:
            await download_media_async(text, video_path, is_audio=False)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 Bosh Menyu", callback_data="menu_help"))
            with open(video_path, 'rb') as v:
                await bot.send_video(message.chat.id, v, caption="✅ *Video tayyor!*", reply_markup=markup)
            await bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            await bot.edit_message_text("❌ Videoni yuklab bo'lmadi. Linkni tekshiring.", message.chat.id, wait_msg.message_id)
        finally:
            if os.path.exists(video_path): os.remove(video_path)
        return

    elif state == "wait_qr":
        user_states.pop(user_id, None)
        img = qrcode.make(text)
        qr_path = f"qr_{user_id}.png"
        img.save(qr_path)
        with open(qr_path, 'rb') as q:
            await bot.send_photo(message.chat.id, q, caption="📱 *Sizning QR kodingiz tayyor!*")
        os.remove(qr_path)
        return

    elif state == "wait_tts":
        user_states.pop(user_id, None)
        tts = gTTS(text=text, lang='uz')
        tts_path = f"tts_{user_id}.mp3"
        tts.save(tts_path)
        with open(tts_path, 'rb') as audio:
            await bot.send_audio(message.chat.id, audio, caption="🎙 *Ovozli xabar tayyor!*")
        os.remove(tts_path)
        return

    elif state == "wait_length":
        user_states.pop(user_id, None)
        await bot.reply_to(message, f"📝 Matn uzunligi: **{len(text)}** ta belgi.")
        return

    elif state == "wait_upper":
        user_states.pop(user_id, None)
        await bot.reply_to(message, text.upper())
        return

    elif state == "wait_lower":
        user_states.pop(user_id, None)
        await bot.reply_to(message, text.lower())
        return

    elif state == "wait_calc":
        user_states.pop(user_id, None)
        try:
            res = eval(text)
            await bot.reply_to(message, f"🧮 Natija: *{res}*")
        except Exception:
            await bot.reply_to(message, "❌ Hisoblashda xatolik! Faqat raqamli misol yuboring (masalan: 2+2*2)")
        return

    # Odatiy holatda AI ga yuborish
    wait_msg = await bot.reply_to(message, "🧠 *AI o'ylamoqda...*")
    ai_response = await ask_ai(text)
    await bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id)

async def main():
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
