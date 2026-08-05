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

import config
from utils.embeds import create_embed, success_embed, error_embed, info_embed


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    # --- ANNOUNCE COMMAND ---
    @commands.command(name="announce")
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        """Send an announcement embed to a target channel."""
        embed = create_embed(
            title=f"{config.EMOJI_PIN} Announcement",
            description=message,
            color=config.COLOR_PRIMARY,
            author_name=ctx.guild.name,
            author_icon=ctx.guild.icon.url if ctx.guild.icon else None
        )
        try:
            await channel.send(embed=embed)
            await ctx.send(embed=success_embed("Announcement Sent", f"Successfully posted announcement in {channel.mention}."))
        except Exception as e:
            await ctx.send(embed=error_embed("Error", f"Failed to send announcement: {e}"))

    # --- SAY COMMAND ---
    @commands.command(name="say")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, message: str):
        """Make the bot say a message in the current channel."""
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(content=message)

    # --- EMBED COMMAND ---
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

        await ctx.send(embed=embed)

    # --- USERINFO COMMAND ---
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

    # --- SERVERINFO COMMAND ---
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

    # --- AVATAR COMMAND ---
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

    # --- CHANNELINFO COMMAND ---
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

    # --- ROLEINFO COMMAND ---
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

    # --- BOTINFO COMMAND ---
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

    # --- PING COMMAND ---
    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)
        embed = info_embed("Pong! 🏓", f"Bot WebSocket Latency: **{latency}ms**")
        await ctx.send(embed=embed)

    # --- UPTIME COMMAND ---
    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        """Check how long the bot has been online."""
        uptime_sec = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        uptime_str = f"**{days}** days, **{hours}** hours, **{minutes}** minutes, **{seconds}** seconds"
        embed = info_embed("Bot Uptime ⏳", f"Online for: {uptime_str}")
        await ctx.send(embed=embed)

    # --- INVITE COMMAND ---
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
