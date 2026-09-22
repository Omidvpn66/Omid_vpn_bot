import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

CARD_NUMBER = "6104 3378 8405 1481"

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
            [InlineKeyboardButton("✅ پرداخت کردم", callback_data=f"paid_{package_id}")],
            [InlineKeyboardButton("❌ لغو", callback_data="cancel")],
        ]

        await query.edit_message_text(
            f"💳 اطلاعات پرداخت\n\n"
            f"بسته: {name}\n"
            f"💰 مبلغ: {price}\n\n"
            f"💳 شماره کارت:\n"
            f"`{CARD_NUMBER}`\n\n"
            f"لطفاً مبلغ را به شماره کارت بالا واریز کنید.\n"
            f"سپس روی «پرداخت کردم» بزنید.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("paid_"):
        package_id = query.data.split("_")[1]
        name, price, days = PACKAGES[package_id]

        context.user_data["waiting_receipt"] = package_id

        await query.edit_message_text(
            f"✅ درخواست شما ثبت شد.\n\n"
            f"📦 بسته: {name}\n"
            f"💰 مبلغ: {price}\n"
            f"⏳ مدت: {days}\n\n"
            f"📸 لطفاً عکس رسید پرداخت را همینجا ارسال کنید.\n\n"
            f"بعد از بررسی، پرداخت شما تأیید می‌شود."
        )

    elif query.data == "cancel":
        await query.edit_message_text("❌ سفارش لغو شد.")


async def receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_receipt"):
        return

    if not update.message.photo:
        await update.message.reply_text(
            "📸 لطفاً رسید پرداخت را به صورت عکس ارسال کنید."
        )
        return

    package_id = context.user_data["waiting_receipt"]
    name, price, days = PACKAGES[package_id]

    user = update.effective_user
    user_name = user.first_name or "بدون نام"

    if not ADMIN_ID:
        await update.message.reply_text(
            "⚠️ شناسه ادمین تنظیم نشده است."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ تأیید پرداخت",
                callback_data=f"approve_{user.id}_{package_id}",
            ),
            InlineKeyboardButton(
                "❌ رد پرداخت",
                callback_data=f"reject_{user.id}_{package_id}",
            ),
        ]
    ]

    try:
        photo_id = update.message.photo[-1].file_id

        await context.bot.send_photo(
            chat_id=int(ADMIN_ID),
            photo=photo_id,
            caption=(
                "🔔 رسید پرداخت جدید\n\n"
                f"👤 کاربر: {user_name}\n"
                f"🆔 ID: {user.id}\n"
                f"📦 بسته: {name}\n"
                f"💰 مبلغ: {price}\n"
                f"⏳ مدت: {days}\n\n"
                "لطفاً رسید را بررسی کنید."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        await update.message.reply_text(
            "✅ رسید شما دریافت شد.\n\n"
            "رسید برای ادمین ارسال شد و پس از بررسی نتیجه به شما اعلام می‌شود."
        )

        context.user_data["waiting_receipt"] = None

    except Exception:
        await update.message.reply_text(
            "❌ ارسال رسید با مشکل مواجه شد. لطفاً دوباره تلاش کنید."
        )


async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("approve_"):
        _, user_id, package_id = data.split("_")
        name, price, days = PACKAGES[package_id]

        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=(
                    "✅ پرداخت شما تأیید شد.\n\n"
                    f"📦 بسته: {name}\n"
                    f"💰 مبلغ: {price}\n"
                    f"⏳ مدت: {days}\n\n"
                    "سفارش شما تأیید شد."
                ),
            )

            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ پرداخت تأیید شد."
            )

        except Exception:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n⚠️ پرداخت تأیید شد، اما ارسال پیام به کاربر ناموفق بود."
            )

    elif data.startswith("reject_"):
        _, user_id, package_id = data.split("_")

        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=(
                    "❌ پرداخت شما تأیید نشد.\n\n"
                    "لطفاً رسید یا مبلغ پرداختی را بررسی کنید و در صورت نیاز دوباره ارسال کنید."
                ),
            )

            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ پرداخت رد شد."
            )

        except Exception:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ پرداخت رد شد."
            )


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(
            admin_action,
            pattern=r"^(approve_|reject_)"
        )
    )

    app.add_handler(CallbackQueryHandler(button))

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            receipt
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
