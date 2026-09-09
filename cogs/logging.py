"""
Logging System Cog.

Monitors Discord events and posts audit logs to LOG_CHANNEL_ID:
- Message Deletes & Message Edits
- Member Ban & Unban Events
- Member Join & Leave Events
- Role Add / Remove Changes
- Command Errors & System Startup Log
"""

import discord
from discord.ext import commands
import config
from utils.embeds import create_embed
from utils.logger import send_log, logger


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content or "*[No text content / Only attachments/embeds]*"
        if len(content) > 1024:
            content = content[:1020] + "..."

        await send_log(
            self.bot,
            "Message Deleted",
            f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
            f"**Channel:** {message.channel.mention}\n"
            f"**Content:**\n{content}",
            color=config.COLOR_DANGER,
            author=message.author
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return

        if before.content == after.content:
            return

        before_text = before.content or "*[Empty]*"
        after_text = after.content or "*[Empty]*"

        if len(before_text) > 500:
            before_text = before_text[:495] + "..."
        if len(after_text) > 500:
            after_text = after_text[:495] + "..."

        await send_log(
            self.bot,
            "Message Edited",
            f"**Author:** {before.author.mention} (`{before.author.id}`)\n"
            f"**Channel:** {before.channel.mention}\n"
            f"[Jump to Message]({after.jump_url})\n\n"
            f"**Before:**\n{before_text}\n\n"
            f"**After:**\n{after_text}",
            color=config.COLOR_WARNING,
            author=before.author
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await send_log(
            self.bot,
            "User Banned",
            f"**User:** {user.name} (`{user.id}`)",
            color=config.COLOR_DANGER
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await send_log(
            self.bot,
            "User Unbanned",
            f"**User:** {user.name} (`{user.id}`)",
            color=config.COLOR_SUCCESS
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Role changes log
        if before.roles != after.roles:
            added_roles = [r.mention for r in after.roles if r not in before.roles]
            removed_roles = [r.mention for r in before.roles if r not in after.roles]

            changes = []
            if added_roles:
                changes.append(f"**Added Roles:** {', '.join(added_roles)}")
            if removed_roles:
                changes.append(f"**Removed Roles:** {', '.join(removed_roles)}")

            if changes:
                await send_log(
                    self.bot,
                    "Member Roles Updated",
                    f"**Member:** {after.mention} (`{after.id}`)\n" + "\n".join(changes),
                    color=config.COLOR_PRIMARY,
                    author=after
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(Logging(bot))
