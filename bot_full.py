import asyncio
import os
import time
import aiohttp
import urllib.parse
import random
import re
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import yt_dlp

TOKEN = "8521430059:AAGfd5eMdZaatX79rHp3UCXCiIlwwhtutck"
bot = AsyncTeleBot(TOKEN, parse_mode="Markdown")

async def download_mp3_async(query, output_path):
    loop = asyncio.get_running_loop()
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1:'
    }
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
    await loop.run_in_executor(None, download)
    return output_path + ".mp3"

async def download_video_async(url, output_path):
    loop = asyncio.get_running_loop()
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    await loop.run_in_executor(None, download)
    return output_path

def latin_to_cyrillic(text):
    chart = {'a':'а','b':'б','d':'д','e':'е','f':'ф','g':'г','h':'х','i':'и','j':'ж','k':'к','l':'л','m':'м','n':'н','o':'о','p':'п','q':'к','r':'р','s':'с','t':'т','u':'у','v':'в','x':'х','y':'й','z':'з'}
    return "".join(chart.get(c.lower(), c) for c in text)

def cyrillic_to_latin(text):
    chart = {'а':'a','б':'b','д':'d','е':'e','ф':'f','г':'g','х':'h','и':'i','ж':'j','к':'k','л':'l','m':'m','н':'n','о':'o','п':'p','к':'q','р':'r','с':'s','т':'t','у':'u','в':'v','й':'y','з':'z'}
    return "".join(chart.get(c.lower(), c) for c in text)

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎧 Musiqa Qidirish (MP3)", callback_data="f_mp3"),
        types.InlineKeyboardButton("📥 Video Yuklagich", callback_data="f_down"),
        types.InlineKeyboardButton("📱 QR Kod Yaratish", callback_data="f_qr"),
        types.InlineKeyboardButton("🎙 Matnni Ovozga Aylantirish", callback_data="f_tts"),
        types.InlineKeyboardButton("💱 Valyuta Kurslari", callback_data="f_valyuta"),
        types.InlineKeyboardButton("🌤 Ob-Havo", callback_data="f_weather"),
        types.InlineKeyboardButton("🆔 Mening Profilim", callback_data="f_myid"),
        types.InlineKeyboardButton("🔐 Parol Yaratish", callback_data="f_pass"),
        types.InlineKeyboardButton("🎲 Tanga / Tasodifiy Son", callback_data="f_dice"),
        types.InlineKeyboardButton("🔄 Lotin -> Kirill", callback_data="f_l2c"),
        types.InlineKeyboardButton("🔄 Kirill -> Lotin", callback_data="f_c2l"),
        types.InlineKeyboardButton("⏱ Hozirgi Vaqt", callback_data="f_time"),
        types.InlineKeyboardButton("📏 Matn Uzunligi", callback_data="f_len"),
        types.InlineKeyboardButton("🔠 Katta Harflar", callback_data="f_upper"),
        types.InlineKeyboardButton("🔡 Kichik Harflar", callback_data="f_lower"),
        types.InlineKeyboardButton("🔍 Google Qidiruv Linki", callback_data="f_google"),
        types.InlineKeyboardButton("🌐 IP-Manzil Ma'lumoti", callback_data="f_ip"),
        types.InlineKeyboardButton("🧮 Kalkulyator", callback_data="f_calc"),
        types.InlineKeyboardButton("📊 Bot Holati", callback_data="f_status"),
        types.InlineKeyboardButton("💡 Motivatsiya", callback_data="f_quote"),
        types.InlineKeyboardButton("ℹ️ Yordam / Qo'llanma", callback_data="f_help")
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    text = (
        f"👋 Salom, *{message.from_user.first_name}*!\n\n"
        f"🚀 *20-in-1 Mega Botga xush kelibsiz!*\n\n"
        f"• Qo'shiq yuklash uchun shunchaki **nomini** yozing!\n"
        f"• Video yuklash uchun **Instagram, YouTube yoki TikTok linkini** yuboring!\n"
        f"• Boshqa xizmatlar uchun quyidagi tugmalardan foydalaning."
    )
    await bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message):
    text = message.text
    user_id = message.from_user.id

    if text.startswith("http"):
        wait_msg = await bot.reply_to(message, "⏳ *Video yuklanmoqda...*")
        video_path = f"vid_{user_id}_{int(time.time())}.mp4"
        try:
            await download_video_async(text, video_path)
            with open(video_path, 'rb') as v:
                await bot.send_video(message.chat.id, v, caption="✅ *Video tayyor!*")
            await bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            await bot.edit_message_text("❌ Videoni yuklab bo'lmadi.", message.chat.id, wait_msg.message_id)
        finally:
            if os.path.exists(video_path): os.remove(video_path)
    else:
        wait_msg = await bot.reply_to(message, f"🔍 *'{text}' musiqasi MP3 yuklanmoqda...*")
        file_base = f"music_{user_id}_{int(time.time())}"
        try:
            mp3_file = await download_mp3_async(text, file_base)
            with open(mp3_file, 'rb') as audio:
                await bot.send_audio(message.chat.id, audio, caption=f"🎵 *{text}*")
            await bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            await bot.edit_message_text("❌ Qo'shiq topilmadi.", message.chat.id, wait_msg.message_id)
        finally:
            expected_mp3 = file_base + ".mp3"
            if os.path.exists(expected_mp3): os.remove(expected_mp3)

@bot.callback_query_handler(func=lambda call: True)
async def callback_listener(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "f_mp3":
        await bot.send_message(chat_id, "🎵 *Qo'shiq nomi yoki ijrochisini yozib yuboring:*")
    elif data == "f_valyuta":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/") as resp:
                    res = await resp.json()
                    usd = next(item for item in res if item["Ccy"] == "USD")['Rate']
                    eur = next(item for item in res if item["Ccy"] == "EUR")['Rate']
                    await bot.send_message(chat_id, f"💱 *Markaziy Bank Kurslari:*\n\n🇺🇸 1 USD = {usd} so'm\n🇪🇺 1 EUR = {eur} so'm")
        except:
            await bot.send_message(chat_id, "❌ Xatolik yuz berdi.")
    elif data == "f_myid":
        await bot.send_message(chat_id, f"🆔 *Sizning ID:* `{call.from_user.id}`")
    elif data == "f_pass":
        pwd = "".join(random.choice("abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*") for _ in range(12))
        await bot.send_message(chat_id, f"🔐 *Parol:* `{pwd}`")
    elif data == "f_dice":
        await bot.send_message(chat_id, f"🎯 *Son:* `{random.randint(1, 100)}`")
    elif data == "f_time":
        await bot.send_message(chat_id, f"⏱ *Vaqt:* `{time.strftime('%Y-%m-%d %H:%M:%S')}`")
    elif data == "f_status":
        await bot.send_message(chat_id, "📊 *Bot Holati:* ONLINE ✅ (Render Server)")
    elif data == "f_quote":
        await bot.send_message(chat_id, "💡 *Haqiqiy g'alaba — bu kechagidan yaxshiroq bo'lishdir.*")
    elif data == "f_weather":
        await bot.send_message(chat_id, "🌤 *Ob-havo:* +30°C, Musaffo osmon.")
    elif data == "f_help":
        await bot.send_message(chat_id, "ℹ️ Link yuboring (Video) yoki Qo'shiq nomini yozing (MP3).")
    elif data == "f_qr":
        msg = await bot.send_message(chat_id, "📱 *QR-kod uchun matn yuboring:*")
        bot.register_next_step_handler(msg, step_qr)
    elif data == "f_tts":
        msg = await bot.send_message(chat_id, "🎙 *Inglizcha matn yuboring:*")
        bot.register_next_step_handler(msg, step_tts)
    elif data == "f_l2c":
        msg = await bot.send_message(chat_id, "🔄 *Lotincha matn yuboring:*")
        bot.register_next_step_handler(msg, step_l2c)
    elif data == "f_c2l":
        msg = await bot.send_message(chat_id, "🔄 *Kirillcha matn yuboring:*")
        bot.register_next_step_handler(msg, step_c2l)
    elif data == "f_len":
        msg = await bot.send_message(chat_id, "📏 *Matn yuboring:*")
        bot.register_next_step_handler(msg, step_len)
    elif data == "f_upper":
        msg = await bot.send_message(chat_id, "🔠 *Matn yuboring:*")
        bot.register_next_step_handler(msg, step_upper)
    elif data == "f_lower":
        msg = await bot.send_message(chat_id, "🔡 *Matn yuboring:*")
        bot.register_next_step_handler(msg, step_lower)
    elif data == "f_google":
        msg = await bot.send_message(chat_id, "🔍 *Qidiruv so'zini yuboring:*")
        bot.register_next_step_handler(msg, step_google)
    elif data == "f_ip":
        msg = await bot.send_message(chat_id, "🌐 *IP-manzilni yuboring:*")
        bot.register_next_step_handler(msg, step_ip)
    elif data == "f_calc":
        msg = await bot.send_message(chat_id, "🧮 *Misol yuboring (masalan 12+15):*")
        bot.register_next_step_handler(msg, step_calc)
    elif data == "f_down":
        await bot.send_message(chat_id, "📥 *Video havolasini yuboring!*")

async def step_qr(message):
    encoded = urllib.parse.quote(message.text)
    await bot.send_photo(message.chat.id, f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}")

async def step_tts(message):
    encoded = urllib.parse.quote(message.text)
    await bot.send_audio(message.chat.id, f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=en&client=tw-ob")

async def step_l2c(message):
    await bot.send_message(message.chat.id, f"🔄 *Kirillcha:* {latin_to_cyrillic(message.text)}")

async def step_c2l(message):
    await bot.send_message(message.chat.id, f"🔄 *Lotincha:* {cyrillic_to_latin(message.text)}")

async def step_len(message):
    await bot.send_message(message.chat.id, f"📏 *Belgilar:* {len(message.text)} ta | *So'zlar:* {len(message.text.split())} ta")

async def step_upper(message):
    await bot.send_message(message.chat.id, message.text.upper())

async def step_lower(message):
    await bot.send_message(message.chat.id, message.text.lower())

async def step_google(message):
    encoded = urllib.parse.quote(message.text)
    await bot.send_message(message.chat.id, f"https://www.google.com/search?q={encoded}")

async def step_ip(message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://ip-api.com/json/{message.text}") as resp:
                data = await resp.json()
                await bot.send_message(message.chat.id, f"🌐 *IP:* {data['query']}\n🏳️ *Davlat:* {data['country']}\n🏙 *Shahar:* {data['city']}")
    except:
        await bot.send_message(message.chat.id, "❌ Xatolik.")

async def step_calc(message):
    try:
        res = eval(re.sub(r'[^0-9+\-*/().]', '', message.text))
        await bot.send_message(message.chat.id, f"🧮 *Natija:* `{res}`")
    except:
        await bot.send_message(message.chat.id, "❌ Xatolik.")

async def main():
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
