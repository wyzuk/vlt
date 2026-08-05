"""
Logger utility for sending audit log embeds to LOG_CHANNEL_ID.
"""

import discord
import logging
from typing import Optional
import config
from utils.embeds import create_embed

# Setup standard python logger
logger = logging.getLogger("ShopBot")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'))
logger.addHandler(handler)


async def send_log(
    bot: discord.Client,
    title: str,
    description: str,
    color: int = config.COLOR_PRIMARY,
    fields: Optional[dict] = None,
    author: Optional[discord.User | discord.Member] = None
):
    """Send an audit log embed to the configured LOG_CHANNEL_ID."""
    if not config.LOG_CHANNEL_ID:
        return

    try:
        channel = bot.get_channel(config.LOG_CHANNEL_ID)
        if not channel:
            try:
                channel = await bot.fetch_channel(config.LOG_CHANNEL_ID)
            except Exception:
                return

        if not channel:
            return

        embed = create_embed(
            title=f"{config.EMOJI_LOG} {title}",
            description=description,
            color=color,
            author_name=str(author) if author else None,
            author_icon=author.display_avatar.url if author else None
        )

        if fields:
            for name, val in fields.items():
                embed.add_field(name=name, value=str(val), inline=True)

        await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Failed to send log entry: {e}")
