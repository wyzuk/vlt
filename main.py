"""
Discord Shop Bot - Main Entry Point.

Production-ready, modular architecture supporting Python 3.13+ and discord.py 2.x.
Includes dynamic cog auto-loading, global error handling, persistent UI views,
and modern dark-themed embeds.
"""

import discord
from discord.ext import commands
import asyncio
import os
import sys
import traceback
import config
from utils.embeds import error_embed, create_embed
from utils.logger import send_log, logger
from database.db_manager import db
from utils.ui_components import GiveawayView


class ShopBot(commands.Bot):
    def __init__(self):
        # Configure Intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        intents.guilds = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(config.PREFIX),
            intents=intents,
            help_command=None,  # Handled by custom Help cog
            case_insensitive=True
        )

    async def setup_hook(self):
        """Asynchronous setup hook for loading cogs and persistent views."""
        logger.info("Initializing bot cogs and modules...")

        # Dynamic Cog Loader
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    logger.info(f"Loaded extension: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load extension {cog_name}: {e}")

        # Register Persistent Giveaway Views from Database
        try:
            active_gwy = db.get_active_giveaways()
            for gwy in active_gwy:
                view = GiveawayView(gwy['message_id'], gwy['end_time'])
                self.add_view(view)
            logger.info(f"Registered {len(active_gwy)} persistent giveaway views.")
        except Exception as e:
            logger.error(f"Failed registering persistent views: {e}")

    async def on_ready(self):
        """Executed when the bot successfully connects to Discord."""
        banner = f"""
=====================================================
  Shop Management Bot is ONLINE!
  Logged in as: {self.user} (ID: {self.user.id})
  Prefix: {config.PREFIX}
  discord.py Version: {discord.__version__}
  Python Version: {sys.version.split()[0]}
=====================================================
"""
        print(banner)

        # Set presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config.PREFIX}help | Shop Management"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

        # Log startup to Discord audit channel
        await send_log(
            self,
            "Bot System Online",
            f"**Bot Tag:** `{self.user}`\n"
            f"**Prefix:** `{config.PREFIX}`\n"
            f"**Connected Guilds:** `{len(self.guilds)}`",
            color=config.COLOR_SUCCESS
        )

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global command error handler covering all failure modes cleanly."""
        # Unhandled command errors wrapped in CommandInvokeError
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        # Command Not Found (silently ignore or subtle alert)
        if isinstance(error, commands.CommandNotFound):
            return

        # Missing User Permissions
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions).replace("_", " ").title()
            await ctx.send(embed=error_embed("Permission Denied", f"You require the following permission(s) to run this command: `{perms}`"))
            return

        # Missing Bot Permissions
        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions).replace("_", " ").title()
            await ctx.send(embed=error_embed("Bot Permission Missing", f"I require the following permission(s) to execute this command: `{perms}`"))
            return

        # Missing Required Argument
        if isinstance(error, commands.MissingRequiredArgument):
            param = error.param.name
            await ctx.send(embed=error_embed("Missing Argument", f"Missing required parameter: `{param}`.\nUsage: `{config.PREFIX}help {ctx.command.name}`"))
            return

        # Bad / Invalid Argument
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=error_embed("Invalid Argument", f"Invalid argument provided: {error}.\nCheck command usage with `{config.PREFIX}help`"))
            return

        # Command Cooldown
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=error_embed("Command Cooldown", f"Please wait `{error.retry_after:.1f}s` before reusing this command."))
            return

        # Member / User / Channel / Role Not Found
        if isinstance(error, (commands.MemberNotFound, commands.UserNotFound, commands.ChannelNotFound, commands.RoleNotFound)):
            await ctx.send(embed=error_embed("Not Found", f"Specified target could not be found: {error}"))
            return

        # Catch-all unexpected runtime errors
        logger.error(f"Unhandled error in command {ctx.command}: {error}", exc_info=error)
        await ctx.send(embed=error_embed("Internal Error", "An unexpected error occurred while executing this command. The issue has been logged."))

        await send_log(
            self,
            "Command Error Alert",
            f"**Command:** `{ctx.message.content}`\n"
            f"**Author:** {ctx.author.mention} (`{ctx.author.id}`)\n"
            f"**Error:** ```py\n{error}\n```",
            color=config.COLOR_DANGER
        )


def main():
    if not config.TOKEN or config.TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        logger.critical("Bot token is not configured in config.py! Please provide a valid Discord bot token.")
        sys.exit(1)

    bot = ShopBot()
    try:
        bot.run(config.TOKEN)
    except discord.LoginFailure:
        logger.critical("Invalid bot token provided! Please check config.py.")
    except Exception as e:
        logger.critical(f"Fatal startup error: {e}")


if __name__ == "__main__":
    main()
