# ⚡ Link Bypass Telegram Bot

A high-performance, automated multi-tier shortlink bypass Telegram bot built with **Python**, **aiogram 3**, **Playwright**, and **aiohttp**.

Bypasses complex ad-link networks (`vplink.in`, `gplinks`, `droplink`, etc.) and standard shorteners (`bit.ly`, `tinyurl`, `t.co`, `is.gd`, `cutt.ly`), returning exact destination URLs (websites, Telegram bots/channels, TeraBox, Mega, Drive, etc.).

---

## 🚀 Features

- **⚡ Parallel Multi-Link Processing**: Bypass up to 5 links simultaneously in a single message.
- **🛡️ Full Ad-Shield Resolver**: Handles multi-page publisher blogs, countdown timers, session handshakes, and anti-bot checks.
- **🎯 100% Exact Target Extraction**: Extracts authentic target links directly from final `#gt-link` tokens.
- **🌐 Dual-Engine Architecture**:
  - **Standard Shorteners**: 0.2s ultra-fast async HTTP resolver (`aiohttp`).
  - **Monetized Shorteners**: Headless Chromium solver (`Playwright`) with C++ level asset blocking.
- **⚡ Instant Smart Cache**: Repeated/duplicate links return instantly in **0.01s**.
- **☁️ Render Ready**: Pre-configured `Dockerfile` and `render.yaml` with integrated health check web server.

---

## 🌐 Deploy to Render (render.com) - Step by Step

### Method 1: Deploy with Docker (Recommended)

1. Fork or push this repository to your **GitHub** account (`link-bypass`).
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Connect your GitHub account and select your `link-bypass` repository.
4. Set the following settings:
   - **Name**: `link-bypass-bot`
   - **Region**: Any (e.g. `Oregon (US West)`)
   - **Branch**: `main`
   - **Runtime**: **Docker**
   - **Instance Type**: **Free**
5. Under **Environment Variables**, add:
   - `BOT_TOKEN`: Your Telegram Bot Token from `@BotFather`
   - `PORT`: `10000`
   - `MAX_HOPS`: `25`
   - `REQUEST_TIMEOUT`: `40`
6. Click **Deploy Web Service**!

Render will build the Docker container with all Chromium dependencies pre-installed and start the bot automatically.

---

## 🛠️ Local Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/Amanalria/link-bypass.git
   cd link-bypass
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and put your BOT_TOKEN
   ```

4. **Run the bot**:
   ```bash
   python3 bot.py
   ```

---

## 📜 License

MIT License. Free for personal and community use.
