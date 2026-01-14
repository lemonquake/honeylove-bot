import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import time
import uuid

DATA_FILE = "data/schedules.json"

class ScheduleModal(discord.ui.Modal, title="Schedule Announcement"):
    def __init__(self, cog, channel, color, image_url, ping, interval_seconds):
        super().__init__()
        self.cog = cog
        self.channel = channel
        self.color = color
        self.image_url = image_url
        self.ping = ping
        self.interval_seconds = interval_seconds

    announcement_title = discord.ui.TextInput(
        label="Title",
        placeholder="Announcement Title",
        required=True,
        max_length=256
    )

    message = discord.ui.TextInput(
        label="Message",
        style=discord.TextStyle.paragraph,
        placeholder="Type your announcement here...",
        required=True,
        max_length=4000
    )

    async def on_submit(self, interaction: discord.Interaction):
        schedule_id = str(uuid.uuid4())[:8]
        # First run is now + interval (so it doesn't spam immediately upon creation, or should it run immediately? Usually schedule implies "starting now". Let's do next run immediately? No, "every X minutes" implies wait X minutes. Or maybe run once now. Let's do wait.)
        # Actually user might want it to start shortly. Let's set next_run to now + interval.
        next_run = time.time() + self.interval_seconds
        
        data = {
            "id": schedule_id,
            "channel_id": self.channel.id,
            "title": self.announcement_title.value,
            "message": self.message.value,
            "color": self.color.value,
            "image_url": self.image_url,
            "ping": self.ping,
            "interval_seconds": self.interval_seconds,
            "next_run": next_run
        }
        
        self.cog.schedules.append(data)
        self.cog.save_schedules()
        
        embed = discord.Embed(title="Schedule Created", description=f"ID: `{schedule_id}`\nChannel: {self.channel.mention}\nNext Run: <t:{int(next_run)}:R>", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedules = []
        self.load_schedules()
        self.announcement_loop.start()

    def load_schedules(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, 'r') as f:
                self.schedules = json.load(f)
        except Exception as e:
            print(f"Failed to load schedules: {e}")

    def save_schedules(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.schedules, f, indent=4)
        except Exception as e:
            print(f"Failed to save schedules: {e}")

    def cog_unload(self):
        self.announcement_loop.cancel()

    @tasks.loop(seconds=60)
    async def announcement_loop(self):
        now = time.time()
        
        # Iterate over a copy since we might modify
        # Actually we won't remove unless valid, but we update next_run
        
        for schedule in self.schedules:
            if schedule['next_run'] <= now:
                # Run it
                channel = self.bot.get_channel(schedule['channel_id'])
                if channel:
                    embed = discord.Embed(
                        title=schedule.get('title'),
                        description=schedule.get('message'),
                        color=discord.Color(schedule.get('color', 0xFFD700))
                    )
                    if schedule.get('image_url'):
                        embed.set_image(url=schedule['image_url'])
                    
                    try:
                        ping_content = schedule.get('ping')
                        await channel.send(content=ping_content, embed=embed)
                    except Exception as e:
                        print(f"Error sending schedule {schedule['id']}: {e}")
                else:
                    print(f"Channel {schedule['channel_id']} not found.")

                # Update next run
                # To prevent drift, we could add interval to expected next_run, but if bot was off for long time, this would cause burst.
                # Safer: reset to now + interval
                schedule['next_run'] = now + schedule['interval_seconds']
        
        self.save_schedules()

    @announcement_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="schedule", description="Schedule a recurring announcement")
    @app_commands.choices(unit=[
        app_commands.Choice(name="Minutes", value="minutes"),
        app_commands.Choice(name="Hours", value="hours"),
        app_commands.Choice(name="Days", value="days")
    ])
    @app_commands.describe(
        channel="Channel to announce in",
        unit="Time unit (Minutes, Hours, Days)",
        interval="Amount of time units",
        color="Hex color code",
        image_url="Optional image",
        ping="Optional mention"
    )
    async def schedule(self, interaction: discord.Interaction, channel: discord.TextChannel, unit: app_commands.Choice[str], interval: int, color: str = None, image_url: str = None, ping: str = None):
        seconds = 0
        if unit.value == "minutes":
            seconds = interval * 60
        elif unit.value == "hours":
            seconds = interval * 3600
        elif unit.value == "days":
            seconds = interval * 86400
        
        if seconds < 60:
             await interaction.response.send_message("Interval must be at least 1 minute!", ephemeral=True)
             return

        discord_color = discord.Color.gold()
        if color:
             try:
                 clean_color = color.replace("#", "").replace("0x", "")
                 discord_color = discord.Color(int(clean_color, 16))
             except ValueError:
                 pass 

        if not channel.permissions_for(interaction.guild.me).send_messages:
             await interaction.response.send_message(f"I don't have permission to send messages in {channel.mention}!", ephemeral=True)
             return

        await interaction.response.send_modal(ScheduleModal(self, channel, discord_color, image_url, ping, seconds))

    @app_commands.command(name="schedules", description="List active schedules")
    async def list_schedules(self, interaction: discord.Interaction):
        if not self.schedules:
            await interaction.response.send_message("No active schedules.", ephemeral=True)
            return
        
        desc = ""
        for s in self.schedules:
            next_run = int(s['next_run'])
            desc += f"🆔 `{s['id']}` | 📢 <#{s['channel_id']}> | ⏳ <t:{next_run}:R>\n"
            desc += f"📄 {s['title']}\n"
            desc += "--------------------------------\n"
        
        embed = discord.Embed(title="Active Schedules", description=desc, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unschedule", description="Delete a schedule by ID")
    async def unschedule(self, interaction: discord.Interaction, schedule_id: str):
        original_len = len(self.schedules)
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        
        if len(self.schedules) < original_len:
            self.save_schedules()
            await interaction.response.send_message(f"Schedule `{schedule_id}` deleted!", ephemeral=True)
        else:
            await interaction.response.send_message(f"Schedule `{schedule_id}` not found!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
