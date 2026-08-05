"""
Standardized Embed Builder module ensuring modern dark-themed aesthetic across the bot.
Theme: Dark charcoal background (#2B2D31), Blurple primary (#5865F2).
Includes timestamps, footers, and bot avatars automatically.
"""

import discord
from datetime import datetime
from typing import Optional
import config


def create_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: int = config.COLOR_PRIMARY,
    footer_text: Optional[str] = None,
    footer_icon: Optional[str] = None,
    author_name: Optional[str] = None,
    author_icon: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None,
    timestamp: bool = True
) -> discord.Embed:
    """Create a standardized modern dark-styled Discord embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow() if timestamp else None
    )

    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon)

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    if image_url:
        embed.set_image(url=image_url)

    # Standardized Footer
    footer = footer_text or "Shop Management Bot • Powered by Components V2"
    if footer_icon:
        embed.set_footer(text=footer, icon_url=footer_icon)
    else:
        embed.set_footer(text=footer)

    return embed


def success_embed(title: str, description: str) -> discord.Embed:
    """Embed for successful operations."""
    return create_embed(
        title=f"{config.EMOJI_SUCCESS} {title}",
        description=description,
        color=config.COLOR_SUCCESS
    )


def error_embed(title: str, description: str) -> discord.Embed:
    """Embed for failed operations / error handling."""
    return create_embed(
        title=f"{config.EMOJI_ERROR} {title}",
        description=description,
        color=config.COLOR_DANGER
    )


def warning_embed(title: str, description: str) -> discord.Embed:
    """Embed for warning alerts."""
    return create_embed(
        title=f"{config.EMOJI_WARNING} {title}",
        description=description,
        color=config.COLOR_WARNING
    )


def info_embed(title: str, description: str) -> discord.Embed:
    """Embed for general information."""
    return create_embed(
        title=f"{config.EMOJI_SHIELD} {title}",
        description=description,
        color=config.COLOR_PRIMARY
    )
