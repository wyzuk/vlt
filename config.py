"""
Configuration file for Discord Shop Bot.
All IDs, tokens, colors, emojis, and default settings are centralized here.
"""

import os

TOKEN = os.getenv("TOKEN")
PREFIX = "+"
GUILD_ID = None  # Set if lock to a specific guild, or None for global commands

PROTECTED_CATEGORY_ID = 1372922294405431436
PROTECTED_CHANNEL_IDS = [
    1372922819838611567
]

LOG_CHANNEL_ID = 1534412536424960010

COLOR_PRIMARY = 0x5865F2     # Blurple
COLOR_SUCCESS = 0x57F287     # Green
COLOR_WARNING = 0xFEE75C     # Yellow
COLOR_DANGER = 0xED4245      # Red
COLOR_DARK = 0x2B2D31        # Dark Charcoal / Dark Theme
COLOR_INFO = 0x3498DB        # Light Blue

EMOJI_SHIELD = "🛡️"
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARNING = "⚠️"
EMOJI_GIVEAWAY = "🎉"
EMOJI_TIME = "⏳"
EMOJI_ENTRIES = "📊"
EMOJI_USER = "👤"
EMOJI_MOD = "🔨"
EMOJI_BOT = "🤖"
EMOJI_LOCK = "🔒"
EMOJI_UNLOCK = "🔓"
EMOJI_LOG = "📋"
EMOJI_PIN = "📌"
EMOJI_CROWN = "👑"
EMOJI_STAR = "⭐"
