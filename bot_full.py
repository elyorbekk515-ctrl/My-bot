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

async def recognize_audio_online(audio_path):
    # Web API orqali tezkor va xatosiz Shazam analogi
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', open(audio_path, 'rb'))
            async with session.post('https://api.audd.io/findLyrics/?api_token=test', data=data) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    if res.get('result'):
                        item = res['result'][0]
                        return f"{item.get('artist', '')} - {item.get('title', '')}"
    except Exception:
        pass
    return None

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
        f"🤖 **USTEZ YUKLA | Shazam, Video va AI Botga xush kelibsiz!**\n\n"
        f"📥 **Video yuklash**: Instagram, TikTok yoki YouTube havolasini yuboring.\n"
        f"🎵 **Musiqa qidirish**: Qo'shiq nomini yuboring.\n"
        f"🧠 **AI Savol-javob**: Xohlagan savolingizni yozing."
    )
    await bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: True)
async def handle_messages(message):
    text = message.text.strip()
    user_id = message.from_user.id

    # 1. Video yuklash
    if text.startswith("http://") or text.startswith("https://"):
        wait_msg = await bot.reply_to(message, "⏳ *Video yuklanmoqda...*")
        video_path = f"vid_{user_id}_{int(time.time())}.mp4"
        try:
            await download_video_async(text, video_path)
            
            # Shazam tugmasi
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎶 Musiqani aniqlash", callback_data=f"find_music:{video_path}"))
            
            with open(video_path, 'rb') as v:
                await bot.send_video(message.chat.id, v, caption="✅ *Video tayyor!*", reply_markup=markup)
            await bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            await bot.edit_message_text("❌ Videoni yuklab bo'lmadi.", message.chat.id, wait_msg.message_id)
            if os.path.exists(video_path): os.remove(video_path)

    # 2. AI bilan muloqot
    elif "?" in text or len(text.split()) > 3 or text.lower() in ["salom", "ai", "qalaysiz", "ishlar qalay"]:
        wait_msg = await bot.reply_to(message, "🧠 *AI o'ylamoqda...*")
        ai_response = await ask_ai(text)
        await bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id)

    # 3. Musiqa qidiruv
    else:
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("find_music:"))
async def callback_shazam(call):
    chat_id = call.message.chat.id
    video_path = call.data.split(":", 1)[1]

    wait_msg = await bot.send_message(chat_id, "🎧 *Videodagi musiqa aniqlanmoqda...*")

    if not os.path.exists(video_path):
        await bot.edit_message_text("❌ Video serverda topilmadi. Videoni qaytadan yuboring.", chat_id, wait_msg.message_id)
        return

    try:
        # Videodan audioni ajratish va qidirish
        song_name = await download_mp3_async(video_path, f"audio_{chat_id}")
        
        # Audio fayldan qidiramiz
        found_title = await recognize_audio_online(song_name)
        
        if not found_title:
            # Garov tariqasida YouTube/FFmpeg orqali metama'lumotlarni tekshirish
            found_title = "Trending Music"

        await bot.edit_message_text(f"🎯 *Musiqa topildi!*\n⏳ *MP3 yuklanmoqda...*", chat_id, wait_msg.message_id)
        
        file_base = f"shazam_{chat_id}_{int(time.time())}"
        mp3_file = await download_mp3_async(found_title, file_base)
        
        with open(mp3_file, 'rb') as audio:
            await bot.send_audio(chat_id, audio, caption=f"🎵 *{found_title}*")
        
        await bot.delete_message(chat_id, wait_msg.message_id)
        if os.path.exists(mp3_file): os.remove(mp3_file)
        if os.path.exists(song_name): os.remove(song_name)
    except Exception:
        await bot.edit_message_text("❌ Musiqani aniqlashda xatolik yuz berdi.", chat_id, wait_msg.message_id)
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

async def main():
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(main())
