import discord
import datetime

WARTERAUM_NAME = "Büro-Warteraum"
TEAM_NOTIFICATION_KANAL = "team-notifikation"

async def handle_warteraum(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState, bot: discord.Client):
    if member.bot:
        return

    # Prüfen ob der User den Warteraum betritt
    if after.channel and after.channel.name == WARTERAUM_NAME:
        guild = member.guild
        voice_channel = after.channel
        print(f"🔥 ERFOLG: {member.name} hat den Warteraum betreten!")

        vc = discord.utils.get(bot.voice_clients, guild=guild)
        if not vc:
            try:
                vc = await voice_channel.connect()
                print("✅ Bot hat sich erfolgreich mit dem Warteraum verbunden!")
            except Exception as e:
                print(f"❌ Verbindungsfehler: {e}")
                return

        # Team benachrichtigen
        team_kanal = discord.utils.get(guild.text_channels, name=TEAM_NOTIFICATION_KANAL)
        if team_kanal:
            await team_kanal.send(f"🚨 @here Der Spieler {member.mention} wartet im **{voice_channel.name}**!")

    # Prüfen ob der User den Warteraum verlässt
    if before.channel and before.channel.name == WARTERAUM_NAME:
        voice_channel = before.channel
        guild = member.guild
        echte_user = [m for m in voice_channel.members if not m.bot]

        if len(echte_user) == 0:
            vc = discord.utils.get(bot.voice_clients, guild=guild)
            if vc:
                print("🛑 Warteraum leer. Bot verlässt den Channel.")
                await vc.disconnect()
