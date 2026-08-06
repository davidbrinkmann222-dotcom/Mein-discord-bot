import discord
from discord import app_commands
import datetime

# Speicher für Voice-Zeiten
vc_zeiten = {}
tages_vc_striche = {}

# ==================== CONFIGURATION ====================
STRICH_ROLLEN = [
    "| Strich 1",
    "| Strich 2",
    "| Strich 3",
    "| Strich 4",
    "| Strich 5"
]

HIGHSTAFF_ROLLEN = [
    "┗⎯⎯⎯|🔴|HIGHTEAM|🔴|⎯⎯⎯┑",
    "┗⎯⎯⎯|▪️|PROJEKT LEAD|▪️|⎯⎯⎯┓",
    "┗⎯⎯⎯|▪️|REAL CREATORS|▪️|⎯⎯⎯┓"
]

REQUEST_KANAL_NAME = "uprank-requests"


# ==================== BESTÄTIGUNGS-BUTTONS (SICHERHEITSABFRAGE) ====================
class ConfirmUprankView(discord.ui.View):
    def __init__(self, target_user: discord.Member, selected_role: discord.Role, original_message: discord.Message):
        super().__init__(timeout=60) # 60 Sekunden Zeit zum Bestätigen
        self.target_user = target_user
        self.selected_role = selected_role
        self.original_message = original_message

    @discord.ui.button(label="✅ Ja, Bestätigen & Vergeben", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Nur das Highstaff-Team kann Anfragen bearbeiten!", ephemeral=True)
            return

        # 1. Strich-Rollen beim Spieler entfernen
        for r_name in STRICH_ROLLEN:
            rolle = discord.utils.get(interaction.guild.roles, name=r_name)
            if rolle and rolle in self.target_user.roles:
                await self.target_user.remove_roles(rolle)

        # 2. Neue Rang-Rolle vergeben
        await self.target_user.add_roles(self.selected_role)

        # 3. Originale Antrag-Nachricht aktualisieren & deaktivieren
        embed = self.original_message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ UPRANK GENEHMIGT"
        embed.add_field(name="Neuer Rang", value=self.selected_role.mention, inline=False)
        embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=False)

        await self.original_message.edit(embed=embed, view=None)

        # 4. Bestätigungsnachricht anpassen
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(
            content=f"🎉 **Erfolg!** {self.target_user.mention} hat die Rolle {self.selected_role.mention} erhalten. Striche wurden zurückgesetzt!", 
            view=self
        )

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Nur das Highstaff-Team kann Anfragen bearbeiten!", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(content="❌ Vorgehen abgebrochen. Es wurden keine Rollen verändert.", view=self)


# ==================== ANTRAGS-BUTTONS (NUR FÜR ABLEHNEN) ====================
class UprankRequestView(discord.ui.View):
    def __init__(self, target_user: discord.Member):
        super().__init__(timeout=None)
        self.target_user = target_user

    @discord.ui.button(label="❌ Antrag Ablehnen", style=discord.ButtonStyle.red, custom_id="uprank_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Nur das Highstaff-Team kann Anfragen bearbeiten!", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ UPRANK ABGELEHNT"
        embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=False)

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"❌ Der Uprank-Antrag für {self.target_user.mention} wurde abgelehnt.")


# ==================== MAIN SETUP ====================
def setup_rangsystem(bot):

    # Hilfsfunktion: Einzeiligen Strich vergeben
    async def add_strike(member: discord.Member) -> str:
        current_level = 0
        for index, role_name in enumerate(STRICH_ROLLEN, start=1):
            if any(r.name == role_name for r in member.roles):
                current_level = index
        
        if current_level >= 5:
            return "MAX_REACHED"

        next_index = current_level
        next_role_name = STRICH_ROLLEN[next_index]

        next_role = discord.utils.get(member.guild.roles, name=next_role_name)
        if not next_role:
            return f"ROLE_NOT_FOUND:{next_role_name}"

        # Alte Strich-Rollen entfernen
        for r_name in STRICH_ROLLEN:
            old_role = discord.utils.get(member.guild.roles, name=r_name)
            if old_role and old_role in member.roles:
                await member.remove_roles(old_role)

        # Neue Rolle vergeben
        await member.add_roles(next_role)
        return "SUCCESS"

    # EVENT: REAKTION AUF ANTWORT-NACHRICHTEN
    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if message.reference and message.channel.name == REQUEST_KANAL_NAME:
            try:
                referenced_msg = await message.channel.fetch_message(message.reference.message_id)
            except Exception:
                return

            if referenced_msg.author == bot.user and referenced_msg.embeds:
                if not any(r.name in HIGHSTAFF_ROLLEN for r in message.author.roles):
                    await message.channel.send("❌ Nur das Highstaff-Team kann auf Anträge antworten!", delete_after=5)
                    return

                if not message.role_mentions:
                    await message.channel.send("⚠️ Bitte antworte und erwähne die Rolle (z. B. `@NeuerRang`), die vergeben werden soll!", delete_after=8)
                    return

                selected_role = message.role_mentions[0]

                embed = referenced_msg.embeds[0]
                target_user = None
                
                for field in embed.fields:
                    if field.name == "Spieler":
                        import re
                        match = re.search(r'`(\d+)`', field.value)
                        if match:
                            user_id = int(match.group(1))
                            target_user = message.guild.get_member(user_id)

                if not target_user:
                    await message.channel.send("❌ Spieler konnte nicht gefunden werden!", delete_after=5)
                    return

                confirm_view = ConfirmUprankView(target_user=target_user, selected_role=selected_role, original_message=referenced_msg)
                
                await message.reply(
                    f"❓ **Bist du sicher?**\n\n"
                    f"• **Spieler:** {target_user.mention}\n"
                    f"• **Neue Rolle:** {selected_role.mention}\n"
                    f"• **Aktion:** Alle 5 Striche werden zurückgesetzt.",
                    view=confirm_view
                )

        await bot.process_commands(message)

    # VOICE STATE UPDATE
    @bot.event
    async def on_voice_state_update(member, before, after):
        if member.bot:
            return

        heute = datetime.date.today()
        user_id = member.id

        if before.channel is None and after.channel is not None:
            vc_zeiten[user_id] = datetime.datetime.now()

        elif before.channel is not None and after.channel is None:
            if user_id in vc_zeiten:
                start_zeit = vc_zeiten.pop(user_id)
                dauer = datetime.datetime.now() - start_zeit
                stunden = int(dauer.total_seconds() // 3600)

                if stunden >= 1:
                    user_stats = tages_vc_striche.get(user_id, {"date": heute, "count": 0})
                    if user_stats["date"] != heute:
                        user_stats = {"date": heute, "count": 0}

                    mögliche_striche = min(stunden, 2 - user_stats["count"])

                    for _ in range(mögliche_striche):
                        res = await add_strike(member)
                        if res == "SUCCESS":
                            user_stats["count"] += 1
                            tages_vc_striche[user_id] = user_stats

    # COMMAND: /givestrike MIT VARIABLE ANZAHL
    @bot.tree.command(name="givestrike", description="Vergibt manuell Striche an einen Spieler")
    @app_commands.describe(
        spieler="Der Spieler, der die Striche erhält",
        anzahl="Anzahl der Striche (Standard ist 1)"
    )
    async def givestrike(interaction: discord.Interaction, spieler: discord.Member, anzahl: int = 1):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Du hast keine Berechtigung dafür!", ephemeral=True)
            return

        if anzahl <= 0:
            await interaction.response.send_message("⚠️ Die Anzahl muss mindestens 1 sein!", ephemeral=True)
            return

        vergebene_striche = 0
        letzter_status = ""

        # Vergabe-Schleife für die gewünschte Anzahl an Strichen
        for _ in range(anzahl):
            res = await add_strike(spieler)
            letzter_status = res
            if res == "SUCCESS":
                vergebene_striche += 1
            elif res == "MAX_REACHED" or res.startswith("ROLE_NOT_FOUND"):
                break

        if vergebene_striche > 0:
            await interaction.response.send_message(f"🎓 **{spieler.mention}** hat erfolgreich **{vergebene_striche} Strich(e)** erhalten!")
        elif letzter_status == "MAX_REACHED":
            await interaction.response.send_message(f"⚠️ **{spieler.mention}** hat bereits alle 5 Striche!", ephemeral=True)
        elif letzter_status.startswith("ROLE_NOT_FOUND"):
            role_name = letzter_status.split(":")[1]
            await interaction.response.send_message(f"❌ Die Rolle `{role_name}` existiert auf dem Server nicht! Bitte erstelle sie exakt so.", ephemeral=True)

    # COMMAND: /uprankrequest
    @bot.tree.command(name="uprankrequest", description="Fordere einen Uprank an")
    async def uprankrequest(interaction: discord.Interaction):
        hat_strich_5 = any(r.name == STRICH_ROLLEN[4] for r in interaction.user.roles)

        if not hat_strich_5:
            await interaction.response.send_message("❌ Du benötigst **5 Striche**, um einen Uprank anzufordern!", ephemeral=True)
            return

        request_kanal = discord.utils.get(interaction.guild.text_channels, name=REQUEST_KANAL_NAME)
        if not request_kanal:
            await interaction.response.send_message(f"❌ Kanal `{REQUEST_KANAL_NAME}` nicht gefunden!", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 NEUER UPRANK-ANTRAG",
            description=(
                f"Der Spieler {interaction.user.mention} hat **5 Striche** und fordert einen Uprank an!\n\n"
                f"📌 **ANLEITUNG FÜR HIGHSTAFF:**\n"
                f"1. Antworte auf diese Nachricht (Reply).\n"
                f"2. Pinge/Erwähne die Rolle, die der Spieler erhalten soll (z. B. `@NeuerRang`).\n"
                f"3. Bestätige im Anschluss die Abfrage mit dem Button!"
            ),
            color=discord.Color.gold()
        )
        embed.add_field(name="Spieler", value=f"{interaction.user.name} (`{interaction.user.id}`)", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await request_kanal.send(embed=embed, view=UprankRequestView(target_user=interaction.user))
        await interaction.response.send_message("✅ Uprank-Antrag übermittelt!", ephemeral=True)
