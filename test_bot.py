# -*- coding: utf-8 -*-
import sys
print("Starting test...", flush=True)
print(f"Python version: {sys.version}", flush=True)

try:
    import discord
    print(f"Discord.py version: {discord.__version__}", flush=True)
except Exception as e:
    print(f"Error importing discord: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from discord.ext import commands
    print("Commands imported!", flush=True)
except Exception as e:
    print(f"Error importing commands: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
    import os
    TOKEN = os.getenv('DISCORD_TOKEN')
    print(f"Token loaded: {'Yes' if TOKEN else 'No'}", flush=True)
except Exception as e:
    print(f"Error loading env: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All imports successful!", flush=True)
