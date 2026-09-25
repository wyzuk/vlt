"""Helpers for sending every bot response as a Discord Components V2 message."""

from __future__ import annotations

from typing import Iterable, Optional

import discord

import config


def embed_text(embed: discord.Embed) -> str:
    """Render the useful parts of a legacy embed as Markdown for a TextDisplay."""
    parts: list[str] = []

    if embed.author and embed.author.name:
        parts.append(f"*{embed.author.name}*")
    if embed.title:
        title = f"## {embed.title}"
        if embed.url:
            title = f"## [{embed.title}]({embed.url})"
        parts.append(title)
    if embed.description:
        parts.append(embed.description)

    for field in embed.fields:
        parts.append(f"**{field.name}**\n{field.value}")

    if embed.image and embed.image.url:
        parts.append(f"[View image]({embed.image.url})")
    if embed.thumbnail and embed.thumbnail.url:
        parts.append(f"[Thumbnail]({embed.thumbnail.url})")
    if embed.timestamp:
        parts.append(f"-# <t:{int(embed.timestamp.timestamp())}:F>")
    if embed.footer and embed.footer.text:
        parts.append(f"-# {embed.footer.text}")

    return "\n\n".join(parts) or "\u200b"


def render_message(
    content: Optional[str] = None,
    embed: Optional[discord.Embed] = None,
    embeds: Optional[Iterable[discord.Embed]] = None,
) -> tuple[str, int]:
    parts = [content.strip()] if content and content.strip() else []
    if embed is not None:
        parts.append(embed_text(embed))
        color = embed.color.value if embed.color else config.COLOR_PRIMARY
    else:
        color = config.COLOR_PRIMARY
    if embeds:
        for item in embeds:
            parts.append(embed_text(item))
            if item.color:
                color = item.color.value
    return "\n\n".join(parts) or "\u200b", color


def _text_chunks(text: str, limit: int = 3900) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if current and len(current) + len(line) > limit:
            chunks.append(current)
            current = ""
        current += line
    if current or not chunks:
        chunks.append(current or "\u200b")
    return chunks


class V2LayoutView(discord.ui.LayoutView):
    """LayoutView with a colored Components V2 container for message text."""

    def __init__(self, content: str = "", *, accent_color: int = config.COLOR_PRIMARY, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self._accent_color = accent_color
        self._extra_content_containers = []
        self._content_container = discord.ui.Container(accent_color=accent_color)
        self.add_item(self._content_container)
        self.set_content(content)

    def set_content(self, content: str) -> None:
        self._text_content = content
        for container in self._extra_content_containers:
            self.remove_item(container)
        self._extra_content_containers.clear()
        self._content_container.clear_items()
        chunks = _text_chunks(content)
        for start in range(0, len(chunks), 10):
            group = chunks[start:start + 10]
            if start == 0:
                container = self._content_container
            else:
                container = discord.ui.Container(accent_color=self._accent_color)
                self.add_item(container)
                self._extra_content_containers.append(container)
            for chunk in group:
                container.add_item(discord.ui.TextDisplay(chunk))


def _make_view(content: Optional[str], embed: Optional[discord.Embed], embeds, *, accent_color=None):
    text, color = render_message(content, embed, embeds)
    return V2LayoutView(text, accent_color=accent_color or color)


async def send_v2(target, content: Optional[str] = None, *, embed=None, embeds=None, view=None, **kwargs):
    """Send a channel, context, DM, or interaction response using Components V2."""
    if view is None:
        view = _make_view(content, embed, embeds)
    elif isinstance(view, discord.ui.LayoutView):
        if content is not None or embed is not None or embeds is not None:
            text, color = render_message(content, embed, embeds)
            if hasattr(view, "set_content"):
                view.set_content(text)
            else:
                raise TypeError("A Components V2 LayoutView with text must provide set_content().")
    else:
        raise TypeError("Components V2 messages require discord.ui.LayoutView.")

    if isinstance(target, discord.Interaction):
        if target.response.is_done():
            return await target.followup.send(view=view, **kwargs)
        return await target.response.send_message(view=view, **kwargs)
    return await target.send(view=view, **kwargs)


async def edit_v2(target, *, content: Optional[str] = None, embed=None, embeds=None, view=None, **kwargs):
    """Edit a message into a Components V2 layout, clearing legacy message fields."""
    if view is None:
        view = _make_view(content, embed, embeds)
    elif isinstance(view, discord.ui.LayoutView):
        if content is not None or embed is not None or embeds is not None:
            text, color = render_message(content, embed, embeds)
            if hasattr(view, "set_content"):
                view.set_content(text)
            else:
                raise TypeError("A Components V2 LayoutView with text must provide set_content().")
    else:
        raise TypeError("Components V2 messages require discord.ui.LayoutView.")

    kwargs.setdefault("content", None)
    kwargs.setdefault("embeds", [])
    kwargs.setdefault("attachments", [])
    return await target.edit(view=view, **kwargs)


async def edit_interaction_v2(interaction: discord.Interaction, *, content=None, embed=None, embeds=None, view=None):
    """Acknowledge a component interaction by editing its message with V2 components."""
    if view is None:
        view = _make_view(content, embed, embeds)
    elif content is not None or embed is not None or embeds is not None:
        text, color = render_message(content, embed, embeds)
        if not hasattr(view, "set_content"):
            raise TypeError("A Components V2 LayoutView with text must provide set_content().")
        view.set_content(text)
    return await interaction.response.edit_message(content=None, embeds=[], view=view)
