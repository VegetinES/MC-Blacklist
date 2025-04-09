import discord
from discord import app_commands
from discord.ext import commands

class BlacklistLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cargado correctamente")
    
    async def leave_command(self, interaction: discord.Interaction, servidor: str):
        allowed_ids = [327157607724875776, 702934069138161835]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
            return
        
        try:
            server_id = int(servidor.strip())
        except ValueError:
            await interaction.response.send_message("Por favor, proporciona un ID de servidor válido.", ephemeral=True)
            return
        
        guild = self.bot.get_guild(server_id)
        if not guild:
            await interaction.response.send_message(f"No se encontró ningún servidor con el ID {server_id}.", ephemeral=True)
            return
        
        server_name = guild.name
        
        try:
            await guild.leave()
            await interaction.response.send_message(f"✅ El bot ha salido del servidor `{server_name}` (ID: {server_id}).", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al salir del servidor `{server_name}` (ID: {server_id}): {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BlacklistLeave(bot))