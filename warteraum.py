import discord
import datetime

# ==================== WARTERAUM CONFIGURATION ====================
WARTERAUM_NAME = "Büro-Warteraum"  # Exakter Name deines Sprachkanals
TEAM_NOTIFICATION_KANAL = "《🗣》support-anfrage" # Kanal für die Team-Nachricht

# Direkter Link zu "Local Forecast - Elevator" von Kevin MacLeod
WARTERAUM_MUSIK_URL = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Local%20Forecast%20-%20Elevator.mp3"


# ==================== WARTERAUM LOGIK ====================

def play_warteraum_music(vc):
    """Spielt die Warteraum-Musik in einer Endlosschleife (Loop)."""
    if not vc.is_connected():
        return

    # FFmpeg-Optionen für stabilen Audio-Stream
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    def after_playing(error):
        if error:
            print(f"⚠️ Musik-Fehler im Warteraum: {error}")
        if vc.is_connected():
            play_warteraum_music(vc)

    try:
        source = discord.FFmpegPCMAudio(WARTERAUM_MUSIK_URL, **ffmpeg_options)
        vc.play(source, after=after_playing)
        print("🎵 Warteraum-Musik erfolgreich gestartet.")
    except Exception as e:
        print(f"❌ Fehler beim Abspielen der Musik: {e}")


async def handle_warteraum(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState, bot: discord.Client):
    """Prüft, ob jemand den Büro-Warteraum betritt oder verlässt."""
    if member.bot:
        return

    # Debug-Ausgabe zur Kontrolle in den Logs
    if after.channel:
        print(f"🔍 DEBUG Voice Update: {member.name} ist in Channel '{after.channel.name}' (ID: {after.channel.id})")
    if before.channel:
        print(f"🔍 DEBUG Voice Update: {member.name} hat Channel '{before.channel.name}' verlassen.")

    # 1. USER BETRITT DEN BÜRO-WARTERAUM (Sowohl über Namen als auch über exakten Textabgleich abgesichert)
    is_target_channel = (after.channel and (after.channel.name == WARTERAUM_NAME or WARTERAUM_NAME.lower() in after.channel.name.lower()))

    if is_target_channel:
        guild = member.guild
        voice_channel = after.channel
        print(f"✅ TREFFER! {member.name} hat den Warteraum betreten.")

        vc = discord.utils.get(bot.voice_clients, guild=guild)

        if not vc:
            try:
                vc = await voice_channel.connect()
                print("✅ Bot hat sich erfolgreich mit dem Warteraum-Voice verbunden!")
            except Exception as e:
                print(f"❌ Konnte dem Büro-Warteraum nicht beitreten: {e}")
                return
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        if not vc.is_playing():
            play_warteraum_music(vc)

        team_kanal = discord.utils.get(guild.text_channels, name=TEAM_NOTIFICATION_KANAL)
        if team_kanal:
            embed = discord.Embed(
                title="🔔 JEMAND WARTET IM BÜRO-WARTERAUM!",
                description=f"Der Spieler {member.mention} hat den **{voice_channel.name}** betreten und wartet auf ein Teammitglied!",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await team_kanal.send(content="🚨 @here", embed=embed)
            except Exception as e:
                print(f"❌ Konnte Team-Nachricht nicht senden: {e}")

    # 2. USER VERLÄSST DEN BÜRO-WARTERAUM
    was_target_channel = (before.channel and (before.channel.name == WARTERAUM_NAME or WARTERAUM_NAME.lower() in before.channel.name.lower()))

    if was_target_channel:
        voice_channel = before.channel
        guild = member.guild
        print(f"🛑 {member.name} hat den Warteraum verlassen.")

        echte_user = [m for m in voice_channel.members if not m.bot]

        if len(echte_user) == 0:
            vc = discord.utils.get(bot.voice_clients, guild=guild)
            if vc:
                print("🛑 Niemand mehr im Warteraum. Bot verlässt den Channel.")
                await vc.disconnect()
