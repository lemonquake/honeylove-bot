# -*- coding: utf-8 -*-
print("Starting bot script...")
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timezone

# Load environment variables
print("Loading environment variables...")
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APP_ID = os.getenv('APP_ID')
print(f"Token present: {bool(TOKEN)}")
print(f"App ID present: {bool(APP_ID)}")

# Logs channel ID
LOGS_CHANNEL_ID = 1452444862212214950

# Setup Intents
intents = discord.Intents.default()
intents.members = True  # Required for on_member_join events - Re-enabled for role detection
# intents.message_content = True

class HoneyloveBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=APP_ID,
            help_command=None
        )

    async def setup_hook(self):
        # Load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # Sync commands with Discord
        await self.tree.sync()
        print("Commands synced!")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        
        # Send official log message to the logs channel
        logs_channel = self.get_channel(LOGS_CHANNEL_ID)
        if logs_channel:
            # Create a rich embed for the startup log
            embed = discord.Embed(
                title="🟢 Bot Online",
                description="**Honeylove Announcer** has successfully started and is now online!",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="🤖 Bot Name", value=str(self.user), inline=True)
            embed.add_field(name="🆔 Bot ID", value=str(self.user.id), inline=True)
            embed.add_field(name="🌐 Servers", value=str(len(self.guilds)), inline=True)
            embed.add_field(name="📡 Latency", value=f"{round(self.latency * 1000)}ms", inline=True)
            embed.add_field(name="🐍 Discord.py", value=discord.__version__, inline=True)
            embed.set_thumbnail(url=self.user.display_avatar.url if self.user.display_avatar else None)
            embed.set_footer(text="Startup Log")
            
            await logs_channel.send(embed=embed)
            print(f"Sent startup log to #{logs_channel.name}")
        else:
            print(f"Warning: Could not find logs channel with ID {LOGS_CHANNEL_ID}")

async def main():
    bot = HoneyloveBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        pass
