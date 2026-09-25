"""Small, real Components V2 examples for diagnostics and bot status."""

from __future__ import annotations

import discord
from discord.ext import commands

import config
from cogs.help import help_text
from utils.components_v2 import V2LayoutView, edit_interaction_v2, send_v2
from utils.logger import logger


class OwnerView(V2LayoutView):
    """Owner-restricted V2 view with timeout and interaction error handling."""

    def __init__(self, owner_id: int, content: str, *, accent_color: int = config.COLOR_PRIMARY):
        super().__init__(content, accent_color=accent_color, timeout=180)
        self.owner_id = owner_id
        self.bound_message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await send_v2(
                interaction,
                f"{config.EMOJI_WARNING} This panel belongs to someone else.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.walk_children():
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True
        if self.bound_message:
            try:
                await self.bound_message.edit(view=self)
            except discord.NotFound:
                logger.info("A timed-out V2 panel was already deleted.")
            except discord.HTTPException as error:
                logger.warning(f"Could not disable timed-out V2 panel: {error}")

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item, /) -> None:
        logger.error(
            f"Components V2 interaction failed for {item!r}",
            exc_info=(type(error), error, error.__traceback__),
        )
        try:
            await send_v2(
                interaction,
                f"{config.EMOJI_WARNING} That interaction failed. Please run the command again.",
                ephemeral=True,
            )
        except discord.HTTPException:
            logger.warning("Could not send a Components V2 interaction error response.")


class V2TestButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Test Button", style=discord.ButtonStyle.primary, custom_id="v2demo:test")

    async def callback(self, interaction: discord.Interaction) -> None:
        await send_v2(interaction, f"{config.EMOJI_BOT} The Components V2 button responded successfully.", ephemeral=True)


class V2TestSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Information", value="information"),
            discord.SelectOption(label="Settings", value="settings"),
            discord.SelectOption(label="Help", value="help"),
            discord.SelectOption(label="About", value="about"),
        ]
        super().__init__(
            placeholder="Choose an option...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="v2demo:select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, V2TestView):
            await send_v2(interaction, f"{config.EMOJI_WARNING} This panel is no longer available.", ephemeral=True)
            return

        content = {
            "information": (
                f"## {config.EMOJI_INFORMATION} Components V2 Information\n"
                "This panel uses a V2 Container, Text Display, Section, Thumbnail, Media Gallery, "
                "Separator, Action Row, Button, and Select menu."
            ),
            "settings": f"## {config.EMOJI_UTILITY} Settings\nThe current command prefix is `{config.PREFIX}`.",
            "help": help_text(),
            "about": f"## {config.EMOJI_BOT} About\nPowered by `discord.py {discord.__version__}`.",
        }[self.values[0]]
        view.set_content(content)
        await edit_interaction_v2(interaction, view=view)


class V2TestView(OwnerView):
    def __init__(self, owner: discord.abc.User, bot_user: discord.ClientUser):
        super().__init__(
            owner.id,
            "## Components V2\n"
            "This message uses Discord's Components V2 layout and message flag.\n\n"
            "**Included:** containers, text displays, profile sections, image gallery, button, and select menu.\n\n"
            "Use the button or choose an option below.",
            accent_color=config.COLOR_INFO,
        )

        profile = discord.ui.Section(
            discord.ui.TextDisplay(f"**{owner.display_name}**\nComponents V2 test requester"),
            accessory=discord.ui.Thumbnail(owner.display_avatar.url, description=f"{owner.display_name}'s avatar"),
        )
        self.add_item(profile)
        self.add_item(discord.ui.Separator())

        gallery = discord.ui.MediaGallery(
            discord.MediaGalleryItem(media=owner.display_avatar.url, description="Command author's avatar"),
            discord.MediaGalleryItem(media=bot_user.display_avatar.url, description="Bot avatar"),
        )
        self.add_item(gallery)

        button_row = discord.ui.ActionRow()
        button_row.add_item(V2TestButton())
        self.add_item(button_row)

        select_row = discord.ui.ActionRow()
        select_row.add_item(V2TestSelect())
        self.add_item(select_row)


class DashboardButton(discord.ui.Button):
    def __init__(self, action: str, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=f"v2dashboard:{action}")
        self.action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, DashboardView):
            await send_v2(interaction, f"{config.EMOJI_WARNING} This dashboard is no longer available.", ephemeral=True)
            return

        if self.action == "statistics":
            await edit_interaction_v2(interaction, content=view.statistics_text(), view=view)
        elif self.action == "settings":
            await send_v2(
                interaction,
                f"## {config.EMOJI_UTILITY} Settings\n"
                f"**Prefix:** `{config.PREFIX}`\n"
                f"**Audit log channel:** `{config.LOG_CHANNEL_ID or 'Not configured'}`",
                ephemeral=True,
            )
        else:
            await send_v2(interaction, help_text(), ephemeral=True)


class DashboardView(OwnerView):
    def __init__(self, bot: commands.Bot, owner_id: int):
        self.bot = bot
        super().__init__(owner_id, self.statistics_text(), accent_color=config.COLOR_PRIMARY)
        row = discord.ui.ActionRow()
        row.add_item(DashboardButton("statistics", "Statistics"))
        row.add_item(DashboardButton("settings", "Settings"))
        row.add_item(DashboardButton("help", "Help"))
        self.add_item(row)

    def statistics_text(self) -> str:
        members = sum(guild.member_count or 0 for guild in self.bot.guilds)
        latency = round(self.bot.latency * 1000)
        return (
            f"## {config.EMOJI_BOT} Bot Dashboard\n"
            "**Status:** Online\n\n"
            f"**Servers:** {len(self.bot.guilds)}\n"
            f"**Members:** {members:,}\n"
            f"**Ping:** {latency} ms\n\n"
            "Choose a button to view statistics, settings, or help."
        )


class V2Demo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="v2test")
    async def v2test(self, ctx: commands.Context) -> None:
        """Send a Components V2 message with working button and select controls."""
        if not self.bot.user:
            await send_v2(ctx, f"{config.EMOJI_WARNING} The bot profile is not ready yet.")
            return
        view = V2TestView(ctx.author, self.bot.user)
        message = await send_v2(ctx, view=view)
        view.bound_message = message

    @commands.command(name="dashboard")
    async def dashboard(self, ctx: commands.Context) -> None:
        """Show a reusable Components V2 status dashboard."""
        view = DashboardView(self.bot, ctx.author.id)
        message = await send_v2(ctx, view=view)
        view.bound_message = message


async def setup(bot: commands.Bot):
    await bot.add_cog(V2Demo(bot))
