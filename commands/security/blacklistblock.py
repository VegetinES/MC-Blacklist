import discord
from discord import app_commands
from discord.ext import commands
from .mongo import mongo_report_storage

class BlacklistBlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cargado correctamente")
    
    async def block_command(self, interaction: discord.Interaction, acción: str, servidor: str = None):
        allowed_ids = [327157607724875776, 702934069138161835]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        if acción == "datos":
            blocked_servers = await mongo_report_storage.get_blocked_servers()
            
            if not blocked_servers:
                await interaction.followup.send("No hay servidores bloqueados.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="Servidores Bloqueados",
                description="Lista de servidores bloqueados que no pueden usar el bot.",
                color=discord.Color.red()
            )
            
            server_list = ""
            for server_id in blocked_servers:
                server = self.bot.get_guild(server_id)
                server_list += f"• `{server_id}`\n"
            
            embed.add_field(
                name="Servidores",
                value=server_list if server_list else "No hay servidores bloqueados.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if not servidor:
            await interaction.followup.send("Debes proporcionar al menos un ID de servidor para esta acción.", ephemeral=True)
            return
        
        server_ids = []
        for server_id in servidor.split():
            try:
                server_ids.append(int(server_id.strip()))
            except ValueError:
                continue
        
        if not server_ids:
            await interaction.followup.send("No se proporcionaron IDs de servidor válidos.", ephemeral=True)
            return
        
        success_servers = []
        failure_servers = []
        
        for server_id in server_ids:
            if acción == "añadir":
                success = await mongo_report_storage.add_blocked_server(server_id)
                if success:
                    success_servers.append(server_id)
                    
                    guild = self.bot.get_guild(server_id)
                    if guild:
                        try:
                            await guild.leave()
                        except Exception as e:
                            print(f"Error al salir del servidor {server_id}: {e}")
                else:
                    failure_servers.append(server_id)
            elif acción == "eliminar":
                success = await mongo_report_storage.remove_blocked_server(server_id)
                if success:
                    success_servers.append(server_id)
                else:
                    failure_servers.append(server_id)
        
        if acción == "añadir":
            action_text = "bloqueados"
        else:
            action_text = "desbloqueados"
        
        result = f"Servidores {action_text}:\n"
        if success_servers:
            result += "✅ " + ", ".join([f"`{sid}`" for sid in success_servers]) + "\n"
        if failure_servers:
            result += "❌ " + ", ".join([f"`{sid}`" for sid in failure_servers])
        
        await interaction.followup.send(result, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BlacklistBlock(bot))