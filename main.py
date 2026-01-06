import discord
from discord.ext import commands
import os
import asyncio
import re
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

INTENTS = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ---------------- CONFIG ---------------- #

SPAM_LIMIT = 5          # Nachrichten
SPAM_TIME = 6           # Sekunden
TIMEOUT_DURATION = 10   # Minuten

INVITE_REGEX = re.compile(r"(discord\.gg\/|discord\.com\/invite\/)", re.IGNORECASE)

message_logs = defaultdict(list)

# ---------------------------------------- #

def is_whitelisted(member: discord.Member):
    if member.guild.owner_id == member.id:
        return True

    bot_member = member.guild.me
    return member.top_role > bot_member.top_role

# ---------------------------------------- #

@bot.event
async def on_ready():
    print(f"[SECURITY] Bot online als {bot.user}")

# ----------- ANTI BOT INVITE ------------- #

@bot.event
async def on_member_join(member):
    if member.bot and not is_whitelisted(member):
        await member.kick(reason="Anti Bot Invite")
        print(f"[SECURITY] Bot {member} gekickt")

# ----------- ANTI WEBHOOK ---------------- #

@bot.event
async def on_webhooks_update(channel):
    guild = channel.guild
    webhooks = await channel.webhooks()

    for webhook in webhooks:
        creator = webhook.user
        if creator and not is_whitelisted(creator):
            await webhook.delete(reason="Anti Webhook")
            print(f"[SECURITY] Webhook gelöscht in {channel}")

# --------------- ANTI SPAM --------------- #

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    if is_whitelisted(message.author):
        return

    # Invite Spam
    if INVITE_REGEX.search(message.content):
        await message.delete()
        await punish(message.author, "Invite Spam")
        return

    # Message Spam
    now = message.created_at.timestamp()
    logs = message_logs[message.author.id]
    logs.append(now)

    message_logs[message.author.id] = [
        t for t in logs if now - t <= SPAM_TIME
    ]

    if len(message_logs[message.author.id]) >= SPAM_LIMIT:
        await punish(message.author, "Spam")
        message_logs[message.author.id].clear()
        return

    await bot.process_commands(message)

# --------------- PUNISH ------------------ #

async def punish(member: discord.Member, reason: str):
    try:
        await member.timeout(
            discord.utils.utcnow() + discord.timedelta(minutes=TIMEOUT_DURATION),
            reason=f"Security: {reason}"
        )
        print(f"[SECURITY] {member} getimeouted ({reason})")
    except:
        pass

# ---------------------------------------- #

bot.run(TOKEN)
