# -*- coding: utf-8 -*-
"""
Onboarding Cog - Welcomes new members based on which invite link they used.

- Ambassador invite (https://discord.gg/EA6jRfvFQv) -> Channel 1461061865449984105
- Creator invite (https://discord.gg/ZFYV3vaHVf) -> Channel 1461062991536460123
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone


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
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Cache of invites per guild: {guild_id: {invite_code: uses}}
        self.invite_cache = {}
        # Cooldown cache to prevent spamming welcomes if roles are toggled: {member_id: timestamp}
        self.welcome_cooldown = {}
    
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
        channel = member.guild.get_channel(config["channel_id"])
        
        # Determine the role name/type for logging
        role_label = config.get("role_name") or config.get("role_type") or "Unknown"

        if channel:
            # Check cooldown (avoid spamming if roles are added/removed quickly)
            now = datetime.now(timezone.utc).timestamp()
            last_welcome = self.welcome_cooldown.get(member.id, 0)
            if now - last_welcome < 60: # 1 minute cooldown
                return

            welcome_message = (
                f"Hi, {member.mention}! Welcome to Honeylove's Official Discord! "
                f"Please provide your Tiktok handle in this channel."
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
