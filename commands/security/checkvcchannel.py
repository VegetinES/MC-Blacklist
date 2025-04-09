import discord
from discord.ext import commands
from .mongo_utils import get_specific_field, get_server_language
from .mongo import mongo_report_storage

class CheckVcChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            if member.bot:
                return
                
            user_id = member.id
            
            user_reports = await mongo_report_storage.get_user_reports(user_id)
            
            if not user_reports:
                return
            
            server_id = member.guild.id
            security_config = await get_specific_field(server_id, "security")
            
            if not security_config:
                return
            
            channel_id = security_config.get("channel", 0)
            
            if channel_id == 0:
                return
            
            alert_channel = member.guild.get_channel(channel_id)
            
            if not alert_channel:
                return
            
            language = await get_server_language(server_id)
            
            if before.channel is None and after.channel is not None:
                if language == "es":
                    await alert_channel.send(
                        f"⚠️ Un usuario malicioso {member.mention} (`{member.name}`, ID: {member.id}) ha entrado al canal de voz {after.channel.mention}."
                    )
                else:
                    await alert_channel.send(
                        f"⚠️ A malicious user {member.mention} (`{member.name}`, ID: {member.id}) has joined the voice channel {after.channel.mention}."
                    )
            
            elif before.channel is not None and after.channel is None:
                if language == "es":
                    await alert_channel.send(
                        f"⚠️ Un usuario malicioso {member.mention} (`{member.name}`, ID: {member.id}) ha salido del canal de voz {before.channel.mention}."
                    )
                else:
                    await alert_channel.send(
                        f"⚠️ A malicious user {member.mention} (`{member.name}`, ID: {member.id}) has left the voice channel {before.channel.mention}."
                    )
            
        except Exception as e:
            print(f"Error en on_voice_state_update: {str(e)}")

async def setup(bot):
    await bot.add_cog(CheckVcChannel(bot))