"""QANOT.AI Telegram bot: confirms "Telegram orqali kirish" requests with inline buttons.

Run with `python -m app.bot`. It shares the database with the API; the API creates the tables.
"""

import asyncio
import html
import logging
from datetime import UTC, datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from sqlalchemy import select

from .config import get_settings
from .db import SessionLocal
from .models import TelegramLogin, User

log = logging.getLogger("qanot.bot")
dp = Dispatcher()

SITE = get_settings().public_url


async def _find_user(session, telegram_id: int) -> User | None:
    return (await session.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()


@dp.message(CommandStart(deep_link=True))
async def start_with_token(message: Message, command: CommandObject) -> None:
    token = command.args or ""
    async with SessionLocal() as session:
        login = await session.get(TelegramLogin, token)
        if login is None or login.status != "pending" or login.expires_at < datetime.now(UTC):
            await message.answer("⌛️ Bu havola eskirgan. Saytda «Telegram orqali davom etish» tugmasini qayta bosing.")
            return
        existing = await _find_user(session, message.from_user.id)

    action = "kirishni" if existing else "ro'yxatdan o'tishni"
    text = (
        f"👋 Assalomu alaykum, <b>{html.escape(message.from_user.full_name)}</b>!\n\n"
        f"<b>QANOT.AI</b> saytiga {action} tasdiqlaysizmi?\n\n"
        f"💻 Qurilma: {html.escape(login.device or 'nomaʼlum')}\n\n"
        "<i>Agar bu siz bo'lmasangiz, «Bekor qilish»ni bosing.</i>"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok:{token}")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"no:{token}")],
        ]
    )
    await message.answer(text, reply_markup=keyboard)


@dp.message(CommandStart())
async def start_plain(message: Message) -> None:
    await message.answer(
        "👋 <b>QANOT.AI</b> botiga xush kelibsiz!\n\n"
        f"Tizimga kirish uchun saytda «Telegram orqali davom etish» tugmasini bosing:\n{SITE}"
    )


@dp.callback_query(F.data.startswith(("ok:", "no:")))
async def decide(query: CallbackQuery) -> None:
    action, token = query.data.split(":", 1)
    tg = query.from_user
    ask_phone = False

    async with SessionLocal() as session:
        login = await session.get(TelegramLogin, token, with_for_update=True)
        if login is None or login.status != "pending" or login.expires_at < datetime.now(UTC):
            await query.answer("Bu so'rov eskirgan yoki allaqachon ko'rib chiqilgan.", show_alert=True)
            await query.message.edit_reply_markup(reply_markup=None)
            return

        if action == "no":
            login.status = "rejected"
            await session.commit()
            await query.message.edit_text("❌ Kirish bekor qilindi.")
            await query.answer()
            return

        user = await _find_user(session, tg.id)
        is_new = user is None
        if is_new:
            user = User(full_name=tg.full_name, telegram_id=tg.id)
            session.add(user)
        user.telegram_username = tg.username
        user.language_code = tg.language_code
        user.last_login_at = datetime.now(UTC)
        await session.flush()

        login.status = "confirmed"
        login.user_id = user.id
        ask_phone = user.phone is None
        await session.commit()

    done = "Ro'yxatdan o'tish" if is_new else "Kirish"
    await query.message.edit_text(f"✅ {done} tasdiqlandi!\n\nSaytga qayting — sahifa avtomatik yangilanadi.")
    await query.answer("Tasdiqlandi!")

    if ask_phone:
        await query.message.answer(
            "📱 Profilingizni to'ldirish uchun telefon raqamingizni yuboring (ixtiyoriy):",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )


@dp.message(F.contact)
async def save_phone(message: Message) -> None:
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("Iltimos, o'zingizning raqamingizni yuboring.")
        return
    phone = contact.phone_number if contact.phone_number.startswith("+") else f"+{contact.phone_number}"
    async with SessionLocal() as session:
        user = await _find_user(session, message.from_user.id)
        if user is None:
            await message.answer("Avval saytda ro'yxatdan o'ting.", reply_markup=ReplyKeyboardRemove())
            return
        user.phone = phone
        await session.commit()
    await message.answer("✅ Rahmat! Telefon raqamingiz saqlandi.", reply_markup=ReplyKeyboardRemove())


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    token = get_settings().telegram_bot_token
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    bot = Bot(token, default=DefaultBotProperties(parse_mode="HTML"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
