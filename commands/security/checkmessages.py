import discord
from discord.ext import commands
from .mongo_utils import get_specific_field, get_server_language
from .mongo import mongo_report_storage

class CheckMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.author.bot:
                return
                
            user_id = message.author.id
            
            user_reports = await mongo_report_storage.get_user_reports(user_id)
            
            if not user_reports:
                return
            
            server_id = message.guild.id
            security_config = await get_specific_field(server_id, "security")
            
            if not security_config:
                return
            
            channel_id = security_config.get("channel", 0)
            
            if channel_id == 0:
                return
            
            alert_channel = message.guild.get_channel(channel_id)
            
            if not alert_channel:
                return
            
            language = await get_server_language(server_id)
            
            link_button = discord.ui.View()
            link_button.add_item(discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Ir al mensaje" if language == "es" else "Go to message",
                url=message.jump_url
            ))
            
            if language == "es":
                await alert_channel.send(
                    f"⚠️ Un usuario malicioso {message.author.mention} (`{message.author.name}`, ID: {message.author.id}) ha enviado un mensaje en {message.channel.mention}. Contenido de mensaje: \n{message.content}",
                    view=link_button
                )
            else:
                await alert_channel.send(
                    f"⚠️ A malicious user {message.author.mention} (`{message.author.name}`, ID: {message.author.id}) has sent a message in {message.channel.mention}. Message content: \n{message.content}",
                    view=link_button
                )
            
        except Exception as e:
            print(f"Error en on_message: {str(e)}")

async def setup(bot):
    await bot.add_cog(CheckMessages(bot))