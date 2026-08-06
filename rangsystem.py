import discord
from discord import app_commands
import datetime

# Speicher für Voice-Zeiten
vc_zeiten = {}
tages_vc_striche = {}

# ==================== CONFIGURATION ====================
STRICH_ROLLEN = [
    "│ Strich 1",
    "│ Strich 2",
    "│ Strich 3",
    "│ Strich 4",
    "│ Strich 5"
]

HIGHSTAFF_ROLLEN = [
    "┗⎯⎯⎯|🔴|HIGHTEAM|🔴|⎯⎯⎯┑",
    "┗⎯⎯⎯|▪️|PROJEKT LEAD|▪️|⎯⎯⎯┓",
    "┗⎯⎯⎯|▪️|REAL CREATORS|▪️|⎯⎯⎯┓"
]

REQUEST_KANAL_NAME = "uprank-requests"


# ==================== UPRANK BUTTONS ====================
class UprankRequestView(discord.ui.View):
    def __init__(self, target_user: discord.Member):
        super().__init__(timeout=None)
        self.target_user = target_user

    @discord.ui.button(label="✅ Genehmigen (Uprank)", style=discord.ButtonStyle.green, custom_id="uprank_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Nur das Highstaff-Team kann Anfragen bearbeiten!", ephemeral=True)
            return

        # Striche vom Ziel-User entfernen
        removed_any = False
        for r_name in STRICH_ROLLEN:
            rolle = discord.utils.get(interaction.guild.roles, name=r_name)
            if rolle and rolle in self.target_user.roles:
                await self.target_user.remove_roles(rolle)
                removed_any = True

        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ UPRANK GENEHMIGT"
        embed.add_field(name="Bearbeitet von", value=interaction.user.mention, inline=False)
        
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"🎉 Der Uprank für {self.target_user.mention} wurde genehmigt! Striche wurden zurückgesetzt.")

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

    # Hilfsfunktion: Strich vergeben
    async def add_strike(member: discord.Member) -> str:
        # Welche Strich-Rollen hat der User aktuell?
        current_striche = [r.name for r in member.roles if r.name in STRICH_ROLLEN]
        
        if len(current_striche) >= 5:
            return "MAX_REACHED"

        # Bestimmen, welcher Strich als nächstes kommt
        next_index = len(current_striche) # 0 = Strich 1, 1 = Strich 2 ...
        next_role_name = STRICH_ROLLEN[next_index]

        # Rolle auf Discord suchen
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


    # COMMAND: /givestrike
    @bot.tree.command(name="givestrike", description="Vergibt manuell einen Strich")
    @app_commands.describe(spieler="Der Spieler, der den Strich erhält")
    async def givestrike(interaction: discord.Interaction, spieler: discord.Member):
        if not any(r.name in HIGHSTAFF_ROLLEN for r in interaction.user.roles):
            await interaction.response.send_message("❌ Du hast keine Berechtigung dafür!", ephemeral=True)
            return

        res = await add_strike(spieler)

        if res == "SUCCESS":
            await interaction.response.send_message(f"🎓 **{spieler.mention}** hat erfolgreich einen Strich erhalten!")
        elif res == "MAX_REACHED":
            await interaction.response.send_message(f"⚠️ **{spieler.mention}** hat bereits alle 5 Striche!", ephemeral=True)
        elif res.startswith("ROLE_NOT_FOUND"):
            role_name = res.split(":")[1]
            await interaction.response.send_message(f"❌ Die Rolle `{role_name}` existiert auf dem Server nicht! Bitte erstelle sie exakt so.", ephemeral=True)


    # COMMAND: /uprankrequest
    @bot.tree.command(name="uprankrequest", description="Fordere einen Uprank an")
    async def uprankrequest(interaction: discord.Interaction):
        current_striche = [r.name for r in interaction.user.roles if r.name in STRICH_ROLLEN]

        if len(current_striche) < 5 and STRICH_ROLLEN[4] not in current_striche:
            await interaction.response.send_message("❌ Du benötigst **5 Striche**, um einen Uprank anzufordern!", ephemeral=True)
            return

        request_kanal = discord.utils.get(interaction.guild.text_channels, name=REQUEST_KANAL_NAME)
        if not request_kanal:
            await interaction.response.send_message(f"❌ Kanal `{REQUEST_KANAL_NAME}` nicht gefunden!", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 NEUER UPRANK-ANTRAG",
            description=f"Der Spieler {interaction.user.mention} hat **5 Striche** und fordert einen Uprank an!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Spieler", value=f"{interaction.user.name} (`{interaction.user.id}`)", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await request_kanal.send(embed=embed, view=UprankRequestView(target_user=interaction.user))
        await interaction.response.send_message("✅ Uprank-Antrag übermittelt!", ephemeral=True)
