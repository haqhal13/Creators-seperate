import logging
import requests
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("multi-bots")

# ---------------- FastAPI ----------------
app = FastAPI()
START_TIME = datetime.now()

# ---------------- Config ----------------
BASE_URL = "https://creators-seperate.onrender.com"  # your Render domain

# ---------------- Universal text (edit once, used by all bots) ----------------
SHARED_TEXT = {
    "paypal": (
        "💸 **PayPal**\n\n"
        "**Price:** {price}\n"
        "`{paypal_tag}`\n\n"
        "⚠️ Use **Friends & Family** only.\n"
        "After paying, tap **I’ve paid** below."
    ),
    "crypto": (
        "₿ **Crypto Payments**\n\n"
        "**Price:** {price}\n"
        "Join: {crypto_room}\n\n"
        "Follow the instructions inside.\n"
        "After paying, tap **I’ve paid** below."
    ),
    "paid_thanks": (
        "✅ **Thanks for your {method} payment!**\n\n"
        "• If you paid with **PayPal or Crypto**, message {support} with your receipt and the bot name (**{brand_title}**) so we can verify you.\n"
        "• If you paid with **Apple Pay / Google Pay / Card**, your access link is **emailed instantly** — check the email on your order (and spam)."
    ),
}

# Each dict key is the webhook path: /webhook/<brand>
BOTS = {
    "b1g_butlx": {
        "TITLE": "💎 **B1G BURLZ VIP**",
        "DESCRIPTION": (
            "🎥 One-time payment for **all her tapes & pics!** 🔥\n"
            "📈 Updated frequently when new tapes drop.\n\n"
            "⚡ *Instant access to the VIP link sent directly to your email!*\n"
            "📌 Questions? Link not working? Contact support 🔍👀"
        ),
        "TOKEN": "8219976154:AAEHiQ92eZM0T62auqP45X-yscJsUpQUsq8",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£15", "crypto": "£15"},  # <— set per-bot
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101524603254:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "monica_minx": {
        "TITLE": "💎 **Monica Minx VIP**",
        "DESCRIPTION": (
            "🎥 One-time payment for **all tapes & pics!** 👑\n"
            "📈 Regularly updated with new drops.\n\n"
            "⚡ *Instant access to the VIP link sent directly to your email!*\n"
            "📌 Questions? Link not working? Contact support 🔍👀"
        ),
        "TOKEN": "8490676478:AAH49OOhbEltLHVRN2Ic1Eyg-JDSPAIuj-k",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£15", "crypto": "£15"},
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101529452918:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "mexicuban": {
        "TITLE": "💎 **Mexicuban VIP**",
        "DESCRIPTION": (
            "🎥 One-time payment for **all her tapes + collabs (FanBus etc)** 🔥\n"
            "📈 Always updated when new content drops.\n\n"
            "⚡ *Instant access to the VIP link sent directly to your email!*\n"
            "📌 Questions? Link not working? Contact support 🔍👀"
        ),
        "TOKEN": "8406486106:AAHZHqPW-AyBIuFD9iDQzzbyiGXTZB7hrrw",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£18", "crypto": "£18"},
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101534138742:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "zaystheway_vip": {
        "TITLE": "💎 **ZTW VIP**",
        "DESCRIPTION": (
            "💎 **Welcome to ZTW VIP!**\n\n"
            "🔥 Access to **all up-to-date content** (OnlyFans, Patreon, Fansly).\n\n"
            "⚡ *Instant access to the VIP link sent directly to your email!*\n"
            "📌 Questions? Link not working? Contact support 🔍👀"
        ),
        "TOKEN": "PUT-ZAYSTHEWAY-TOKEN-HERE",  # add real token
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£10", "crypto": "£10"},
        "PAYMENT_INFO": {
            "shopify_1m": "https://yourshopify.com/cart/DDD:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "exclusivebyaj": {
        "TITLE": "💎 **ExclusiveByAj VIP**",
        "DESCRIPTION": (
            "💎 Exclusive drops curated by AJ.\n\n"
            "⚡ *Instant access to the VIP link sent directly to your email!*\n"
            "📌 Questions? Link not working? Contact support 🔍👀"
        ),
        "TOKEN": "8213329606:AAFRtJ3_6RkVrrNk_cWPTExOk8OadIUC314",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£13", "crypto": "£13"},
        "PAYMENT_INFO": {
            "shopify_1m": "https://nt9qev-td.myshopify.com/cart/56080557048182:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    "lil_bony1": {
        "TITLE": "💎 **LIL.BONY1 VIP**",
        "DESCRIPTION": (
            "🎥 Lifetime access to **all LilBony1’s tapes & pics** 👑\n"
            "📈 Updated frequently with brand new drops.\n\n"
            "⚡ *Instant access to the VIP link sent directly to your email!*\n"
            "📌 Questions? Link not working? Contact support 🔍👀"
        ),
        "TOKEN": "8269169417:AAGhMfMONQFy7bqdckeugMti4VDqPMcg0w8",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£12", "crypto": "£12"},
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101539152246:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
    # (Your HOB VIP CREATOR block from before can stay as-is; add PRICES there too if needed)
}

APPS: dict[str, Application] = {}

# ---------------- Handlers ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = context.bot_data["brand"]
    cfg = BOTS[brand]
    pay = cfg["PAYMENT_INFO"]

    keyboard: list[list[InlineKeyboardButton]] = []
    if "shopify_life" in pay:
        keyboard.append([InlineKeyboardButton("💳 Apple/Google Pay (ONE-TIME)", web_app=WebAppInfo(url=pay["shopify_life"]))])
    if "shopify_1m" in pay:
        keyboard.append([InlineKeyboardButton("💳 Apple/Google Pay (1 Month)", web_app=WebAppInfo(url=pay["shopify_1m"]))])

    # Crypto/PayPal (shared flows)
    keyboard.append([InlineKeyboardButton("💸 PayPal (read note)", callback_data=f"{brand}:paypal")])
    keyboard.append([InlineKeyboardButton("₿ Crypto (instructions)", callback_data=f"{brand}:crypto")])
    keyboard.append([InlineKeyboardButton("💬 Support", callback_data=f"{brand}:support")])

    await update.effective_message.reply_text(
        f"{cfg['TITLE']}\n\n{cfg['DESCRIPTION']}\n\n"
        "🧾 **Card orders** (Apple Pay / Google Pay / card) are **emailed instantly** — "
        "check the email used at checkout (and spam).",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data.split(":")
    brand, action = data[0], data[1]
    cfg = BOTS[brand]
    pay = cfg["PAYMENT_INFO"]
    prices = cfg.get("PRICES", {})
    support = cfg["SUPPORT_CONTACT"]
    brand_title = cfg["TITLE"].replace("*", "")  # plain for message

    if action == "paypal":
        text = SHARED_TEXT["paypal"].format(
            price=prices.get("paypal", "£—"),
            paypal_tag=pay["paypal"],
        )
        kb = [
            [InlineKeyboardButton("✅ I’ve paid (PayPal)", callback_data=f"{brand}:paid:paypal")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")],
        ]
        await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif action == "crypto":
        text = SHARED_TEXT["crypto"].format(
            price=prices.get("crypto", "£—"),
            crypto_room=pay["crypto"],
        )
        kb = [
            [InlineKeyboardButton("✅ I’ve paid (Crypto)", callback_data=f"{brand}:paid:crypto")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")],
        ]
        await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif action == "paid":
        method = data[2] if len(data) > 2 else "payment"
        nice = "PayPal" if method == "paypal" else ("Crypto" if method == "crypto" else "payment")
        text = SHARED_TEXT["paid_thanks"].format(method=nice, support=support, brand_title=brand_title)
        kb = [[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]
        await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif action == "support":
        kb = [[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]
        await q.edit_message_text(
            text=f"💬 Need help? Contact {support}",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )

    elif action == "back":
        # Return to the main menu for this brand
        await start(update, context)

    else:
        await start(update, context)

# ---------------- FastAPI Routes ----------------
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

# ---------------- Helper: set all webhooks ----------------
def set_all_webhooks():
    for brand, cfg in BOTS.items():
        token = cfg["TOKEN"]
        if not token or token.startswith("PUT-"):
            log.warning(f"[{brand}] Skipping webhook (no token).")
            continue
        webhook_url = f"{BASE_URL}/webhook/{brand}"
        api_url = f"https://api.telegram.org/bot{token}/setWebhook"
        try:
            r = requests.post(
                api_url,
                json={
                    "url": webhook_url,
                    "drop_pending_updates": True,
                    "allowed_updates": ["message", "callback_query"],
                },
                timeout=20,
            )
            ok = r.status_code == 200 and r.json().get("ok")
            if ok:
                log.info(f"[{brand}] Webhook set: {webhook_url}")
            else:
                log.error(f"[{brand}] Failed setting webhook: {r.text}")
        except Exception as e:
            log.error(f"[{brand}] Error setting webhook: {e}")

if __name__ == "__main__":
    log.info("Setting all webhooks to your Render domain...")
    set_all_webhooks()
    log.info("Done. Start server with: uvicorn multi_bots:app --host 0.0.0.0 --port $PORT")
