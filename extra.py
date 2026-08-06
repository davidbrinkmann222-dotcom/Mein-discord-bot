import discord
from discord import app_commands
import random
import datetime

# Speicher für die RP-Steckbriefe
steckbriefe = {}

# ==================== 🎫 TICKET SYSTEM BUTTON ====================
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket öffnen", style=discord.ButtonStyle.green, custom_id="ticket_button")
    async def ticket_erstellen(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # Prüfen, ob der Kanal schon existiert
        channel_name = f"ticket-{user.name}".lower()
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        
        if existing_channel:
            await interaction.response.send_message(f"❌ Du hast bereits ein offenes Ticket: {existing_channel.mention}", ephemeral=True)
            return

        # Berechtigungen für das Ticket festlegen
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Ticket-Kanal erstellen
        ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"🎫 Ticket von {user.name}",
            description="Willkommen! Ein Teammitglied wird sich in Kürze um dein Anliegen kümmern.\n\nVerwende `/ticket_schliessen`, um dieses Ticket zu beenden.",
            color=discord.Color.green()
        )
        await ticket_channel.send(content=f"{user.mention}", embed=embed)
        await interaction.response.send_message(f"✅ Dein Ticket wurde erstellt: {ticket_channel.mention}", ephemeral=True)


def setup_extra_commands(bot):

    # ==================== 🎫 TICKET BEFEHLE ====================

    @bot.tree.command(name="ticket_senden", description="Sendet die Ticket-Erstellungs-Nachricht in den Kanal")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_senden(interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Support & RP-Anträge",
            description="Klicke auf den Button unten, um ein privates Ticket mit dem Team zu öffnen!",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=embed, view=TicketButton())
        await interaction.response.send_message("✅ Ticket-Button gesendet!", ephemeral=True)

    @bot.tree.command(name="ticket_schliessen", description="Schließt das aktuelle Ticket")
    async def ticket_schliessen(interaction: discord.Interaction):
        if "ticket-" in interaction.channel.name:
            await interaction.response.send_message("🔒 Dieses Ticket wird in 5 Sekunden gelöscht...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Dieser Befehl kann nur in einem Ticket-Kanal genutzt werden!", ephemeral=True)


    # ==================== 🛡️ MODERATION & ROLLEN ====================

    @bot.tree.command(name="rolle_geben", description="Gibt einem Mitglied eine bestimmte Rolle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rolle_geben(interaction: discord.Interaction, spieler: discord.Member, rolle: discord.Role):
        if rolle in spieler.roles:
            await interaction.response.send_message(f"❌ {spieler.mention} hat die Rolle {rolle.mention} bereits!", ephemeral=True)
            return
        
        await spieler.add_roles(rolle)
        await interaction.response.send_message(f"✅ Rolle {rolle.mention} wurde {spieler.mention} gegeben!")

    @bot.tree.command(name="rolle_nehmen", description="Entzieht einem Mitglied eine bestimmte Rolle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rolle_nehmen(interaction: discord.Interaction, spieler: discord.Member, rolle: discord.Role):
        if rolle not in spieler.roles:
            await interaction.response.send_message(f"❌ {spieler.mention} hat die Rolle {rolle.mention} gar nicht!", ephemeral=True)
            return
        
        await spieler.remove_roles(rolle)
        await interaction.response.send_message(f"✅ Rolle {rolle.mention} wurde {spieler.mention} entfernt!")

    @bot.tree.command(name="mute", description="Schickt ein Mitglied für eine bestimmte Zeit in eine Pause")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute_slash(interaction: discord.Interaction, spieler: discord.Member, minuten: int, grund: str = "Kein Grund angegeben"):
        dauer = datetime.timedelta(minutes=minuten)
        await spieler.timeout(dauer, reason=grund)
        
        embed = discord.Embed(
            title="🤫 Mitglied stummgeschaltet",
            description=f"{spieler.mention} wurde für **{minuten} Minuten** stummgeschaltet.\n**Grund:** {grund}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="unmute", description="Hebt den Mute eines Mitglieds auf")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute_slash(interaction: discord.Interaction, spieler: discord.Member):
        await spieler.timeout(None)
        await interaction.response.send_message(f"🔊 Mute für {spieler.mention} wurde aufgehoben!")


    # ==================== 📢 KREATIVE & RP BEFEHLE ====================

    @bot.tree.command(name="embed_ersteller", description="Erstelle eine schöne Ankündigung als Embed")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed_ersteller(interaction: discord.Interaction, titel: str, nachricht: str, farbe: str = "blau"):
        farben_dict = {
            "blau": discord.Color.blue(),
            "rot": discord.Color.red(),
            "grün": discord.Color.green(),
            "gelb": discord.Color.gold(),
            "lila": discord.Color.purple()
        }
        gewaehlte_farbe = farben_dict.get(farbe.lower(), discord.Color.blue())

        embed = discord.Embed(
            title=titel,
            description=nachricht,
            color=gewaehlte_farbe
        )
        embed.set_footer(text=f"Ankündigung von {interaction.user.name}")
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Ankündigung erfolgreich gesendet!", ephemeral=True)

    @bot.tree.command(name="sozialstunden", description="Verhängt zufällige RP-Sozialstunden für jemanden")
    async def sozialstunden(interaction: discord.Interaction, spieler: discord.Member, grund: str):
        stunden = random.randint(1, 15)
        embed = discord.Embed(
            title="⚖️ RP-Gerichtsurteil",
            description=f"{spieler.mention} wurde zu **{stunden} Sozialstunden** verdonnert!\n**Vergehen:** {grund}",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)


    # ==================== 🎭 RP STECKBRIEF SYSTEM ====================

    @bot.tree.command(name="steckbrief_erstellen", description="Erstelle deinen RP-Steckbrief für den Server")
    async def steckbrief_erstellen(interaction: discord.Interaction, name: str, alter: int, beruf: str, story: str):
        user_id = interaction.user.id
        steckbriefe[user_id] = {"name": name, "alter": alter, "beruf": beruf, "story": story}

        embed = discord.Embed(title="✅ RP-Steckbrief gespeichert!", color=discord.Color.green())
        embed.add_field(name="📛 Name", value=name, inline=True)
        embed.add_field(name="🎂 Alter", value=str(alter), inline=True)
        embed.add_field(name="💼 Beruf", value=beruf, inline=True)
        embed.add_field(name="📖 Story", value=story, inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="steckbrief_zeigen", description="Zeigt den RP-Steckbrief eines Spielers an")
    async def steckbrief_zeigen(interaction: discord.Interaction, spieler: discord.Member = None):
        target = spieler or interaction.user
        if target.id not in steckbriefe:
            await interaction.response.send_message(f"❌ {target.mention} hat noch keinen RP-Steckbrief!", ephemeral=True)
            return

        daten = steckbriefe[target.id]
        embed = discord.Embed(title=f"🎭 RP-Steckbrief von {target.display_name}", color=discord.Color.purple())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="📛 Name", value=daten["name"], inline=True)
        embed.add_field(name="🎂 Alter", value=str(daten["alter"]), inline=True)
        embed.add_field(name="💼 Beruf", value=daten["beruf"], inline=True)
        embed.add_field(name="📖 Story", value=daten["story"], inline=False)
        await interaction.response.send_message(embed=embed)


    # ==================== 📊 UTILITY & INFO BEFEHLE ====================

    @bot.tree.command(name="userinfo", description="Zeigt detaillierte Infos über einen Spieler an")
    async def userinfo_slash(interaction: discord.Interaction, spieler: discord.Member = None):
        target = spieler or interaction.user
        rollen = [r.mention for r in target.roles if r.name != "@everyone"]
        rollen_str = ", ".join(rollen) if rollen else "Keine Rollen"

        embed = discord.Embed(title=f"👤 Userinfo • {target.name}", color=discord.Color.blue())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Discord Tag", value=f"`{target}`", inline=True)
        embed.add_field(name="ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Server beigetreten", value=target.joined_at.strftime("%d.%m.%Y"), inline=False)
        embed.add_field(name="Account erstellt", value=target.created_at.strftime("%d.%m.%Y"), inline=False)
        embed.add_field(name=f"Rollen ({len(rollen)})", value=rollen_str, inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="serverinfo", description="Zeigt Informationen über diesen Discord-Server")
    async def serverinfo_slash(interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"🏰 Serverinfo • {guild.name}", color=discord.Color.gold())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="👥 Mitglieder", value=str(guild.member_count), inline=True)
        embed.add_field(name="💬 Kanäle", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unbekannt", inline=True)
        embed.add_field(name="🚀 Boost-Level", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="📅 Erstellt am", value=guild.created_at.strftime("%d.%m.%Y"), inline=True)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="avatar", description="Zeigt den Avatar eines Nutzers in groß an")
    async def avatar_slash(interaction: discord.Interaction, spieler: discord.Member = None):
        target = spieler or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar von {target.name}", color=discord.Color.dark_theme())
        embed.set_image(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="clear", description="Lösche eine bestimmte Anzahl an Nachrichten")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_slash(interaction: discord.Interaction, anzahl: int):
        if anzahl < 1 or anzahl > 100:
            await interaction.response.send_message("❌ Bitte gib eine Zahl zwischen 1 und 100 an!", ephemeral=True)
            return
        deleted = await interaction.channel.purge(limit=anzahl)
        await interaction.response.send_message(f"✅ Es wurden `{len(deleted)}` Nachrichten gelöscht.", ephemeral=True)
