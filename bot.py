import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

PACKAGES = {
    "15": ("۱۵ گیگ", "۱۰۰ هزار تومان", "۳۰ روز"),
    "30": ("۳۰ گیگ", "۲۰۰ هزار تومان", "۶۰ روز"),
    "50": ("۵۰ گیگ", "۴۰۰ هزار تومان", "۹۰ روز"),
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("۱۵ گیگ | ۱۰۰ هزار تومان | ۳۰ روز", callback_data="pkg_15")],
        [InlineKeyboardButton("۳۰ گیگ | ۲۰۰ هزار تومان | ۶۰ روز", callback_data="pkg_30")],
        [InlineKeyboardButton("۵۰ گیگ | ۴۰۰ هزار تومان | ۹۰ روز", callback_data="pkg_50")],
    ]

    await update.message.reply_text(
        "سلام 🌹 به امید وی پی ان خوش آمدید.\n\n"
        "لطفاً بسته موردنظر خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("pkg_"):
        package_id = query.data.split("_")[1]
        name, price, days = PACKAGES[package_id]

        keyboard = [
            [InlineKeyboardButton("💳 پرداخت", callback_data=f"pay_{package_id}")],
            [InlineKeyboardButton("❌ لغو", callback_data="cancel")],
        ]

        await query.edit_message_text(
            f"📦 سفارش شما\n\n"
            f"حجم: {name}\n"
            f"💰 مبلغ: {price}\n"
            f"⏳ مدت: {days}\n\n"
            f"آیا سفارش را ثبت می‌کنید؟",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("pay_"):
        package_id = query.data.split("_")[1]
        name, price, days = PACKAGES[package_id]

        keyboard = [
            [InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"confirm_{package_id}")],
        ]

        await query.edit_message_text(
            f"💳 مرحله پرداخت\n\n"
            f"بسته: {name}\n"
            f"مبلغ: {price}\n"
            f"مدت: {days}\n\n"
            f"لطفاً پرداخت را انجام دهید و سپس روی «تأیید پرداخت» بزنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("confirm_"):
        package_id = query.data.split("_")[1]
        name, price, days = PACKAGES[package_id]

        user = query.from_user
        user_name = user.first_name or "بدون نام"

        await query.edit_message_text(
            f"✅ سفارش شما ثبت شد.\n\n"
            f"{name}\n"
            f"💰 {price}\n"
            f"⏳ {days}\n\n"
            f"🆔 شناسه کاربر: {user.id}\n\n"
            f"رسید پرداخت شما برای بررسی ارسال شد."
        )

        # پیام برای ادمین
        ADMIN_ID = os.getenv("ADMIN_ID")

        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    chat_id=int(ADMIN_ID),
                    text=(
                        "🔔 پرداخت جدید\n\n"
                        f"👤 کاربر: {user_name}\n"
                        f"🆔 ID: {user.id}\n"
                        f"📦 بسته: {name}\n"
                        f"💰 مبلغ: {price}\n"
                        f"⏳ مدت: {days}\n\n"
                        "⏳ در انتظار بررسی پرداخت"
                    ),
                )
            except Exception:
                pass

    elif query.data == "cancel":
        await query.edit_message_text("❌ سفارش لغو شد.")


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()


if __name__ == "__main__":
    main()
