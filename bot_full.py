import asyncio
import os
import time
import aiohttp
import urllib.parse
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

async def ask_ai(prompt):
    try:
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
    except Exception:
        pass
    return "Kechirasiz, AI javob berishda xatolik yuz berdi."

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    text = (
        f"👋 Salom, *{message.from_user.first_name}*!\n\n"
        f"🤖 **Smart Shazam & AI Botga xush kelibsiz!**\n\n"
        f"📥 **Video yuklash**: Instagram, TikTok yoki YouTube havolasini yuboring.\n"
        f"🎵 **Musiqa yuklash**: Qo'shiq nomini yozib yuboring.\n"
        f"🧠 **AI Aqlli Yordamchi**: Xohlagan savolingizni berishingiz mumkin!"
    )
    await bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: True)
async def handle_messages(message):
    text = message.text.strip()
    user_id = message.from_user.id

    if text.startswith("http://") or text.startswith("https://"):
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

    elif len(text.split()) <= 4 and not text.endswith("?"):
        wait_msg = await bot.reply_to(message, f"🔍 *'{text}' musiqasi qidirilmoqda...*")
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

    else:
        wait_msg = await bot.reply_to(message, "🧠 *AI o'ylamoqda...*")
        ai_response = await ask_ai(text)
        await bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id)

async def main():
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
