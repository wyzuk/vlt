"""
Giveaway System Cog.

Provides giveaway creation, management, timer tasks, reaction/button sync,
and winner selection (with support for forced winners).

Commands (Admin / Manage Guild only):
- +gwy <time> <winner_count> <item_name> [forced_user_id]
- +reroll <message_id>
- +gend <message_id>
- +gcancel <message_id>
- +glist
"""

import discord
from discord.ext import commands, tasks
import asyncio
import random
import time
from typing import Optional

import config
from utils.embeds import create_embed, success_embed, error_embed, info_embed
from utils.time_parser import parse_duration, format_duration
from utils.ui_components import GiveawayView
from utils.logger import send_log, logger
from database.db_manager import db


class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    # --- BACKGROUND TIMER TASK ---
    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        """Check database every 10 seconds for expired active giveaways."""
        await self.bot.wait_until_ready()
        try:
            active_giveaways = db.get_active_giveaways()
            now = time.time()

            for gwy in active_giveaways:
                if now >= gwy['end_time']:
                    await self._finish_giveaway(gwy)
        except Exception as e:
            logger.error(f"Error in giveaway background task loop: {e}")

    async def _finish_giveaway(self, gwy: dict):
        """Finalize a giveaway, pick winners, update embed, and notify channel."""
        message_id = gwy['message_id']
        channel_id = gwy['channel_id']
        guild_id = gwy['guild_id']
        prize = gwy['prize']
        winner_count = gwy['winner_count']
        forced_user_id = gwy.get('forced_user_id')
        entries = gwy['entries']

        db.end_giveaway(message_id)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        try:
            msg = await channel.fetch_message(message_id)
        except Exception:
            logger.warning(f"Could not fetch message for giveaway {message_id}")
            return

        # Synchronize reactions if any users reacted with 🎉 directly
        try:
            for reaction in msg.reactions:
                if str(reaction.emoji) == config.EMOJI_GIVEAWAY:
                    async for user in reaction.users():
                        if not user.bot and user.id not in entries:
                            entries.append(user.id)
                            db.add_giveaway_entry(message_id, user.id)
        except Exception:
            pass

        # Select Winner(s)
        winners = []
        if forced_user_id:
            forced_member = guild.get_member(forced_user_id) or await self.bot.fetch_user(forced_user_id)
            if forced_member:
                winners.append(forced_member)

        # Fill remaining winner slots randomly if needed
        remaining_slots = winner_count - len(winners)
        if remaining_slots > 0 and entries:
            # Filter out forced winner if already added
            eligible = [uid for uid in entries if not (forced_user_id and uid == forced_user_id)]
            random.shuffle(eligible)
            for uid in eligible[:remaining_slots]:
                member = guild.get_member(uid)
                if not member:
                    try:
                        member = await self.bot.fetch_user(uid)
                    except Exception:
                        pass
                if member:
                    winners.append(member)

        # Update Embed
        embed = msg.embeds[0] if msg.embeds else create_embed(title=f"Giveaway Ended: {prize}")
        embed.color = config.COLOR_DARK
        embed.set_field_at(4, name="Status", value="**ENDED**", inline=True)

        if winners:
            winner_mentions = ", ".join([w.mention for w in winners])
            embed.description = f"**Winner(s):** {winner_mentions}\n**Prize:** `{prize}`"

            # Disable buttons
            view = GiveawayView(message_id, gwy['end_time'])
            for child in view.children:
                child.disabled = True

            await msg.edit(embed=embed, view=view)

            win_embed = create_embed(
                title=f"{config.EMOJI_GIVEAWAY} Giveaway Winner(s) Announced!",
                description=f"Congratulations {winner_mentions}! You won **{prize}**!\n[Jump to Giveaway]({msg.jump_url})",
                color=config.COLOR_SUCCESS
            )
            await channel.send(content=winner_mentions, embed=win_embed)

            await send_log(
                self.bot, "Giveaway Ended",
                f"**Prize:** {prize}\n**Winners:** {winner_mentions}\n**Channel:** {channel.mention}",
                color=config.COLOR_SUCCESS
            )
        else:
            embed.description = f"**Giveaway Cancelled**\nNo valid entries participated in this giveaway."
            view = GiveawayView(message_id, gwy['end_time'])
            for child in view.children:
                child.disabled = True

            await msg.edit(embed=embed, view=view)
            cancel_embed = error_embed(
                "Giveaway Cancelled",
                f"The giveaway for **{prize}** was cancelled due to lack of participants.\n[Jump to Giveaway]({msg.jump_url})"
            )
            await channel.send(embed=cancel_embed)

    # --- +GWY COMMAND ---
    @commands.command(name="gwy")
    @commands.has_permissions(manage_guild=True)
    async def create_giveaway(
        self,
        ctx: commands.Context,
        time_str: str,
        winner_count: int,
        prize: str,
        forced_user: Optional[discord.User | discord.Member] = None
    ):
        """
        Create a new giveaway.
        Syntax: +gwy <time> <winner_count> <prize> [forced_user_id]
        Example: +gwy 2h 1 Discord_Nitro
        """
        # Delete original command invocation immediately for complete privacy
        try:
            await ctx.message.delete()
        except Exception:
            pass

        seconds = parse_duration(time_str)
        if not seconds or seconds < 10:
            err_msg = await ctx.send(embed=error_embed("Invalid Duration", "Please specify a duration of at least 10 seconds (e.g. 5m, 2h, 1d)."))
            await err_msg.delete(delay=5)
            return

        if winner_count <= 0 or winner_count > 50:
            err_msg = await ctx.send(embed=error_embed("Invalid Winner Count", "Winner count must be between 1 and 50."))
            await err_msg.delete(delay=5)
            return

        end_timestamp = time.time() + seconds

        embed = create_embed(
            title=f"{config.EMOJI_GIVEAWAY} GIVEAWAY: {prize}",
            description=f"React with {config.EMOJI_GIVEAWAY} or click **Join Giveaway** below to enter!",
            color=config.COLOR_PRIMARY
        )

        embed.add_field(name="Prize", value=f"**{prize}**", inline=True)
        embed.add_field(name="Hosted By", value=ctx.author.mention, inline=True)
        embed.add_field(name="Ends", value=f"<t:{int(end_timestamp)}:R> (<t:{int(end_timestamp)}:F>)", inline=False)
        embed.add_field(name="Winner Count", value=f"**{winner_count}**", inline=True)
        embed.add_field(name="Entries", value="**0** participants", inline=True)
        embed.add_field(name="Status", value="**ACTIVE**", inline=True)

        # Ping @everyone AND @here
        announce_content = "@everyone @here"

        try:
            msg = await ctx.send(content=announce_content, embed=embed)

            # Attach Components V2 Buttons
            view = GiveawayView(msg.id, end_timestamp)
            await msg.edit(view=view)

            # Automatically react with 🎉
            await msg.add_reaction(config.EMOJI_GIVEAWAY)

            # Save giveaway to database
            forced_id = forced_user.id if forced_user else None
            db.save_giveaway(
                message_id=msg.id,
                channel_id=ctx.channel.id,
                guild_id=ctx.guild.id,
                prize=prize,
                host_id=ctx.author.id,
                winner_count=winner_count,
                end_time=end_timestamp,
                forced_user_id=forced_id
            )

            await send_log(
                self.bot, "Giveaway Created",
                f"**Prize:** {prize}\n**Duration:** {format_duration(seconds)}\n**Host:** {ctx.author.mention}\n**Channel:** {ctx.channel.mention}",
                color=config.COLOR_PRIMARY, author=ctx.author
            )
        except Exception as e:
            err_msg = await ctx.send(embed=error_embed("Error", f"Failed to create giveaway: {e}"))
            await err_msg.delete(delay=5)

    # --- REACTION LISTENERS FOR EASY REACTION JOINING ---
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """User joined giveaway via reaction."""
        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) == config.EMOJI_GIVEAWAY:
            giveaway = db.get_giveaway(payload.message_id)
            if giveaway and giveaway['ended'] == 0:
                db.add_giveaway_entry(payload.message_id, payload.user_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """User removed reaction from giveaway."""
        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) == config.EMOJI_GIVEAWAY:
            giveaway = db.get_giveaway(payload.message_id)
            if giveaway and giveaway['ended'] == 0:
                db.remove_giveaway_entry(payload.message_id, payload.user_id)

    # --- GIVEAWAY MANAGER COMMANDS ---

    @commands.command(name="reroll")
    @commands.has_permissions(manage_guild=True)
    async def reroll(self, ctx: commands.Context, message_id: int):
        """Reroll new winner(s) for an ended giveaway."""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        gwy = db.get_giveaway(message_id)
        if not gwy:
            err_msg = await ctx.send(embed=error_embed("Not Found", f"Giveaway message ID `{message_id}` not found."))
            await err_msg.delete(delay=5)
            return

        entries = gwy['entries']
        if not entries:
            err_msg = await ctx.send(embed=error_embed("No Entries", "Cannot reroll giveaway because no users participated."))
            await err_msg.delete(delay=5)
            return

        winner_id = random.choice(entries)
        winner = ctx.guild.get_member(winner_id) or await self.bot.fetch_user(winner_id)

        reroll_embed = success_embed(
            "New Winner Selected! 🎉",
            f"The new winner for **{gwy['prize']}** is {winner.mention}!"
        )
        await ctx.send(content=winner.mention, embed=reroll_embed)

    @commands.command(name="gend")
    @commands.has_permissions(manage_guild=True)
    async def gend(self, ctx: commands.Context, message_id: int):
        """Force end an active giveaway immediately."""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        gwy = db.get_giveaway(message_id)
        if not gwy:
            err_msg = await ctx.send(embed=error_embed("Not Found", f"Giveaway with ID `{message_id}` not found."))
            await err_msg.delete(delay=5)
            return

        if gwy['ended'] == 1:
            err_msg = await ctx.send(embed=info_embed("Already Ended", "This giveaway has already ended."))
            await err_msg.delete(delay=5)
            return

        await self._finish_giveaway(gwy)

    @commands.command(name="gcancel")
    @commands.has_permissions(manage_guild=True)
    async def gcancel(self, ctx: commands.Context, message_id: int):
        """Cancel an active giveaway without picking winners."""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        gwy = db.get_giveaway(message_id)
        if not gwy:
            err_msg = await ctx.send(embed=error_embed("Not Found", f"Giveaway with ID `{message_id}` not found."))
            await err_msg.delete(delay=5)
            return

        db.end_giveaway(message_id)

        try:
            channel = ctx.guild.get_channel(gwy['channel_id'])
            if channel:
                msg = await channel.fetch_message(message_id)
                embed = msg.embeds[0]
                embed.description = "**GIVEAWAY CANCELLED**"
                embed.color = config.COLOR_DANGER
                await msg.edit(embed=embed, view=None)
        except Exception:
            pass

    @commands.command(name="glist")
    @commands.has_permissions(manage_guild=True)
    async def glist(self, ctx: commands.Context):
        """List all currently active giveaways in the server."""
        try:
            await ctx.message.delete()
        except Exception:
            pass

        active = db.get_active_giveaways()
        server_active = [g for g in active if g['guild_id'] == ctx.guild.id]

        if not server_active:
            err_msg = await ctx.send(embed=info_embed("Active Giveaways", "There are currently no active giveaways."))
            await err_msg.delete(delay=5)
            return

        embed = create_embed(
            title=f"{config.EMOJI_GIVEAWAY} Active Giveaways ({len(server_active)})",
            color=config.COLOR_PRIMARY
        )

        for g in server_active[:10]:
            end_ts = int(g['end_time'])
            embed.add_field(
                name=f"Prize: {g['prize']}",
                value=f"**Message ID:** `{g['message_id']}`\n**Ends:** <t:{end_ts}:R>\n**Entries:** `{len(g['entries'])}`",
                inline=False
            )

        msg = await ctx.send(embed=embed)
        await msg.delete(delay=15)


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
