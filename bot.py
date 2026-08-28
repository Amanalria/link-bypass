import os
import asyncio
import time
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from config import Config
from unshortener import FastUniversalUnshortener

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()
unshortener = FastUniversalUnshortener(max_hops=Config.MAX_HOPS, timeout=Config.REQUEST_TIMEOUT)

MAX_BATCH_LINKS = 5
PORT = int(os.getenv("PORT", "10000"))

# --- Lightweight Health Check Server for Render Web Service ---
async def handle_health_check(request):
    return web.json_response({
        "status": "healthy",
        "service": "link-bypass-bot",
        "timestamp": int(time.time()),
        "uptime": "online"
    })

async def handle_root(request):
    return web.Response(
        text="<h2>⚡ Universal Shortlink Bypass Bot is Running!</h2><p>Send links to your Telegram bot to bypass.</p>",
        content_type="text/html"
    )

def create_health_app():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health_check)
    return app

# --- Telegram Bot Handlers ---
@dp.message(CommandStart())
async def handle_start(message: types.Message):
    welcome_text = (
        "⚡ <b>UNIVERSAL SHORTLINK BYPASS BOT</b>\n"
        "<i>High-Speed Automated Multi-Tier Link Resolver</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ <b>KEY FEATURES</b>\n"
        f"• <b>Parallel Multi-Bypass:</b> Process up to <b>{MAX_BATCH_LINKS} links</b> simultaneously.\n"
        "• <b>Turbo Engine:</b> Optimized background solver with instant smart caching.\n"
        "• <b>Full Ad-Shield Resolver:</b> Auto-bypasses multi-page timers, redirects & session checks.\n"
        "• <b>Exact Target Extraction:</b> 100% authentic destination link guarantee.\n\n"
        "🌐 <b>SUPPORTED SHORTENERS</b>\n"
        "• <b>Monetized Networks:</b> <code>vplink.in</code>, <code>gplinks</code>, <code>droplink</code>, <code>linkvertise</code>, etc.\n"
        "• <b>Standard Services:</b> <code>bit.ly</code>, <code>tinyurl.com</code>, <code>t.co</code>, <code>is.gd</code>, <code>cutt.ly</code>\n"
        "• <b>Direct Destinations:</b> Telegram Bots (<code>telegram.dog</code>, <code>t.me</code>), Google Drive, TeraBox, Mega, MediaFire, Web Links\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>HOW TO USE</b>\n"
        f"Paste any 1 to {MAX_BATCH_LINKS} short link(s) in this chat and receive direct destination URLs instantly!"
    )
    
    help_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 View Instructions & Help", callback_data="show_help")]
        ]
    )
    await message.answer(welcome_text, parse_mode=ParseMode.HTML, reply_markup=help_kb)

@dp.message(Command("help"))
async def handle_help(message: types.Message):
    help_text = (
        "📖 <b>USER GUIDE & HELP</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ <b>Copy Short Link(s):</b>\n"
        "• Copy single or multiple short links from any site or Telegram channel.\n\n"
        f"2️⃣ <b>Send to Bot:</b>\n"
        f"• Paste links directly in chat (up to <b>{MAX_BATCH_LINKS} links</b> per message).\n\n"
        "3️⃣ <b>Get Direct Links:</b>\n"
        "• The turbo engine solves all countdown timers, publisher blogs, and session tokens concurrently and provides clean destination links.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "show_help")
async def callback_help(callback: types.CallbackQuery):
    await handle_help(callback.message)
    await callback.answer()

@dp.message(F.text)
async def handle_message(message: types.Message):
    text = message.text.strip()
    raw_urls = unshortener.extract_urls(text)

    if not raw_urls:
        error_box = (
            "⚠️ <b>INVALID INPUT</b>\n\n"
            "Please provide valid HTTP/HTTPS short URLs.\n"
            "<i>Example:</i> <code>https://vplink.in/peWy3u</code> or <code>https://bit.ly/3xyz</code>"
        )
        await message.answer(error_box, parse_mode=ParseMode.HTML)
        return

    # Limit to max allowed batch
    urls = raw_urls[:MAX_BATCH_LINKS]
    total_count = len(urls)

    if total_count == 1:
        status_text = (
            "⚡ <b>BYPASS IN PROGRESS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 <b>Target URL:</b>\n"
            f"<code>{urls[0]}</code>\n\n"
            "⏳ <i>Bypassing timers, publisher hops & decrypting final destination...</i>"
        )
    else:
        status_text = (
            f"🚀 <b>PARALLEL BYPASS IN PROGRESS ({total_count} Links)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚡ <b>Engine:</b> <i>Concurrent multi-thread turbo resolver</i>\n"
            "⏳ <i>Processing all links simultaneously. Please wait a moment...</i>"
        )

    status_msg = await message.answer(status_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    t_start = time.time()

    try:
        # Execute concurrent parallel resolution
        results = await asyncio.gather(*[unshortener.unshorten(url) for url in urls], return_exceptions=True)
        total_duration = round(time.time() - t_start, 2)

        items = []
        keyboard_buttons = []
        success_count = 0

        for idx, (original_url, res) in enumerate(zip(urls, results), 1):
            if isinstance(res, Exception):
                item_card = (
                    f"🏷️ <b>LINK #{idx}</b>\n"
                    f"🔗 <b>Short URL:</b>\n<code>{original_url}</code>\n\n"
                    f"❌ <b>Status:</b> <i>Timeout / Could not resolve link</i>"
                )
            elif res.success and res.final_url:
                success_count += 1
                hop_str = f"{len(res.hops)-1} Redirect Hops Bypassed" if len(res.hops) > 1 else "Direct Fast Resolution"
                cached_tag = " • ⚡ Instant Cache" if res.cached else ""
                item_card = (
                    f"🏷️ <b>LINK #{idx}</b>\n"
                    f"🔗 <b>Short URL:</b>\n<code>{original_url}</code>\n\n"
                    f"🎯 <b>Original Destination:</b>\n<code>{res.final_url}</code>\n\n"
                    f"📊 <b>Telemetry:</b> <code>{hop_str} • {res.duration}s{cached_tag}</code>"
                )
                if res.final_url.startswith("http"):
                    btn_label = f"🌐 Open Link #{idx}" if total_count > 1 else "🌐 Open Destination Link"
                    keyboard_buttons.append(InlineKeyboardButton(text=btn_label, url=res.final_url))
            else:
                item_card = (
                    f"🏷️ <b>LINK #{idx}</b>\n"
                    f"🔗 <b>Short URL:</b>\n<code>{original_url}</code>\n\n"
                    f"❌ <b>Error:</b> <code>{res.error or 'Failed to bypass'}</code>"
                )
            
            items.append(item_card)

        # Header summary block
        header = (
            "🎉 <b>BYPASS COMPLETED SUCCESSFULLY</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 <b>Status:</b> <code>{success_count}/{total_count} Resolved</code>\n"
            f"⏱️ <b>Total Parallel Time:</b> <code>{total_duration}s</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        full_message = header + "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n".join(items)

        # Build grid keyboard (max 2 buttons per row)
        kb = None
        if keyboard_buttons:
            rows = []
            for i in range(0, len(keyboard_buttons), 2):
                rows.append(keyboard_buttons[i:i+2])
            kb = InlineKeyboardMarkup(inline_keyboard=rows)

        await status_msg.edit_text(full_message, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error in batch bypass: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ <b>PROCESS ERROR</b>\n\n"
            f"An unexpected error occurred while processing links:\n<code>{str(e)[:150]}</code>",
            parse_mode=ParseMode.HTML
        )

async def start_web_server():
    """Starts the lightweight aiohttp health check web server for Render"""
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Health check web server listening on 0.0.0.0:{PORT}")

async def main():
    # Start web server for Render health check
    await start_web_server()
    logger.info("🚀 Starting Universal Shortlink Bypass Bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await unshortener.close()

if __name__ == "__main__":
    asyncio.run(main())
