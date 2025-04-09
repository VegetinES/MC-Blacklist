import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from .mongo_utils import get_specific_field, get_server_data, update_server_data, get_server_language

class BlacklistCommands(commands.GroupCog, name="blacklist"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command(name="list", description="List blacklisted users in this server")
    async def blacklist_list(self, interaction: discord.Interaction):
        if not await self.check_permissions(interaction):
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("No tienes permisos para usar este comando. Se requiere ser Administrador o tener un rol con permisos de seguridad.", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have permissions to use this command. You must be an Administrator or have a role with security permissions.", ephemeral=True)
            return
            
        cog = self.bot.get_cog("BlacklistList")
        if cog:
            await cog.execute_list_command(interaction)
        else:
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("Error: El módulo de lista no está cargado.", ephemeral=True)
            else:
                await interaction.response.send_message("Error: The list module is not loaded.", ephemeral=True)
    
    @app_commands.command(name="userinfo", description="View detailed information about a blacklisted user")
    @app_commands.describe(usuario="ID of the user to check")
    async def blacklist_userinfo(self, interaction: discord.Interaction, usuario: str):
        if not await self.check_permissions(interaction):
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("No tienes permisos para usar este comando. Se requiere ser Administrador o tener un rol con permisos de seguridad.", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have permissions to use this command. You must be an Administrator or have a role with security permissions.", ephemeral=True)
            return

        cog = self.bot.get_cog("BlacklistUser")
        if cog:
            await cog.blacklistuser(interaction, usuario)
        else:
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("Error: El módulo de información de usuario no está cargado.", ephemeral=True)
            else:
                await interaction.response.send_message("Error: The user information module is not loaded.", ephemeral=True)
    
    @app_commands.command(name="modify", description="Modify information of a blacklisted user")
    @app_commands.describe(usuario="ID of the user to modify")
    async def blacklist_modificar(self, interaction: discord.Interaction, usuario: str):
        if not await self.check_admin_permissions(interaction):
            await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
            return

        cog = self.bot.get_cog("BlacklistModify")
        if cog:
            await cog.modify_user(interaction, usuario)
        else:
            await interaction.response.send_message("Error: El módulo de modificación no está cargado.", ephemeral=True)
    
    @app_commands.command(name="add", description="Add one or more users to the blacklist")
    @app_commands.describe(
        usuarios="User(s) to add (mentions or IDs separated by spaces)",
        razon="Reason for the report",
        imagen1="First proof (image, required)",
        imagen2="Second proof (image, optional)",
        imagen3="Third proof (image, optional)",
        imagen4="Fourth proof (image, optional)",
        imagen5="Fifth proof (image, optional)",
        imagen6="Sixth proof (image, optional)"
    )
    async def blacklist_add(
        self, 
        interaction: discord.Interaction, 
        usuarios: str, 
        razon: str,
        imagen1: discord.Attachment,
        imagen2: Optional[discord.Attachment] = None,
        imagen3: Optional[discord.Attachment] = None,
        imagen4: Optional[discord.Attachment] = None,
        imagen5: Optional[discord.Attachment] = None,
        imagen6: Optional[discord.Attachment] = None
    ):
        if not await self.check_admin_permissions(interaction):
            await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
            return

        cog = self.bot.get_cog("BlacklistAdd")
        print(f"[DEBUG] BlacklistAdd cog: {cog}")
        if cog:
            await cog.add_to_blacklist(
                interaction, 
                usuarios, 
                razon, 
                imagen1, 
                imagen2, 
                imagen3, 
                imagen4, 
                imagen5, 
                imagen6
            )
        else:
            await interaction.response.send_message("Error: El módulo de añadir usuario no está cargado.", ephemeral=True)
    
    @app_commands.command(name="image", description="Añade imágenes a un reporte usando un código de validación")
    @app_commands.describe(
        codigo="Código de validación proporcionado por el bot",
        imagen1="Primera imagen (obligatoria)",
        imagen2="Segunda imagen (opcional)",
        imagen3="Tercera imagen (opcional)",
        imagen4="Cuarta imagen (opcional)",
        imagen5="Quinta imagen (opcional)",
        imagen6="Sexta imagen (opcional)",
        imagen7="Séptima imagen (opcional)",
        imagen8="Octava imagen (opcional)"
    )
    async def blacklist_image(
        self, 
        interaction: discord.Interaction, 
        codigo: str,
        imagen1: discord.Attachment,
        imagen2: Optional[discord.Attachment] = None,
        imagen3: Optional[discord.Attachment] = None,
        imagen4: Optional[discord.Attachment] = None,
        imagen5: Optional[discord.Attachment] = None,
        imagen6: Optional[discord.Attachment] = None,
        imagen7: Optional[discord.Attachment] = None,
        imagen8: Optional[discord.Attachment] = None
    ):
        cog = self.bot.get_cog("BlacklistImage")
        if cog:
            await cog.image(
                interaction, 
                codigo, 
                imagen1, 
                imagen2, 
                imagen3, 
                imagen4, 
                imagen5, 
                imagen6,
                imagen7,
                imagen8
            )
        else:
            await interaction.response.send_message("Error: El módulo de imágenes no está cargado.", ephemeral=True)
    
    @app_commands.command(name="info", description="Muestra información sobre el bot MC Blacklist")
    async def blacklist_info(self, interaction: discord.Interaction):
        cog = self.bot.get_cog("BlacklistInfo")
        if cog:
            await cog.info(interaction)
        else:
            await interaction.response.send_message("Error: El módulo de información no está cargado.", ephemeral=True)
    
    @app_commands.command(name="perms", description="Configure security permissions")
    @app_commands.describe(
        accion="Add or remove permissions",
        roles="Roles to assign/remove permission (separate multiple roles with spaces)"
    )
    @app_commands.choices(accion=[
        app_commands.Choice(name="añadir", value="añadir"),
        app_commands.Choice(name="eliminar", value="eliminar"),
        app_commands.Choice(name="add", value="añadir"),
        app_commands.Choice(name="remove", value="eliminar")
    ])
    async def security_perms(self, interaction: discord.Interaction, accion: str, roles: str):
        if not self.is_admin(interaction):
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("No tienes permisos para usar este comando. Se requiere ser Administrador del servidor.", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have permissions to use this command. You must be a Server Administrator.", ephemeral=True)
            return
        
        from .securityperms import update_security_perms
        await update_security_perms(interaction, accion, roles)

    @app_commands.command(name="alert", description="Configure security alert channel and message")
    @app_commands.describe(
        canal="Channel where security alerts will be sent",
        mensaje="Alert message (you can use {user}, {usertag} and {userid})"
    )
    async def security_alert(self, interaction: discord.Interaction, canal: discord.TextChannel, mensaje: str):
        if not self.is_admin(interaction):
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("No tienes permisos para usar este comando. Se requiere ser Administrador del servidor.", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have permissions to use this command. You must be a Server Administrator.", ephemeral=True)
            return
        
        from .securityalert import set_security_alert
        await set_security_alert(interaction, canal, mensaje)

    @app_commands.command(name="data", description="Show current security configuration")
    async def security_data(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("No tienes permisos para usar este comando. Se requiere ser Administrador del servidor.", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have permissions to use this command. You must be a Server Administrator.", ephemeral=True)
            return
        
        from .securitydata import show_security_data
        await show_security_data(interaction)
    
    @app_commands.command(name="report", description="Report one or more users")
    @app_commands.describe(
        usuarios="User(s) to report (mentions or IDs separated by spaces)",
        razon="Reason for the report",
        imagen1="First proof (image, required)",
        imagen2="Second proof (image, optional)",
        imagen3="Third proof (image, optional)",
        imagen4="Fourth proof (image, optional)",
        imagen5="Fifth proof (image, optional)",
        imagen6="Sixth proof (image, optional)"
    )
    async def report(
        self, 
        interaction: discord.Interaction, 
        usuarios: str, 
        razon: str,
        imagen1: discord.Attachment,
        imagen2: Optional[discord.Attachment] = None,
        imagen3: Optional[discord.Attachment] = None,
        imagen4: Optional[discord.Attachment] = None,
        imagen5: Optional[discord.Attachment] = None,
        imagen6: Optional[discord.Attachment] = None
    ):
        cog = self.bot.get_cog("ReportCommand")
        if cog:
            if not await cog.check_permissions(interaction):
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
            
            await cog.report(
                interaction, 
                usuarios, 
                razon, 
                imagen1, 
                imagen2, 
                imagen3, 
                imagen4, 
                imagen5, 
                imagen6
            )
        else:
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("Error: El módulo de reportes no está cargado.", ephemeral=True)
            else:
                await interaction.response.send_message("Error: The reports module is not loaded.", ephemeral=True)
    
    @app_commands.command(name="help", description="Show bot commands help")
    async def ayuda(self, interaction: discord.Interaction):
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
            
        from .securityhelp import show_security_help
        await show_security_help(interaction)
    
    @app_commands.command(name="language", description="Change bot language")
    @app_commands.describe(language="Language to set (Español or English)")
    async def languaje(self, interaction: discord.Interaction, language: str):
        from .changelanguage import change_language
        
        if not self.is_admin(interaction):
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.response.send_message("No tienes permisos para usar este comando. Se requiere ser Administrador del servidor.", ephemeral=True)
            else:
                await interaction.response.send_message("You don't have permissions to use this command. You must be a Server Administrator.", ephemeral=True)
            return
        
        await change_language(interaction, language)
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        return False
    
    async def check_permissions(self, interaction):
        if not hasattr(interaction.user, 'guild_permissions'):
            return False
            
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
    
    async def check_admin_permissions(self, interaction):
        allowed_ids = [702934069138161835, 327157607724875776]
        return interaction.user.id in allowed_ids

async def setup(bot):
    await bot.add_cog(BlacklistCommands(bot))