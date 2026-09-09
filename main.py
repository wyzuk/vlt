"""
Discord Shop Bot - Main Entry Point.

Production-ready, modular architecture supporting Python 3.13+ and discord.py 2.x.
Includes dynamic cog auto-loading, global error handling, persistent UI views,
and modern dark-themed embeds.
"""

import discord
from discord.ext import commands
import os
import sys
import config

from utils.embeds import error_embed
from utils.logger import send_log, logger
from database.db_manager import db
from utils.ui_components import GiveawayView
from keep_alive import keep_alive


class ShopBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        intents.guilds = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(config.PREFIX),
            intents=intents,
            help_command=None,
            case_insensitive=True
        )

    async def setup_hook(self):
        """Asynchronous setup hook for loading cogs and persistent views."""
        logger.info("Initializing bot cogs and modules...")

        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")

        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"cogs.{filename[:-3]}"

                try:
                    await self.load_extension(cog_name)
                    logger.info(f"Loaded extension: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load extension {cog_name}: {e}")

        try:
            active_giveaways = db.get_active_giveaways()

            for giveaway in active_giveaways:
                view = GiveawayView(
                    giveaway["message_id"],
                    giveaway["end_time"]
                )
                self.add_view(view)

            logger.info(
                f"Registered {len(active_giveaways)} persistent giveaway views."
            )

        except Exception as e:
            logger.error(f"Failed registering persistent views: {e}")

    async def on_ready(self):
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

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config.PREFIX}help | Shop Management"
        )

        await self.change_presence(
            status=discord.Status.online,
            activity=activity
        )

        await send_log(
            self,
            "Bot System Online",
            f"**Bot Tag:** `{self.user}`\n"
            f"**Prefix:** `{config.PREFIX}`\n"
            f"**Connected Guilds:** `{len(self.guilds)}`",
            color=config.COLOR_SUCCESS
        )

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions).replace("_", " ").title()

            await ctx.send(
                embed=error_embed(
                    "Permission Denied",
                    f"You require: `{perms}`"
                )
            )
            return

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions).replace("_", " ").title()

            await ctx.send(
                embed=error_embed(
                    "Bot Permission Missing",
                    f"I require: `{perms}`"
                )
            )
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                embed=error_embed(
                    "Missing Argument",
                    f"Missing parameter: `{error.param.name}`"
                )
            )
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=error_embed(
                    "Invalid Argument",
                    str(error)
                )
            )
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                embed=error_embed(
                    "Cooldown",
                    f"Please wait `{error.retry_after:.1f}s`."
                )
            )
            return

        logger.error(
            f"Unhandled error in command {ctx.command}",
            exc_info=error
        )

        await ctx.send(
            embed=error_embed(
                "Internal Error",
                "An unexpected error occurred."
            )
        )

        await send_log(
            self,
            "Command Error Alert",
            f"**Command:** `{ctx.message.content}`\n"
            f"**Author:** {ctx.author.mention}\n"
            f"**Error:** ```py\n{error}\n```",
            color=config.COLOR_DANGER
        )


def main():
    if not config.TOKEN:
        logger.critical(
            "Bot token is missing! Please set TOKEN in your .env file."
        )
        sys.exit(1)

    keep_alive()

    bot = ShopBot()

    try:
        bot.run(config.TOKEN)

    except discord.LoginFailure:
        logger.critical("Invalid Discord bot token.")

    except Exception as e:
        logger.critical(f"Fatal startup error: {e}")


if __name__ == "__main__":
    main()
