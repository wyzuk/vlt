"""Interactive Components V2 views used by giveaways."""

import time

import discord

import config
from database.db_manager import db
from utils.components_v2 import V2LayoutView, edit_interaction_v2, send_v2


class GiveawayView(V2LayoutView):
    """Persistent Components V2 message layout with giveaway action buttons."""

    def __init__(self, message_id: int, end_timestamp: float, content: str = "", entries_count: int = 0):
        super().__init__(content, timeout=None)
        self.message_id = message_id
        self.end_timestamp = end_timestamp
        self.entries_count = entries_count
        row = discord.ui.ActionRow()
        row.add_item(GiveawayJoinButton(message_id))
        row.add_item(GiveawayEntriesButton(message_id))
        row.add_item(GiveawayTimeButton(message_id))
        self.add_item(row)

    def update_entries(self, count: int) -> None:
        self.entries_count = count
        if "**Entries:**" in self._text_content:
            import re
            self.set_content(re.sub(r"\*\*Entries:\*\* \d+", f"**Entries:** {count}", self._text_content))

    def disable_buttons(self) -> None:
        for item in self.walk_children():
            if isinstance(item, discord.ui.Button):
                item.disabled = True


class GiveawayJoinButton(discord.ui.Button):
    def __init__(self, message_id: int):
        super().__init__(
            label="Join",
            style=discord.ButtonStyle.primary,
            emoji=config.EMOJI_BOT,
            custom_id=f"gwy:join:{message_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        giveaway = db.get_giveaway(self.message_id)
        if not giveaway or giveaway.get("ended", 0) == 1:
            await send_v2(interaction, f"{config.EMOJI_WARNING} This giveaway has ended.", ephemeral=True)
            return

        user_id = interaction.user.id
        if user_id in giveaway["entries"]:
            db.remove_giveaway_entry(self.message_id, user_id)
            confirmation = f"{config.EMOJI_WARNING} You left the giveaway."
        else:
            db.add_giveaway_entry(self.message_id, user_id)
            confirmation = f"{config.EMOJI_BOT} You entered the giveaway. Good luck!"

        updated = db.get_giveaway(self.message_id)
        count = len(updated["entries"]) if updated else 0
        view = self.view
        if isinstance(view, GiveawayView):
            view.update_entries(count)
            await edit_interaction_v2(interaction, view=view)
            await send_v2(interaction, f"{confirmation} Entries: **{count}**", ephemeral=True)
        else:
            await send_v2(interaction, f"{confirmation} Entries: **{count}**", ephemeral=True)


class GiveawayEntriesButton(discord.ui.Button):
    def __init__(self, message_id: int):
        super().__init__(
            label="Entries",
            style=discord.ButtonStyle.secondary,
            emoji=config.EMOJI_INFORMATION,
            custom_id=f"gwy:entries:{message_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        giveaway = db.get_giveaway(self.message_id)
        if not giveaway:
            await send_v2(interaction, f"{config.EMOJI_WARNING} Giveaway not found.", ephemeral=True)
            return
        await send_v2(
            interaction,
            f"## {config.EMOJI_INFORMATION} Giveaway Statistics\n"
            f"**Prize:** {giveaway['prize']}\n"
            f"**Entries:** {len(giveaway['entries'])}\n"
            f"**Status:** {'Ended' if giveaway['ended'] else 'Active'}",
            ephemeral=True,
        )


class GiveawayTimeButton(discord.ui.Button):
    def __init__(self, message_id: int):
        super().__init__(
            label="Time left",
            style=discord.ButtonStyle.secondary,
            emoji=config.EMOJI_TIMEOUT,
            custom_id=f"gwy:time:{message_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        giveaway = db.get_giveaway(self.message_id)
        view = self.view
        end_timestamp = view.end_timestamp if isinstance(view, GiveawayView) else time.time()
        if not giveaway or giveaway.get("ended", 0) == 1 or end_timestamp <= time.time():
            message = f"{config.EMOJI_TIMEOUT} This giveaway has ended or is ending now."
        else:
            message = (
                f"{config.EMOJI_TIMEOUT} Ends <t:{int(end_timestamp)}:R> "
                f"(<t:{int(end_timestamp)}:F>)."
            )
        await send_v2(interaction, message, ephemeral=True)
