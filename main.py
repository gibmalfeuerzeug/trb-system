import discord
from discord.ext import commands
import os
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# CONFIG
# =====================
SPAM_LIMIT = 5            # Nachrichten
SPAM_SECONDS = 5          # Sekunden
MENTION_LIMIT = 5         # Erwähnungen pro Nachricht

ALLOWED_BOT_ROLES = []    # Rollen-IDs, die Bots einladen dürfen

LOG_CHANNEL_NAME = "security-logs"

# =====================
# SPAM TRACKER
# =====================
message_cache = defaultdict(list)

# =====================
# EVENTS
# =====================

@bot.event
async def on_ready():
    print(f"✅ Bot online als {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = datetime.utcnow()
    user_msgs = message_cache[message.author.id]

    user_msgs.append(now)
    message_cache[message.author.id] = [
        t for t in user_msgs if now - t < timedelta(seconds=SPAM_SECONDS)
    ]

    # Anti-Spam
    if len(message_cache[message.author.id]) > SPAM_LIMIT:
        await message.delete()
        await message.channel.send(
            f"⚠️ {message.author.mention} bitte kein Spam!",
            delete_after=5
        )
        return

    # Anti-Mention-Spam
    if len(message.mentions) >= MENTION_LIMIT:
        await message.delete()
        await message.channel.send(
            f"⚠️ {message.author.mention} Mention-Spam erkannt!",
            delete_after=5
        )
        return

    await bot.process_commands(message)

@bot.event
async def on_webhooks_update(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
        webhook = entry.target
        await webhook.delete()

        log = await get_log_channel(channel.guild)
        await log.send(f"🚫 Webhook gelöscht in {channel.mention}")

@bot.event
async def on_member_join(member):
    if member.bot:
        allowed = False
        for role in member.guild.roles:
            if role.id in ALLOWED_BOT_ROLES:
                allowed = True

        if not allowed:
            await member.kick(reason="Anti-Bot Invite")
            log = await get_log_channel(member.guild)
            await log.send(f"🤖 Bot **{member.name}** automatisch gekickt")

# =====================
# HELPERS
# =====================

async def get_log_channel(guild):
    channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if not channel:
        channel = await guild.create_text_channel(LOG_CHANNEL_NAME)
    return channel

# =====================
# COMMANDS
# =====================

@bot.command()
@commands.has_permissions(administrator=True)
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
@commands.has_permissions(administrator=True)
async def security(ctx):
    embed = discord.Embed(
        title="🛡 Security Bot",
        description="Anti-Spam | Anti-Webhook | Anti-Bot-Invite",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# =====================
# START
# =====================

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
