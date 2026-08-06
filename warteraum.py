import discord
import datetime

WARTERAUM_NAME = "Büro-Warteraum"
TEAM_NOTIFICATION_KANAL = "team-notifikation"
WARTERAUM_MUSIK_URL = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Local%20Forecast%20-%20Elevator.mp3"

def play_warteraum_music(vc):
    if not vc.is_connected():
        return

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    def after_playing(error):
        if error:
            print(f"⚠️ Musik-Fehler: {error}")
        if vc.is_connected():
            play_warteraum_music(vc)

    try:
        source = discord.FFmpegPCMAudio(WARTERAUM_MUSIK_URL, **ffmpeg_options)
        vc.play(source, after=after_playing)
        print("🎵 Warteraum-Musik gestartet.")
    except Exception as e:
        print(f"❌ Fehler beim Abspielen: {e}")

async def handle_warteraum(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState, bot: discord.Client):
    if member.bot:
        return

    if after.channel and after.channel.name == WARTERAUM_NAME:
        guild = member.guild
        voice_channel = after.channel
        print(f"🔥 ERFOLG: {member.name} hat den Warteraum betreten!")

        vc = discord.utils.get(bot.voice_clients, guild=guild)
        if not vc:
            try:
                vc = await voice_channel.connect()
                print("✅ Bot mit Warteraum verbunden!")
            except Exception as e:
                print(f"❌ Verbindungsfehler: {e}")
                return

        if not vc.is_playing():
            play_warteraum_music(vc)

        team_kanal = discord.utils.get(guild.text_channels, name=TEAM_NOTIFICATION_KANAL)
        if team_kanal:
            await team_kanal.send(f"🚨 @here Der Spieler {member.mention} wartet im **{voice_channel.name}**!")

    if before.channel and before.channel.name == WARTERAUM_NAME:
        voice_channel = before.channel
        guild = member.guild
        echte_user = [m for m in voice_channel.members if not m.bot]

        if len(echte_user) == 0:
            vc = discord.utils.get(bot.voice_clients, guild=guild)
            if vc:
                print("🛑 Warteraum leer. Bot verlässt den Channel.")
                await vc.disconnect()
