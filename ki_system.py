import os
import discord
from discord import app_commands
from openai import OpenAI

aktive_ki_chats = set()

def setup_ki_commands(bot):
    
    @bot.tree.command(name="startki", description="Erlaubt einem Spieler, mit der KI zu chatten (Nur Team)")
    @app_commands.describe(spieler="Der Spieler, der freigeschaltet wird")
    async def startki(interaction: discord.Interaction, spieler: discord.Member):
        team_role = discord.utils.get(interaction.guild.roles, name="♕✯ |❘| David | Founder")
        
        if team_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Dazu hast du keine Berechtigung!", ephemeral=True)
            return

        aktive_ki_chats.add(spieler.id)
        await interaction.response.send_message(f"✅ Die KI wurde für {spieler.mention} freigeschaltet!")
        await interaction.channel.send(f"🎉 {spieler.mention}, du wurdest freigeschaltet! Du kannst jetzt den Bot pingen, um mit der KI zu sprechen.")

    @bot.tree.command(name="stopki", description="Beendet den KI-Chat für einen Spieler (Nur Team)")
    @app_commands.describe(spieler="Der Spieler, dessen KI-Chat beendet wird")
    async def stopki(interaction: discord.Interaction, spieler: discord.Member):
        team_role = discord.utils.get(interaction.guild.roles, name="♕✯ |❘| David | Founder")
        
        if team_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Dazu hast du keine Berechtigung!", ephemeral=True)
            return

        if spieler.id in aktive_ki_chats:
            aktive_ki_chats.remove(spieler.id)
            await interaction.response.send_message(f"🛑 Der KI-Chat für {spieler.mention} wurde beendet.")
            await interaction.channel.send(f"🔒 {spieler.mention}, der Support-Chat mit der KI wurde beendet.")
        else:
            await interaction.response.send_message(f"⚠️ {spieler.mention} hatte keinen aktiven KI-Chat.", ephemeral=True)

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        if bot.user in message.mentions:
            if message.author.id in aktive_ki_chats:
                frage = message.content.replace(f"<@{bot.user.id}>", "").strip()
                
                async with message.channel.typing():
                    try:
                        # Client wird erst hier erstellt, wenn der Key sicher geladen ist
                        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Du bist ein hilfsbereiter Support-Assistent auf einem Discord Roleplay Server."},
                                {"role": "user", "content": frage}
                            ]
                        )
                        antwort = response.choices[0].message.content
                        await message.reply(antwort)
                    except Exception as e:
                        await message.reply(f"❌ Es gab einen Fehler bei der KI-Abfrage: {e}")
            else:
                await message.reply("❌ Du hast keine Erlaubnis, mit mir zu reden. Ein Teammitglied muss dich mit `/startki` freischalten!", delete_after=10)

        await bot.process_commands(message)
