"""
Utility & Information System Cog.

Provides utility & server info commands:
- Announce / Say / Custom Embed
- User Info / Server Info / Channel Info / Role Info / Avatar / Bot Info
- Ping / Uptime / Invite
"""

import discord
from discord.ext import commands
from typing import Optional
import time
import datetime
import platform
import re

import config
from utils.embeds import create_embed, success_embed, error_embed, info_embed
from utils.components_v2 import send_v2


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="announce")
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """Send a Components V2 announcement to a target channel."""
        embed = create_embed(
            title=f"{config.EMOJI_PIN} Announcement",
            description=message,
            color=config.COLOR_PRIMARY,
            author_name=ctx.guild.name,
            author_icon=ctx.guild.icon.url if ctx.guild.icon else None
        )
        try:
            await send_v2(channel, embed=embed)
            await ctx.send(embed=success_embed("Announcement Sent", f"Successfully posted announcement in {channel.mention}."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to send announcement: {e}"))

    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, message: str):
        """Make the bot say a message in the current channel."""
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(content=message)

    @commands.command(name="vch")
    @commands.has_permissions(manage_messages=True)
    async def vch(self, ctx: commands.Context, *, details: str):
        """Relay a purchase as `+rep <caller_id> <product> | <price>`."""
        match = re.fullmatch(r"\s*(.+?)\s*\(([^()]+)\)\s*", details)
        if not match:
            await ctx.send(
                embed=error_embed(
                    "Invalid Syntax",
                    f"Use `{config.PREFIX}vch <product name> (<price>)`, for example "
                    f"`{config.PREFIX}vch Minecraft host (700BDT)`."
                )
            )
            return

        product = match.group(1).strip()
        price = match.group(2).strip()
        price = re.sub(r"^(\d+(?:[.,]\d+)?)\s*([A-Za-z]{3,})$", r"\1 \2", price)
        if not product or not price:
            await ctx.send(embed=error_embed("Invalid Syntax", "Include both a product name and a price."))
            return

        # This plain command relay is intentionally readable by the separate +rep bot.
        await ctx.channel.send(
            f"+rep {ctx.author.id} {product} | {price}",
            allowed_mentions=discord.AllowedMentions.none()
        )

    @commands.command(name="status")
    @commands.is_owner()
    async def status(self, ctx: commands.Context, *, activity: str):
        """Set the bot presence: playing/watching/listening/streaming/competing, or a custom status."""
        activity_types = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "streaming": discord.ActivityType.streaming,
            "competing": discord.ActivityType.competing,
        }
        parts = activity.strip().split(maxsplit=1)
        kind = parts[0].casefold()

        if kind in activity_types:
            if len(parts) < 2 or not parts[1].strip():
                await ctx.send(embed=error_embed(
                    "Missing Activity Name",
                    f"Use `{config.PREFIX}status <activity> <activity name>`."
                ))
                return
            activity_name = parts[1].strip()
            if kind == "streaming":
                if not re.match(r"^https?://", activity_name, re.IGNORECASE):
                    await ctx.send(embed=error_embed(
                        "Streaming URL Required",
                        "For streaming status, include a link such as `https://strm.link`."
                    ))
                    return
                selected_activity = discord.Streaming(name=activity_name, url=activity_name)
            elif kind == "playing":
                selected_activity = discord.Game(name=activity_name)
            else:
                selected_activity = discord.Activity(type=activity_types[kind], name=activity_name)
            label = f"{kind.title()} — {activity_name}"
        else:
            # An unrecognized activity word (for example, `+status hii`) is
            # treated as the custom status text exactly as requested.
            activity_name = activity.strip()
            selected_activity = discord.CustomActivity(name=activity_name)
            label = f"Custom status — {activity_name}"

        status = discord.Status.online
        self.bot.configured_presence = (status, selected_activity)
        await self.bot.change_presence(status=status, activity=selected_activity)
        await ctx.send(embed=success_embed("Bot Status Updated", f"The bot now shows **{label}**."))

    @commands.command(name="rename")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def rename(self, ctx: commands.Context, *, channel_new_name: str):
        """Rename the channel where this command is used."""
        new_name = channel_new_name.strip()
        if not new_name or len(new_name) > 100:
            await ctx.send(embed=error_embed("Invalid Channel Name", "Channel names must contain between 1 and 100 characters."))
            return

        try:
            await ctx.channel.edit(name=new_name, reason=f"Channel renamed by {ctx.author}")
        except discord.Forbidden:
            await ctx.send(embed=error_embed("Permission Denied", "I cannot rename this channel."))
        except discord.HTTPException as exc:
            await ctx.send(embed=error_embed("Rename Failed", f"Discord could not rename this channel: {exc}"))
            return
        else:
            await ctx.send(embed=success_embed("Channel Renamed", f"This channel is now named **{new_name}**."))

    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_cmd(self, ctx: commands.Context, *, args: str):
        """
        Send a custom embed.
        Syntax: +embed Title | Description | [Color Hex e.g. 5865F2]
        """
        parts = [p.strip() for p in args.split("|")]
        if len(parts) < 2:
            await ctx.send(embed=error_embed("Invalid Syntax", "Syntax: `+embed Title | Description | [Color Hex]`"))
            return

        title = parts[0]
        description = parts[1]
        color = config.COLOR_PRIMARY

        if len(parts) >= 3:
            try:
                hex_str = parts[2].lstrip("#")
                color = int(hex_str, 16)
            except ValueError:
                pass

        embed = create_embed(
            title=title,
            description=description,
            color=color,
            author_name=ctx.author.display_name,
            author_icon=ctx.author.display_avatar.url
        )

        try:
            await ctx.message.delete()
        except Exception:
            pass

        await send_v2(ctx, embed=embed)

    @commands.command(name="userinfo")
    async def userinfo(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Display information about a user."""
        target = member or ctx.author
        roles = [r.mention for r in target.roles if r != ctx.guild.default_role]

        embed = create_embed(
            title=f"User Info - {target.name}",
            color=target.color if target.color != discord.Color.default() else config.COLOR_PRIMARY,
            thumbnail_url=target.display_avatar.url
        )

        embed.add_field(name="Username", value=f"`{target.name}` ({target.mention})", inline=True)
        embed.add_field(name="User ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Bot Account?", value="Yes" if target.bot else "No", inline=True)

        created_ts = int(target.created_at.timestamp())
        embed.add_field(name="Created Account", value=f"<t:{created_ts}:F> (<t:{created_ts}:R>)", inline=False)

        if isinstance(target, discord.Member) and target.joined_at:
            joined_ts = int(target.joined_at.timestamp())
            embed.add_field(name="Joined Server", value=f"<t:{joined_ts}:F> (<t:{joined_ts}:R>)", inline=False)

        embed.add_field(name=f"Roles [{len(roles)}]", value=", ".join(roles[:10]) if roles else "None", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx: commands.Context):
        """Display information about the current server."""
        guild = ctx.guild
        owner = guild.owner

        embed = create_embed(
            title=f"Server Information - {guild.name}",
            color=config.COLOR_PRIMARY,
            thumbnail_url=guild.icon.url if guild.icon else None
        )

        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Owner", value=f"{owner.mention if owner else 'Unknown'}", inline=True)
        embed.add_field(name="Created On", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=True)

        embed.add_field(name="Total Members", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="Text Channels", value=f"`{len(guild.text_channels)}`", inline=True)
        embed.add_field(name="Voice Channels", value=f"`{len(guild.voice_channels)}`", inline=True)
        embed.add_field(name="Roles Count", value=f"`{len(guild.roles)}`", inline=True)
        embed.add_field(name="Emojis Count", value=f"`{len(guild.emojis)}`", inline=True)
        embed.add_field(name="Boost Level", value=f"Tier `{guild.premium_tier}` ({guild.premium_subscription_count} boosts)", inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="avatar")
    async def avatar(self, ctx: commands.Context, member: Optional[discord.Member | discord.User] = None):
        """Display a member's avatar."""
        target = member or ctx.author
        embed = create_embed(
            title=f"Avatar - {target.display_name}",
            color=config.COLOR_PRIMARY,
            image_url=target.display_avatar.url
        )
        await ctx.send(embed=embed)

    @commands.command(name="channelinfo")
    async def channelinfo(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Display information about a channel."""
        target = channel or ctx.channel
        embed = create_embed(
            title=f"Channel Info - #{target.name}",
            color=config.COLOR_PRIMARY
        )
        embed.add_field(name="Channel ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Category", value=f"{target.category.name if target.category else 'None'}", inline=True)
        embed.add_field(name="Created On", value=f"<t:{int(target.created_at.timestamp())}:F>", inline=True)
        embed.add_field(name="NSFW?", value="Yes" if target.is_nsfw() else "No", inline=True)
        embed.add_field(name="Slowmode", value=f"`{target.slowmode_delay}s`", inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="roleinfo")
    async def roleinfo(self, ctx: commands.Context, role: discord.Role):
        """Display information about a role."""
        embed = create_embed(
            title=f"Role Info - {role.name}",
            color=role.color if role.color != discord.Color.default() else config.COLOR_PRIMARY
        )
        embed.add_field(name="Role ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="Color Hex", value=f"`{str(role.color)}`", inline=True)
        embed.add_field(name="Position", value=f"`{role.position}`", inline=True)
        embed.add_field(name="Members Count", value=f"`{len(role.members)}`", inline=True)
        embed.add_field(name="Hoisted?", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Mentionable?", value="Yes" if role.mentionable else "No", inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="botinfo")
    async def botinfo(self, ctx: commands.Context):
        """Display information and system specifications about the bot."""
        uptime_sec = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        embed = create_embed(
            title=f"{config.EMOJI_BOT} Discord Shop Management Bot",
            description="A premium, high-performance Discord shop and server management bot built with discord.py 2.x and Components V2 UI.",
            color=config.COLOR_PRIMARY,
            thumbnail_url=self.bot.user.display_avatar.url
        )

        embed.add_field(name="Python Version", value=f"`{platform.python_version()}`", inline=True)
        embed.add_field(name="discord.py Version", value=f"`{discord.__version__}`", inline=True)
        embed.add_field(name="Bot Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="Guilds Count", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Total Users", value=f"`{sum(g.member_count for g in self.bot.guilds if g.member_count)}`", inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)
        embed = info_embed(f"Pong! {config.EMOJI_INFORMATION}", f"Bot WebSocket Latency: **{latency}ms**")
        await ctx.send(embed=embed)

    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        """Check how long the bot has been online."""
        uptime_sec = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        uptime_str = f"**{days}** days, **{hours}** hours, **{minutes}** minutes, **{seconds}** seconds"
        embed = info_embed(f"Bot Uptime {config.EMOJI_TIMEOUT}", f"Online for: {uptime_str}")
        await ctx.send(embed=embed)

    @commands.command(name="invite")
    async def invite(self, ctx: commands.Context):
        """Get the bot invite link."""
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions(8)  # Administrator
        )
        embed = create_embed(
            title="Invite Bot",
            description=f"Click [here]({invite_url}) to invite the bot to your server with Administrator permissions.",
            color=config.COLOR_PRIMARY
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
