"""
Help System Cog using Components V2 Interactive UI.

Public categories:
- Moderation
- Utility
- Management
- Information

Private Owner/Admin Category:
- Giveaway Help (+ghlp)
"""

import discord
from discord.ext import commands
import config
from utils.embeds import create_embed, error_embed
from utils.ui_components import HelpNavView


PUBLIC_HELP_DATA = {
    "Moderation": {
        "emoji": config.EMOJI_MOD,
        "description": "Server moderation and disciplinary action commands.",
        "commands": {
            "ban @user [reason]": "Ban a member from the server.",
            "kick @user [reason]": "Kick a member from the server.",
            "timeout @user <time> [reason]": "Timeout a member (e.g., 30s, 5m, 2h, 1d).",
            "untimeout @user [reason]": "Remove timeout from a member.",
            "mute @user [reason]": "Mute a member (timeout / muted role).",
            "unmute @user [reason]": "Unmute a member.",
            "warn @user <reason>": "Issue an official warning to a member.",
            "warnings @user": "View warning history for a member.",
            "clear <amount>": "Purge X messages from the current channel (alias: +purge)."
        }
    },
    "Management": {
        "emoji": config.EMOJI_SHIELD,
        "description": "Channel & role management commands.",
        "commands": {
            "lock [channel] [reason]": "Prevent @everyone from sending messages.",
            "unlock [channel] [reason]": "Restore message sending permissions.",
            "slowmode <seconds>": "Set message slowmode delay for the channel.",
            "nick @user [new_nick]": "Change or reset a member's nickname.",
            "role @user <role>": "Assign a role to a member.",
            "removerole @user <role>": "Remove a role from a member.",
            "hide [channel]": "Hide a channel from @everyone.",
            "unhide [channel]": "Restore channel visibility for @everyone."
        }
    },
    "Utility": {
        "emoji": "⚙️",
        "description": "Broadcasting and custom message commands.",
        "commands": {
            "announce #channel <msg>": "Post a structured announcement embed.",
            "say <message>": "Make the bot repeat your message.",
            "embed Title | Text | [Hex]": "Send a formatted custom embed."
        }
    },
    "Information": {
        "emoji": "ℹ️",
        "description": "Server, user, bot, and latency status commands.",
        "commands": {
            "userinfo [@user]": "View detailed account & join dates for a user.",
            "serverinfo": "View server stats, member count, and creation date.",
            "avatar [@user]": "View a user's full resolution avatar.",
            "channelinfo [#channel]": "View metadata for a channel.",
            "roleinfo <role>": "View details about a role.",
            "botinfo": "View bot specifications, uptime, and system info.",
            "ping": "Check bot WebSocket latency.",
            "uptime": "Check how long the bot has been online.",
            "invite": "Get the bot's invite link."
        }
    }
}

GIVEAWAY_HELP_DATA = {
    "gwy <time> <winners> <prize> [forced_id]": "Create a new giveaway with optional forced winner.",
    "reroll <message_id>": "Pick a new random winner for an ended giveaway.",
    "gend <message_id>": "Force-end an active giveaway immediately.",
    "gcancel <message_id>": "Cancel an active giveaway without picking winners.",
    "glist": "List all currently active server giveaways."
}


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.remove_command("help")  # Override default help command

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context, category: str = None):
        """Public Components V2 Help Menu (Excludes private giveaway commands)."""

        if category:
            matched_cat = None
            for cat_name in PUBLIC_HELP_DATA.keys():
                if cat_name.lower() == category.lower():
                    matched_cat = cat_name
                    break

            if matched_cat:
                data = PUBLIC_HELP_DATA[matched_cat]
                embed = create_embed(
                    title=f"{data['emoji']} {matched_cat} Commands",
                    description=data['description'],
                    color=config.COLOR_PRIMARY
                )
                for cmd, desc in data['commands'].items():
                    embed.add_field(name=f"`{config.PREFIX}{cmd}`", value=desc, inline=False)
                await ctx.send(embed=embed)
                return

        # Public Overview Embed with Interactive Components V2 Navigation
        embed = create_embed(
            title=f"{config.EMOJI_BOT} Discord Shop Bot Command Center",
            description=(
                f"Welcome to the **Shop Management Bot** command hub!\n"
                f"Use the buttons or dropdown menu below to explore commands by category.\n\n"
                f"**Default Prefix:** `{config.PREFIX}`\n"
                f"**Categories:** Moderation, Utility, Management, Information"
            ),
            color=config.COLOR_PRIMARY,
            thumbnail_url=self.bot.user.display_avatar.url if self.bot.user else None
        )

        embed.add_field(name="🛡️ Moderation", value=f"`{config.PREFIX}help Moderation`", inline=True)
        embed.add_field(name="⚙️ Utility", value=f"`{config.PREFIX}help Utility`", inline=True)
        embed.add_field(name="🔒 Management", value=f"`{config.PREFIX}help Management`", inline=True)
        embed.add_field(name="ℹ️ Information", value=f"`{config.PREFIX}help Information`", inline=True)

        view = HelpNavView(PUBLIC_HELP_DATA, ctx.author.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="ghlp")
    @commands.has_permissions(manage_guild=True)
    async def ghlp(self, ctx: commands.Context):
        """Private Giveaway Help Command (Owners / Admins Only)."""
        # Automatically delete original command message to maintain privacy
        try:
            await ctx.message.delete()
        except Exception:
            pass

        embed = create_embed(
            title=f"{config.EMOJI_GIVEAWAY} Private Giveaway Management Suite",
            description=(
                f"Confidential giveaway management panel for administrators.\n"
                f"Commands executed will post clean embeds without revealing raw command syntax.\n\n"
                f"**Prefix:** `{config.PREFIX}`"
            ),
            color=config.COLOR_PRIMARY,
            thumbnail_url=self.bot.user.display_avatar.url if self.bot.user else None
        )

        for cmd, desc in GIVEAWAY_HELP_DATA.items():
            embed.add_field(name=f"`{config.PREFIX}{cmd}`", value=desc, inline=False)

        embed.set_footer(text="Private Admin Menu • Authorized Personnel Only")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
