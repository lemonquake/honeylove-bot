# -*- coding: utf-8 -*-
"""
Onboarding Cog - Welcomes new members based on which invite link they used.

- Ambassador invite (https://discord.gg/EA6jRfvFQv) -> Channel 1461061865449984105
- Creator invite (https://discord.gg/ZFYV3vaHVf) -> Channel 1461062991536460123
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
import json
import os
from discord import ui, app_commands

DATA_FILE = "./data/welcome_config.json"

class WelcomeEditModal(ui.Modal):
    def __init__(self, key, config, save_callback):
        super().__init__(title=f"Edit Welcome Message ({key})")
        self.key = key
        self.save_callback = save_callback
        self.message = ui.TextInput(
            label="Message Content",
            style=discord.TextStyle.paragraph,
            placeholder="Type your welcome message here... Use {user} to mention.",
            default=config.get("message", ""),
            max_length=2000,
            required=True
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction):
        await self.save_callback(interaction, self.key, self.message.value)

class WelcomeConfigView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.selected_key = "Ambassador" # Default

    @discord.ui.select(
        placeholder="1. Select Audience To Edit",
        options=[
            discord.SelectOption(label="Ambassador", value="Ambassador", description="Channel: ambassador-welcome"),
            discord.SelectOption(label="Creator", value="Creator", description="Channel: creator-welcome"),
        ],
        row=0
    )
    async def select_callback(self, interaction: discord.Interaction, select: ui.Select):
        self.selected_key = select.values[0]
        # Inform user of selection
        config = self.cog.get_config(self.selected_key)
        chan_id = config.get("channel_id")
        chan_text = f"<#{chan_id}>" if chan_id else "Default"
        await interaction.response.send_message(f"Selected **{self.selected_key}**. Current Channel: {chan_text}", ephemeral=True)

    @discord.ui.select(
        placeholder="2. (Optional) Change Target Channel",
        cls=ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        row=1
    )
    async def channel_callback(self, interaction: discord.Interaction, select: ui.ChannelSelect):
        channel = select.values[0]
        await self.cog.save_welcome_channel(interaction, self.selected_key, channel.id)

    @discord.ui.button(label="Edit Message", style=discord.ButtonStyle.primary, emoji="✏️", row=2)
    async def edit_button(self, interaction: discord.Interaction, button: ui.Button):
        current_config = self.cog.get_config(self.selected_key)
        modal = WelcomeEditModal(self.selected_key, current_config, self.cog.save_welcome_message)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Test Message", style=discord.ButtonStyle.secondary, emoji="🧪", row=2)
    async def test_button(self, interaction: discord.Interaction, button: ui.Button):
        config = self.cog.get_config(self.selected_key)
        message_template = config.get("message", self.cog.DEFAULT_MESSAGE)
        
        # Determine channel to send to
        channel_id = config.get("channel_id")
        # Fallback to defaults if not set in config
        if not channel_id:
             if self.selected_key == "Ambassador":
                 channel_id = 1461061865449984105
             elif self.selected_key == "Creator":
                 channel_id = 1461062991536460123
        
        target_channel = interaction.guild.get_channel(channel_id)
        
        formatted_message = message_template.format(
            user=interaction.user.mention,
            username=interaction.user.name,
            server=interaction.guild.name
        )
        
        if target_channel:
            await target_channel.send(f"**[TEST MESSAGE]**\n{formatted_message}")
            await interaction.response.send_message(f"✅ Test message sent to {target_channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Could not find target channel (ID: {channel_id})", ephemeral=True)


class Onboarding(commands.Cog):
    """Handles new member onboarding based on invite link used."""
    
    # Invite link configuration
    # Invite link configuration
    INVITE_CONFIG = {
        "EA6jRfvFQv": {  # Ambassador invite code
            "channel_id": 1461061865449984105,
            "role_type": "Ambassador"
        },
        "ZFYV3vaHVf": {  # Creator invite code
            "channel_id": 1461062991536460123,
            "role_type": "Creator"
        }
    }

    # Role link configuration
    ROLE_CONFIG = {
        1452695482626478201: {  # Ambassador Role ID
            "channel_id": 1461061865449984105,
            "role_name": "Ambassador"
        },
        1452648024172920885: {  # Creator Role ID
            "channel_id": 1461062991536460123,
            "role_name": "Creator"
        }
    }

    DEFAULT_MESSAGE = "Hi, {user}! Welcome to Honeylove's Official Discord! Please provide your Tiktok handle in this channel."
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_config = {}
        self.load_config()
        # Cache of invites per guild: {guild_id: {invite_code: uses}}
        self.invite_cache = {}
        # Cooldown cache to prevent spamming welcomes if roles are toggled: {member_id: timestamp}
        self.welcome_cooldown = {}

    def load_config(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.welcome_config = json.load(f)
            except Exception as e:
                print(f"Error loading welcome config: {e}")
                self.welcome_config = {}
        else:
            self.welcome_config = {}

    def save_config(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.welcome_config, f, indent=4)
        except Exception as e:
            print(f"Error saving welcome config: {e}")

    def get_config(self, key):
        return self.welcome_config.get(key, {})

    async def save_welcome_message(self, interaction: discord.Interaction, key: str, message: str):
        if key not in self.welcome_config:
            self.welcome_config[key] = {}
        
        self.welcome_config[key]["message"] = message
        self.save_config()
        await interaction.response.send_message(f"✅ Welcome message for **{key}** updated!", ephemeral=True)

    async def save_welcome_channel(self, interaction: discord.Interaction, key: str, channel_id: int):
        if key not in self.welcome_config:
            self.welcome_config[key] = {}
            
        self.welcome_config[key]["channel_id"] = channel_id
        self.save_config()
        await interaction.response.send_message(f"✅ Target channel for **{key}** updated to <#{channel_id}>!", ephemeral=True)

    @app_commands.command(name="welcome_settings", description="Configure welcome messages for Ambassador and Creator channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_settings(self, interaction: discord.Interaction):
        view = WelcomeConfigView(self)
        await interaction.response.send_message("Please select a channel type to configure:", view=view, ephemeral=True)
    
    async def cache_invites(self, guild: discord.Guild):
        """Cache the current invite uses for a guild."""
        try:
            invites = await guild.invites()
            self.invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}
        except discord.Forbidden:
            print(f"Warning: Missing permissions to fetch invites for {guild.name}")
        except Exception as e:
            print(f"Error caching invites for {guild.name}: {e}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Cache invites for all guilds when bot starts."""
        print("Onboarding cog loaded - caching invites...")
        for guild in self.bot.guilds:
            await self.cache_invites(guild)
        print(f"Cached invites for {len(self.invite_cache)} guild(s)")
    
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Update cache when a new invite is created."""
        if invite.guild.id not in self.invite_cache:
            self.invite_cache[invite.guild.id] = {}
        self.invite_cache[invite.guild.id][invite.code] = invite.uses
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """Update cache when an invite is deleted."""
        if invite.guild.id in self.invite_cache:
            self.invite_cache[invite.guild.id].pop(invite.code, None)
    
    async def send_welcome_message(self, member: discord.Member, config):
        """Helper to send the welcome message."""
        channel_id = config.get("channel_id")
        
        # If channel_id is in the custom config, use it. Otherwise use the hardcoded default from INVITE_CONFIG/ROLE_CONFIG
        if not channel_id:
             channel_id = config.get("channel_id") # This refers to the dictionary passed in, not our custom config

        # However, 'config' passed to this function IS from INVITE_CONFIG or ROLE_CONFIG usually.
        # We need to overlay our custom config.
        
        # Determine the key to look up in welcome_config
        key = "Ambassador" if "Ambassador" in role_label else "Creator" if "Creator" in role_label else role_label
        # Fallback mapping
        if key not in ["Ambassador", "Creator"]:
             if channel_id == 1461061865449984105: key = "Ambassador"
             elif channel_id == 1461062991536460123: key = "Creator"
        
        # Check custom config for channel override
        custom_config = self.welcome_config.get(key, {})
        if "channel_id" in custom_config:
            channel_id = custom_config["channel_id"]

        channel = member.guild.get_channel(channel_id)
        
        if channel:
            # Check cooldown (avoid spamming if roles are added/removed quickly)
            now = datetime.now(timezone.utc).timestamp()
            last_welcome = self.welcome_cooldown.get(member.id, 0)
            if now - last_welcome < 60: # 1 minute cooldown
                return

            # Get message from config
            message_template = self.welcome_config.get(key, {}).get("message", self.DEFAULT_MESSAGE)
            
            welcome_message = message_template.format(
                user=member.mention,
                username=member.name,
                server=member.guild.name
            )
            
            try:
                await channel.send(welcome_message)
                print(f"Welcomed {role_label} {member} in #{channel.name}")
                self.welcome_cooldown[member.id] = now
            except Exception as e:
                 print(f"Error sending welcome to {channel.name}: {e}")
        else:
            print(f"Warning: Could not find channel {config['channel_id']} for {role_label}")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Detect when a member gets a role."""
        if before.roles == after.roles:
            return

        # Check for new roles
        new_roles = set(after.roles) - set(before.roles)
        
        for role in new_roles:
            if role.id in self.ROLE_CONFIG:
                await self.send_welcome_message(after, self.ROLE_CONFIG[role.id])

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle new member joins and detect which invite was used."""
        guild = member.guild
        
        # Skip bots
        if member.bot:
            return
        
        # Check if member already has one of the roles
        role_matched = False
        for role in member.roles:
            if role.id in self.ROLE_CONFIG:
                await self.send_welcome_message(member, self.ROLE_CONFIG[role.id])
                role_matched = True
        
        # If we already matched a role, we might still want to track invites 
        # but the cooldown in send_welcome_message will prevent double posting.
        
        used_invite_code = None
        
        try:
            # Get current invites and compare with cache
            current_invites = await guild.invites()
            current_invite_dict = {invite.code: invite.uses for invite in current_invites}
            
            # Find the invite whose use count increased
            cached_invites = self.invite_cache.get(guild.id, {})
            
            for code, uses in current_invite_dict.items():
                cached_uses = cached_invites.get(code, 0)
                if uses > cached_uses:
                    used_invite_code = code
                    break
            
            # Update the cache
            self.invite_cache[guild.id] = current_invite_dict
            
        except discord.Forbidden:
            print(f"Warning: Missing permissions to fetch invites for {guild.name}")
            return
        except Exception as e:
            print(f"Error detecting invite for {member}: {e}")
            return
        
        # Check if the invite matches our tracked invites
        if used_invite_code and used_invite_code in self.INVITE_CONFIG:
            config = self.INVITE_CONFIG[used_invite_code]
            # Use the shared helper method which has cooldown logic
            await self.send_welcome_message(member, config)
        else:
            # Log if member joined through unknown/other invite
            if used_invite_code:
                print(f"Member {member} joined via invite: {used_invite_code} (not tracked)")
            else:
                print(f"Member {member} joined but invite could not be detected")


async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot))
