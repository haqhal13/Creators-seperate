"""
MULTI-BOT FASTAPI APP (6 BOTS, 1 SERVICE)
-----------------------------------------
✅ Stable webhook mode (cheap + fast).
✅ One Render service hosts all bots.
✅ Easy config: just edit the BOTS dictionary below.

SETUP STEPS:
1. Create 6 bots in BotFather -> get 6 tokens.
2. Add tokens to Render ENV VARS (recommended) OR temporarily paste them in the placeholders.
3. Edit each bot’s COPY_TITLE, COPY_BODY, and PAYMENT links.
4. Deploy to Render.
5. Run set_webhooks.py once to point Telegram to your Render URLs.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("multi-bots")

app = FastAPI()
START_TIME = datetime.now()

# ==========================================================
#  CONFIG: Define your 6 bots here
# ==========================================================
BOTS = {
    "creator1": {
        "TOKEN": os.getenv("CREATOR1_BOT_TOKEN", "PUT-CREATOR1-TOKEN-HERE"),
        "SUPPORT": "@YourSupportHandle",
        "COPY_TITLE": "💎 Creator 1 VIP",
        "COPY_BODY": (
            "⚡ Exclusive Creator 1 VIP content.\n\n"
            "📩 Apple/Google Pay receipts delivered instantly by email."
        ),
        "PAYMENT": {
            "apple_google": "https://yourshopify.com/cart/111:1",  # <-- EDIT
            "paypal": "PayPal link coming soon",
            "crypto": "Crypto link coming soon",
        },
    },
    "creator2": {
        "TOKEN": os.getenv("CREATOR2_BOT_TOKEN", "PUT-CREATOR2-TOKEN-HERE"),
        "SUPPORT": "@YourSupportHandle",
        "COPY_TITLE": "🔥 Creator 2 VIP",
        "COPY_BODY": "Exclusive Creator 2 media access.",
        "PAYMENT": {
            "apple_google": "https://yourshopify.com/cart/222:1",
            "paypal": "PayPal link coming soon",
            "crypto": "Crypto link coming soon",
        },
    },
    "creator3": {
        "TOKEN": os.getenv("CREATOR3_BOT_TOKEN", "PUT-CREATOR3-TOKEN-HERE"),
        "SUPPORT": "@YourSupportHandle",
        "COPY_TITLE": "💎 Creator 3 VIP",
        "COPY_BODY": "Exclusive Creator 3 media access.",
        "PAYMENT": {
            "apple_google": "https://yourshopify.com/cart/333:1",
            "paypal": "PayPal link coming soon",
            "crypto": "Crypto link coming soon",
        },
    },
    "creator4": {
        "TOKEN": os.getenv("CREATOR4_BOT_TOKEN", "PUT-CREATOR4-TOKEN-HERE"),
        "SUPPORT": "@YourSupportHandle",
        "COPY_TITLE": "💎 Creator 4 VIP",
        "COPY_BODY": "Exclusive Creator 4 media access.",
        "PAYMENT": {
            "apple_google": "https://yourshopify.com/cart/444:1",
            "paypal": "PayPal link coming soon",
            "crypto": "Crypto link coming soon",
        },
    },
    "creator5": {
        "TOKEN": os.getenv("CREATOR5_BOT_TOKEN", "PUT-CREATOR5-TOKEN-HERE"),
        "SUPPORT": "@YourSupportHandle",
        "COPY_TITLE": "💎 Creator 5 VIP",
        "COPY_BODY": "Exclusive Creator 5 media access.",
        "PAYMENT": {
            "apple_google": "https://yourshopify.com/cart/555:1",
            "paypal": "PayPal link coming soon",
            "crypto": "Crypto link coming soon",
        },
    },
    "creator6": {
        "TOKEN": os.getenv("CREATOR6_BOT_TOKEN", "PUT-CREATOR6-TOKEN-HERE"),
        "SUPPORT": "@YourSupportHandle",
        "COPY_TITLE": "💎 Creator 6 VIP",
        "COPY_BODY": "Exclusive Creator 6 media access.",
        "PAYMENT": {
            "apple_google": "https://yourshopify.com/cart/666:1",
            "paypal": "PayPal link coming soon",
            "crypto": "Crypto link coming soon",
        },
    },
}

# Store Telegram Applications
APPS: dict[str, Application] = {}

# ==========================================================
#  HANDLERS
# ==========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Universal /start handler."""
    brand = context.bot_data["brand"]
    cfg = BOTS[brand]

    kb = [
        [InlineKeyboardButton("Apple Pay & Google Pay", web_app=WebAppInfo(url=cfg["PAYMENT"]["apple_google"]))],
        [InlineKeyboardButton("PayPal Payment", callback_data=f"{brand}:paypal")],
        [InlineKeyboardButton("Crypto Payment", callback_data=f"{brand}:crypto")],
        [InlineKeyboardButton("Support", callback_data=f"{brand}:support")],
    ]

    message = update.effective_message
    await message.reply_text(
        f"{cfg['COPY_TITLE']}\n\n{cfg['COPY_BODY']}",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

async def handle_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles PayPal, Crypto, Support, Back, ThankYou buttons."""
    q = update.callback_query
    await q.answer()
    brand, action = q.data.split(":")
    cfg = BOTS[brand]

    if action == "paypal":
        await q.edit_message_text(
            f"💸 **Pay with PayPal!**\n\n`{cfg['PAYMENT']['paypal']}`\n\n✅ After payment, tap Thank You.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Thank You", callback_data=f"{brand}:thankyou")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")],
            ]),
            parse_mode="Markdown",
        )
    elif action == "crypto":
        await q.edit_message_text(
            f"⚡ **Crypto Payment**\n\n{cfg['PAYMENT']['crypto']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Thank You", callback_data=f"{brand}:thankyou")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")],
            ]),
            parse_mode="Markdown",
        )
    elif action == "thankyou":
        await q.edit_message_text("✅ **Thanks for your payment!**\n\nPlease show proof to support.")
    elif action == "support":
        await q.edit_message_text(f"💬 Need help? Contact {cfg['SUPPORT']}")
    elif action == "back":
        await start(update, context)

# ==========================================================
#  FASTAPI ROUTES
# ==========================================================
@app.get("/")
async def root():
    return JSONResponse({"status": "ok", "bots": list(BOTS.keys())})

@app.get("/uptime")
async def uptime():
    return JSONResponse({"status": "online", "uptime": str(datetime.now() - START_TIME)})

@app.on_event("startup")
async def on_startup():
    for brand, cfg in BOTS.items():
        token = cfg["TOKEN"]
        if not token or token.startswith("PUT-"):
            log.warning(f"[{brand}] No token set, skipping.")
            continue
        app_obj = Application.builder().token(token).build()
        app_obj.add_handler(CommandHandler("start", start))
        app_obj.add_handler(CallbackQueryHandler(handle_actions))
        app_obj.bot_data["brand"] = brand
        await app_obj.initialize()
        APPS[brand] = app_obj
        log.info(f"[{brand}] Bot initialized.")

@app.post("/webhook/{brand}")
async def webhook(brand: str, request: Request):
    app_obj = APPS.get(brand)
    if not app_obj:
        return JSONResponse({"error": "unknown brand"}, status_code=404)
    update = Update.de_json(await request.json(), app_obj.bot)
    await app_obj.process_update(update)
    return JSONResponse({"ok": True})

@app.head("/uptime")
async def uptime_head():
    return Response(status_code=200)
