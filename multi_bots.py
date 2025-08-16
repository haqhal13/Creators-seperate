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

# ============== EDIT ME ==============
BOTS = {
    # Each key becomes your webhook path: /webhook/<brand>
    "exclusivebyaj": {
        "TITLE": "💎 **ExclusiveByAj**",
        "TOKEN": os.getenv("8213329606:AAFRtJ3_6RkVrrNk_cWPTExOk8OadIUC314", "8213329606:AAFRtJ3_6RkVrrNk_cWPTExOk8OadIUC314"),
        "SUPPORT_CONTACT": "@Sebvip",  # change if needed
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/AAA:1",     # 1 month
            "shopify_life": "https://yourshopify.com/cart/AAB:1",   # lifetime
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "b1g_butlx": {
        "TITLE": "💎 **B1G BUTLX**",
        "TOKEN": os.getenv("8219976154:AAEHiQ92eZM0T62auqP45X-yscJsUpQUsq8", "8219976154:AAEHiQ92eZM0T62auqP45X-yscJsUpQUsq8"),
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/BBB:1",
            "shopify_life": "https://yourshopify.com/cart/BBC:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "monica_minx": {
        "TITLE": "💎 **Monica Minx**",
        "TOKEN": os.getenv("8490676478:AAH49OOhbEltLHVRN2Ic1Eyg-JDSPAIuj-k", "8490676478:AAH49OOhbEltLHVRN2Ic1Eyg-JDSPAIuj-k"),
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/CCC:1",
            "shopify_life": "https://yourshopify.com/cart/CCD:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "zaystheway_vip": {
        "TITLE": "💎 **ZAYSTHEWAY VIP**",
        "TOKEN": os.getenv("ZAYSTHEWAY_BOT_TOKEN", "PUT-ZAYSTHEWAY-TOKEN-HERE"),
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/DDD:1",
            "shopify_life": "https://yourshopify.com/cart/DDE:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "mexicuban": {
        "TITLE": "💎 **MEXICUBAN**",
        "TOKEN": os.getenv("8406486106:AAHZHqPW-AyBIuFD9iDQzzbyiGXTZB7hrrw", "8406486106:AAHZHqPW-AyBIuFD9iDQzzbyiGXTZB7hrrw"),
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/EEE:1",
            "shopify_life": "https://yourshopify.com/cart/EEF:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "lil_bony1": {
        "TITLE": "💎 **LIL.BONY1**",
        "TOKEN": os.getenv("8269169417:AAGhMfMONQFy7bqdckeugMti4VDqPMcg0w8", "8269169417:AAGhMfMONQFy7bqdckeugMti4VDqPMcg0w8"),
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/FFF:1",
            "shopify_life": "https://yourshopify.com/cart/FFG:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
}
# ============ END EDIT ME ============

APPS: dict[str, Application] = {}

# ---------- Shared handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = context.bot_data["brand"]
    cfg = BOTS[brand]
    pay = cfg["PAYMENT_INFO"]

    keyboard = [
        [InlineKeyboardButton("Apple Pay / Google Pay (Lifetime)", web_app=WebAppInfo(url=pay["shopify_life"]))],
        [InlineKeyboardButton("Apple Pay / Google Pay (1 Month)", web_app=WebAppInfo(url=pay["shopify_1m"]))],
        [InlineKeyboardButton("PayPal (read note)", callback_data=f"{brand}:paypal")],
        [InlineKeyboardButton("Crypto (instructions)", callback_data=f"{brand}:crypto")],
        [InlineKeyboardButton("Support", callback_data=f"{brand}:support")],
    ]

    message = update.effective_message
    await message.reply_text(
        f"{cfg['TITLE']}\n\n"
        "⚡ Instant access (Shopify emails link instantly for Apple/Google Pay)\n"
        "📌 If anything fails, use Support below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    brand, action = q.data.split(":")
    cfg = BOTS[brand]
    pay = cfg["PAYMENT_INFO"]

    if action == "paypal":
        await q.edit_message_text(
            text=f"💸 **PayPal**\n\n`{pay['paypal']}`\n\nUse **Friends & Family** only.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]),
            parse_mode="Markdown",
        )
    elif action == "crypto":
        await q.edit_message_text(
            text=f"⚡ **Crypto**\n\n{pay['crypto']}\n\nFollow the instructions in the linked room.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]),
            parse_mode="Markdown",
        )
    elif action == "support":
        await q.edit_message_text(
            text=f"💬 Need help? Contact {cfg['SUPPORT_CONTACT']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]),
            parse_mode="Markdown",
        )
    elif action == "back":
        await start(update, context)
    else:
        await start(update, context)

# ---------- FastAPI ----------
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
        app_obj = Application.builder().token(token).updater(None).build()
        app_obj.add_handler(CommandHandler("start", start))
        app_obj.add_handler(CallbackQueryHandler(on_cb))
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
