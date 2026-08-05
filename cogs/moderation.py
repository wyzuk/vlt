"""
Moderation System Cog.

Provides complete server management & moderation capabilities:
- Ban / Kick / Timeout / Untimeout
- Mute / Unmute
- Warn / Warnings list
- Clear / Purge messages
- Lock / Unlock channels
- Slowmode configuration
- Nickname management
- Role add / remove
- Hide / Unhide channels
"""

import discord
from discord.ext import commands
from typing import Optional
import datetime
import time

import config
from utils.embeds import success_embed, error_embed, info_embed, create_embed
from utils.time_parser import parse_duration, format_duration
from utils.logger import send_log, logger
from database.db_manager import db


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- BAN COMMAND ---
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member | discord.User, *, reason: Optional[str] = None):
        """Ban a member from the server."""
        reason = reason or "No reason provided."

        if isinstance(member, discord.Member):
            if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
                await ctx.send(embed=error_embed("Permission Denied", "You cannot ban a member with an equal or higher role than yours."))
                return
            if not member.bannable:
                await ctx.send(embed=error_embed("Action Failed", "I do not have permission to ban this user."))
                return

        try:
            # DM user if possible
            if isinstance(member, discord.Member):
                try:
                    dm_embed = error_embed("Banned", f"You were banned from **{ctx.guild.name}**.\n**Reason:** {reason}")
                    await member.send(embed=dm_embed)
                except Exception:
                    pass

            await ctx.guild.ban(member, reason=f"Banned by {ctx.author}: {reason}")
            await ctx.send(embed=success_embed("Member Banned", f"Successfully banned **{member}**.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Member Banned",
                f"**Target:** {member} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_DANGER, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not ban member: {e}"))

    # --- KICK COMMAND ---
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        """Kick a member from the server."""
        reason = reason or "No reason provided."

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("Permission Denied", "You cannot kick a member with an equal or higher role than yours."))
            return

        if not member.kickable:
            await ctx.send(embed=error_embed("Action Failed", "I do not have permission to kick this user."))
            return

        try:
            try:
                dm_embed = warning_embed("Kicked", f"You were kicked from **{ctx.guild.name}**.\n**Reason:** {reason}")
                await member.send(embed=dm_embed)
            except Exception:
                pass

            await member.kick(reason=f"Kicked by {ctx.author}: {reason}")
            await ctx.send(embed=success_embed("Member Kicked", f"Successfully kicked **{member}**.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Member Kicked",
                f"**Target:** {member} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_WARNING, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not kick member: {e}"))

    # --- TIMEOUT COMMAND ---
    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration_str: str, *, reason: Optional[str] = None):
        """Timeout a member for a specified duration (e.g. 30s, 5m, 2h, 1d)."""
        reason = reason or "No reason provided."
        seconds = parse_duration(duration_str)

        if not seconds:
            await ctx.send(embed=error_embed("Invalid Duration", "Please provide a valid time format like `30s`, `5m`, `2h`, `1d`."))
            return

        if seconds > 2419200:  # 28 days max in Discord API
            await ctx.send(embed=error_embed("Limit Exceeded", "Timeout duration cannot exceed 28 days."))
            return

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("Permission Denied", "You cannot timeout a member with an equal or higher role."))
            return

        until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)

        try:
            await member.timeout(until, reason=f"Timed out by {ctx.author}: {reason}")
            fmt_dur = format_duration(seconds)
            await ctx.send(embed=success_embed("Member Timed Out", f"Successfully timed out **{member}** for `{fmt_dur}`.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Member Timed Out",
                f"**Target:** {member} (`{member.id}`)\n**Duration:** {fmt_dur}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_WARNING, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not timeout member: {e}"))

    # --- UNTIMEOUT COMMAND ---
    @commands.command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        """Remove timeout from a member."""
        reason = reason or "No reason provided."

        try:
            await member.timeout(None, reason=f"Untimed out by {ctx.author}: {reason}")
            await ctx.send(embed=success_embed("Timeout Removed", f"Successfully removed timeout for **{member}**.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Member Untimed Out",
                f"**Target:** {member} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_SUCCESS, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not remove timeout: {e}"))

    # --- MUTE COMMAND ---
    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        """Mute a member (applies standard timeout or Muted role)."""
        reason = reason or "No reason provided."
        # Standard default 24h timeout or Muted role lookup
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if muted_role:
            try:
                await member.add_roles(muted_role, reason=f"Muted by {ctx.author}: {reason}")
            except Exception:
                pass

        # Also apply 24h timeout to ensure text & voice mute
        until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        try:
            await member.timeout(until, reason=f"Muted by {ctx.author}: {reason}")
            await ctx.send(embed=success_embed("Member Muted", f"Successfully muted **{member}**.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Member Muted",
                f"**Target:** {member} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_WARNING, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not mute member: {e}"))

    # --- UNMUTE COMMAND ---
    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = None):
        """Unmute a member."""
        reason = reason or "No reason provided."

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            try:
                await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}: {reason}")
            except Exception:
                pass

        try:
            await member.timeout(None, reason=f"Unmuted by {ctx.author}: {reason}")
            await ctx.send(embed=success_embed("Member Unmuted", f"Successfully unmuted **{member}**.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Member Unmuted",
                f"**Target:** {member} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_SUCCESS, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not unmute member: {e}"))

    # --- WARN COMMAND ---
    @commands.command(name="warn")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Issue an official warning to a member."""
        if not reason:
            await ctx.send(embed=error_embed("Missing Argument", "Please provide a reason for the warning."))
            return

        db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason, time.time())
        user_warns = db.get_warnings(ctx.guild.id, member.id)

        try:
            dm_embed = warning_embed("Warning Received", f"You were warned in **{ctx.guild.name}**.\n**Reason:** {reason}\n**Total Warnings:** {len(user_warns)}")
            await member.send(embed=dm_embed)
        except Exception:
            pass

        await ctx.send(embed=success_embed("Member Warned", f"Successfully warned **{member}**.\n**Reason:** {reason}\n**Total Warnings:** `{len(user_warns)}`"))

        await send_log(
            self.bot, "Warning Issued",
            f"**Target:** {member} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}\n**Total Warns:** {len(user_warns)}",
            color=config.COLOR_WARNING, author=ctx.author
        )

    # --- WARNINGS COMMAND ---
    @commands.command(name="warnings")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        """View warnings issued to a member."""
        user_warns = db.get_warnings(ctx.guild.id, member.id)

        if not user_warns:
            await ctx.send(embed=info_embed("Warning History", f"**{member}** has no recorded warnings."))
            return

        embed = create_embed(
            title=f"Warnings for {member}",
            description=f"Total Warnings: `{len(user_warns)}`",
            color=config.COLOR_PRIMARY
        )

        for i, w in enumerate(user_warns[:10], 1):
            mod = ctx.guild.get_member(w['moderator_id'])
            mod_str = mod.mention if mod else f"ID: {w['moderator_id']}"
            date_str = f"<t:{int(w['timestamp'])}:R>"
            embed.add_field(
                name=f"#{i} • {date_str}",
                value=f"**Reason:** {w['reason']}\n**Moderator:** {mod_str}",
                inline=False
            )

        await ctx.send(embed=embed)

    # --- CLEAR / PURGE COMMAND ---
    @commands.command(name="clear", aliases=["purge"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int):
        """Purge X messages from the current channel."""
        if amount <= 0 or amount > 1000:
            await ctx.send(embed=error_embed("Invalid Amount", "Please specify an amount between 1 and 1000."))
            return

        # Delete command message first
        try:
            await ctx.message.delete()
        except Exception:
            pass

        try:
            deleted = await ctx.channel.purge(limit=amount)
            msg = await ctx.send(embed=success_embed("Purged Messages", f"Successfully deleted `{len(deleted)}` messages."))
            await msg.delete(delay=5)

            await send_log(
                self.bot, "Messages Purged",
                f"**Channel:** {ctx.channel.mention}\n**Amount:** {len(deleted)}\n**Moderator:** {ctx.author.mention}",
                color=config.COLOR_DANGER, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to purge messages: {e}"))

    # --- LOCK COMMAND ---
    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None, *, reason: Optional[str] = None):
        """Prevent @everyone from sending messages in a channel."""
        target_channel = channel or ctx.channel
        reason = reason or "No reason provided."

        overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False

        try:
            await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Locked by {ctx.author}: {reason}")
            await ctx.send(embed=success_embed("Channel Locked", f"{config.EMOJI_LOCK} {target_channel.mention} has been locked.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Channel Locked",
                f"**Channel:** {target_channel.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_WARNING, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to lock channel: {e}"))

    # --- UNLOCK COMMAND ---
    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None, *, reason: Optional[str] = None):
        """Restore message sending permissions for @everyone in a channel."""
        target_channel = channel or ctx.channel
        reason = reason or "No reason provided."

        overwrite = target_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None

        try:
            await target_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unlocked by {ctx.author}: {reason}")
            await ctx.send(embed=success_embed("Channel Unlocked", f"{config.EMOJI_UNLOCK} {target_channel.mention} has been unlocked.\n**Reason:** {reason}"))

            await send_log(
                self.bot, "Channel Unlocked",
                f"**Channel:** {target_channel.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                color=config.COLOR_SUCCESS, author=ctx.author
            )
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to unlock channel: {e}"))

    # --- SLOWMODE COMMAND ---
    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int):
        """Set slowmode delay for the channel in seconds (0 to disable)."""
        if seconds < 0 or seconds > 21600:
            await ctx.send(embed=error_embed("Invalid Seconds", "Slowmode delay must be between 0 and 21600 seconds (6 hours)."))
            return

        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                await ctx.send(embed=success_embed("Slowmode Disabled", "Slowmode has been turned off for this channel."))
            else:
                await ctx.send(embed=success_embed("Slowmode Updated", f"Slowmode delay set to `{seconds}` seconds."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to set slowmode: {e}"))

    # --- NICK COMMAND ---
    @commands.command(name="nick")
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: discord.Member, *, new_nickname: Optional[str] = None):
        """Change a member's nickname (pass no nickname to reset)."""
        try:
            await member.edit(nick=new_nickname, reason=f"Nickname changed by {ctx.author}")
            if new_nickname:
                await ctx.send(embed=success_embed("Nickname Changed", f"Changed nickname for **{member}** to `{new_nickname}`."))
            else:
                await ctx.send(embed=success_embed("Nickname Reset", f"Reset nickname for **{member}**."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not change nickname: {e}"))

    # --- ROLE COMMAND ---
    @commands.command(name="role")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        """Assign a role to a member."""
        if role.position >= ctx.author.top_role.position and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("Permission Denied", "You cannot assign a role higher than or equal to your top role."))
            return

        try:
            await member.add_roles(role, reason=f"Role added by {ctx.author}")
            await ctx.send(embed=success_embed("Role Added", f"Added role {role.mention} to **{member}**."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to add role: {e}"))

    # --- REMOVEROLE COMMAND ---
    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx: commands.Context, member: discord.Member, role: discord.Role):
        """Remove a role from a member."""
        if role.position >= ctx.author.top_role.position and ctx.author.id != ctx.guild.owner_id:
            await ctx.send(embed=error_embed("Permission Denied", "You cannot remove a role higher than or equal to your top role."))
            return

        try:
            await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
            await ctx.send(embed=success_embed("Role Removed", f"Removed role {role.mention} from **{member}**."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to remove role: {e}"))

    # --- HIDE COMMAND ---
    @commands.command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Hide a channel from @everyone."""
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.read_messages = False

        try:
            await target.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Hidden by {ctx.author}")
            await ctx.send(embed=success_embed("Channel Hidden", f"Hidden {target.mention} from @everyone."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not hide channel: {e}"))

    # --- UNHIDE COMMAND ---
    @commands.command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Unhide a channel for @everyone."""
        target = channel or ctx.channel
        overwrite = target.overwrites_for(ctx.guild.default_role)
        overwrite.read_messages = None

        try:
            await target.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unhidden by {ctx.author}")
            await ctx.send(embed=success_embed("Channel Unhidden", f"Restored visibility for {target.mention} to @everyone."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Could not unhide channel: {e}"))


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
