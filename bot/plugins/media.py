import asyncio
import datetime

from pyrogram import Client, Filters, InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils import is_valid_file, generate_stream_link, get_duration, gen_ik_buttons
from config import Config
from bot import db


@Client.on_message(Filters.private & Filters.media)
async def _(c, m):
    if not await db.is_user_exist(m.chat.id):
        await db.add_user(m.chat.id)
        await c.send_message(
            Config.LOG_CHANNEL,
            f"New User [{m.from_user.first_name}](tg://user?id={m.chat.id}) started."
        )
    
    ban_status = await db.get_ban_status(m.chat.id)
    if ban_status['is_banned']:
        if (datetime.date.today() - datetime.date.fromisoformat(ban_status['banned_on'])).days > ban_status['ban_duration']:
            await db.remove_ban(m.chat.id)
        else:
            await m.reply_text(
                f"Sorry Dear, You misused me. So you are Blocked!.\n\nBlock Reason: __{ban_status['ban_reason']}__",
                quote=True
            )
            return
    
    if not is_valid_file(m):
        return
    
    snt = await m.reply_text("Hi there, Please wait while I'm getting everything ready to process your request!", quote=True)
    
    file_link = await generate_stream_link(m)
    if file_link is None:
        await snt.edit_text("😟 Sorry! I cannot help you right now, I'm having hard time processing the file.")
        l = await m.forward(Config.LOG_CHANNEL)
        await l.reply_text(f'Could not create stream link', True)
        return
    
    duration = await get_duration(file_link)
    if isinstance(duration, str):
        await snt.edit_text("😟 Sorry! I cannot open the file.")
        l = await m.forward(Config.LOG_CHANNEL)
        await l.reply_text(f'stream link : {file_link}\n\n {duration}', True)
        return
    
    btns = gen_ik_buttons()
    
    if duration >= 600:
        btns.append([InlineKeyboardButton('Generate Sample Video!', 'smpl')])
    
    await snt.edit_text(
        text=f"Hi, Choose the number of screenshots you need.\n\nTotal duration: `{datetime.timedelta(seconds=duration)}` (`{duration}s`)",
        reply_markup=InlineKeyboardMarkup(btns)
    )
