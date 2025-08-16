# betbot.py
import os
import asyncio
import logging
import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@YourChannel")

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not set. Exiting.")
    raise SystemExit("Provide TELEGRAM_BOT_TOKEN env var")

DB = "betbot.db"

def init_db():
    conn = sqlite3.connect(DB, check_same_thread=False)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 100,
        banned INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        opt1 TEXT NOT NULL,
        opt2 TEXT NOT NULL,
        published_msg_chat INTEGER,
        published_msg_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER,
        user_id INTEGER,
        option_index INTEGER,
        amount INTEGER
    );
    """)
    conn.commit()
    return conn

conn = init_db()

# Minimal /start and /balance to verify deployment
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users(user_id, username, balance, banned) VALUES (?, ?, 100, 0)", (uid, username))
    conn.commit()
    await update.message.reply_text(f"Welcome {username}! Your wallet: 100 credits.\nYou are running on Railway.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    if not r:
        await update.message.reply_text("Not registered. Send /start.")
        return
    await update.message.reply_text(f"Balance: {r[0]} credits")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    # add your full handlers here (create_scenario, bet, result, etc.)
    app.run_polling()

if __name__ == "__main__":
    main()
