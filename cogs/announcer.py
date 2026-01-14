import discord
from discord import app_commands
from discord.ext import commands

class AnnouncementModal(discord.ui.Modal, title="Make an Announcement"):
    def __init__(self, channel: discord.TextChannel, color: discord.Color, image_url: str = None, ping: str = None):
        super().__init__()
        self.channel = channel
        self.color = color
        self.image_url = image_url
        self.ping = ping

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
        embed = discord.Embed(
            title=self.announcement_title.value,
            description=self.message.value,
            color=self.color
        )
        if self.image_url:
            embed.set_image(url=self.image_url)
        
        embed.set_footer(text=f"Announced by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        content = self.ping if self.ping else None

        try:
            await self.channel.send(content=content, embed=embed)
            await interaction.response.send_message(f"Announcement sent to {self.channel.mention}!", ephemeral=True)
        except discord.Forbidden:
             await interaction.response.send_message(f"Failed to send! I do not have permission to speak in {self.channel.mention}.", ephemeral=True)
        except Exception as e:
             await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

class Announcer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="announce", description="Send a formatted announcement to a channel")
    @app_commands.describe(
        channel="The channel to send the announcement to",
        color="The color of the embed (hex code e.g. FF0000, default is Gold)",
        image_url="Optional image URL for the specific announcement",
        ping="Optional text to ping (e.g. @everyone or a role mention)"
    )
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, color: str = None, image_url: str = None, ping: str = None):
        # Default color logic
        if color:
            try:
                # Remove # or 0x prefix if present
                clean_color = color.replace("#", "").replace("0x", "")
                c_val = int(clean_color, 16)
                discord_color = discord.Color(c_val)
            except ValueError:
                await interaction.response.send_message(f"Invalid color format '{color}'! Use hex (e.g. #FF5500).", ephemeral=True)
                return
        else:
            discord_color = discord.Color.gold()
        
        # Check permissions early
        if not channel.permissions_for(interaction.guild.me).send_messages:
             await interaction.response.send_message(f"I don't have permission to send messages in {channel.mention}!", ephemeral=True)
             return

        await interaction.response.send_modal(AnnouncementModal(channel, discord_color, image_url, ping))

async def setup(bot):
    await bot.add_cog(Announcer(bot))
