import discord
from discord import app_commands
import datetime

# Speicher-Mappen
vc_zeiten = {}          # Speichert Beitrittszeit: {user_id: datetime}
tages_vc_striche = {}   # Speichert VC-Striche pro Tag: {user_id: {"date": date, "count": int}}

# ==================== CONFIG: ROLLEN-NAMEN ====================
STRICH_ROLLEN = [
    "│ Strich 1",
    "│ Strich 2",
    "│ Strich 3",
    "│ Strich 4",
    "│ Strich 5"
]

# Deine 3 Highstaff-Rollen
HIGHSTAFF_ROLLEN = [
    "┗⎯⎯⎯|🔴|HIGHTEAM|🔴|⎯⎯⎯┑",
    "┗⎯⎯⎯|▪️|PROJEKT LEAD|▪️|⎯⎯⎯┓",
    "┗⎯⎯⎯|▪️|REAL CREATORS|▪️|⎯⎯⎯┓"
]

REQUEST_KANAL_NAME = "uprank-requests"


# ==================== 📩 UPRANK REQUEST BUTTONS ====================
class UprankRequestView(discord.ui.View):
    def __init__(self, target_user: discord.Member):
        super().__init__(timeout=None)
        self.target_user = target_user

    @discord.ui.button(label="✅ Genehmigen (Uprank)", style=discord.ButtonStyle.green, custom_id="uprank_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Nur das Highstaff-Team kann Anfragen bearbeiten!", ephemeral=True)
            return

        # Alle Strich-Rollen beim User entfernen
        for r_name in STRICH_ROLLEN:
            rolle = discord.utils.get(interaction.guild.roles, name=r_name)
            if rolle and rolle in self.target_user.roles:
                await self.target_user.remove_roles(rolle)

        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ UPRANK GENEHMIGT"
        embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=False)
        
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"🎉 Der Uprank für {self.target_user.mention} wurde genehmigt! Die Striche wurden zurückgesetzt.")

    @discord.ui.button(label="❌ Ablehnen", style=discord.ButtonStyle.red, custom_id="uprank_deny")
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

    # Hilfsfunktion: Vergibt sauber den nächsten Strich
    async def vergebe_naechsten_strich(member: discord.Member, anzahl: int = 1):
        # 1. Aktuelle Strich-Anzahl ermitteln
        aktuelle_striche = 0
        for i, r_name in enumerate(STRICH_ROLLEN, start=1):
            if any(r.name == r_name for r in member.roles):
                aktuelle_striche = i

        # Wenn bereits 5 Striche vorhanden sind
        if aktuelle_striche >= 5:
            return False

        # Neue Anzahl berechnen (max. 5)
        neue_anzahl = min(aktuelle_striche + anzahl, 5)

        # 2. Alte Strich-Rollen vorsichtshalber entfernen
        for r_name in STRICH_ROLLEN:
            alte_rolle = discord.utils.get(member.guild.roles, name=r_name)
            if alte_rolle and alte_rolle in member.roles:
                await member.remove_roles(alte_rolle)

        # 3. Neue Strich-Rolle vergeben
        ziel_rollen_name = STRICH_ROLLEN[neue_anzahl - 1]
        neue_rolle = discord.utils.get(member.guild.roles, name=ziel_rollen_name)
        
        if neue_rolle:
            await member.add_roles(neue_rolle)
            return True
            
        return False

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
                stunden_im_vc = int(dauer.total_seconds() // 3600)

                if stunden_im_vc >= 1:
                    user_stats = tages_vc_striche.get(user_id, {"date": heute, "count": 0})
                    if user_stats["date"] != heute:
                        user_stats = {"date": heute, "count": 0}

                    verfuegbare_vc_striche = min(stunden_im_vc, 2 - user_stats["count"])

                    if verfuegbare_vc_striche > 0:
                        erfolg = await vergebe_naechsten_strich(member, verfuegbare_vc_striche)
                        if erfolg:
                            user_stats["count"] += verfuegbare_vc_striche
                            tages_vc_striche[user_id] = user_stats

    @bot.tree.command(name="givestrike", description="Vergibt manuell einen Strich (z.B. nach mündlicher Prüfung)")
    @app_commands.describe(spieler="Der Spieler, der den Strich erhält")
    async def givestrike(interaction: discord.Interaction, spieler: discord.Member):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Nur Mitglieder des Highstaffs dürfen Striche vergeben!", ephemeral=True)
            return

        erfolg = await vergebe_naechsten_strich(spieler, 1)
        if erfolg:
            await interaction.response.send_message(f"🎓 {interaction.user.mention} hat **{spieler.mention}** erfolgreich einen Strich vergeben!")
        else:
            await interaction.response.send_message(f"⚠️ {spieler.mention} hat bereits alle 5 Striche!", ephemeral=True)

    @bot.tree.command(name="uprankrequest", description="Fordere einen Uprank an, sobald du 5 Striche hast")
    async def uprankrequest(interaction: discord.Interaction):
        hat_strich_5 = any(r.name == STRICH_ROLLEN[4] for r in interaction.user.roles)
        
        if not hat_strich_5:
            await interaction.response.send_message("❌ Du benötigst **5 Striche**, um einen Uprank anzufordern!", ephemeral=True)
            return

        request_kanal = discord.utils.get(interaction.guild.text_channels, name=REQUEST_KANAL_NAME)
        if not request_kanal:
            await interaction.response.send_message(f"❌ Kanal `{REQUEST_KANAL_NAME}` wurde nicht gefunden! Bitte erstelle ihn.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 NEUER UPRANK-ANTRAG",
            description=f"Der Spieler {interaction.user.mention} hat **5 Striche** gesammelt und fordert einen Uprank an!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Spieler", value=f"{interaction.user.name} (`{interaction.user.id}`)", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await request_kanal.send(embed=embed, view=UprankRequestView(target_user=interaction.user))
        await interaction.response.send_message("✅ Dein Uprank-Antrag wurde erfolgreich an das Highstaff-Team übermittelt!", ephemeral=True)
