import os
import logging
from datetime import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("multi-bots")

app = FastAPI()
START_TIME = datetime.now()

# ============== EDIT ME ==============
BASE_URL = "https://creators-seperate.onrender.com"  # your Render domain

BOTS = {
    "b1gburlz": {
        "TITLE": "💎 **B1gburlz VIP**",
        "DESCRIPTION": "🎥 One-time payment for **all her tapes & pics!** 🔥",
        "TOKEN": "8219976154:AAEHiQ92eZM0T62auqP45X-yscJsUpQUsq8",
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/AAA:1",
            "shopify_life": "https://yourshopify.com/cart/AAB:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "mexicuban": {
        "TITLE": "💎 **Mexicuban VIP**",
        "DESCRIPTION": "🎥 One-time payment for **all her tapes + collabs (FanBus etc)** 🔥",
        "TOKEN": "8406486106:AAHZHqPW-AyBIuFD9iDQzzbyiGXTZB7hrrw",
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/BBB:1",
            "shopify_life": "https://yourshopify.com/cart/BBC:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "monica": {
        "TITLE": "💎 **Monica Minx VIP**",
        "DESCRIPTION": "🎥 One-time payment for **all tapes & pics!** 👑",
        "TOKEN": "8490676478:AAH49OOhbEltLHVRN2Ic1Eyg-JDSPAIuj-k",
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/CCC:1",
            "shopify_life": "https://yourshopify.com/cart/CCD:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "exclusivebyaj": {
        "TITLE": "💎 **ExclusiveByAj VIP**",
        "DESCRIPTION": "💎 Exclusive drops curated by AJ.",
        "TOKEN": "8213329606:AAFRtJ3_6RkVrrNk_cWPTExOk8OadIUC314",
        "SUPPORT_CONTACT": "@Sebvip",
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/EEE:1",
            "shopify_life": "https://yourshopify.com/cart/EEF:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "lilbony1": {
        "TITLE": "💎 **LilBony1 VIP**",
        "DESCRIPTION": "🎥 Lifetime access to **all LilBony1’s tapes & pics** 👑",
        "TOKEN": "8269169417:AAGhMfMONQFy7bqdckeugMti4VDqPMcg0w8",
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
        [InlineKeyboardButton("💳 Apple/Google Pay (Lifetime)", web_app=WebAppInfo(url=pay["shopify_life"]))],
        [InlineKeyboardButton("💳 Apple/Google Pay (1 Month)", web_app=WebAppInfo(url=pay["shopify_1m"]))],
        [InlineKeyboardButton("💸 PayPal (read note)", callback_data=f"{brand}:paypal")],
        [InlineKeyboardButton("₿ Crypto (instructions)", callback_data=f"{brand}:crypto")],
        [InlineKeyboardButton("💬 Support", callback_data=f"{brand}:support")],
    ]

    await update.effective_message.reply_text(
        f"{cfg['TITLE']}\n\n{cfg['DESCRIPTION']}",
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
            text=f"💸 **PayPal**\n\n`{pay['paypal']}`\n\n⚠️ Use **Friends & Family only**.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]),
            parse_mode="Markdown",
        )
    elif action == "crypto":
        await q.edit_message_text(
            text=f"₿ **Crypto Payments**\n\nJoin: {pay['crypto']}\n\nFollow the instructions inside.",
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

# ---------- Helper to set all webhooks ----------
def set_all_webhooks():
    for brand, cfg in BOTS.items():
        token = cfg["TOKEN"]
        if not token or token.startswith("PUT-"):
            continue
        webhook_url = f"{BASE_URL}/webhook/{brand}"
        api_url = f"https://api.telegram.org/bot{token}/setWebhook"
        try:
            r = requests.post(api_url, json={"url": webhook_url})
            if r.status_code == 200 and r.json().get("ok"):
                log.info(f"[{brand}] Webhook set: {webhook_url}")
            else:
                log.error(f"[{brand}] Failed: {r.text}")
        except Exception as e:
            log.error(f"[{brand}] Exception: {e}")

if __name__ == "__main__":
    log.info("Setting all webhooks...")
    set_all_webhooks()
    log.info("Done. Now run with: uvicorn multi_bots:app --host 0.0.0.0 --port 10000")
