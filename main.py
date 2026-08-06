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

# Der Bot reagiert zeitgleich auf /, ^ und $
bot = commands.Bot(command_prefix=["/", "^", "$"], intents=intents, help_command=None)

# Speicherung im RAM für Verwarnungen
verwarnungen_speicher = {}

# ==================== DEINE SERVER CONFIG ====================
# 1. GANZ HOHE ROLLEN (Absolut geschützt vor Kicks, Downranks, Strikes, Suspendierungen!)
PROJEKTLEITUNG_ROLLEN = [
    "⚒︎ || Head behind everything", 
    "♕✯ |❘| David | Founder", 
    "✵ || Mika | Co-Founder"
]

# 2. NORMALE SPIELER & VIP (Werden beim Teamkick NIEMALS gelöscht)
NORMALE_SPIELER_ROLLEN = [
    "🟢 || Verify", 
    "✋ 〣 Member", 
    "-------Others--------", 
    "👮 〣  Polizei", 
    "@everyone"
]

# 3. ERLAUBTE STAFF-ROLLEN (Nur wer eine dieser Rollen hat, darf die System-Befehle nutzen!)
ERLAUBTE_STAFF_ROLLEN = [
    "┗⎯⎯⎯|▪️|PROJEKT LEAD|▪️|⎯⎯⎯┓", 
    "┗⎯⎯⎯|▪️|REAL CREATORS|▪️|⎯⎯⎯┓", 
    "┗⎯⎯⎯|🛑|OWNERS|🛑|⎯⎯⎯┑", 
    "┗⎯⎯⎯|🔴|HIGHTEAM|🔴|⎯⎯⎯┑"
]

# 4. DIE SUSPENDIERT-ROLLE (Wird beim Befehl ^suspend vergeben)
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
    await bot.change_presence(activity=discord.Game(name="System-Verwaltung aktiv"))
    keep_alive() # Startet den Webserver automatisch beim Bot-Start

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓 Dein Bot funktioniert!")

@bot.command()
async def hallo(ctx):
    await ctx.send(f"Hallo {ctx.author.mention}! Schön dich zu sehen.")

# ==================== UPRANK BEFEHL ====================
@bot.command()
async def uprank(ctx, target: discord.Member = None, neue_rolle: discord.Role = None, *, grund: str = "Kein Grund angegeben"):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        await ctx.send("❌ **Fehler:** Deine Rolle ist nicht berechtigt!")
        return
    if not target or not neue_rolle:
        await ctx.send(f"❌ **Fehler:** Nutzen: `{ctx.prefix}uprank @Spieler @Rolle [Grund]`")
        return
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        await ctx.send("❌ **System-Schutz:** Die Führungsebene kann nicht bearbeitet werden!")
        return
    if ctx.author.top_role <= target.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ **Fehler:** Dein Rang ist zu niedrig!")
        return

    alte_rolle = target.top_role
    try:
        await target.add_roles(neue_rolle)
        embed = discord.Embed(title="🚨 SYSTEM: BEOBACHTUNG / UPRANK", color=discord.Color.green())
        embed.add_field(name="👤 Spieler", value=target.mention, inline=False)
        embed.add_field(name="🔼 Neuer Rang", value=neue_rolle.mention, inline=True)
        embed.add_field(name="🔽 Alter Rang", value=alte_rolle.name, inline=True)
        embed.add_field(name="📝 Grund", value=grund, inline=False)
        embed.add_field(name="✍️ Gegeben von", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **System-Fehler:** Mir fehlen die Rechte! Ziehe meine Rolle ganz nach oben.")

# ==================== DOWNRANK BEFEHL ====================
@bot.command()
async def downrank(ctx, target: discord.Member = None, neue_rolle: discord.Role = None, *, grund: str = "Kein Grund angegeben"):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        await ctx.send("❌ **Fehler:** Keine Berechtigung!")
        return
    if not target or not neue_rolle:
        await ctx.send(f"❌ **Fehler:** Nutzen: `{ctx.prefix}downrank @Spieler @Rolle [Grund]`")
        return
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        await ctx.send("❌ **System-Schutz:** Die Führungsebene ist geschützt!")
        return
    if ctx.author.top_role <= target.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ **Fehler:** Dein Rang ist zu niedrig!")
        return

    alte_rolle = target.top_role
    try:
        await target.remove_roles(alte_rolle)
        await target.add_roles(neue_rolle)
        embed = discord.Embed(title="🚨 SYSTEM: DEGRADIERUNG / DOWNRANK", color=discord.Color.orange())
        embed.add_field(name="👤 Spieler", value=target.mention, inline=False)
        embed.add_field(name="🔽 Neuer Rang", value=neue_rolle.mention, inline=True)
        embed.add_field(name="🔼 Alter Rang", value=alte_rolle.name, inline=True)
        embed.add_field(name="📝 Grund", value=grund, inline=False)
        embed.add_field(name="✍️ Ausgeführt von", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ **System-Fehler:** Rechte fehlen!")

# ==================== TEAMKICK BEFEHL ====================
@bot.command()
async def teamkick(ctx, target: discord.Member = None, *, grund: str = "Kein Grund angegeben"):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        await ctx.send("❌ **Fehler:** Keine Berechtigung!")
        return
    if not target:
        await ctx.send(f"❌ **Fehler:** Nutzen: `{ctx.prefix}teamkick @Spieler [Grund]`")
        return
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        await ctx.send("❌ **System-Schutz:** Führungsebene geschützt!")
        return
    if ctx.author.top_role <= target.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ **Fehler:** Dein Rang ist zu niedrig!")
        return

    try:
        entfernte_rollen = []
        for index_rolle in target.roles:
            if index_rolle.name not in NORMALE_SPIELER_ROLLEN and index_rolle.name not in PROJEKTLEITUNG_ROLLEN:
                try:
                    await target.remove_roles(index_rolle)
                    entfernte_rollen.append(index_rolle.name)
                except discord.Forbidden:
                    continue
        
        embed = discord.Embed(title="🚪 SYSTEM: TEAM-AUSSCHLUSS", color=discord.Color.red())
        embed.add_field(name="👤 Ex-Mitglied", value=target.mention, inline=False)
        embed.add_field(name="📋 Entfernte Ränge", value=", ".join(entfernte_rollen) if entfernte_rollen else "Keine Ränge entfernt", inline=False)
        embed.add_field(name="📝 Begründung", value=grund, inline=False)
        embed.add_field(name="✍️ Ausgeführt von", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Fehler beim Teamkick: {e}")

# ==================== VERWARNUNG SYSTEM ====================
@bot.command()
async def warn(ctx, target: discord.Member = None, *, grund: str = "Kein Grund angegeben"):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        await ctx.send("❌ **Fehler:** Keine Berechtigung!")
        return
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}warn @Spieler [Grund]`")
        return
        
    if target.id not in verwarnungen_speicher:
        verwarnungen_speicher[target.id] = 0
    verwarnungen_speicher[target.id] += 1

    embed = discord.Embed(title="⚠️ SYSTEM: VERWARNUNG ERTEILT", color=discord.Color.yellow())
    embed.add_field(name="👤 Verwarnter Spieler", value=target.mention, inline=True)
    embed.add_field(name="📊 Verwarnungen Gesamt", value=f"**{verwarnungen_speicher[target.id]}**", inline=True)
    embed.add_field(name="📝 Grund", value=grund, inline=False)
    embed.add_field(name="✍️ Ausgestellt von", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def clearwarns(ctx, target: discord.Member = None):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        return
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}clearwarns @Spieler`")
        return
    verwarnungen_speicher[target.id] = 0
    await ctx.send(f"✅ Alle Verwarnungen für {target.mention} wurden gelöscht.")

# ==================== TEAM STRIKE ====================
@bot.command()
async def strike(ctx, target: discord.Member = None, *, grund: str = "Fehlverhalten im Dienst"):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        return
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}strike @Spieler [Grund]`")
        return
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        await ctx.send("❌ Führungsebene kann keine Strikes erhalten!")
        return

    embed = discord.Embed(title="🛡️ SYSTEM: TEAM-STRIKE", color=discord.Color.dark_red())
    embed.add_field(name="👤 Staff-Mitglied", value=target.mention, inline=False)
    embed.add_field(name="⚠️ Status", value="1x Verwarnung im Dienst-Akte eingetragen", inline=False)
    embed.add_field(name="📝 Begründung", value=grund, inline=False)
    embed.add_field(name="✍️ Unterschrift", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)

# ==================== SUSPENDIEREN ====================
@bot.command()
async def suspend(ctx, target: discord.Member = None, *, grund: str = "Dienstvergehen / Untersuchung"):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        return
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}suspend @Spieler [Grund]`")
        return
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        await ctx.send("❌ Führungsebene kann nicht suspendiert werden!")
        return
        
    try:
        suspend_rolle = discord.utils.get(ctx.guild.roles, name=SUSPEND_ROLLE_NAME)
        if not suspend_rolle:
            await ctx.send(f"❌ Fehler: Bitte erstelle zuerst eine Rolle namens `{SUSPEND_ROLLE_NAME}` auf deinem Server!")
            return
            
        for index_rolle in target.roles:
            if index_rolle.name not in NORMALE_SPIELER_ROLLEN:
                try:
                    await target.remove_roles(index_rolle)
                except:
                    continue
            
        await target.add_roles(suspend_rolle)
        embed = discord.Embed(title="🛑 SYSTEM: DIENSTSUSPENDIERUNG", color=discord.Color.purple())
        embed.add_field(name="👤 Betroffener", value=target.mention, inline=False)
        embed.add_field(name="🔒 Status", value="Alle Dienst-Rechte entzogen. Temporäre Auszeit.", inline=False)
        embed.add_field(name="📝 Grund", value=grund, inline=False)
        embed.add_field(name="✍️ Unterschrift", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Fehler bei der Suspendierung: {e}")

# ==================== UNSUSPEND ====================
@bot.command()
async def unsuspend(ctx, target: discord.Member = None, alte_rolle: discord.Role = None):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner:
        return
    if not target or not alte_rolle:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}unsuspend @Spieler @AlteStaffRolle`")
        return
        
    try:
        suspend_rolle = discord.utils.get(ctx.guild.roles, name=SUSPEND_ROLLE_NAME)
        if suspend_rolle in target.roles:
            await target.remove_roles(suspend_rolle)
            
        await target.add_roles(alte_rolle)
        embed = discord.Embed(title="🔓 SYSTEM: REINTEGRATION", color=discord.Color.blue())
        embed.add_field(name="👤 Mitarbeiter", value=target.mention, inline=False)
        embed.add_field(name="✅ Status", value=f"Suspendierung aufgehoben. Rolle {alte_rolle.mention} wiederhergestellt.", inline=False)
        embed.add_field(name="✍️ Freigegeben von", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Fehler beim Aufheben der Suspendierung: {e}")

# ==================== BOT-STATUS ====================
@bot.command()
async def status(ctx):
    embed = discord.Embed(title="🤖 System-Zentrale Status", color=discord.Color.blue())
    embed.add_field(name="🟢 Bot-Status", value="Online & Einsatzbereit", inline=True)
    embed.add_field(name="📶 Server-Latenz", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="👥 Überwachte Mitglieder", value=f"{ctx.guild.member_count}", inline=False)
    await ctx.send(embed=embed)

# ==================== HILFE BEFEHL ====================
@bot.command(name="help", aliases=["hilfe"])
async def help_command(ctx):
    embed = discord.Embed(
        title="📋 System-Zentrale: Befehlsübersicht", 
        description="Hier sind alle verfügbaren Befehle für das RP-Projekt.\nNutze `^`, `/` oder `$` vor dem Befehl.",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🔼 Team-Verwaltung", 
        value=(
            "`uprank @Spieler @Rolle [Grund]`\nBefördert ein Teammitglied.\n\n"
            "`downrank @Spieler @Rolle [Grund]`\nDegradiert ein Teammitglied.\n\n"
            "`teamkick @Spieler [Grund]`\nEntfernt alle Team-Ränge."
        ), 
        inline=False
    )
    
    embed.add_field(
        name="🛑 Sanktionen & Akten", 
        value=(
            "`warn @Spieler [Grund]`\nErteilt eine Verwarnung.\n\n"
            "`clearwarns @Spieler`\nLöscht alle Verwarnungen.\n\n"
            "`strike @Spieler [Grund]`\nTrägt einen Team-Strike ein.\n\n"
            "`suspend @Spieler [Grund]`\nEntzieht alle Rechte (Auszeit).\n\n"
            "`unsuspend @Spieler @AlteStaffRolle`\nHolt jemanden aus der Suspendierung."
        ), 
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Allgemeines", 
        value=(
            "`status`\nZeigt die Bot-Latenz und Server-Auslastung.\n\n"
            "`ping`\nSchneller Funktionstest."
        ), 
        inline=False
    )
    
    embed.set_footer(text=f"Abgerufen von {ctx.author.name}")
    await ctx.send(embed=embed)

token = os.environ.get('DISCORD_TOKEN')
if token:
    bot.run(token)
else:
    print("❌ FEHLER: Kein DISCORD_TOKEN in den Environment Variables gefunden!")
