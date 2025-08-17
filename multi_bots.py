# multi_bots.py
import logging
import re
import requests
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import httpx  # optional uptime ping

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("multi-bots")

# ---------------- FastAPI ----------------
app = FastAPI()
START_TIME = datetime.now()

# ---------------- Config ----------------
BASE_URL = "https://creators-seperate.onrender.com"  # your Render domain
ADMIN_CHAT_ID = 7914196017  # Admin pings go here for ALL brands
PAID_DEBOUNCE_SECONDS = 60   # Anti-spam for "I've paid"

# Savings + freshness display
BUNDLE_SAVING_TEXT = "💡 Save £45+ vs buying separately (best value)."
LAST_UPDATED_FMT = "%d %b %Y"  # e.g., 17 Aug 2025

DISCLAIMER = (
    "💳 **Billing note:** Your statement shows an **education company** (nothing weird). "
    "Want something custom on your bill? DM support and we can personalize it."
)

# ---------------- Universal text (edit once) ----------------
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
        "{crypto_link}\n\n"
        "Follow the instructions inside.\n"
        "After paying, tap **I’ve paid** below."
    ),
    "paid_thanks_pp_crypto": (
        "✅ **Thanks for your {method} payment!**\n\n"
        "• If you paid with **PayPal or Crypto**, message {support} with your receipt and the bot name (**{brand_title}**) so we can verify you.\n"
        "• If you paid with **Apple Pay / Google Pay / Card**, your access link is **emailed instantly** — check the email on your order (and spam)."
    ),
    "paid_card": (
        "✅ **Thanks!**\n\n"
        "Card orders (Apple Pay / Google Pay / card) are **emailed instantly** to the email used at checkout.\n"
        "👉 Please check your inbox and spam for **{brand_title}**.\n\n"
        "If you don’t see it in 10 minutes, message {support} with your **Order #** or **checkout email**."
    ),
    "card_info_inline": (
        "🧾 **Card orders** (Apple Pay / Google Pay / card) are **emailed instantly** — "
        "check the email used at checkout (and spam)."
    ),
    "support_panel": (
        "💬 **Need Assistance? We're Here to Help!**\n\n"
        "🕒 **Working Hours:** 8:00 AM - 12:00 AM BST\n"
        "📨 For support, contact us directly at:\n"
        "👉 {support}\n\n"
        "Please include your **Order #** or your **screenshot/transaction ID** (for PayPal/Crypto) so we can help fast."
    ),
    "faq": (
    "❓ **Frequently Asked Questions (FAQ)**\n\n"

    "• **How do I get my link?**\n"
    "  • **Card / Apple Pay / Google Pay** → Link is emailed **instantly** to your checkout email.\n"
    "  • **PayPal / Crypto** → Links are sent **manually** after you show proof of payment.\n\n"

    "• **I don’t see the email.**\n"
    "  • Check your **spam/junk folder**.\n"
    "  • Make sure you entered the **correct email at checkout**.\n"
    "  • Still nothing after 10 minutes? Contact {support}.\n\n"

    "• **What proof do you need for PayPal/Crypto?**\n"
    "  Send either:\n"
    "  • A **screenshot** of the transaction, or\n"
    "  • The **transaction ID/hash**\n"
    "  ➝ Always include which **bot** you purchased so we know what to send you.\n\n"

    "• **Can I upgrade to the all-in-one bundle?**\n"
    "  ✅ Yes — tap **⬆️ Upgrade: HOB VIP CREATOR BUNDLE** below.\n"
    "  👉 It’s our **most popular deal** and you {saving} compared to buying groups one by one.\n\n"

    "• **What shows on my bank/PayPal statement?**\n"
    "  💳 Payments are billed under an **education company** (nothing weird).\n"
    "  Want a custom label? DM {support} before paying and we’ll personalize it.\n\n"

    "• **Do payments renew automatically?**\n"
    "  • If you picked **monthly/3-month/6-month plans** → they renew automatically unless you cancel.\n"
    "  • One-time/lifetime payments are **permanent** (no renewal).\n\n"

    "• **Can I cancel my subscription?**\n"
    "  Yes — you can cancel anytime from your payment provider (Shopify, PayPal, or Crypto wallet). \n"
    "  Access stays until the end of your billing period.\n\n"

    "• **I pressed 'I’ve Paid' but nothing happened.**\n"
    "  That button just logs your request — you still need to message {support} with proof if you paid via PayPal or Crypto.\n\n"

    "• **How long until I get access after PayPal/Crypto?**\n"
    "  Usually within **5–15 minutes** if proof is sent, but it can take longer if outside UK hours. Be patient — you’ll always get what you paid for.\n\n"

    "• **Why should I choose the bundle?**\n"
    "  • It’s the **cheapest way** to access everything.\n"
    "  • **Most popular choice** (majority of members buy the bundle).\n"
    "  • You {saving} instantly vs buying groups separately.\n\n"

    "• **What if I need help?**\n"
    "  Contact {support} any time — we’re here to sort out payments, links, or upgrades fast."
),

# Helper snippet shown on the START screen for specific lifetime bots
def lifetime_desc_lines(display_name: str) -> str:
    return (
        f"🎥 Lifetime access to **all {display_name}’s tapes & pics** 👑\n"
        "📈 Updated frequently with brand new drops **whenever they post tapes**\n\n"
        "🔒 Worried about what will show up on your card? → **Check the FAQ**"
    )

# ---------------- Bots config (EDIT THIS SECTION) ----------------
BOTS = {
    "b1g_butlx": {
        "TITLE": "💎 **B1G BURLZ VIP**",
        "DESCRIPTION": lifetime_desc_lines("B1G BURLZ") + f"\n\n{DISCLAIMER}",
        "TOKEN": "8219976154:AAEHiQ92eZM0T62auqP45X-yscJsUpQUsq8",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£6", "crypto": "£6"},
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101524603254:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
        "PLANS": {
            "lifetime": {"label": "Lifetime (£6)", "display": "LIFETIME", "price_gbp": "£6.00"},
        },
    },
    "monica_minx": {
        "TITLE": "💎 **Monica Minx VIP**",
        "DESCRIPTION": lifetime_desc_lines("Monica Minx") + f"\n\n{DISCLAIMER}",
        "TOKEN": "8490676478:AAH49OOhbEltLHVRN2Ic1Eyg-JDSPAIuj-k",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£6", "crypto": "£6"},
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101529452918:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
        "PLANS": {
            "lifetime": {"label": "Lifetime (£6)", "display": "LIFETIME", "price_gbp": "£6.00"},
        },
    },
    "mexicuban": {
        "TITLE": "💎 **Mexicuban VIP**",
        "DESCRIPTION": lifetime_desc_lines("Mexicuban") + f"\n\n{DISCLAIMER}",
        "TOKEN": "8406486106:AAHZHqPW-AyBIuFD9iDQzzbyiGXTZB7hrrw",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£15", "crypto": "£15"},
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101534138742:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
        "PLANS": {
            "lifetime": {"label": "Lifetime (£15)", "display": "LIFETIME", "price_gbp": "£15.00"},
        },
    },

    # ZTW — 1/3/6 month plans (with savings vs retail)
    "zaystheway_vip": {
        "TITLE": "💎 **ZTW VIP**",
        "DESCRIPTION": (
            "💎 *All up to date content - OF, Patreon, Fansly - from ZTW!*\n"
            "⚡ Instant access sent to your email after checkout.\n\n"
            f"{DISCLAIMER}"
        ),
        "TOKEN": "7718373318:-qdrQru770jXaX58HM",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£15", "crypto": "£15"},
        "PLANS": {
            "1_month": {"label": "1 Month (£15)", "display": "1 MONTH", "price_gbp": "£15.00"},
            "3_month": {"label": "3 Months (£31) 🔥 Most Popular", "display": "3 MONTHS", "price_gbp": "£31.00", "popular": True},
            "6_month": {"label": "6 Months (£58.50)", "display": "6 MONTHS", "price_gbp": "£58.50"},
        },
        "RETAIL_USD": {"1_month": 40.0, "3_month": 84.0, "6_month": 156.0},
        "PAYMENT_INFO": {
            "shopify_1m": "https://nt9qev-td.myshopify.com/cart/REPLACE_ZTW_1M:1",
            "shopify_3m": "https://nt9qev-td.myshopify.com/cart/REPLACE_ZTW_3M:1",
            "shopify_6m": "https://nt9qev-td.myshopify.com/cart/REPLACE_ZTW_6M:1",
            "crypto": "https://t.me/+318ocdUDrbA4ODk0",
            "paypal": "@Aieducation ON PAYPAL F&F only we cant process order if it isnt F&F",
        },
    },

    "exclusivebyaj": {
        "TITLE": "💎 **ExclusiveByAj VIP**",
        "DESCRIPTION": (
            "💎 Exclusive drops curated by AJ — **Early Access**.\n"
            "⚡ Instant link emailed after checkout.\n\n"
            f"{DISCLAIMER}"
        ),
        "TOKEN": "8213329606:AAFRtJ3_6RkVrrNk_cWPTExOk8OadIUC314",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£8", "crypto": "£8"},
        "PAYMENT_INFO": {
            "shopify_1m": "https://nt9qev-td.myshopify.com/cart/56080557048182:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
        "PLANS": {
            "1_month": {"label": "Early Access – 1 Month (£8)", "display": "1 MONTH", "price_gbp": "£8.00"},
        },
    },
    "lil_bony1": {
        "TITLE": "💎 **LIL.BONY1 VIP**",
        "DESCRIPTION": lifetime_desc_lines("LilBony1") + f"\n\n{DISCLAIMER}",
        "TOKEN": "8269169417:AAGhMfMONQFy7bqdckeugMti4VDqPMcg0w8",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£20", "crypto": "£20"},
        "PAYMENT_INFO": {
            "shopify_life": "https://nt9qev-td.myshopify.com/cart/56101539152246:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
        "PLANS": {
            "lifetime": {"label": "Lifetime (£20)", "display": "LIFETIME", "price_gbp": "£20.00"},
        },
    },

    # ---------------- HOB VIP CREATOR (BUNDLE 1/3/6) ----------------
    "hob_vip_creator": {
        "TITLE": "💎 **HOB VIP CREATOR BUNDLE**",
        "DESCRIPTION": (
            "🏛️ Central hub for **all single creator VIP groups**.\n"
            "✅ Includes: B1G BURLZ, Monica Minx, Mexicuban, LIL.BONY1, ExclusiveByAj, ZTW.\n"
            "💸 Buying separately would cost £80+ — bundle is the **best value**.\n\n"
            f"{DISCLAIMER}"
        ),
        "TOKEN": "8332913011:AAEz8LpOgG_FGEmP_7eqrLh23E7_MUNvuvE",
        "SUPPORT_CONTACT": "@Sebvip",
        "PRICES": {"paypal": "£25", "crypto": "£25"},  # fallback
        "PLANS": {
            "1_month": {"label": "1 Month (£15)", "display": "1 MONTH", "price_gbp": "£15.00"},
            "3_month": {"label": "3 Months (£31) 🔥 Most Popular", "display": "3 MONTHS", "price_gbp": "£31.00", "popular": True},
            "6_month": {"label": "6 Months (£58.50)", "display": "6 MONTHS", "price_gbp": "£58.50"},
        },
        "RETAIL_USD": {"1_month": 40.0, "3_month": 84.0, "6_month": 156.0},
        "PAYMENT_INFO": {
            "shopify_1m": "https://nt9qev-td.myshopify.com/cart/REPLACE_HOB_1M:1",
            "shopify_3m": "https://nt9qev-td.myshopify.com/cart/REPLACE_HOB_3M:1",
            "shopify_6m": "https://nt9qev-td.myshopify.com/cart/REPLACE_HOB_6M:1",
            "crypto": "https://t.me/+yourCryptoRoom",
            "paypal": "@YourPayPalTag (F&F only)",
        },
    },
}

APPS: dict[str, Application] = {}
STARTUP_RESULTS: dict[str, str] = {}  # brand -> "ok" or error message

# ---------------- Helpers ----------------
def parse_price_number(gbp_str: str) -> float:
    m = re.findall(r"[0-9]+(?:\.[0-9]+)?", (gbp_str or "").replace(",", ""))
    return float(m[0]) if m else 0.0

def pct_saving(our_price: float, retail_price: float) -> str:
    if retail_price and retail_price > 0:
        return f"Save {round((1 - our_price / retail_price) * 100)}%"
    return ""

def plan_label(cfg: dict, key: str, fallback: str) -> str:
    lbl = cfg.get("PLANS", {}).get(key, {}).get("label", fallback)
    price_gbp = cfg.get("PLANS", {}).get(key, {}).get("price_gbp")
    retail = cfg.get("RETAIL_USD", {}).get(key)
    suffix = ""
    if price_gbp and retail:
        our = parse_price_number(price_gbp)
        suffix = f" • {pct_saving(our, float(retail))} vs ${int(retail)}"
    return f"{lbl}{suffix}"

def get_plan_price_text(cfg: dict, plan_key: str | None, fallback_price: str) -> str:
    if not plan_key:
        return fallback_price
    plan = cfg.get("PLANS", {}).get(plan_key)
    if plan:
        return plan.get("price_gbp", fallback_price)
    return fallback_price

def has_any_plan(pay: dict) -> bool:
    return any(k in pay for k in ("shopify_1m", "shopify_3m", "shopify_6m", "shopify_life"))

def card_button_label(brand: str) -> str:
    if brand == "exclusivebyaj":
        return "💳 Early Access (Card) – Instant"
    return "💳 Apple/Google Pay – Instant Access"

def upsell_button_row() -> list[InlineKeyboardButton]:
    # Static Linktree upsell per your ask
    return [InlineKeyboardButton("🔥 Upgrade: HOB VIP CREATOR", url="https://linktr.ee/HOBCREATORS")]

async def admin_ping(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        log.warning(f"Admin ping failed: {e}")

def fmt_user(update_or_query) -> tuple[str, int]:
    u = update_or_query.from_user
    return (u.username or "NoUsername", u.id)

# ---------------- Generic handlers (all non-ZTW brands) ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    brand = context.bot_data["brand"]
    if brand == "zaystheway_vip":
        return await ztw_start(update, context)

    cfg = BOTS[brand]
    pay = cfg["PAYMENT_INFO"]
    keyboard: list[list[InlineKeyboardButton]] = []

    # --- START SCREEN: plan buttons if any exist ---
    if "PLANS" in cfg and has_any_plan(pay):
        if "shopify_1m" in pay and "1_month" in cfg["PLANS"]:
            keyboard.append([InlineKeyboardButton(plan_label(cfg, "1_month", "1 Month"), callback_data=f"{brand}:plan:1_month")])
        if "shopify_3m" in pay and "3_month" in cfg["PLANS"]:
            keyboard.append([InlineKeyboardButton(plan_label(cfg, "3_month", "3 Months"), callback_data=f"{brand}:plan:3_month")])
        if "shopify_6m" in pay and "6_month" in cfg["PLANS"]:
            keyboard.append([InlineKeyboardButton(plan_label(cfg, "6_month", "6 Months"), callback_data=f"{brand}:plan:6_month")])
        if "shopify_life" in pay and "lifetime" in cfg["PLANS"]:
            keyboard.append([InlineKeyboardButton(plan_label(cfg, "lifetime", "Lifetime"), callback_data=f"{brand}:plan:lifetime")])
    else:
        # No plan buttons available; show direct methods instead
        keyboard.append([InlineKeyboardButton("💸 PayPal (read note)", callback_data=f"{brand}:paypal")])
        keyboard.append([InlineKeyboardButton("₿ Crypto (instructions)", callback_data=f"{brand}:crypto")])

    # Global actions
    keyboard.append([InlineKeyboardButton("❓ FAQ", callback_data=f"{brand}:faq")])
    keyboard.append([InlineKeyboardButton("💬 Support", callback_data=f"{brand}:support")])

    # Upsell (everywhere)
    keyboard.append(upsell_button_row())

    last_updated = datetime.now().strftime(LAST_UPDATED_FMT)
    await update.effective_message.reply_text(
        f"{cfg['TITLE']}\n\n"
        f"{cfg['DESCRIPTION']}\n\n"
        f"📅 This Bot was Last Updated: *{last_updated}*\n"
        f"{SHARED_TEXT['card_info_inline']}\n"
        f"{BUNDLE_SAVING_TEXT}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    # ZTW uses its own callback formats (keep compatibility)
    if data.startswith(("select_", "payment_", "paid", "back", "support", "faq", "copy_")):
        return await ztw_router(q, context)

    parts = data.split(":")
    brand, action = parts[0], parts[1]
    cfg = BOTS[brand]
    pay = cfg["PAYMENT_INFO"]
    support = cfg["SUPPORT_CONTACT"]
    prices = cfg.get("PRICES", {})
    brand_title_plain = cfg["TITLE"].replace("*", "")
    username, user_id = fmt_user(q)

    # ---- PLAN PRESSED (2nd screen) ----
    if action == "plan":
        plan_key = parts[2] if len(parts) > 2 else None
        context.user_data["plan_key"] = plan_key
        plan_display = cfg.get("PLANS", {}).get(plan_key, {}).get("display") if cfg.get("PLANS") else (
            "1 MONTH" if plan_key == "1_month" else "LIFETIME"
        )
        context.user_data["plan_text"] = plan_display or "PLAN"

        # The detailed selection text you requested
        selection_text = (
            f"⭐️ You have chosen the **{context.user_data['plan_text']}** plan.\n\n"
            "💳 **Apple Pay/Google Pay:** 🚀 Instant VIP access (**link emailed immediately** — check spam!).\n"
            "⚡️ **Crypto:** (30 - 60 min wait time), VIP link sent **manually**.\n"
            "📧 **PayPal:** (30 - 60 min wait time), VIP link sent **manually**.\n\n"
            "🎉 Choose your preferred payment method below and get access today!"
        )

        kb = [
            [InlineKeyboardButton(card_button_label(brand), callback_data=f"{brand}:method:card")],
            [InlineKeyboardButton("⚡ Crypto ⏳ (30 - 60 min wait)", callback_data=f"{brand}:method:crypto")],
            [InlineKeyboardButton("📧 PayPal 💌 (30 - 60 min wait)", callback_data=f"{brand}:method:paypal")],
            [InlineKeyboardButton("🔙 Go Back", callback_data=f"{brand}:back")],
        ]
        kb.append(upsell_button_row())

        await admin_ping(context, (
            "✅ **Plan Selected**\n"
            f"🏷️ **Brand:** {brand_title_plain}\n"
            f"📋 **Plan:** {context.user_data['plan_text']}\n"
            f"👤 **User:** @{username} (`{user_id}`)\n"
            f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
        ))
        return await q.edit_message_text(selection_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    # ---- METHOD CHOSEN ----
    if action == "method":
        method = parts[2] if len(parts) > 2 else None
        context.user_data["method"] = method
        plan_key = context.user_data.get("plan_key")
        plan_text = context.user_data.get("plan_text", "PLAN")

        await admin_ping(context, (
            "🧭 **Entered Payment Method**\n"
            f"🏷️ **Brand:** {brand_title_plain}\n"
            f"📋 **Plan:** {plan_text}\n"
            f"💳 **Method:** {method}\n"
            f"👤 **User:** @{username} (`{user_id}`)\n"
            f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
        ))

        if method == "paypal":
            price = get_plan_price_text(cfg, plan_key, prices.get("paypal", "£—"))
            text = SHARED_TEXT["paypal"].format(price=price, paypal_tag=pay["paypal"])
            kb = [
                [InlineKeyboardButton("📋 Copy PayPal Tag", callback_data=f"{brand}:copy:paypal")],
                [InlineKeyboardButton("✅ I’ve paid (PayPal)", callback_data=f"{brand}:paid:paypal")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:plan:{plan_key}")],
            ]
            kb.append(upsell_button_row())
            return await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

        if method == "crypto":
            price = get_plan_price_text(cfg, plan_key, prices.get("crypto", "£—"))
            crypto_link = pay["crypto"]
            text = SHARED_TEXT["crypto"].format(price=price, crypto_link=crypto_link)
            kb = [
                [InlineKeyboardButton("📋 Copy Crypto Link", callback_data=f"{brand}:copy:crypto")],
                [InlineKeyboardButton("✅ I’ve paid (Crypto)", callback_data=f"{brand}:paid:crypto")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:plan:{plan_key}")],
            ]
            kb.append(upsell_button_row())
            return await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

        if method == "card":
            kb = []
            if plan_key == "1_month" and "shopify_1m" in pay:
                kb.append([InlineKeyboardButton(card_button_label(brand), web_app=WebAppInfo(url=pay["shopify_1m"]))])
            elif plan_key == "3_month" and "shopify_3m" in pay:
                kb.append([InlineKeyboardButton(card_button_label(brand), web_app=WebAppInfo(url=pay["shopify_3m"]))])
            elif plan_key == "6_month" and "shopify_6m" in pay:
                kb.append([InlineKeyboardButton(card_button_label(brand), web_app=WebAppInfo(url=pay["shopify_6m"]))])
            elif plan_key == "lifetime" and "shopify_life" in pay:
                kb.append([InlineKeyboardButton(card_button_label(brand), web_app=WebAppInfo(url=pay["shopify_life"]))])
            else:
                await q.answer("This plan isn’t available by card right now.", show_alert=True)

            kb.append([InlineKeyboardButton("✅ I’ve paid (Card)", callback_data=f"{brand}:paid:card")])
            kb.append([InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:plan:{plan_key}")])
            kb.append(upsell_button_row())
            return await q.edit_message_text(
                text="🚀 **Pay by card** — instant access emailed after checkout.\n\n" + SHARED_TEXT["card_info_inline"],
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown"
            )

    # ---- COPY BUTTONS ----
    if action == "copy":
        what = parts[2]
        if what == "paypal":
            tag = cfg["PAYMENT_INFO"]["paypal"]
            await q.answer("PayPal tag copied — also sent in chat.", show_alert=True)
            await q.message.reply_text(f"`{tag}`", parse_mode="Markdown")
            await admin_ping(context, (
                "📋 **Copy Pressed** (PayPal)\n"
                f"🏷️ **Brand:** {brand_title_plain}\n"
                f"👤 **User:** @{username} (`{user_id}`)\n"
                f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
            ))
        elif what == "crypto":
            link = cfg["PAYMENT_INFO"]["crypto"]
            await q.answer("Crypto link copied — also sent in chat.", show_alert=True)
            await q.message.reply_text(link)
            await admin_ping(context, (
                "📋 **Copy Pressed** (Crypto)\n"
                f"🏷️ **Brand:** {brand_title_plain}\n"
                f"👤 **User:** @{username} (`{user_id}`)\n"
                f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
            ))
        return

    # ---- DIRECT METHOD FLOW (fallback when no plan buttons exist) ----
    if action == "paypal":
        text = SHARED_TEXT["paypal"].format(price=prices.get("paypal", "£—"), paypal_tag=pay["paypal"])
        kb = [
            [InlineKeyboardButton("📋 Copy PayPal Tag", callback_data=f"{brand}:copy:paypal")],
            [InlineKeyboardButton("✅ I’ve paid (PayPal)", callback_data=f"{brand}:paid:paypal")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")],
        ]
        kb.append(upsell_button_row())
        await admin_ping(context, (
            "🧭 **Entered Payment Method**\n"
            f"🏷️ **Brand:** {brand_title_plain}\n"
            f"💳 **Method:** PayPal\n"
            f"👤 **User:** @{username} (`{user_id}`)\n"
            f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
        ))
        return await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    if action == "crypto":
        text = SHARED_TEXT["crypto"].format(price=prices.get("crypto", "£—"), crypto_link=pay["crypto"])
        kb = [
            [InlineKeyboardButton("📋 Copy Crypto Link", callback_data=f"{brand}:copy:crypto")],
            [InlineKeyboardButton("✅ I’ve paid (Crypto)", callback_data=f"{brand}:paid:crypto")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")],
        ]
        kb.append(upsell_button_row())
        await admin_ping(context, (
            "🧭 **Entered Payment Method**\n"
            f"🏷️ **Brand:** {brand_title_plain}\n"
            f"💳 **Method:** Crypto\n"
            f"👤 **User:** @{username} (`{user_id}`)\n"
            f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
        ))
        return await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    if action == "paid":
        # Debounce spam taps
        last_ts = context.user_data.get("last_paid_ts")
        now_ts = datetime.now().timestamp()
        if last_ts and now_ts - last_ts < PAID_DEBOUNCE_SECONDS:
            await q.answer("Already received — give us a minute 🙏", show_alert=False)
            return
        context.user_data["last_paid_ts"] = now_ts

        method = parts[2] if len(parts) > 2 else "payment"
        nice = "Card" if method == "card" else ("PayPal" if method == "paypal" else ("Crypto" if method == "crypto" else "payment"))
        plan_text = context.user_data.get("plan_text", "N/A")
        await admin_ping(context, (
            "📝 **Payment Notification**\n"
            f"🏷️ **Brand:** {brand_title_plain}\n"
            f"👤 **User:** @{username} (`{user_id}`)\n"
            f"📋 **Plan:** {plan_text}\n"
            f"💳 **Method:** {nice}\n"
            f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
        ))

        # User confirmation
        if method == "card":
            text = SHARED_TEXT["paid_card"].format(support=support, brand_title=brand_title_plain)
        else:
            text = SHARED_TEXT["paid_thanks_pp_crypto"].format(method=nice, support=support, brand_title=brand_title_plain)

        kb = [[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]
        kb.append(upsell_button_row())
        return await q.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    if action == "faq":
        kb = [[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]
        kb.append(upsell_button_row())
        return await q.edit_message_text(
            text=SHARED_TEXT["faq"].format(support=support, saving=BUNDLE_SAVING_TEXT),
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )

    if action == "support":
        kb = [[InlineKeyboardButton("🔙 Back", callback_data=f"{brand}:back")]]
        kb.append(upsell_button_row())
        return await q.edit_message_text(
            text=SHARED_TEXT["support_panel"].format(support=support),
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )

    if action == "back":
        return await start(update, context)

    # fallback
    return await start(update, context)

# ---------------- ZTW-specific handlers (now 1/3/6 month) ----------------
def ztw_make_plan_label(plan_key: str) -> str:
    cfg = BOTS["zaystheway_vip"]
    return plan_label(cfg, plan_key, cfg["PLANS"][plan_key]["label"])

async def ztw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = BOTS["zaystheway_vip"]
    keyboard = [
        [InlineKeyboardButton(ztw_make_plan_label("1_month"), callback_data="select_1_month")],
        [InlineKeyboardButton(ztw_make_plan_label("3_month"), callback_data="select_3_month")],
        [InlineKeyboardButton(ztw_make_plan_label("6_month"), callback_data="select_6_month")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("💬 Support", callback_data="support")],
    ]
    keyboard.append(upsell_button_row())

    last_updated = datetime.now().strftime(LAST_UPDATED_FMT)
    msg = update.effective_message
    await msg.reply_text(
        "💎 **Welcome to ZTW VIP Bot!**\n\n"
        "💎 *All up to date content - OF, Patreon, Fansly - from ZTW!*\n"
        "⚡ *Instant access to the VIP link sent directly to your email!*\n"
        f"📅 This Bot was Last Updated: *{last_updated}*\n"
        f"{BUNDLE_SAVING_TEXT}\n\n"
        f"{DISCLAIMER}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def ztw_handle_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, plan_key = query.data.split("_", 1)  # e.g., select_1_month
    context.user_data["plan_key"] = plan_key
    plan_text = BOTS["zaystheway_vip"]["PLANS"][plan_key]["display"]
    context.user_data["plan_text"] = plan_text

    username, user_id = fmt_user(query)
    await admin_ping(context, (
        "✅ **Plan Selected**\n"
        "🏷️ **Brand:** ZTW VIP\n"
        f"📋 **Plan:** {plan_text}\n"
        f"👤 **User:** @{username} (`{user_id}`)\n"
        f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
    ))

    # The detailed selection text you requested
    selection_text = (
        f"⭐️ You have chosen the **{plan_text}** plan.\n\n"
        "💳 **Apple Pay/Google Pay:** 🚀 Instant VIP access (**link emailed immediately** — check spam!).\n"
        "⚡️ **Crypto:** (30 - 60 min wait time), VIP link sent **manually**.\n"
        "📧 **PayPal:** (30 - 60 min wait time), VIP link sent **manually**.\n\n"
        "🎉 Choose your preferred payment method below and get access today!"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Apple Pay/Google Pay 🚀 (Instant Access)", callback_data=f"payment_shopify_{plan_key}")],
        [InlineKeyboardButton("⚡ Crypto ⏳ (30 - 60 min wait)", callback_data=f"payment_crypto_{plan_key}")],
        [InlineKeyboardButton("📧 PayPal 💌 (30 - 60 min wait)", callback_data=f"payment_paypal_{plan_key}")],
        [InlineKeyboardButton("🔙 Go Back", callback_data="back")],
    ]
    keyboard.append(upsell_button_row())

    await query.edit_message_text(
        text=selection_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def ztw_handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cfg = BOTS["zaystheway_vip"]
    info = cfg["PAYMENT_INFO"]

    _, method, plan_key = query.data.split("_", 2)  # payment_{method}_{plan_key}
    context.user_data["plan_key"] = plan_key
    context.user_data["plan_text"] = cfg["PLANS"][plan_key]["display"]
    context.user_data["method"] = method
    username, user_id = fmt_user(query)

    await admin_ping(context, (
        "🧭 **Entered Payment Method**\n"
        "🏷️ **Brand:** ZTW VIP\n"
        f"📋 **Plan:** {context.user_data['plan_text']}\n"
        f"💳 **Method:** {method}\n"
        f"👤 **User:** @{username} (`{user_id}`)\n"
        f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
    ))

    price = cfg["PLANS"][plan_key]["price_gbp"]
    if method == "shopify":
        url_key = "shopify_1m" if plan_key == "1_month" else ("shopify_3m" if plan_key == "3_month" else "shopify_6m")
        message = (
            "🚀 **Instant Access with Apple Pay/Google Pay!**\n\n"
            f"🎁 **Plan:** {context.user_data['plan_text']}: **{price}** 🌟\n\n"
            "🛒 Click below to pay securely and get **INSTANT VIP access** delivered to your email! 📧\n\n"
            "✅ After payment, click 'I've Paid' to confirm."
        )
        keyboard = [
            [InlineKeyboardButton(f"⏳ {context.user_data['plan_text']} ({price})", web_app=WebAppInfo(url=info[url_key]))],
            [InlineKeyboardButton("✅ I've Paid", callback_data="paid")],
            [InlineKeyboardButton("🔙 Go Back", callback_data="back")]
        ]
    elif method == "crypto":
        message = (
            "⚡ **Pay Securely with Crypto!**\n\n"
            f"{info['crypto']}\n\n"
            "💎 **Plan:**\n"
            f"⏳ {context.user_data['plan_text']}: **{price} GBP** 🌟\n\n"
            "✅ Once you've sent the payment, click 'I've Paid' to confirm."
        )
        keyboard = [
            [InlineKeyboardButton("📋 Copy Crypto Link", callback_data="copy_crypto")],
            [InlineKeyboardButton("✅ I've Paid", callback_data="paid")],
            [InlineKeyboardButton("🔙 Go Back", callback_data="back")]
        ]
    elif method == "paypal":
        message = (
            "💸 **Easy Payment with PayPal!**\n\n"
            f"`{info['paypal']}`\n\n"
            "💎 **Plan:**\n"
            f"⏳ {context.user_data['plan_text']}: **{price}** 🌟\n\n"
            "✅ Once payment is complete, click 'I've Paid' to confirm."
        )
        keyboard = [
            [InlineKeyboardButton("📋 Copy PayPal Tag", callback_data="copy_paypal")],
            [InlineKeyboardButton("✅ I've Paid", callback_data="paid")],
            [InlineKeyboardButton("🔙 Go Back", callback_data="back")]
        ]
    keyboard.append(upsell_button_row())

    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def ztw_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    last_ts = context.user_data.get("last_paid_ts")
    now_ts = datetime.now().timestamp()
    if last_ts and now_ts - last_ts < PAID_DEBOUNCE_SECONDS:
        await query.answer("Already received — give us a minute 🙏", show_alert=False)
        return
    context.user_data["last_paid_ts"] = now_ts

    plan_text = context.user_data.get("plan_text", "PLAN")
    method = context.user_data.get("method", "N/A")
    username, user_id = fmt_user(query)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    await admin_ping(context, (
        "📝 **Payment Notification**\n"
        f"🏷️ **Brand:** ZTW VIP\n"
        f"👤 **User:** @{username} (`{user_id}`)\n"
        f"📋 **Plan:** {plan_text}\n"
        f"💳 **Method:** {method.capitalize()}\n"
        f"🕒 **Time:** {current_time}"
    ))

    support = BOTS["zaystheway_vip"]["SUPPORT_CONTACT"]
    kb = [[InlineKeyboardButton("🔙 Go Back", callback_data="back")]]
    kb.append(upsell_button_row())
    await query.edit_message_text(
        text=(
            "✅ **Payment Received! Thank You!** 🎉\n\n"
            "📸 Please send a **screenshot** or **transaction ID** to our support team for verification.\n"
            f"👉 {support}\n\n"
            "⚡ **Important:**\n"
            "• If you paid via **Apple Pay/Google Pay**, check your email inbox for the VIP link.\n"
            "• If you paid via **PayPal or Crypto**, your VIP link will be sent manually."
        ),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def ztw_handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    support = BOTS["zaystheway_vip"]["SUPPORT_CONTACT"]
    kb = [[InlineKeyboardButton("🔙 Go Back", callback_data="back")]]
    kb.append(upsell_button_row())
    await query.edit_message_text(
        text=SHARED_TEXT["support_panel"].format(support=support),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def ztw_handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    support = BOTS["zaystheway_vip"]["SUPPORT_CONTACT"]
    kb = [[InlineKeyboardButton("🔙 Go Back", callback_data="back")]]
    kb.append(upsell_button_row())
    await query.edit_message_text(
        text=SHARED_TEXT["faq"].format(support=support, saving=BUNDLE_SAVING_TEXT),
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def ztw_handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await ztw_start(update, context)

async def ztw_copy_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cfg = BOTS["zaystheway_vip"]
    data = query.data
    username, user_id = fmt_user(query)
    if data == "copy_paypal":
        tag = cfg["PAYMENT_INFO"]["paypal"]
        await query.answer("PayPal tag copied — also sent in chat.", show_alert=True)
        await query.message.reply_text(f"`{tag}`", parse_mode="Markdown")
        await admin_ping(context, (
            "📋 **Copy Pressed** (PayPal)\n"
            "🏷️ **Brand:** ZTW VIP\n"
            f"👤 **User:** @{username} (`{user_id}`)\n"
            f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
        ))
    elif data == "copy_crypto":
        link = cfg["PAYMENT_INFO"]["crypto"]
        await query.answer("Crypto link copied — also sent in chat.", show_alert=True)
        await query.message.reply_text(link)
        await admin_ping(context, (
            "📋 **Copy Pressed** (Crypto)\n"
            "🏷️ **Brand:** ZTW VIP\n"
            f"👤 **User:** @{username} (`{user_id}`)\n"
            f"🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
        ))

# Small router for ZTW callbacks
async def ztw_router(q, context):
    data = q.data
    if data.startswith("select_"):
        return await ztw_handle_subscription(q, context)
    if data.startswith("payment_"):
        return await ztw_handle_payment(q, context)
    if data == "paid":
        return await ztw_confirm_payment(q, context)
    if data == "back":
        return await ztw_handle_back(q, context)
    if data == "support":
        return await ztw_handle_support(q, context)
    if data == "faq":
        return await ztw_handle_faq(q, context)
    if data in ("copy_paypal","copy_crypto"):
        return await ztw_copy_buttons(q, context)

# ---------------- FastAPI Routes ----------------
@app.get("/")
async def root():
    return JSONResponse({"status": "ok", "bots": list(BOTS.keys())})

@app.get("/uptime")
async def uptime():
    return JSONResponse({"status": "online", "uptime": str(datetime.now() - START_TIME)})

@app.get("/status")
async def status():
    return JSONResponse({
        "loaded_bots": list(APPS.keys()),
        "startup_results": STARTUP_RESULTS,
        "uptime": str(datetime.now() - START_TIME),
    })

# -------- Fault-tolerant startup: one bad bot won't block others --------
@app.on_event("startup")
async def on_startup():
    for brand, cfg in BOTS.items():
        try:
            token = cfg["TOKEN"]
            if not token or token.startswith("PUT-"):
                msg = f"[{brand}] No/placeholder token, skipping."
                log.warning(msg)
                STARTUP_RESULTS[brand] = "skipped:no_token"
                continue

            # Build app per brand
            app_obj = Application.builder().token(token).updater(None).build()

            # Handlers per brand
            if brand == "zaystheway_vip":
                app_obj.add_handler(CommandHandler("start", ztw_start))
                app_obj.add_handler(CallbackQueryHandler(ztw_handle_subscription, pattern="select_.*"))
                app_obj.add_handler(CallbackQueryHandler(ztw_handle_payment, pattern="payment_.*"))
                app_obj.add_handler(CallbackQueryHandler(ztw_confirm_payment, pattern="paid"))
                app_obj.add_handler(CallbackQueryHandler(ztw_handle_back, pattern="back"))
                app_obj.add_handler(CallbackQueryHandler(ztw_handle_support, pattern="support"))
                app_obj.add_handler(CallbackQueryHandler(ztw_handle_faq, pattern="faq"))
                app_obj.add_handler(CallbackQueryHandler(ztw_copy_buttons, pattern="copy_.*"))
                # Optional uptime ping (non-fatal if it fails)
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.get(f"{BASE_URL}/uptime")
                    log.info(f"[{brand}] Uptime Monitoring OK")
                except Exception as ping_err:
                    log.warning(f"[{brand}] Uptime ping failed: {ping_err}")
            else:
                app_obj.add_handler(CommandHandler("start", start))
                app_obj.add_handler(CallbackQueryHandler(on_cb))

            app_obj.bot_data["brand"] = brand

            # Initialize
            try:
                await app_obj.initialize()
            except Exception as init_err:
                STARTUP_RESULTS[brand] = f"init_error:{init_err}"
                log.error(f"[{brand}] Initialize failed: {init_err}")
                continue  # move on to next brand

            # Webhook setup (delete + set)
            try:
                await app_obj.bot.delete_webhook(drop_pending_updates=True)
                await app_obj.bot.set_webhook(
                    f"{BASE_URL}/webhook/{brand}",
                    allowed_updates=["message", "callback_query"]
                )
                log.info(f"[{brand}] Webhook set to {BASE_URL}/webhook/{brand}")
            except Exception as wh_err:
                STARTUP_RESULTS[brand] = f"webhook_error:{wh_err}"
                log.error(f"[{brand}] Failed to set webhook: {wh_err}")
                # still keep the app in APPS so brand can be retried later
                APPS[brand] = app_obj
                continue

            # Success
            APPS[brand] = app_obj
            STARTUP_RESULTS[brand] = "ok"
            log.info(f"[{brand}] Bot initialized.")

        except Exception as e:
            # Catch-all so one bot never kills the loop
            STARTUP_RESULTS[brand] = f"fatal_error:{e}"
            log.exception(f"[{brand}] Fatal error during startup (skipping): {e}")

    # Summary
    ok = [b for b, s in STARTUP_RESULTS.items() if s == "ok"]
    bad = {b: s for b, s in STARTUP_RESULTS.items() if s != "ok"}
    log.info(f"Startup summary -> OK: {ok} | Issues: {bad}")

# -------- Robust webhook: per-update isolation --------
@app.post("/webhook/{brand}")
async def webhook(brand: str, request: Request):
    app_obj = APPS.get(brand)
    if not app_obj:
        # Brand not initialized — return 404 so Telegram stops retrying this URL
        return JSONResponse({"error": f"unknown or inactive brand '{brand}'"}, status_code=404)

    try:
        payload = await request.json()
    except Exception as e:
        log.error(f"[{brand}] Bad JSON in webhook: {e}")
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)

    try:
        update = Update.de_json(payload, app_obj.bot)
        await app_obj.process_update(update)
        return JSONResponse({"ok": True})
    except Exception as e:
        # Swallow per-update errors so the server stays up
        log.exception(f"[{brand}] Error processing update: {e}")
        # Return 200 so Telegram doesn't hammer retries forever
        return JSONResponse({"ok": False, "error": "update_processing_error"}, status_code=200)

@app.head("/uptime")
async def uptime_head():
    return Response(status_code=200)

# (Optional helper retained but not called to avoid double webhook sets)
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
    log.info("Start server with: uvicorn multi_bots:app --host 0.0.0.0 --port $PORT")
