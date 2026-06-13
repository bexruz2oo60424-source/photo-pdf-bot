"""
Photo to PDF Bot
----------------
Foydalanuvchi rasm yuborganda, botni PDF formatga aylantirib qaytaradi.
Bir nechta rasm yuborilsa, ularni bitta PDF faylga birlashtirib beradi.

O'rnatish:
    pip install python-telegram-bot Pillow

Ishga tushirish:
    python photo_to_pdf_bot.py
"""

import io
import logging

from PIL import Image
from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# === SOZLAMALAR ===
TOKEN = "8876087394:AAH_c5ZAk_VDJggfVbPHyRe0XSVUYX1DOBg"

# Logging sozlamasi
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Har bir foydalanuvchi yuborgan rasmlarni vaqtincha shu yerda saqlaymiz
user_images: dict[int, list[Image.Image]] = {}


# === BUYRUQLAR ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Botni boshlash - salomlashuv xabari."""
    await update.message.reply_text(
        "👋 Salom! Men *Photo to PDF Bot*.\n\n"
        "📸 Menga bitta yoki bir nechta rasm yuboring.\n"
        "✅ Rasmlarni yuborib bo'lgach, /done buyrug'ini yuboring — "
        "men ularni bitta PDF faylga aylantirib beraman.\n\n"
        "Buyruqlar haqida: /help",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yordam xabari."""
    await update.message.reply_text(
        "📖 *Qanday foydalanish:*\n\n"
        "1️⃣ Menga bir yoki bir nechta rasm yuboring\n"
        "2️⃣ Barcha rasmlarni yuborib bo'lgach, /done deb yozing\n"
        "3️⃣ Men ularni tartib bo'yicha bitta PDF faylga aylantirib qaytaraman\n\n"
        "❌ Yuborgan rasmlarni bekor qilish uchun: /cancel\n"
        "ℹ️ Bot haqida: /about",
        parse_mode="Markdown",
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot haqida ma'lumot."""
    await update.message.reply_text(
        "🔧 Bu bot rasmlaringizni tezda PDF formatga aylantiradi.\n"
        "🔒 Fayllar serverda saqlanmaydi, faqat konvertatsiya uchun ishlatiladi."
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchining rasmlarini tozalash."""
    user_id = update.effective_user.id
    if user_images.pop(user_id, None) is not None:
        await update.message.reply_text("🗑 Yuborilgan rasmlar bekor qilindi.")
    else:
        await update.message.reply_text("📭 Bekor qilish uchun hech qanday rasm yo'q.")


# === RASM QABUL QILISH ===

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi yuborgan rasmni qabul qilish va saqlash."""
    user_id = update.effective_user.id

    # Eng yuqori sifatdagi rasmni olish (oxirgi element)
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    image = Image.open(io.BytesIO(bytes(photo_bytes)))

    # PDF uchun RGB rejimiga o'tkazish
    if image.mode != "RGB":
        image = image.convert("RGB")

    user_images.setdefault(user_id, []).append(image)
    count = len(user_images[user_id])

    await update.message.reply_text(
        f"✅ Rasm qabul qilindi. Jami: *{count}* ta.\n"
        f"Yana rasm yuboring yoki /done deb yozing.",
        parse_mode="Markdown",
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fayl sifatida yuborilgan rasmlarni ham qabul qilish."""
    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text(
            "⚠️ Faqat rasm fayllarni qabul qila olaman (jpg, png, webp va h.k.)."
        )
        return

    user_id = update.effective_user.id
    file = await doc.get_file()
    file_bytes = await file.download_as_bytearray()

    try:
        image = Image.open(io.BytesIO(bytes(file_bytes)))
        if image.mode != "RGB":
            image = image.convert("RGB")except Exception:
        await update.message.reply_text("❌ Faylni ochib bo'lmadi. Boshqa rasm yuboring.")
        return

    user_images.setdefault(user_id, []).append(image)
    count = len(user_images[user_id])

    await update.message.reply_text(
        f"✅ Rasm (fayl) qabul qilindi. Jami: *{count}* ta.\n"
        f"Yana rasm yuboring yoki /done deb yozing.",
        parse_mode="Markdown",
    )


# === PDF YASASH ===

async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saqlangan rasmlarni bitta PDF faylga birlashtirish."""
    user_id = update.effective_user.id
    images = user_images.get(user_id)

    if not images:
        await update.message.reply_text(
            "📭 Hali hech qanday rasm yubormadingiz. Avval rasm yuboring."
        )
        return

    await update.message.reply_text("⏳ PDF tayyorlanmoqda...")

    try:
        pdf_buffer = io.BytesIO()
        first, rest = images[0], images[1:]
        first.save(pdf_buffer, format="PDF", save_all=True, append_images=rest)
        pdf_buffer.seek(0)

        await update.message.reply_document(
            document=pdf_buffer,
            filename="natija.pdf",
            caption=f"📄 Tayyor! *{len(images)}* ta rasm bitta PDF faylga aylandi.",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error("PDF yaratishda xatolik: %s", e)
        await update.message.reply_text(
            "❌ PDF yaratishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
        )
    finally:
        # Xato bo'lsa ham xotirani tozalash
        user_images.pop(user_id, None)


# === BOT BUYRUQLARI MENYUSI ===

async def post_init(application: Application) -> None:
    """Bot ishga tushganda buyruqlar menyusini o'rnatish."""
    commands = [
        BotCommand("start",  "Botni ishga tushirish"),
        BotCommand("help",   "Yordam olish"),
        BotCommand("about",  "Bot haqida ma'lumot"),
        BotCommand("done",   "Yuborilgan rasmlarni PDF qilish"),
        BotCommand("cancel", "Yuborilgan rasmlarni bekor qilish"),
    ]
    await application.bot.set_my_commands(commands)


# === ASOSIY FUNKSIYA ===

def main() -> None:
    """Botni ishga tushirish."""
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # Buyruq handlerlari
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("help",   help_command))
    app.add_handler(CommandHandler("about",  about_command))
    app.add_handler(CommandHandler("done",   done_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Xabar handlerlari
    app.add_handler(MessageHandler(filters.PHOTO,    handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    logger.info("Bot ishlamoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()