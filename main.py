import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

# Importiere deine Module
from extra import setup_extra_commands
from rangsystem import setup_rangsystem
from warteraum import handle_warteraum
from ki_system import setup_ki_commands
from moderation import setup_moderation

# Kleiner Webserver für Render
app = Flask('')

@app.route('/')
def home():
    return "Bot läuft!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# WICHTIG: Hier sind jetzt alle Intents (auch voice_states für den Warteraum) aktiv!
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True  # Zwingend notwendig für den Warteraum!

bot = commands.Bot(command_prefix=["/", "^", "$"], intents=intents, help_command=None)

setup_ki_commands(bot)
setup_moderation(bot)

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
    
    try:
        setup_extra_commands(bot)
        setup_rangsystem(bot)
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash-Commands erfolgreich mit Discord synchronisiert!")
    except Exception as e:
        print(f"❌ Fehler beim Synchronisieren der Slash-Commands: {e}")

# ==================== WARTERAUM EVENT ====================
@bot.event
async def on_voice_state_update(member, before, after):
    # Leitet den Voice-Wechsel direkt an deine warteraum.py weiter
    await handle_warteraum(member, before, after, bot)


# ==================== HELPER LOGIKEN ====================
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

async def do_downrank(author, guild, target, neue_rolle, grund):
    if not hat_rolle_aus_liste(author, ERLAUBTE_STAFF_ROLLEN) and author != guild.owner:
        return False, "❌ **Fehler:** Keine Berechtigung!"
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        return False, "❌ **System-Schutz:** Die Führungsebene ist geschützt!"
    if author.top_role <= target.top_role and author != guild.owner:
        return False, "❌ **Fehler:** Dein Rang ist zu niedrig!"

    alte_rolle = target.top_role
    try:
        await target.remove_roles(alte_rolle)
        await target.add_roles(neue_rolle)
        embed = discord.Embed(
            title="📉 SYSTEM X EH RP • DEGRADIERUNG", 
            description=f"Ein Teammitglied wurde im Rang zurückgestuft.\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=discord.Color.from_rgb(230, 126, 34)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👤 Betroffener", value=f"{target.mention}\n`({target.id})`", inline=True)
        embed.add_field(name="✍️ Ausgeführt von", value=f"{author.mention}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="🔼 Alter Rang", value=f"`{alte_rolle.name}`", inline=True)
        embed.add_field(name="🔽 Neuer Rang", value=f"{neue_rolle.mention}", inline=True)
        embed.add_field(name="📝 Begründung", value=f"```text\n{grund}\n```", inline=False)
        embed.set_footer(text="SYSTEM X EH RP • Personalverwaltung", icon_url=guild.icon.url if guild.icon else None)
        return True, embed
    except discord.Forbidden:
        return False, "❌ **System-Fehler:** Rechte fehlen!"

async def do_teamkick(author, guild, target, grund):
    if not hat_rolle_aus_liste(author, ERLAUBTE_STAFF_ROLLEN) and author != guild.owner:
        return False, "❌ **Fehler:** Keine Berechtigung!"
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        return False, "❌ **System-Schutz:** Führungsebene geschützt!"
    if author.top_role <= target.top_role and author != guild.owner:
        return False, "❌ **Fehler:** Dein Rang ist zu niedrig!"

    try:
        entfernte_rollen = []
        for index_rolle in target.roles:
            if index_rolle.name not in NORMALE_SPIELER_ROLLEN and index_rolle.name not in PROJEKTLEITUNG_ROLLEN:
                try:
                    await target.remove_roles(index_rolle)
                    entfernte_rollen.append(index_rolle.name)
                except discord.Forbidden:
                    continue
        
        embed = discord.Embed(
            title="🚪 SYSTEM X EH RP • TEAM-AUSSCHLUSS", 
            description=f"Ein Mitglied wurde aus dem Team entfernt.\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=discord.Color.from_rgb(231, 76, 60)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👤 Ex-Mitglied", value=f"{target.mention}\n`({target.id})`", inline=True)
        embed.add_field(name="✍️ Ausgeführt von", value=f"{author.mention}", inline=True)
        
        rollen_text = ", ".join([f"`{r}`" for r in entfernte_rollen]) if entfernte_rollen else "*Keine Team-Ränge gefunden*"
        embed.add_field(name="📋 Entfernte Ränge", value=rollen_text, inline=False)
        embed.add_field(name="📝 Begründung", value=f"```text\n{grund}\n```", inline=False)
        embed.set_footer(text="SYSTEM X EH RP • Sanktionsverwaltung", icon_url=guild.icon.url if guild.icon else None)
        return True, embed
    except Exception as e:
        return False, f"❌ Fehler beim Teamkick: {e}"

async def do_warn(author, guild, target, grund):
    if not hat_rolle_aus_liste(author, ERLAUBTE_STAFF_ROLLEN) and author != guild.owner:
        return False, "❌ **Fehler:** Keine Berechtigung!"
        
    if target.id not in verwarnungen_speicher:
        verwarnungen_speicher[target.id] = 0
    verwarnungen_speicher[target.id] += 1

    embed = discord.Embed(
        title="⚠️ SYSTEM X EH RP • VERWARNUNG", 
        description=f"Gegen ein Mitglied wurde eine Verwarnung ausgesprochen.\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=discord.Color.from_rgb(241, 196, 15)
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="👤 Betroffener", value=f"{target.mention}", inline=True)
    embed.add_field(name="📊 Aktuelle Warns", value=f"`{verwarnungen_speicher[target.id]}`", inline=True)
    embed.add_field(name="✍️ Ausgestellt von", value=f"{author.mention}", inline=True)
    embed.add_field(name="📝 Grund", value=f"```text\n{grund}\n```", inline=False)
    embed.set_footer(text="SYSTEM X EH RP • Aktenführung", icon_url=guild.icon.url if guild.icon else None)
    return True, embed

async def do_strike(author, guild, target, grund):
    if not hat_rolle_aus_liste(author, ERLAUBTE_STAFF_ROLLEN) and author != guild.owner:
        return False, "❌ **Fehler:** Keine Berechtigung!"
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        return False, "❌ Führungsebene kann keine Strikes erhalten!"

    embed = discord.Embed(
        title="🚨 SYSTEM X EH RP • TEAM-STRIKE", 
        description=f"Ein Team-Strike wurde in der Akte vermerkt!\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        color=discord.Color.from_rgb(155, 89, 182)
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="👤 Staff-Mitglied", value=f"{target.mention}", inline=True)
    embed.add_field(name="✍️ Ausgestellt von", value=f"{author.mention}", inline=True)
    embed.add_field(name="📝 Begründung", value=f"```text\n{grund}\n```", inline=False)
    embed.set_footer(text="SYSTEM X EH RP • Team-Akte", icon_url=guild.icon.url if guild.icon else None)
    return True, embed

async def do_suspend(author, guild, target, grund):
    if not hat_rolle_aus_liste(author, ERLAUBTE_STAFF_ROLLEN) and author != guild.owner:
        return False, "❌ **Fehler:** Keine Berechtigung!"
    if hat_rolle_aus_liste(target, PROJEKTLEITUNG_ROLLEN):
        return False, "❌ Führungsebene kann nicht suspendiert werden!"
       
    try:
        suspend_rolle = discord.utils.get(guild.roles, name=SUSPEND_ROLLE_NAME)
        if not suspend_rolle:
            return False, f"❌ Fehler: Bitte erstelle zuerst eine Rolle namens `{SUSPEND_ROLLE_NAME}` auf deinem Server!"
            
        for index_rolle in target.roles:
            if index_rolle.name not in NORMALE_SPIELER_ROLLEN:
                try:
                    await target.remove_roles(index_rolle)
                except:
                    continue
            
        await target.add_roles(suspend_rolle)
        
        embed = discord.Embed(
            title="🛑 SYSTEM X EH RP • DIENSTSUSPENDIERUNG", 
            description=f"Alle Dienst-Rechte wurden vorübergehend entzogen.\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=discord.Color.from_rgb(52, 73, 94)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👤 Betroffener", value=f"{target.mention}", inline=True)
        embed.add_field(name="🔒 Status", value="`Suspendiert`", inline=True)
        embed.add_field(name="✍️ Anordnung von", value=f"{author.mention}", inline=True)
        embed.add_field(name="📝 Grund / Aktenzeichen", value=f"```text\n{grund}\n```", inline=False)
        embed.set_footer(text="SYSTEM X EH RP • Internal Affairs", icon_url=guild.icon.url if guild.icon else None)
        return True, embed
    except Exception as e:
        return False, f"❌ Fehler bei der Suspendierung: {e}"

async def do_unsuspend(author, guild, target, alte_rolle):
    if not hat_rolle_aus_liste(author, ERLAUBTE_STAFF_ROLLEN) and author != guild.owner:
        return False, "❌ **Fehler:** Keine Berechtigung!"
      
    try:
        suspend_rolle = discord.utils.get(guild.roles, name=SUSPEND_ROLLE_NAME)
        if suspend_rolle and suspend_rolle in target.roles:
            await target.remove_roles(suspend_rolle)
            
        await target.add_roles(alte_rolle)
        
        embed = discord.Embed(
            title="🔓 SYSTEM X EH RP • REINTEGRATION", 
            description=f"Die Suspendierung wurde aufgehoben.\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
            color=discord.Color.from_rgb(52, 152, 219)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👤 Mitarbeiter", value=f"{target.mention}", inline=True)
        embed.add_field(name="✅ Wiederhergestellt", value=f"{alte_rolle.mention}", inline=True)
        embed.add_field(name="✍️ Freigegeben von", value=f"{author.mention}", inline=False)
        embed.set_footer(text="SYSTEM X EH RP • Personalverwaltung", icon_url=guild.icon.url if guild.icon else None)
        return True, embed
    except Exception as e:
        return False, f"❌ Fehler beim Aufheben der Suspendierung: {e}"

# ==================== BEFEHLE (PRÄFIX & SLASH) ====================

# --- UPRANK ---
@bot.command(name="uprank")
async def uprank_prefix(ctx, target: discord.Member = None, neue_rolle: discord.Role = None, *, grund: str = "Kein Grund angegeben"):
    if not target or not neue_rolle:
        await ctx.send(f"❌ **Fehler:** Nutzen: `{ctx.prefix}uprank @Spieler @Rolle [Grund]`")
        return
    success, res = await do_uprank(ctx.author, ctx.guild, target, neue_rolle, grund)
    if success: await ctx.send(embed=res)
    else: await ctx.send(res)

@bot.tree.command(name="uprank", description="Befördere ein Teammitglied")
async def uprank_slash(interaction: discord.Interaction, target: discord.Member, neue_rolle: discord.Role, grund: str = "Kein Grund angegeben"):
    success, res = await do_uprank(interaction.user, interaction.guild, target, neue_rolle, grund)
    if success: await interaction.response.send_message(embed=res)
    else: await interaction.response.send_message(res, ephemeral=True)

# --- DOWNRANK ---
@bot.command(name="downrank")
async def downrank_prefix(ctx, target: discord.Member = None, neue_rolle: discord.Role = None, *, grund: str = "Kein Grund angegeben"):
    if not target or not neue_rolle:
        await ctx.send(f"❌ **Fehler:** Nutzen: `{ctx.prefix}downrank @Spieler @Rolle [Grund]`")
        return
    success, res = await do_downrank(ctx.author, ctx.guild, target, neue_rolle, grund)
    if success: await ctx.send(embed=res)
    else: await ctx.send(res)

@bot.tree.command(name="downrank", description="Degradiere ein Teammitglied")
async def downrank_slash(interaction: discord.Interaction, target: discord.Member, neue_rolle: discord.Role, grund: str = "Kein Grund angegeben"):
    success, res = await do_downrank(interaction.user, interaction.guild, target, neue_rolle, grund)
    if success: await interaction.response.send_message(embed=res)
    else: await interaction.response.send_message(res, ephemeral=True)

# --- TEAMKICK ---
@bot.command(name="teamkick")
async def teamkick_prefix(ctx, target: discord.Member = None, *, grund: str = "Kein Grund angegeben"):
    if not target:
        await ctx.send(f"❌ **Fehler:** Nutzen: `{ctx.prefix}teamkick @Spieler [Grund]`")
        return
    success, res = await do_teamkick(ctx.author, ctx.guild, target, grund)
    if success: await ctx.send(embed=res)
    else: await ctx.send(res)

@bot.tree.command(name="teamkick", description="Entferne alle Team-Ränge eines Mitglieds")
async def teamkick_slash(interaction: discord.Interaction, target: discord.Member, grund: str = "Kein Grund angegeben"):
    success, res = await do_teamkick(interaction.user, interaction.guild, target, grund)
    if success: await interaction.response.send_message(embed=res)
    else: await interaction.response.send_message(res, ephemeral=True)

# --- WARN ---
@bot.command(name="warn")
async def warn_prefix(ctx, target: discord.Member = None, *, grund: str = "Kein Grund angegeben"):
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}warn @Spieler [Grund]`")
        return
    success, res = await do_warn(ctx.author, ctx.guild, target, grund)
    if success: await ctx.send(embed=res)
    else: await ctx.send(res)

@bot.tree.command(name="warn", description="Erteile eine Verwarnung")
async def warn_slash(interaction: discord.Interaction, target: discord.Member, grund: str = "Kein Grund angegeben"):
    success, res = await do_warn(interaction.user, interaction.guild, target, grund)
    if success: await interaction.response.send_message(embed=res)
    else: await interaction.response.send_message(res, ephemeral=True)

# --- CLEARWARNS ---
@bot.command(name="clearwarns")
async def clearwarns_prefix(ctx, target: discord.Member = None):
    if not hat_rolle_aus_liste(ctx.author, ERLAUBTE_STAFF_ROLLEN) and ctx.author != ctx.guild.owner: return
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}clearwarns @Spieler`")
        return
    verwarnungen_speicher[target.id] = 0
    await ctx.send(f"✅ Alle Verwarnungen für {target.mention} wurden gelöscht.")

@bot.tree.command(name="clearwarns", description="Lösche alle Verwarnungen eines Spielers")
async def clearwarns_slash(interaction: discord.Interaction, target: discord.Member):
    if not hat_rolle_aus_liste(interaction.user, ERLAUBTE_STAFF_ROLLEN) and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("❌ **Fehler:** Keine Berechtigung!", ephemeral=True)
        return
    verwarnungen_speicher[target.id] = 0
    await interaction.response.send_message(f"✅ Alle Verwarnungen für {target.mention} wurden gelöscht.")

# --- STRIKE ---
@bot.command(name="strike")
async def strike_prefix(ctx, target: discord.Member = None, *, grund: str = "Fehlverhalten im Dienst"):
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}strike @Spieler [Grund]`")
        return
    success, res = await do_strike(ctx.author, ctx.guild, target, grund)
    if success: await ctx.send(embed=res)
    else: await ctx.send(res)

@bot.tree.command(name="strike", description="Trage einen Team-Strike ein")
async def strike_slash(interaction: discord.Interaction, target: discord.Member, grund: str = "Fehlverhalten im Dienst"):
    success, res = await do_strike(interaction.user, interaction.guild, target, grund)
    if success: await interaction.response.send_message(embed=res)
    else: await interaction.response.send_message(res, ephemeral=True)

# --- SUSPEND ---
@bot.command(name="suspend")
async def suspend_prefix(ctx, target: discord.Member = None, *, grund: str = "Dienstvergehen / Untersuchung"):
    if not target:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}suspend @Spieler [Grund]`")
        return
    success, res = await do_suspend(ctx.author, ctx.guild, target, grund)
    if success: await ctx.send(embed=res)
    else: await ctx.send(res)

@bot.tree.command(name="suspend", description="Suspendiere ein Teammitglied temporär")
async def suspend_slash(interaction: discord.Interaction, target: discord.Member, grund: str = "Dienstvergehen / Untersuchung"):
    success, res = await do_suspend(interaction.user, interaction.guild, target, grund)
    if success: await interaction.response.send_message(embed=res)
    else: await interaction.response.send_message(res, ephemeral=True)

# --- UNSUSPEND ---
@bot.command(name="unsuspend")
async def unsuspend_prefix(ctx, target: discord.Member = None, alte_rolle: discord.Role = None):
    if not target or not alte_rolle:
        await ctx.send(f"❌ Nutzen: `{ctx.prefix}unsuspend @Spieler @AlteStaffRolle`")
        return
    success, res = await do_unsuspend(ctx.author, ctx.guild, target, alte_rolle)
    if success: await ctx.send(embed=res)
    else: await ctx.send(res)

@bot.tree.command(name="unsuspend", description="Hebe eine Suspendierung auf")
async def unsuspend_slash(interaction: discord.Interaction, target: discord.Member, alte_rolle: discord.Role):
    success, res = await do_unsuspend(interaction.user, interaction.guild, target, alte_rolle)
    if success: await interaction.response.send_message(embed=res)
    else: await interaction.response.send_message(res, ephemeral=True)

# --- ALLGEMEINE BEFEHLE ---
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong! 🏓 Dein Bot funktioniert!")

@bot.command(name="hallo")
async def hallo(ctx):
    await ctx.send(f"Hallo {ctx.author.mention}! Schön dich zu sehen.")

@bot.command(name="testjoin")
async def testjoin(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        try:
            vc = await channel.connect()
            await ctx.send(f"✅ Konnte mich erfolgreich mit {channel.name} verbinden!")
            await asyncio.sleep(5)
            await vc.disconnect()
        except Exception as e:
            await ctx.send(f"❌ Fehler beim Verbinden: {e}")
    else:
        await ctx.send("❌ Du musst in einem Sprachkanal sein!")

import discord
from discord import app_commands
from discord.ext import commands

import discord
from discord import app_commands

@bot.tree.command(name="rpstatus", description="Ändert den RP-Status mit einem detaillierten Embed")
@app_commands.describe(zustand="Wähle 'an' oder 'aus'")
@app_commands.choices(zustand=[
    app_commands.Choice(name="An", value="an"),
    app_commands.Choice(name="Aus", value="aus")
])
async def rpstatus(interaction: discord.Interaction, zustand: str):
    role_name = "♕✯ |❘| David | Founder"
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    
    if not role or role not in interaction.user.roles:
        await interaction.response.send_message("❌ Dazu hast du keine Berechtigung! Nur der Founder darf das.", ephemeral=True)
        return

    status_channel = discord.utils.get(interaction.guild.text_channels, name="🌐║status")
    
    if status_channel:
        # Alte Nachrichten im Status-Channel löschen, damit es immer übersichtlich bleibt (optional)
        try:
            await status_channel.purge(limit=5)
        except:
            pass

    if not status_channel:
        await interaction.response.send_message("❌ Den Channel `🌐║status` konnte ich nicht finden!", ephemeral=True)
        return

    # Das detaillierte Embed erstellen
    embed = discord.Embed(title="🌐 ┃ ROLLEPLAY STATUS UPDATE", color=0x00FF00 if zustand == "an" else 0xFF0000)
    
    if zustand == "an":
        embed.description = "Der Server-Status wurde soeben vom Management aktualisiert."
        embed.add_field(name="Status", value="🟢 **AKTIV & OFFEN**", inline=False)
        embed.add_field(name="Informationen", value="• Das Roleplay ist nun offiziell im Gange.\n• Alle RP-Regeln sind ab sofort zu befolgen.\n• Viel Spaß an alle Teilnehmer!", inline=False)
        embed.set_footer(text=f"Aktualisiert von {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await status_channel.send(embed=embed)
        await interaction.response.send_message("✅ RP-Status erfolgreich auf **AN** gesetzt und Embed gesendet!", ephemeral=True)
        
    elif zustand == "aus":
        embed.color = 0xFF0000
        embed.description = "Der Server-Status wurde soeben vom Management aktualisiert."
        embed.add_field(name="Status", value="🔴 **INAKTIV / PAUSE**", inline=False)
        embed.add_field(name="Informationen", value="• Das Roleplay ist vorübergehend pausiert oder beendet.\n• Bitte beachtet die OOC-Regeln in den entsprechenden Chats.\n• Weitere Infos folgen in Kürze.", inline=False)
        embed.set_footer(text=f"Aktualisiert von {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        await status_channel.send(embed=embed)
        await interaction.response.send_message("✅ RP-Status erfolgreich auf **AUS** gesetzt und Embed gesendet!", ephemeral=True)

# 2. Lock und Unlock als Slash-Commands (/lock und /unlock)
@bot.tree.command(name="lock", description="Schließt alle Chats für normale User")
async def lock_channels(interaction: discord.Interaction):
    role_name = "♕✯ |❘| David | Founder"
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    
    if not role or role not in interaction.user.roles:
        await interaction.response.send_message("❌ Dazu hast du keine Berechtigung!", ephemeral=True)
        return

    await interaction.response.send_message("🔒 Alle Kanäle werden geschlossen...", ephemeral=True)
    
    for channel in interaction.guild.text_channels:
        # Entzieht der @everyone-Rolle das Schreibrecht komplett
        await channel.set_permissions(interaction.guild.default_role, send_messages=False)
        
    for channel in interaction.guild.text_channels:
        await channel.send("🔒 **Dieser Chat wurde vom Founder geschlossen!**")


@bot.tree.command(name="unlock", description="Öffnet alle Chats wieder für alle")
async def unlock_channels(interaction: discord.Interaction):
    role_name = "♕✯ |❘| David | Founder"
    role = discord.utils.get(interaction.guild.roles, name=role_name)
    
    if not role or role not in interaction.user.roles:
        await interaction.response.send_message("❌ Dazu hast du keine Berechtigung!", ephemeral=True)
        return

    await interaction.response.send_message("🔓 Alle Kanäle werden wieder geöffnet...", ephemeral=True)
    
    for channel in interaction.guild.text_channels:
        # Setzt das Schreibrecht für @everyone auf Standard zurück
        await channel.set_permissions(interaction.guild.default_role, send_messages=None)
        
    for channel in interaction.guild.text_channels:
        await channel.send("🔓 **Dieser Chat ist wieder geöffnet!**")


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

# ==================== START LOGIK ====================
if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        keep_alive()
        bot.run(token)
    else:
        print("❌ FEHLER: Kein DISCORD_TOKEN in den Environment Variables gefunden!")
