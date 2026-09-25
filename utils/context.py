"""Command context that turns command replies into Components V2 messages."""

from __future__ import annotations

import discord
from discord.ext import commands

from utils.components_v2 import V2LayoutView, render_message


class ComponentsV2Context(commands.Context):
    """Route ordinary prefix-command replies through the Components V2 layout."""

    async def send(self, content=None, **kwargs):
        embed = kwargs.pop("embed", None)
        embeds = kwargs.pop("embeds", None)
        view = kwargs.pop("view", None)

        # A classic View cannot be included in a Components V2 message. All
        # interactive bot panels in this project use LayoutView instead.
        if view is not None and not isinstance(view, discord.ui.LayoutView):
            raise TypeError("Command replies must use a discord.ui.LayoutView.")

        if view is None:
            text, color = render_message(content, embed, embeds)
            view = V2LayoutView(text, accent_color=color)
        elif content is not None or embed is not None or embeds is not None:
            text, _ = render_message(content, embed, embeds)
            if not hasattr(view, "set_content"):
                raise TypeError("A Components V2 LayoutView with text must provide set_content().")
            view.set_content(text)

        kwargs["view"] = view
        return await super().send(**kwargs)
