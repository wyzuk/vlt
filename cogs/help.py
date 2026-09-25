"""Paged Components V2 help for the bot's prefix commands."""

import discord
from discord.ext import commands

import config
from utils.components_v2 import V2LayoutView, edit_interaction_v2, send_v2


COMMANDS = [
    (config.EMOJI_BAN, "ban <@user> [reason]", "Ban a member."),
    (config.EMOJI_UNBAN, "unban <user_id> [reason]", "Unban a user by ID."),
    (config.EMOJI_KICK, "kick <@user> [reason]", "Kick a member."),
    (config.EMOJI_TIMEOUT, "timeout <@user> <duration> [reason]", "Timeout for `30s`, `5m`, `2h`, or `1d`."),
    (config.EMOJI_UNTIMEOUT, "untimeout <@user> [reason]", "Remove a member's timeout."),
    (config.EMOJI_MUTE, "mute <@user> [reason]", "Mute a member."),
    (config.EMOJI_MUTE, "unmute <@user> [reason]", "Unmute a member."),
    (config.EMOJI_WARNING, "warn <@user> <reason>", "Issue a warning."),
    (config.EMOJI_WARNING, "warnings <@user>", "Show warning history."),
    (config.EMOJI_MODERATION, "clear <amount>", "Delete up to 1,000 messages. Alias: `+purge`."),
    (config.EMOJI_LOCK, "lock [#channel] [reason]", "Lock a channel."),
    (config.EMOJI_UNLOCK, "unlock [#channel] [reason]", "Unlock a channel."),
    (config.EMOJI_MODERATION, "slowmode <seconds>", "Set channel slowmode; use `0` to disable."),
    (config.EMOJI_NICKNAME, "nick <@user> [new_nickname]", "Change or reset a nickname."),
    (config.EMOJI_ROLES, "role <@user> <role>", "Give a member a role."),
    (config.EMOJI_ROLES, "removerole <@user> <role>", "Remove a member's role."),
    (config.EMOJI_ANNOUNCEMENT, "announce <#channel> <message>", "Post an announcement in Components V2."),
    (config.EMOJI_SAY, "say <message>", "Send a Components V2 message as the bot."),
    (config.EMOJI_EMBED, "embed <title> | <description> | [hex]", "Create a custom Components V2 message."),
    (config.EMOJI_DEVELOPER, "vch <product name> (<price>)", "Send `+rep <your ID> <product> | <price>`. Example: `+vch Minecraft host (700BDT)`."),
    (config.EMOJI_UTILITY, "rename <channel new name>", "Rename the channel where you use this command."),
    (config.EMOJI_BOT, "status <activity> <activity name>", "Set a bot activity; `+status hii` sets a custom status. Owner only."),
    (config.EMOJI_INFORMATION, "userinfo [@user]", "Show account, server, and role information."),
    (config.EMOJI_INFORMATION, "serverinfo", "Show server details and counts."),
    (config.EMOJI_INFORMATION, "avatar [@user]", "Show a user's avatar."),
    (config.EMOJI_INFORMATION, "channelinfo [#channel]", "Show channel details."),
    (config.EMOJI_ROLES, "roleinfo <role>", "Show role details."),
    (config.EMOJI_BOT, "botinfo", "Show bot version, uptime, and statistics."),
    (config.EMOJI_INFORMATION, "ping", "Show bot latency."),
    (config.EMOJI_BOT, "uptime", "Show how long the bot has been online."),
    (config.EMOJI_BOT, "invite", "Get the bot invite link."),
    (config.EMOJI_INFORMATION, "v2test", "Check the Components V2 layout, button, and select."),
    (config.EMOJI_BOT, "dashboard", "Open the interactive bot status dashboard."),
    (config.EMOJI_BOT, "gwy <time> <winners> <prize> [forced_user]", "Create a giveaway. Manage Server permission required."),
    (config.EMOJI_BOT, "reroll <message_id>", "Choose a new giveaway winner."),
    (config.EMOJI_BOT, "gend <message_id>", "End an active giveaway."),
    (config.EMOJI_BOT, "gcancel <message_id>", "Cancel an active giveaway."),
    (config.EMOJI_BOT, "glist", "List active giveaways."),
    (config.EMOJI_DEVELOPER, "ghlp", "Show giveaway commands; Manage Server permission required."),
    (config.EMOJI_BOT, "help", "Show every command, 10 per page."),
]

PAGE_SIZE = 10
HIDDEN_FROM_HELP = {"hide", "unhide"}


def command_entries(bot: commands.Bot):
    """Include any newly registered commands while keeping private hide controls out."""
    entries = list(COMMANDS)
    listed_names = {entry[1].split(maxsplit=1)[0] for entry in entries}
    for command in sorted(bot.commands, key=lambda item: item.name.casefold()):
        if command.name in HIDDEN_FROM_HELP or command.name in listed_names:
            continue
        entries.append((config.EMOJI_BOT, command.name + (f" {command.signature}" if command.signature else ""), command.short_doc or "Bot command."))
    return entries


def help_page_text(entries, page: int) -> str:
    page_count = max(1, (len(entries) + PAGE_SIZE - 1) // PAGE_SIZE)
    start = page * PAGE_SIZE
    lines = [
        f"# {config.EMOJI_BOT} Shop Management Bot",
        f"**Prefix:** `{config.PREFIX}`  ·  **Page {page + 1} of {page_count}**  ·  10 commands per page",
        "",
    ]
    for emoji, syntax, description in entries[start:start + PAGE_SIZE]:
        lines.extend((f"### {emoji} `{config.PREFIX}{syntax}`", description, ""))
    return "\n".join(lines).rstrip()


def help_text() -> str:
    """Return the first help page for use inside the V2 demo panel."""
    return help_page_text(COMMANDS, 0)


class HelpPageButton(discord.ui.Button):
    def __init__(self, direction: int):
        self.direction = direction
        if direction < 0:
            super().__init__(label="◀ Previous", style=discord.ButtonStyle.secondary, custom_id="help:previous")
        else:
            super().__init__(label="Next ▶", style=discord.ButtonStyle.primary, custom_id="help:next")

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, HelpView):
            return
        view.page = max(0, min(view.page + self.direction, view.page_count - 1))
        view.refresh()
        await edit_interaction_v2(interaction, view=view)


class HelpView(V2LayoutView):
    def __init__(self, bot: commands.Bot, owner_id: int):
        self.entries = command_entries(bot)
        self.page = 0
        self.owner_id = owner_id
        self.bound_message = None
        self.page_count = max(1, (len(self.entries) + PAGE_SIZE - 1) // PAGE_SIZE)
        super().__init__(help_page_text(self.entries, self.page), accent_color=config.COLOR_PRIMARY, timeout=600)

        row = discord.ui.ActionRow()
        self.previous_button = HelpPageButton(-1)
        self.next_button = HelpPageButton(1)
        row.add_item(self.previous_button)
        row.add_item(self.next_button)
        self.add_item(row)
        self.refresh()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # The help pages are public, so anyone can use the page controls.
        return True

    def refresh(self) -> None:
        self.set_content(help_page_text(self.entries, self.page))
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.page_count - 1

    async def on_timeout(self) -> None:
        self.previous_button.disabled = True
        self.next_button.disabled = True
        if self.bound_message:
            try:
                await self.bound_message.edit(view=self)
            except discord.HTTPException:
                pass


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        """Show every command in larger text, with 10 commands per page."""
        view = HelpView(self.bot, ctx.author.id)
        view.bound_message = await send_v2(ctx, view=view)

    @commands.command(name="ghlp")
    @commands.has_permissions(manage_guild=True)
    async def giveaway_help(self, ctx: commands.Context):
        """Show the admin-only giveaway commands."""
        text = "## Giveaway Management\n" + "\n".join(
            f"### {config.EMOJI_BOT} `{config.PREFIX}{syntax}`\n{description}"
            for syntax, description in [
                ("gwy <time> <winners> <prize> [forced_user]", "Create a giveaway."),
                ("reroll <message_id>", "Choose a new winner."),
                ("gend <message_id>", "End an active giveaway."),
                ("gcancel <message_id>", "Cancel an active giveaway."),
                ("glist", "List active giveaways."),
            ]
        )
        await send_v2(ctx, text)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
