import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

# Kleiner Webserver für Render
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

bot = commands.Bot(command_prefix=["/", "^", "$"], intents=intents, help_command=None)

verwarnungen_speicher = {}

# ==================== DEINE SERVER CONFIG ====================
PROJEKTLEITUNG_ROLLEN = [
    "⚒︎ || Head behind everything", 
    "♕✯ |❘| David | Founder", 
    "✵ || Mika | Co-Founder"
]

NORMALE_SPIELER_ROLLEN = [
    "🟢 || Verify", 
    "✋ 〣 Member", 
    "-------Others--------", 
    "👮 〣  Polizei", 
    "@everyone"
]

ERLAUBTE_STAFF_ROLLEN = [
    "┗⎯⎯⎯|▪️|PROJEKT LEAD|▪️|⎯⎯⎯┓", 
    "┗⎯⎯⎯|▪️|REAL CREATORS|▪️|⎯⎯⎯┓", 
    "┗⎯⎯⎯|🛑|OWNERS|🛑|⎯⎯⎯┑", 
    "┗⎯⎯⎯|🔴|HIGHTEAM|🔴|⎯⎯⎯┑"
]

SUSPEND_ROLLE_NAME = "Suspendiert"
# =============================================================

def hat_rolle_aus_liste(member, rollen_liste):
    for r in member.roles:
        if r.name in rollen_liste:
            return True
    return False

@bot.event
async def on_ready():
    print(f"Erfolgreich eingeloggt als {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="SYSTEM X EH RP • Online"))
    
    # Synchronisiert die Slash-Commands (Tree) mit Discord
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash-Commands erfolgreich mit Discord synchronisiert!")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Slash-Commands: {e}")
        
    keep_alive()

# ==================== HELPER WORKER FÜR DIE LOGIK ====================
async def do_uprank(author, guild, target, neue_rolle, grund):
    if not hat_rolle_aus_liste(author, ERLAUBTE_STAFF_ROLLEN) and author != guild.owner:
        return False, "❌ **Fehler:** Deine Rolle ist nicht berechtigt!"
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        return False, "❌ **System-Schutz:** Die Führungsebene kann nicht bearbeitet werden!"
    if author.top_role <= target.top_role and author != guild.owner:
        return False, "❌ **Fehler:** Dein Rang ist zu niedrig!"

    alte_rolle = target.top_role
    try:
        await target.add_roles(neue_rolle)
        embed = discord.Embed(
            title="📈 SYSTEM X EH RP • BEFÖRDERUNG", 
            description=f"Ein Teammitglied hat einen neuen Rang erhalten!\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=discord.Color.from_rgb(46, 204, 113)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👤 Betroffener", value=f"{target.mention}\n`({target.id})`", inline=True)
        embed.add_field(name="✍️ Ausgeführt von", value=f"{author.mention}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="🔽 Alter Rang", value=f"`{alte_rolle.name}`", inline=True)
        embed.add_field(name="🔼 Neuer Rang", value=f"{neue_rolle.mention}", inline=True)
        embed.add_field(name="📝 Begründung", value=f"```text\n{grund}\n```", inline=False)
        embed.set_footer(text="SYSTEM X EH RP • Personalverwaltung", icon_url=guild.icon.url if guild.icon else None)
        return True, embed
    except discord.Forbidden:
        return False, "❌ **System-Fehler:** Mir fehlen die Rechte! Ziehe meine Rolle ganz nach oben."

# ==================== UPRANK BEFEHL ====================
# 1. Klassischer Präfix-Befehl (^uprank, /uprank, $uprank)
@bot.command(name="uprank")
async def uprank_prefix(ctx, target: discord.Member = None, neue_rolle: discord.Role = None, *, grund: str = "Kein Grund angegeben"):
    if not target or not neue_rolle:
        await ctx.send(f"❌ **Fehler:** Nutzen: `{ctx.prefix}uprank @Spieler @Rolle [Grund]`")
        return
    success, res = await do_uprank(ctx.author, ctx.guild, target, neue_rolle, grund)
    if success:
        await ctx.send(embed=res)
    else:
        await ctx.send(res)

# 2. Moderner Slash Command (App / Tree)
@bot.tree.command(name="uprank", description="Befördere ein Teammitglied (SYSTEM X EH RP)")
@app_commands.describe(target="Der zu befördernde Spieler", neue_rolle="Die neue Rolle", grund="Grund der Beförderung")
async def uprank_slash(interaction: discord.Interaction, target: discord.Member, neue_rolle: discord.Role, grund: str = "Kein Grund angegeben"):
    success, res = await do_uprank(interaction.user, interaction.guild, target, neue_rolle, grund)
    if success:
        await interaction.response.send_message(embed=res)
    else:
        await interaction.response.send_message(res, ephemeral=True)

# ==================== STATUS & HELP BEFEHLE ====================
@bot.command(name="status")
async def status_prefix(ctx):
    embed = discord.Embed(
        title="⚙️ SYSTEM X EH RP • STATUS ZENTRALE", 
        description="Aktuelle Systemwerte des Server-Bots:\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=discord.Color.from_rgb(41, 128, 185)
    )
    embed.add_field(name="🟢 Status", value="`Online & Bereit`", inline=True)
    embed.add_field(name="📶 Latenz", value=f"`{round(bot.latency * 1000)} ms`", inline=True)
    embed.add_field(name="👥 Mitglieder", value=f"`{ctx.guild.member_count}`", inline=True)
    embed.set_footer(text=f"Abgerufen von {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.tree.command(name="status", description="Zeigt die Systemwerte des Bots an")
async def status_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚙️ SYSTEM X EH RP • STATUS ZENTRALE", 
        description="Aktuelle Systemwerte des Server-Bots:\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=discord.Color.from_rgb(41, 128, 185)
    )
    embed.add_field(name="🟢 Status", value="`Online & Bereit`", inline=True)
    embed.add_field(name="📶 Latenz", value=f"`{round(bot.latency * 1000)} ms`", inline=True)
    embed.add_field(name="👥 Mitglieder", value=f"`{interaction.guild.member_count}`", inline=True)
    embed.set_footer(text=f"Abgerufen von {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓 Dein Bot funktioniert!")

@bot.command(name="help", aliases=["hilfe"])
async def help_command(ctx):
    embed = discord.Embed(
        title="📋 SYSTEM X EH RP • BEFEHLSZENTRALE", 
        description="Übersicht aller verwalterischen System-Befehle.\nPräfixe: `/`, `^`, `$` sowie **Slash Commands**!\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=discord.Color.from_rgb(52, 152, 219)
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    
    embed.add_field(
        name="🔼 Team-Verwaltung", 
        value="▸ `uprank @Spieler @Rolle [Grund]`\n▸ `downrank @Spieler @Rolle [Grund]`\n▸ `teamkick @Spieler [Grund]`\n", 
        inline=False
    )
    embed.add_field(
        name="🛑 Sanktionen & Akten", 
        value="▸ `warn @Spieler [Grund]`\n▸ `clearwarns @Spieler`\n▸ `strike @Spieler [Grund]`\n▸ `suspend @Spieler [Grund]`\n▸ `unsuspend @Spieler @AlteStaffRolle`\n", 
        inline=False
    )
    embed.add_field(
        name="⚙️ System & Info", 
        value="▸ `status` – Zeigt Ping & Serverwerte\n▸ `ping` – Kurzer Verbindungstest\n", 
        inline=False
    )
    embed.set_footer(text="SYSTEM X EH RP • Offizielles Verwaltungssystem", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed)

token = os.environ.get('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ FEHLER: Kein DISCORD_TOKEN in den Environment Variables gefunden!")
