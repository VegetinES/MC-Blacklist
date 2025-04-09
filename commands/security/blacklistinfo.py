import discord
from discord import app_commands
from discord.ext import commands
from .mongo_utils import get_specific_field, get_server_language

class BlacklistInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cargado correctamente")
    
    async def check_permissions(self, interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        
        security_config = await get_specific_field(interaction.guild.id, "security")
        if security_config and "perms" in security_config:
            permitted_roles = security_config["perms"]
            if permitted_roles == 0 or permitted_roles == [0]:
                return False
            
            user_roles = [role.id for role in interaction.user.roles]
            for role_id in permitted_roles:
                if role_id in user_roles and role_id != 0:
                    return True
        
        return False
    
    async def info(self, interaction: discord.Interaction):
        if not await self.check_permissions(interaction):
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message(
                    "No tienes permisos para usar este comando. Se requiere ser Administrador o tener un rol con permisos de seguridad.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You don't have permissions to use this command. You must be an Administrator or have a role with security permissions.",
                    ephemeral=True
                )
            return
        
        language = await get_server_language(interaction.guild.id)
        
        if language == "es":
            embed = discord.Embed(
                title="Información MC Blacklist",
                description="Este bot ha sido creado en Python, para avisar a servidores de Minecraft de usuarios maliciosos.",
                color=0x515F01
            )
            
            embed.add_field(
                name="Creadores",
                value="Mercu `mercurianoooo`\nVegetin `vegetines`",
                inline=True
            )
            
            embed.add_field(
                name="Enlaces de interés",
                value="[Repositorio público](https://github.com/VegetinES/MC-Blacklist)\n[Servidor de Soporte](https://discord.gg/RG4JM59bet)",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="MC Blacklist Information",
                description="This bot has been created in Python, to alert Minecraft servers about malicious users.",
                color=0x515F01
            )
            
            embed.add_field(
                name="Creators",
                value="Mercu `mercurianoooo`\nVegetin `vegetines`",
                inline=True
            )
            
            embed.add_field(
                name="Links of interest",
                value="[Public Repository](https://github.com/VegetinES/MC-Blacklist)\n[Support Server](https://discord.gg/RG4JM59bet)",
                inline=True
            )
        
        embed.set_image(url="https://i.imgur.com/VVoXfQO.png")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BlacklistInfo(bot))