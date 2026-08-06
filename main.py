import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

# Kleiner Webserver für Render, damit der Port aktiv ist
app = Flask('')
@app.route('/')
def home():
    return "Bot läuft!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Erfolgreich eingeloggt als {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="!ping für Hilfe"))

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓 Dein Bot funktioniert!")

@bot.command()
async def hallo(ctx):
    await ctx.send(f"Hallo {ctx.author.mention}! Schön dich zu sehen.")

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel is not None:
        await channel.send(f"Willkommen auf dem Server, {member.mention}! 🎉")

# Startet den Webserver und danach den Bot
keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
