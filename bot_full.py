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

TOKEN = "8521430059:AAGfd5eMdZaatX79rHp3UCXCiIlwwhtutck"
bot = AsyncTeleBot(TOKEN, parse_mode="Markdown")

user_states = {}

# ASOSIY MENU (PASTKI TUGMALAR)
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📥 Video Yuklagich"),
        types.KeyboardButton("🎵 Musiqa Qidirish"),
        types.KeyboardButton("📱 QR Kod Yaratish"),
        types.KeyboardButton("🎙 Matnni Ovozga Aylantirish"),
        types.KeyboardButton("💱 Valyuta Kurslari"),
        types.KeyboardButton("🌤 Ob-Havo"),
        types.KeyboardButton("🆔 Mening Profilim"),
        types.KeyboardButton("🔑 Parol Yaratish"),
        types.KeyboardButton("🎲 Tasodifiy Tanga"),
        types.KeyboardButton("⏱ Hozirgi Vaqt"),
        types.KeyboardButton("💡 Motivation Sitata"),
        types.KeyboardButton("📊 Bot Holati")
    )
    return markup

async def download_media(url, is_audio=False):
    loop = asyncio.get_running_loop()
    file_id = int(time.time())
    out_tmpl = f"audio_{file_id}" if is_audio else f"vid_{file_id}.mp4"
    
    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_tmpl,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True,
            'default_search': 'ytsearch1:'
        }
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': out_tmpl,
            'quiet': True,
        }
    
    def dl():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    
    await loop.run_in_executor(None, dl)
    return out_tmpl + ".mp3" if is_audio else out_tmpl

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

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    text = (
        f"👋 Salom, *{message.from_user.first_name}*!\n\n"
        f"🚀 **Yordamchi Botga xush kelibsiz!**\n"
        f"Quyidagi tugmalardan birini tanlang yoki to'g'ridan-to me'yoriy savol/link yuboring:"
    )
    await bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
async def handle_all(message):
    text = message.text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Menyu tugmalari
    if text == "📥 Video Yuklagich":
        user_states[user_id] = "wait_video"
        await bot.send_message(chat_id, "📥 *Video yuklash uchun Instagram, TikTok yoki YouTube havolasini yuboring:*")
        return

    elif text == "🎵 Musiqa Qidirish":
        user_states[user_id] = "wait_music"
        await bot.send_message(chat_id, "🎵 *Qidirilayotgan qo'shiq nomini yozib yuboring:*")
        return

    elif text == "📱 QR Kod Yaratish":
        user_states[user_id] = "wait_qr"
        await bot.send_message(chat_id, "📱 *QR kod yaratish uchun matn yoki havola yuboring:*")
        return

    elif text == "🎙 Matnni Ovozga Aylantirish":
        user_states[user_id] = "wait_tts"
        await bot.send_message(chat_id, "🎙 *Ovozga aylantirish uchun matn yuboring:*")
        return

    elif text == "💱 Valyuta Kurslari":
        try:
            r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/").json()
            res = "💱 *Markaziy Bank valyuta kurslari:*\n\n"
            for item in r:
                if item['Code'] in ['USD', 'EUR', 'RUB']:
                    res += f"🔹 *{item['Cty_uz']} ({item['Code']}):* {item['Rate']} so'm\n"
            await bot.send_message(chat_id, res)
        except Exception:
            await bot.send_message(chat_id, "❌ Valyuta kurslarini olishda xatolik!")
        return

    elif text == "🌤 Ob-Havo":
        await bot.send_message(chat_id, "🌤 *Farg'ona:* +30°C, Müsaffo havo ☀️")
        return

    elif text == "🆔 Mening Profilim":
        user = message.from_user
        res = f"🆔 *Sizning profilingiz:*\n\n👤 Ism: {user.first_name}\n🔗 Username: @{user.username or 'Mavjud emas'}\n🆔 ID: `{user.id}`"
        await bot.send_message(chat_id, res)
        return

    elif text == "🔑 Parol Yaratish":
        pwd = "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*") for _ in range(12))
        await bot.send_message(chat_id, f"🔑 *Yangi xavfsiz parol:*\n`{pwd}`")
        return

    elif text == "🎲 Tasodifiy Tanga":
        await bot.send_dice(chat_id, emoji='🎲')
        return

    elif text == "⏱ Hozirgi Vaqt":
        t_now = time.strftime("%H:%M:%S | %d-%m-%Y", time.localtime())
        await bot.send_message(chat_id, f"⏱ *Hozirgi vaqt:* `{t_now}`")
        return

    elif text == "💡 Motivation Sitata":
        quotes = [
            "💡 \"Hech qachon taslim bo'lma! G'alaba oxirgi qadamda bo'lishi mumkin.\"",
            "💡 \"Bugungi qilgan harakatingiz — ertangi kelajagingiz poydevori.\"",
            "💡 \"Vaqt bu eng qimmatbaho boylik, uni behuda sarflamang.\""
        ]
        await bot.send_message(chat_id, random.choice(quotes))
        return

    elif text == "📊 Bot Holati":
        await bot.send_message(chat_id, "📊 *Bot holati:* 🟢 Faol (Render 24/7)")
        return

    # Holat va havola tekshirish
    state = user_states.get(user_id)

    if state == "wait_video" or text.startswith("http://") or text.startswith("https://"):
        user_states.pop(user_id, None)
        msg = await bot.reply_to(message, "⏳ *Video yuklanmoqda...*")
        try:
            file_path = await download_media(text, is_audio=False)
            with open(file_path, 'rb') as v:
                await bot.send_video(chat_id, v, caption="✅ *Video tayyor!*")
            await bot.delete_message(chat_id, msg.message_id)
            os.remove(file_path)
        except Exception:
            await bot.edit_message_text("❌ Videoni yuklab bo'lmadi. Linkni tekshiring.", chat_id, msg.message_id)
        return

    elif state == "wait_music":
        user_states.pop(user_id, None)
        msg = await bot.reply_to(message, f"🔍 *'{text}' qidirilmoqda...*")
        try:
            file_path = await download_media(text, is_audio=True)
            with open(file_path, 'rb') as audio:
                await bot.send_audio(chat_id, audio, caption=f"🎵 *{text}*")
            await bot.delete_message(chat_id, msg.message_id)
            os.remove(file_path)
        except Exception:
            await bot.edit_message_text("❌ Qo'shiq topilmadi.", chat_id, msg.message_id)
        return

    elif state == "wait_qr":
        user_states.pop(user_id, None)
        img = qrcode.make(text)
        qr_path = f"qr_{user_id}.png"
        img.save(qr_path)
        with open(qr_path, 'rb') as q:
            await bot.send_photo(chat_id, q, caption="📱 *Sizning QR kodingiz!*")
        os.remove(qr_path)
        return

    elif state == "wait_tts":
        user_states.pop(user_id, None)
        tts = gTTS(text=text, lang='uz')
        tts_path = f"tts_{user_id}.mp3"
        tts.save(tts_path)
        with open(tts_path, 'rb') as audio:
            await bot.send_audio(chat_id, audio, caption="🎙 *Ovozli fayl!*")
        os.remove(tts_path)
        return

    # Odatiy matn bo'lsa AI ga beramiz
    msg = await bot.reply_to(message, "🧠 *AI o'ylamoqda...*")
    res = await ask_ai(text)
    await bot.edit_message_text(res, chat_id, msg.message_id)

async def main():
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
