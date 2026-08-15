import discord
from discord import app_commands
import datetime

def setup_moderation(bot):

    # --- HILFSFUNKTION: Admin & Team Check ---
    def ist_admin(interaction: discord.Interaction):
        return any("Founder" in r.name or "Projektleitung" in r.name or "Admin" in r.name or "Moderator" in r.name for r in interaction.user.roles) or interaction.user.guild_permissions.administrator

    # =========================================================================
    # DIE 22 MODERATIONS-BEFEHLE
    # =========================================================================

    # 1. BAN
    @bot.tree.command(name="ban", description="Bannt einen User dauerhaft vom Server")
    @app_commands.describe(member="Der User", reason="Grund")
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund angegeben"):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 **{member.name}** wurde gebannt. Grund: {reason}")

    # 2. KICK
    @bot.tree.command(name="kick", description="Wirft einen User vom Server")
    @app_commands.describe(member="Der User", reason="Grund")
    async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Kein Grund"):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await member.kick(reason=reason)
        await interaction.response.send_message(f"👢 **{member.name}** wurde gekickt. Grund: {reason}")

    # 3. UNBAN
    @bot.tree.command(name="unban", description="Entbannt einen User über seine ID")
    @app_commands.describe(user_id="Die Discord ID")
    async def unban(interaction: discord.Interaction, user_id: str):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        try:
            user = await bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ **{user.name}** wurde entbannt.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)

    # 4. TIMEOUT (MUTE)
    @bot.tree.command(name="timeout", description="Gibt einem User einen Timeout")
    @app_commands.describe(member="Der User", minutes="Minuten", reason="Grund")
    async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Kein Grund"):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await interaction.response.send_message(f"🔇 **{member.name}** wurde für {minutes} Minuten stummgeschaltet.")

    # 5. UNTIMEOUT
    @bot.tree.command(name="untimeout", description="Hebt den Timeout auf")
    @app_commands.describe(member="Der User")
    async def untimeout(interaction: discord.Interaction, member: discord.Member):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await member.timeout(None)
        await interaction.response.send_message(f"🔊 Timeout von **{member.name}** aufgehoben.")

    # 6. CLEAR (NACHRICHTEN LÖSCHEN)
    @bot.tree.command(name="clear", description="Löscht Nachrichten in einem Channel")
    @app_commands.describe(amount="Anzahl (1-100)")
    async def clear(interaction: discord.Interaction, amount: int):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 {len(deleted)} Nachrichten gelöscht.", ephemeral=True)

    # 7. LOCK CHANNEL
    @bot.tree.command(name="lock", description="Sperrt den aktuellen Channel")
    async def lock(interaction: discord.Interaction):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("🔒 Kanal gesperrt.")

    # 8. UNLOCK CHANNEL
    @bot.tree.command(name="unlock", description="Entsperrt den aktuellen Channel")
    async def unlock(interaction: discord.Interaction):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("🔓 Kanal entsperrt.")

    # 9. SLOWMODE
    @bot.tree.command(name="slowmode", description="Setzt den Slowmode")
    @app_commands.describe(seconds="Sekunden (0 = aus)")
    async def slowmode(interaction: discord.Interaction, seconds: int):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"⏱️ Slowmode auf **{seconds} Sekunden** gesetzt.")

    # 10. NICKNAME ÄNDERN
    @bot.tree.command(name="nick", description="Ändert den Nicknamen eines Users")
    @app_commands.describe(member="Der User", new_name="Neuer Name")
    async def nick(interaction: discord.Interaction, member: discord.Member, new_name: str):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await member.edit(nick=new_name)
        await interaction.response.send_message(f"✏️ Nickname von {member.mention} geändert zu **{new_name}**.")

    # 11. ROLLE GEBEN
    @bot.tree.command(name="giverole", description="Gibt einem User eine Rolle")
    @app_commands.describe(member="Der User", role="Die Rolle")
    async def giverole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Rolle **{role.name}** an {member.mention} vergeben.")

    # 12. ROLLE NEHMEN
    @bot.tree.command(name="takerole", description="Entzieht einem User eine Rolle")
    @app_commands.describe(member="Der User", role="Die Rolle")
    async def takerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await member.remove_roles(role)
        await interaction.response.send_message(f"⚠️ Rolle **{role.name}** von {member.mention} entzogen.")

    # 13. WARN SYSTEM
    warns_db = {}
    @bot.tree.command(name="warn", description="Gibt einem User einen Warn")
    @app_commands.describe(member="Der User", reason="Grund")
    async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        if member.id not in warns_db: warns_db[member.id] = []
        warns_db[member.id].append(reason)
        await interaction.response.send_message(f"⚠️ **{member.name}** gewarnt. Grund: {reason} (Total: {len(warns_db[member.id])})")

    # 14. WARNS ANZEIGEN
    @bot.tree.command(name="warns", description="Zeigt die Warns eines Users")
    @app_commands.describe(member="Der User")
    async def warns(interaction: discord.Interaction, member: discord.Member):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        user_warns = warns_db.get(member.id, [])
        text = "\n".join([f"{i+1}. {w}" for i, w in enumerate(user_warns)]) if user_warns else "Keine Warns."
        embed = discord.Embed(title=f"Warns für {member.name}", description=text, color=0xF1C40F)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 15. WARNS LÖSCHEN
    @bot.tree.command(name="clearwarns", description="Löscht alle Warns eines Users")
    @app_commands.describe(member="Der User")
    async def clearwarns(interaction: discord.Interaction, member: discord.Member):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        warns_db[member.id] = []
        await interaction.response.send_message(f"✅ Alle Warns für **{member.name}** wurden zurückgesetzt.", ephemeral=True)

    # 16. USERINFO
    @bot.tree.command(name="userinfo", description="Zeigt Infos über einen User")
    @app_commands.describe(member="Der User")
    async def userinfo(interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=f"Userinfo: {member.name}", color=0x3498DB)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Beigetreten", value=member.joined_at.strftime("%d.%m.%Y") if member.joined_at else "Unbekannt", inline=True)
        embed.add_field(name="Account erstellt", value=member.created_at.strftime("%d.%m.%Y"), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 17. SERVERINFO
    @bot.tree.command(name="serverinfo", description="Zeigt Infos über den Server")
    async def serverinfo(interaction: discord.Interaction):
        g = interaction.guild
        embed = discord.Embed(title=f"Serverinfo: {g.name}", color=0x2ECC71)
        embed.add_field(name="Mitglieder", value=str(g.member_count), inline=True)
        embed.add_field(name="Boosts", value=str(g.premium_subscription_count), inline=True)
        embed.add_field(name="Rollen", value=str(len(g.roles)), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 18. NICKNAME ZURÜCKSETZEN
    @bot.tree.command(name="resetnick", description="Setzt den Nickname zurück")
    @app_commands.describe(member="Der User")
    async def resetnick(interaction: discord.Interaction, member: discord.Member):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await member.edit(nick=None)
        await interaction.response.send_message(f"🔄 Nickname von {member.mention} zurückgesetzt.")

    # 19. STICKY MESSAGE SIMULATION (SERVER INFO POSTEN)
    @bot.tree.command(name="embed", description="Sendet ein eigenes Embed in den Channel")
    @app_commands.describe(title="Titel", description="Text")
    async def embed(interaction: discord.Interaction, title: str, description: str):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        em = discord.Embed(title=title, description=description, color=0x9B59B6)
        await interaction.channel.send(embed=em)
        await interaction.response.send_message("✅ Embed gesendet!", ephemeral=True)

    # 20. BOT SAY (Bot schreibt Nachricht)
    @bot.tree.command(name="say", description="Lässt den Bot etwas sagen")
    @app_commands.describe(text="Der Text")
    async def say(interaction: discord.Interaction, text: str):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        await interaction.channel.send(text)
        await interaction.response.send_message("✅ Nachricht gesendet!", ephemeral=True)

    # 21. MOVE VOICE (User in anderen Channel verschieben)
    @bot.tree.command(name="move", description="Verschiebt einen User in einen anderen Sprachkanal")
    @app_commands.describe(member="Der User", channel="Ziel-Voicechannel")
    async def move(interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        if not member.voice: return await interaction.response.send_message("❌ User ist in keinem Voicechannel!", ephemeral=True)
        await member.move_to(channel)
        await interaction.response.send_message(f"🚚 {member.mention} wurde verschoben.")

    # 22. KICK AUS VOICE
    @bot.tree.command(name="vickick", description="Wirft einen User aus dem Sprachkanal")
    @app_commands.describe(member="Der User")
    async def vickick(interaction: discord.Interaction, member: discord.Member):
        if not ist_admin(interaction): return await interaction.response.send_message("❌ Keine Berechtigung!", ephemeral=True)
        if not member.voice: return await interaction.response.send_message("❌ User ist in keinem Voicechannel!", ephemeral=True)
        await member.move_to(None)
        await interaction.response.send_message(f"🔌 {member.mention} wurde aus dem Voice geworfen.")
