# Modern Discord Shop Management Bot (discord.py 2.x & Components V2)

A production-ready, modular, high-performance Discord Shop Management Bot built with **Python 3.13+**, **discord.py 2.x**, **Components V2**, and an **SQLite** database layer.

---

## 🌟 Key Features

### 🛡️ Channel Protection System
* Automatically intercepts and reposts messages in configured protected categories and channels.
* **Protected Category ID:** `1372922294405431436`
* **Protected Channel ID:** `1372922819838611567`
* Immediately deletes original user messages and reposts them under the bot's identity while preserving:
  * Text content
  * Embeds
  * Attachments / Files
  * Stickers
  * Top author header: `> **Sent by @User**`

---

### 🔨 Complete Moderation Suite
All moderation commands feature permission checks, dark blurple embeds, and audit logging:
* `+ban @user [reason]` - Permanently ban a member.
* `+kick @user [reason]` - Kick a member from the server.
* `+timeout @user <time> [reason]` - Timeout a user (`30s`, `5m`, `2h`, `1d`).
* `+untimeout @user [reason]` - Remove timeout from a user.
* `+mute @user [reason]` - Mute a user (timeout & Muted role).
* `+unmute @user [reason]` - Unmute a user.
* `+warn @user <reason>` - Issue an official warning stored in SQLite.
* `+warnings @user` - View warning history for a user.
* `+clear <amount>` / `+purge <amount>` - Bulk delete messages.
* `+lock [channel] [reason]` - Restrict `@everyone` from sending messages.
* `+unlock [channel] [reason]` - Restore message permissions.
* `+slowmode <seconds>` - Configure channel slowmode.
* `+nick @user [new_nick]` - Update or reset member nickname.
* `+role @user <role>` - Grant a role to a member.
* `+removerole @user <role>` - Remove a role from a member.
* `+hide [channel]` - Hide channel from `@everyone`.
* `+unhide [channel]` - Restore channel visibility.

---

### 🎉 Advanced Giveaway System (Components V2)
* **Creation Command:** `+gwy <time> <winner_count> <prize> [forced_user_id]`
  * Example: `+gwy 2h 1 Discord_Nitro`
  * Example with Forced Winner: `+gwy 5m 1 Nitro 123456789012345678`
* Automatically pings `@everyone` and `@here`.
* Interactive **Components V2 Buttons**:
  * `🎉 Join Giveaway` (Toggles entry & updates count live)
  * `📊 Entries` (Displays total entries ephemerally)
  * `⏳ Time Left` (Displays dynamic countdown timestamp)
* Users can also enter simply by reacting with 🎉!
* **Forced Winner Logic:** If `forced_user_id` is supplied, that user wins automatically upon conclusion.
* **Giveaway Management Commands:**
  * `+reroll <message_id>` - Reroll new winner(s).
  * `+gend <message_id>` - Force end giveaway immediately.
  * `+gcancel <message_id>` - Cancel giveaway.
  * `+glist` - View active giveaways.

---

### ⚙️ Utility & Information System
* `+announce #channel <message>` - Send styled announcement embed.
* `+say <message>` - Bot repeats message.
* `+embed Title | Description | [Color Hex]` - Custom embed creation.
* `+userinfo [@user]` - Detailed account and join dates.
* `+serverinfo` - Guild stats and member counts.
* `+avatar [@user]` - User avatar viewer.
* `+channelinfo [#channel]` - Channel metadata.
* `+roleinfo <role>` - Role details.
* `+botinfo` - System specs, latency, and uptime.
* `+ping` - WebSocket latency check.
* `+uptime` - Bot runtime uptime counter.
* `+invite` - Bot invite link generator.
* `+help` - Dynamic Components V2 category help menu.

---

### 🎨 Dark Theme & Embed Styling
* Dark Charcoal Background (`#2B2D31`)
* Accent Color: Blurple (`#5865F2`)
* Standardized timestamps, footers, and bot avatars on all embeds.

---

## 📁 Project Architecture

```
vlt/
├── config.py                 # Configuration (Token, IDs, Colors, Emojis)
├── main.py                   # Bot entry point, setup_hook, error handler
├── requirements.txt          # Dependencies
├── README.md                 # Documentation
├── database/
│   ├── __init__.py
│   └── db_manager.py         # SQLite persistence (giveaways, warnings, shop schemas)
├── utils/
│   ├── __init__.py
│   ├── embeds.py             # Unified dark blurple embed generator
│   ├── time_parser.py        # Time duration string parser (30s, 5m, 2h, 1d)
│   ├── ui_components.py      # Components V2 Views, Buttons, Dropdowns, Paginator
│   └── logger.py             # Audit log transmitter
└── cogs/
    ├── __init__.py
    ├── channel_protection.py # Auto reposting protection cog
    ├── moderation.py         # Complete moderation suite
    ├── utility.py            # Utility and information commands
    ├── giveaway.py           # Giveaway system & manager
    ├── logging.py            # Event logger
    └── help.py               # Interactive Components V2 help cog
```

---

## 🚀 Future Ready Expansion Architecture
The database schema (`database/db_manager.py`) and modular cog layout are structured for immediate expansion into:
* 🛒 **Shop & Product Management**
* 📦 **Auto Delivery System**
* 🔑 **License Key Distribution**
* 📊 **Stock Management**
* 💳 **Crypto & Fiat Payments**
* 🎟️ **Support Ticket System**
* 💰 **Economy & Coupons**
* 🌐 **Web Dashboard Integration**

---

## 🛠️ How to Run

1. Clone or navigate to the repository directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python main.py
   ```
