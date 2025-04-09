import discord
from discord.ext import commands
from .mongo_utils import get_specific_field, get_server_language

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        return False
    
    async def has_security_perms(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
            
        security_config = await get_specific_field(interaction.guild.id, "security")
        if security_config and "perms" in security_config:
            permitted_roles = security_config["perms"]
            
            user_roles = [role.id for role in interaction.user.roles]
            for role_id in permitted_roles:
                if role_id in user_roles:
                    return True
        
        return False

    async def get_text(self, interaction, key):
        """Obtiene el texto correspondiente en el idioma configurado"""
        language = await get_server_language(interaction.guild.id)
        
        texts = {
            "es": {
                "no_permissions": "No tienes permisos para usar este comando.",
                "error_occurred": "Ha ocurrido un error: {error}",
                "command_not_found": "Comando no encontrado.",
                "config_updated": "Configuración actualizada correctamente.",
                "config_error": "Error al actualizar la configuración."
            },
            "en": {
                "no_permissions": "You don't have permission to use this command.",
                "error_occurred": "An error occurred: {error}",
                "command_not_found": "Command not found.",
                "config_updated": "Configuration updated successfully.",
                "config_error": "Error updating configuration."
            }
        }
        
        return texts.get(language, texts["en"]).get(key, texts["en"].get(key, key))

async def setup(bot):
    await bot.add_cog(Security(bot))