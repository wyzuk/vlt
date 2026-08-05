"""
Channel Protection System Cog.

Monitors messages in:
- Category ID: 1372922294405431436 (and all channels inside it)
- Channel ID: 1372922819838611567

Behavior:
1. Ignores bot messages and command invocations starting with prefix (e.g. +say, +gwy, +help).
2. For regular messages: Immediately deletes original user message.
3. Reposts identical clear message content via Bot WITHOUT any user tag header.
4. Preserves text, embeds, attachments, and stickers.
"""

import discord
from discord.ext import commands
import io
import config
from utils.logger import logger


class ChannelProtection(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_protected(self, channel: discord.abc.GuildChannel) -> bool:
        """Check if the channel or its parent category is protected."""
        if not channel:
            return False

        # Direct channel match
        if channel.id in config.PROTECTED_CHANNEL_IDS:
            return True

        # Category match
        if getattr(channel, "category_id", None) == config.PROTECTED_CATEGORY_ID:
            return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Intercept and repost messages sent in protected channels/categories."""
        # Never process bot messages or messages outside guilds
        if message.author.bot or not message.guild:
            return

        if not self.is_protected(message.channel):
            return

        # Check if message is a command invocation (starts with prefix or valid command)
        ctx = await self.bot.get_context(message)
        if ctx.valid or (message.content and message.content.startswith(config.PREFIX)):
            # Do NOT repost command invocations! Let the command handler handle it normally.
            return

        # Delete original message
        try:
            await message.delete()
        except discord.Forbidden:
            logger.warning(f"Missing permissions to delete message {message.id} in {message.channel.id}")
            return
        except discord.NotFound:
            pass
        except Exception as e:
            logger.error(f"Error deleting message in protection handler: {e}")

        # Post clear message content without any header
        content = message.content or None

        # Download attachments to re-upload
        files = []
        for attachment in message.attachments:
            try:
                fp = io.BytesIO()
                await attachment.save(fp)
                files.append(discord.File(fp, filename=attachment.filename, spoiler=attachment.is_spoiler()))
            except Exception as e:
                logger.error(f"Failed to fetch attachment {attachment.filename}: {e}")

        # Extract embeds
        embeds = message.embeds if message.embeds else []

        # Extract stickers
        stickers = message.stickers if message.stickers else []

        # Repost clear message as Bot
        try:
            await message.channel.send(
                content=content,
                embeds=embeds,
                files=files,
                stickers=stickers
            )
        except Exception as e:
            logger.error(f"Error reposting protected message in channel {message.channel.id}: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelProtection(bot))
