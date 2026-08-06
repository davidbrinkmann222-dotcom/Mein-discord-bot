import discord
from discord import app_commands
import random

# Funktion, um die neuen Slash-Commands in der main.py zu registrieren
def setup_extra_commands(bot):

    # 🎲 WÜRFEL BEFEHL
    @bot.tree.command(name="wuerfel", description="Würfle eine Zahl von 1 bis 6")
    async def wuerfel_slash(interaction: discord.Interaction):
        zahl = random.randint(1, 6)
        embed = discord.Embed(
            title="🎲 SYSTEM X EH RP • WÜRFEL",
            description=f"{interaction.user.mention} hat eine **{zahl}** gewürfelt!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    # 🪙 MÜNZWURF BEFEHL
    @bot.tree.command(name="muenze", description="Wirf eine Münze (Kopf oder Zahl)")
    async def muenze_slash(interaction: discord.Interaction):
        ergebnis = random.choice(["Kopf 🪙", "Zahl 🪙"])
        embed = discord.Embed(
            title="🪙 SYSTEM X EH RP • MÜNZWURF",
            description=f"Die Münze ist auf **{ergebnis}** gelandet!",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    # 📢 CLEAR / PURGE BEFEHL (Nachrichten löschen)
    @bot.tree.command(name="clear", description="Lösche eine bestimmte Anzahl an Nachrichten")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_slash(interaction: discord.Interaction, anzahl: int):
        if anzahl < 1 or anzahl > 100:
            await interaction.response.send_message("❌ Bitte gib eine Zahl zwischen 1 und 100 an!", ephemeral=True)
            return
        
        deleted = await interaction.channel.purge(limit=anzahl)
        await interaction.response.send_message(f"✅ Es wurden `{len(deleted)}` Nachrichten gelöscht.", ephemeral=True)
