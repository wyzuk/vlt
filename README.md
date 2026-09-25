# Discord Shop Management Bot

A modular Discord bot built with Python and `discord.py`. Prefix command replies, help, giveaways, audit logs, and interactive panels use Discord Components V2. The `+v2test` command demonstrates the V2 layout, images, button, and select menu.

## Commands

### Moderation

- `+ban <@user> [reason]` — Ban a member.
- `+unban <user_id> [reason]` — Unban a user by ID.
- `+kick <@user> [reason]` — Kick a member.
- `+timeout <@user> <duration> [reason]` — Timeout a member (`30s`, `5m`, `2h`, `1d`).
- `+untimeout <@user> [reason]` — Remove a timeout.
- `+mute <@user> [reason]` / `+unmute <@user> [reason]` — Mute or unmute a member.
- `+warn <@user> <reason>` / `+warnings <@user>` — Manage stored warnings.
- `+clear <amount>` — Delete messages; alias: `+purge`.
- `+lock [#channel] [reason]` / `+unlock [#channel] [reason]` — Lock or unlock a channel.
- `+slowmode <seconds>` — Set slowmode (`0` disables it).
- `+nick <@user> [new_nickname]` — Change or reset a nickname.
- `+role <@user> <role>` / `+removerole <@user> <role>` — Manage a member's roles.
- `+hide [#channel]` / `+unhide [#channel]` — Hide or show a channel to everyone.
- `+rename <channel new name>` — Rename the channel where the command is used. Requires Manage Channels.

### Utility and shop

- `+announce <#channel> <message>` — Post an announcement.
- `+say <message>` — Send a message as the bot.
- `+embed <title> | <description> | [hex]` — Create a formatted Components V2 message.
- `+vch <product name> (<price>)` — Staff command (Manage Messages permission). Sends a purchase as `+rep <caller_id> <product name> | <price>` in the current channel. Example: `+vch bought minecraft server host for 1 month mumbai region (700BDT)` sends `+rep <your_id> bought minecraft server host for 1 month mumbai region | 700 BDT`.
- `+status <activity> <activity name>` — Owner-only bot presence control. Supports `playing`, `watching`, `listening`, `streaming`, and `competing`; an unrecognized activity becomes custom status text (`+status hii`). For streaming, pass a URL, such as `+status streaming https://strm.link`.

### Information

- `+userinfo [@user]`, `+serverinfo`, `+avatar [@user]`
- `+channelinfo [#channel]`, `+roleinfo <role>`
- `+botinfo`, `+ping`, `+uptime`, `+invite`
- `+v2test` — Send a V2 layout with a working button and select menu.
- `+dashboard` — Open the interactive bot status dashboard.
- `+help` — Show all commands in larger text, 10 per page, with previous/next buttons. `+hide` and `+unhide` are omitted from help.

### Giveaway management

Requires Manage Server permission.

- `+gwy <time> <winners> <prize> [forced_user]`
- `+reroll <message_id>`, `+gend <message_id>`, `+gcancel <message_id>`, `+glist`
- `+ghlp` — Show giveaway commands.

## Components V2 and emoji setup

Components V2 support in `discord.py` requires version 2.6 or newer. The dependency is specified in `requirements.txt`. The bot uses the custom emoji IDs configured in `config.py`; the bot must be able to use those server emojis.

## Configuration and launch

Set `TOKEN` in the environment, install dependencies from `requirements.txt`, then start the bot. In PowerShell, for example:

```powershell
$env:TOKEN = "YOUR_BOT_TOKEN"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The token is read from the environment variable and is not stored in the source files. Keep it private.

After changing requirements in a cloud host, redeploy or restart its service so it installs the updated `discord.py` version. Use `+v2test` in Discord to check the live V2 message and its interactions.

The bot requires the Message Content and Server Members intents enabled in the Discord Developer Portal. Moderation, announcement, giveaway, and logging features also need their corresponding server permissions.
