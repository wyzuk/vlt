"""
Discord Components V2 UI module.
Provides modern interactive Views, Buttons, Dropdown Select Menus,
Paginators, Help Menu navigation, and Giveaway interaction components.
"""

import discord
import time
from typing import List, Dict, Any, Optional
import config
from utils.embeds import create_embed, info_embed
from database.db_manager import db


# ==========================================
# Giveaway Interaction Buttons (Components V2)
# ==========================================

class GiveawayView(discord.ui.View):
    """
    Components V2 View for active Giveaways.
    Buttons:
    1. 🎉 Join Giveaway (Performs entry toggle)
    2. 📊 Entries (Shows entry count & list in ephemeral msg)
    3. ⏳ Time Left (Shows exact countdown timestamp in ephemeral msg)
    """

    def __init__(self, message_id: int, end_timestamp: float):
        super().__init__(timeout=None)  # Persistent view
        self.message_id = message_id
        self.end_timestamp = end_timestamp

    @discord.ui.button(
        label="Join Giveaway",
        style=discord.ButtonStyle.primary,
        emoji=config.EMOJI_GIVEAWAY,
        custom_id="gwy_join_button"
    )
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway = db.get_giveaway(self.message_id)
        if not giveaway or giveaway.get('ended', 0) == 1:
            await interaction.response.send_message(
                f"{config.EMOJI_ERROR} This giveaway has already ended!", ephemeral=True
            )
            return

        user_id = interaction.user.id
        # Toggle entry logic
        if user_id in giveaway['entries']:
            db.remove_giveaway_entry(self.message_id, user_id)
            updated_gwy = db.get_giveaway(self.message_id)
            count = len(updated_gwy['entries']) if updated_gwy else 0
            await interaction.response.send_message(
                f"{config.EMOJI_WARNING} You left the giveaway! Current total entries: **{count}**",
                ephemeral=True
            )
        else:
            db.add_giveaway_entry(self.message_id, user_id)
            updated_gwy = db.get_giveaway(self.message_id)
            count = len(updated_gwy['entries']) if updated_gwy else 0
            await interaction.response.send_message(
                f"{config.EMOJI_SUCCESS} You entered the giveaway! Best of luck! 🎉 Total entries: **{count}**",
                ephemeral=True
            )

        # Update the message embed with updated entry count
        try:
            embed = interaction.message.embeds[0]
            for idx, field in enumerate(embed.fields):
                if field.name == "Entries":
                    embed.set_field_at(idx, name="Entries", value=f"**{len(updated_gwy['entries'])}** participants", inline=True)
                    break
            await interaction.message.edit(embed=embed)
        except Exception:
            pass

    @discord.ui.button(
        label="Entries",
        style=discord.ButtonStyle.secondary,
        emoji=config.EMOJI_ENTRIES,
        custom_id="gwy_entries_button"
    )
    async def entries_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway = db.get_giveaway(self.message_id)
        if not giveaway:
            await interaction.response.send_message(f"{config.EMOJI_ERROR} Giveaway not found.", ephemeral=True)
            return

        entries = giveaway['entries']
        count = len(entries)
        embed = info_embed(
            title="Giveaway Statistics",
            description=f"**Prize:** {giveaway['prize']}\n**Total Entries:** `{count}`\n**Status:** {'Ended' if giveaway['ended'] else 'Active'}"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Time Left",
        style=discord.ButtonStyle.secondary,
        emoji=config.EMOJI_TIME,
        custom_id="gwy_time_button"
    )
    async def time_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        remaining = int(self.end_timestamp - time.time())
        if remaining <= 0:
            await interaction.response.send_message(f"{config.EMOJI_TIME} This giveaway has ended or is ending right now!", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"{config.EMOJI_TIME} Giveaway ends <t:{int(self.end_timestamp)}:R> (<t:{int(self.end_timestamp)}:F>).",
                ephemeral=True
            )


# ==========================================
# Help Command Category Navigation (Components V2)
# ==========================================

class HelpCategorySelect(discord.ui.Select):
    """Dropdown Select Menu for choosing Public Help Categories."""

    def __init__(self, categories_data: Dict[str, Dict[str, Any]]):
        options = []
        if "Moderation" in categories_data:
            options.append(discord.SelectOption(
                label="Moderation",
                description="Ban, kick, timeout, clear, etc.",
                emoji=config.EMOJI_MOD,
                value="Moderation"
            ))
        if "Utility" in categories_data:
            options.append(discord.SelectOption(
                label="Utility",
                description="Say, embed, announce commands.",
                emoji="⚙️",
                value="Utility"
            ))
        if "Management" in categories_data:
            options.append(discord.SelectOption(
                label="Management",
                description="Channel locks, slowmode, nick, roles.",
                emoji=config.EMOJI_SHIELD,
                value="Management"
            ))
        if "Information" in categories_data:
            options.append(discord.SelectOption(
                label="Information",
                description="Serverinfo, userinfo, ping, uptime.",
                emoji="ℹ️",
                value="Information"
            ))

        super().__init__(placeholder="Select a category to view commands...", min_values=1, max_values=1, options=options)
        self.categories_data = categories_data

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        data = self.categories_data.get(category, {})

        embed = create_embed(
            title=f"{data.get('emoji', '📌')} {category} Commands",
            description=data.get('description', 'Command list for this category.'),
            color=config.COLOR_PRIMARY
        )

        for cmd, info in data.get('commands', {}).items():
            embed.add_field(name=f"`{config.PREFIX}{cmd}`", value=info, inline=False)

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpNavView(discord.ui.View):
    """
    Components V2 Public Help View containing Category Buttons AND Select Dropdown.
    Excludes private Giveaway system.
    """

    def __init__(self, categories_data: Dict[str, Dict[str, Any]], author_id: int):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.categories_data = categories_data
        self.add_item(HelpCategorySelect(categories_data))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(f"{config.EMOJI_ERROR} Only the command author can interact with this help menu.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.primary, emoji=config.EMOJI_MOD, row=1)
    async def btn_mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_category(interaction, "Moderation")

    @discord.ui.button(label="Utility", style=discord.ButtonStyle.primary, emoji="⚙️", row=1)
    async def btn_util(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_category(interaction, "Utility")

    @discord.ui.button(label="Management", style=discord.ButtonStyle.secondary, emoji=config.EMOJI_SHIELD, row=1)
    async def btn_mgmt(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_category(interaction, "Management")

    @discord.ui.button(label="Information", style=discord.ButtonStyle.secondary, emoji="ℹ️", row=1)
    async def btn_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_category(interaction, "Information")

    async def _show_category(self, interaction: discord.Interaction, category: str):
        data = self.categories_data.get(category, {})
        embed = create_embed(
            title=f"{data.get('emoji', '📌')} {category} Commands",
            description=data.get('description', 'Command list for this category.'),
            color=config.COLOR_PRIMARY
        )

        for cmd, info in data.get('commands', {}).items():
            embed.add_field(name=f"`{config.PREFIX}{cmd}`", value=info, inline=False)

        await interaction.response.edit_message(embed=embed, view=self)


# ==========================================
# Generic List Paginator (Components V2)
# ==========================================

class PaginatorView(discord.ui.View):
    """Components V2 Pagination for lists."""

    def __init__(self, pages: List[discord.Embed], author_id: int):
        super().__init__(timeout=120)
        self.pages = pages
        self.author_id = author_id
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(f"{config.EMOJI_ERROR} You cannot interact with this menu.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
