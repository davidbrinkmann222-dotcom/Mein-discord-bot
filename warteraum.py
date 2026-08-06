import discord
import datetime

# ==================== WARTERAUM CONFIGURATION ====================
WARTERAUM_NAME = "Büro-Warteraum"  # Exakter Name deines Sprachkanals
TEAM_NOTIFICATION_KANAL = "team-notifikation" # Kanal für die Team-Nachricht

# Direkter Link zu "Local Forecast - Elevator" von Kevin MacLeod (Incompetech)
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
            print(f"Musik-Fehler im Warteraum: {error}")
        # Wenn der Bot immer noch im Voice ist, Musik von vorn starten (Loop)
        if vc.is_connected():
            play_warteraum_music(vc)

    try:
        source = discord.FFmpegPCMAudio(WARTERAUM_MUSIK_URL, **ffmpeg_options)
        vc.play(source, after=after_playing)
    except Exception as e:
        print(f"Fehler beim Abspielen der Musik: {e}")


async def handle_warteraum(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState, bot: discord.Client):
    """Prüft, ob jemand den Büro-Warteraum betritt oder verlässt."""
    if member.bot:
        return

    # 1. USER BETRITT DEN BÜRO-WARTERAUM
    if after.channel and after.channel.name == WARTERAUM_NAME:
        guild = member.guild
        voice_channel = after.channel

        # Prüfen, ob der Bot schon im Sprachkanal ist
        vc = discord.utils.get(bot.voice_clients, guild=guild)

        if not vc:
            try:
                vc = await voice_channel.connect()
            except Exception as e:
                print(f"Konnte dem Büro-Warteraum nicht beitreten: {e}")
                return
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        # Musik starten, falls sie nicht schon läuft
        if not vc.is_playing():
            play_warteraum_music(vc)

        # Team per Embed-Nachricht benachrichtigen
        team_kanal = discord.utils.get(guild.text_channels, name=TEAM_NOTIFICATION_KANAL)
        if team_kanal:
            embed = discord.Embed(
                title="🔔 JEMAND WARTET IM BÜRO-WARTERAUM!",
                description=f"Der Spieler {member.mention} hat den **{voice_channel.name}** betreten und wartet auf ein Teammitglied!",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await team_kanal.send(content="🚨 @here", embed=embed)

    # 2. USER VERLÄSST DEN BÜRO-WARTERAUM
    if before.channel and before.channel.name == WARTERAUM_NAME:
        voice_channel = before.channel
        guild = member.guild

        # Zählen, wie viele echte User noch im Warteraum sind
        echte_user = [m for m in voice_channel.members if not m.bot]

        # Wenn kein normaler User mehr im Raum ist -> Bot verlässt den Channel & stoppt Musik
        if len(echte_user) == 0:
            vc = discord.utils.get(bot.voice_clients, guild=guild)
            if vc:
                await vc.disconnect()
