# PyBot

A Discord bot built in Python, designed to be easily extended with commands, events, and plugins for your server.

## 🚀 Features

- Fully automated setup: dependencies and configuration handled on first startup  
- Plugin system for adding/removing features without touching core code  
- Supports prefix commands (and/or slash commands)  
- Lightweight and suitable for hobby servers, small communities, or personal use  

## 📦 Getting Started

### Prerequisites  

Before running the bot, you need:

1. A **Discord bot token** from the [Discord Developer Portal](https://discord.com/developers)  
2. Your **Discord user ID** to set as the bot owner (for owner-only commands)  

> The bot will handle installing Python dependencies and generating its configuration on first run.

---

### 🔹 Running the Bot

There are two ways to run PyBot:

#### 1️⃣ Download the release (recommended)

1. Go to the [Releases](https://github.com/DEAMJAVA/PyBot/releases) page  
2. Download the main `main.py` file  
3. Run it:

```bash
python PyBot.py
```

>On first startup, the bot will automatically:
 - Install required Python packages
 - Generate the configuration file
 - Prompt you for the bot token and owner ID
 - This method does not include any plugins by default, so you start with a clean setup.

#### 2️⃣ Clone the repository
```bash
# Clone the repository
git clone https://github.com/DEAMAJVA/PyBot.git
cd PyBot

# Start the bot
python main.py
```
> This method includes all officially made plugins which may be a overbloated bot for many which is why this method is not recommended for basic users.

### 🧩 Plugins

> To load plugins you just simply drop your plugin file in the plugins/ folder, make sure plugins
> is enabled in the bot config.
> 
> plugins allow you to add your own functionality to the bot without modifying the core and potentially risk
> breaking the bot or breaking your features in bot updates

MIT License (c) 2025 DEAMJAVA
