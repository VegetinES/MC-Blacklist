import discord
from discord.ext import commands
from .mongo_utils import get_server_language

async def show_security_help(interaction):
    try:
        language = await get_server_language(interaction.guild.id)
        
        if language == "es":
            embed = discord.Embed(
                title="🛡️ Ayuda de Comandos de Seguridad",
                color=discord.Color.blue(),
                description="Guía completa de los comandos de seguridad disponibles en el bot."
            )

            embed.add_field(
                name="📋 Permisos",
                value=(
                    "Los comandos de seguridad tienen dos niveles de permisos:\n\n"
                    "🔹 **Administradores:** Pueden usar todos los comandos (excepto `/blacklist modify`, `/blacklist add`, `/blacklist block`, `/blacklist leave` y `/blacklist image`)\n"
                    "🔹 **Roles con permisos de seguridad:** Pueden usar `/blacklist help`, `/blacklist list`, `/blacklist userinfo`, `/blacklist report` y `/blacklist info`\n\n"
                    "Para añadir roles con permisos de seguridad, un administrador debe usar `/blacklist perms`."
                ),
                inline=False
            )

            embed.add_field(
                name="⚙️ Comandos de Blacklist",
                value=(
                    "**`/blacklist help`** - Muestra esta ayuda\n"
                    "**`/blacklist language`** - Cambia el idioma del bot (Español o English)\n"
                    "**`/blacklist perms acción:añadir/eliminar roles:@Rol`** - Añade o elimina roles con permisos de seguridad\n"
                    "**`/blacklist alert canal:#canal mensaje:texto`** - Configura el canal y mensaje de alertas cuando un usuario malicioso se una al servidor\n"
                    "**`/blacklist info` - Muestra información sobre el bot MC Blacklist\n"
                    "**`/blacklist data`** - Muestra la configuración actual de seguridad\n\n"
                    "En el mensaje de alerta puedes usar estas variables:\n"
                    "• `{user}` - Mención al usuario malicioso\n"
                    "• `{usertag}` - Nombre del usuario malicioso\n"
                    "• `{userid}` - ID del usuario malicioso"
                ),
                inline=False
            )

            embed.add_field(
                name="⛔ Comandos de Blacklist",
                value=(
                    "**`/blacklist list`** - Muestra usuarios en la blacklist del servidor\n"
                    "**`/blacklist userinfo usuario:123456789`** - Consulta detalles de un usuario en la blacklist"
                ),
                inline=False
            )

            embed.add_field(
                name="🚨 Comando de Report",
                value=(
                    "**`/blacklist report usuarios:1294829384 razon:texto imagen1:archivo`** - Reporta uno o varios usuarios, poniendo su ID separados por espacios\n\n"
                    "Este comando permite a los usuarios con permisos de seguridad reportar comportamientos sospechosos o "
                    "malintencionados para su revisión. Es necesario proporcionar al menos una imagen como prueba."
                ),
                inline=False
            )

            embed2 = discord.Embed(
                title="📝 Ejemplos",
                color=discord.Color.green(),
                description="Ejemplos de uso de los comandos de seguridad"
            )
            
            embed2.add_field(
                name="Configurar permisos",
                value="**`/blacklist perms acción:añadir roles:123456789 3893423`**\nAñade roles a los permisos de seguridad.",
                inline=False
            )
            
            embed2.add_field(
                name="Configurar alertas",
                value="**`/blacklist alert canal:#alertas mensaje:⚠️ Usuario malicioso detectado: {user} ({usertag}). ID: {userid}`**\nEstablece el canal #alertas para las notificaciones con un mensaje personalizado cuando se una un usuario malicioso al servidor.",
                inline=False
            )
            
            embed2.add_field(
                name="Consultar blacklist",
                value="**`/blacklist list`**\nMuestra todos los usuarios en la blacklist o los usuarios de la blacklist que están en el servidor.",
                inline=False
            )
            
            embed2.add_field(
                name="Reportar usuario",
                value="**`/blacklist report usuarios:@Usuario razon:Spam de enlaces sospechosos imagen1:[adjunta captura]`**\nReporta a un usuario por enviar enlaces sospechosos, adjuntando una captura como prueba.",
                inline=False
            )
            
            embed2.add_field(
                name="Cambiar idioma",
                value="**`/blacklist language language:English`**\nCambia el idioma del bot a inglés.",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="🛡️ Security Commands Help",
                color=discord.Color.blue(),
                description="Complete guide to security commands available in the bot."
            )

            embed.add_field(
                name="📋 Permissions",
                value=(
                    "Security commands have two permission levels:\n\n"
                    "🔹 **Administrators:** Can use all commands (except `/blacklist modify`, `/blacklist add`, `/blacklist block`, `/blacklist leave` and `/blacklist image`)\n"
                    "🔹 **Roles with security permissions:** Can use `/blacklist help`, `/blacklist list`, `/blacklist userinfo` and `/blacklist report`\n\n"
                    "To add roles with security permissions, an administrator must use `/blacklist perms`."
                ),
                inline=False
            )

            embed.add_field(
                name="⚙️ Blacklist Commands",
                value=(
                    "**`/blacklist help`** - Shows this help\n"
                    "**`/blacklist language`** - Changes the bot language (Español or English)\n"
                    "**`/blacklist perms acción:add/remove roles:@Role`** - Adds or removes roles with security permissions\n"
                    "**`/blacklist alert canal:#channel mensaje:text`** - Configures the channel and alert message when a malicious user joins the server\n"
                    "**`/blacklist info` - Shows information about the MC Blacklist bot\n"
                    "**`/blacklist data`** - Shows the current security configuration\n\n"
                    "In the alert message you can use these variables:\n"
                    "• `{user}` - Mention to the malicious user\n"
                    "• `{usertag}` - Name of the malicious user\n"
                    "• `{userid}` - ID of the malicious user"
                ),
                inline=False
            )

            embed.add_field(
                name="⛔ Blacklist Commands",
                value=(
                    "**`/blacklist list`** - Shows users in the server's blacklist\n"
                    "**`/blacklist userinfo usuario:123456789`** - Consults details of a user in the blacklist"
                ),
                inline=False
            )

            embed.add_field(
                name="🚨 Report Command",
                value=(
                    "**`/blacklist report usuarios:1294829384 razon:text imagen1:file`** - Reports one or more users, entering their IDs separated by spaces\n\n"
                    "This command allows users with security permissions to report suspicious or "
                    "malicious behaviors for review. At least one image must be provided as proof."
                ),
                inline=False
            )

            embed2 = discord.Embed(
                title="📝 Examples",
                color=discord.Color.green(),
                description="Examples of using security commands"
            )
            
            embed2.add_field(
                name="Configure permissions",
                value="**`/blacklist perms acción:add roles:123456789 3893423`**\nAdds roles to security permissions.",
                inline=False
            )
            
            embed2.add_field(
                name="Configure alerts",
                value="**`/blacklist alert canal:#alerts mensaje:⚠️ Malicious user detected: {user} ({usertag}). ID: {userid}`**\nSets the #alerts channel for notifications with a personalized message when a malicious user joins the server.",
                inline=False
            )
            
            embed2.add_field(
                name="Query blacklist",
                value="**`/blacklist list`**\nShows all users in the blacklist or blacklisted users who are in the server.",
                inline=False
            )
            
            embed2.add_field(
                name="Report user",
                value="**`/blacklist report usuarios:@User razon:Spam of suspicious links imagen1:[attach screenshot]`**\nReports a user for sending suspicious links, attaching a screenshot as proof.",
                inline=False
            )
            
            embed2.add_field(
                name="Change language",
                value="**`/blacklist language language:Español`**\nChanges the bot language to Spanish.",
                inline=False
            )

        await interaction.response.send_message(embeds=[embed, embed2])
    
    except Exception as e:
        print(f"Error en show_security_help: {str(e)}")
        await interaction.response.send_message(
            f"❌ Error: {str(e)}",
            ephemeral=True
        )