import os
import asyncio
import time
import logging
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import Config
from unshortener import UniversalUnshortener

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()
unshortener = UniversalUnshortener(max_hops=Config.MAX_HOPS, timeout=Config.REQUEST_TIMEOUT)

MAX_BATCH_LINKS = 5
PORT = int(os.getenv("PORT", "10000"))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
WEBHOOK_PATH = "/webhook"

# --- High-Performance UptimeRobot & Keep-Alive Web Server ---
async def handle_health_check(request):
    return web.json_response({
        "status": "healthy",
        "service": "link-bypass-bot",
        "timestamp": int(time.time()),
        "mode": "webhook" if RENDER_URL else "polling",
        "uptime": "24/7 online",
        "keepalive": "active"
    })

async def handle_ping(request):
    return web.Response(text="pong", content_type="text/plain")

async def handle_root(request):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Link Bypass Bot • Active</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 2.5rem; border-radius: 1rem; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; max-width: 480px; border: 1px solid #334155; }
        .badge { background: #10b981; color: #fff; font-size: 0.85rem; padding: 0.35rem 0.75rem; border-radius: 9999px; font-weight: 600; display: inline-block; margin-bottom: 1rem; }
        h1 { margin: 0 0 0.5rem; font-size: 1.5rem; }
        p { color: #94a3b8; font-size: 0.95rem; line-height: 1.5; }
        .btn { display: inline-block; margin-top: 1.5rem; background: #3b82f6; color: white; text-decoration: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; transition: 0.2s; }
        .btn:hover { background: #2563eb; }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">🟢 24/7 WEBHOOK DAEMON ACTIVE</div>
        <h1>⚡ Link Bypass Bot is Running</h1>
        <p>Your Telegram shortlink bypass daemon is live with zero conflict webhook routing and UptimeRobot heartbeat.</p>
        <a href="https://t.me/Unlinkk_bot" class="btn" target="_blank">Open Telegram Bot 🚀</a>
    </div>
</body>
</html>"""
    return web.Response(text=html_content, content_type="text/html")

async def self_ping_worker(app):
    """Internal keep-alive background worker that periodically pings itself every 10 minutes"""
    if not RENDER_URL:
        return
    await asyncio.sleep(60)
    logger.info(f"🔄 Self-ping keep-alive background worker active for {RENDER_URL}")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                ping_target = f"{RENDER_URL}/health"
                async with session.get(ping_target, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        logger.info("💓 Keep-alive self-ping heartbeat OK (200)")
                    else:
                        logger.warning(f"⚠️ Self-ping returned status {resp.status}")
            except Exception as e:
                logger.debug(f"Self-ping cycle note: {e}")
                
            await asyncio.sleep(600)

async def start_background_tasks(app):
    app['self_ping_task'] = asyncio.create_task(self_ping_worker(app))

async def cleanup_background_tasks(app):
    if 'self_ping_task' in app:
        app['self_ping_task'].cancel()
        try:
            await app['self_ping_task']
        except asyncio.CancelledError:
            pass

# --- Telegram Bot Handlers ---
@dp.message(CommandStart())
async def handle_start(message: types.Message):
    welcome_text = (
        "⚡ <b>UNIVERSAL SHORTLINK BYPASS BOT</b>\n"
        "<i>High-Speed Automated Multi-Tier Link Resolver (24/7 Online)</i>\n\n"
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
            elif res.success and res.final_url and res.final_url != original_url:
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

async def on_startup(app: web.Application):
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}{WEBHOOK_PATH}"
        logger.info(f"🔗 Setting Telegram Webhook to: {webhook_url}")
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    else:
        logger.info("ℹ️ Running in local mode without webhook URL")

async def on_shutdown(app: web.Application):
    if RENDER_URL:
        logger.info("🧹 Removing Telegram Webhook on shutdown...")
        await bot.delete_webhook()
    await bot.session.close()

def main():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health_check)
    app.router.add_get("/ping", handle_ping)
    
    app.on_startup.append(on_startup)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    app.on_shutdown.append(on_shutdown)

    # If on Render, setup zero-conflict webhook handler
    if RENDER_URL:
        logger.info(f"🚀 Initializing Webhook Server mode for {RENDER_URL} on port {PORT}...")
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=PORT)
    else:
        # Fallback for local testing without public domain
        logger.info("🚀 Initializing Polling mode for local test...")
        async def run_local():
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", PORT)
            await site.start()
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, drop_pending_updates=True)
        asyncio.run(run_local())

if __name__ == "__main__":
    main()
