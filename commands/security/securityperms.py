import discord
from discord.ext import commands
from .mongo_utils import get_server_data, get_specific_field, update_server_data, get_server_language

async def update_security_perms(interaction, accion, roles):
    try:
        server_id = interaction.guild.id
        server_data = await get_server_data(server_id)
        language = await get_server_language(server_id)
        
        if not server_data:
            if language == "es":
                await interaction.response.send_message(
                    "No se encontraron datos para este servidor. Ejecuta `/config update` para inicializar la configuración.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "No data found for this server. Run `/config update` to initialize the configuration.",
                    ephemeral=True
                )
            return

        security_config = await get_specific_field(server_id, "security") or {"channel": 0, "message": "", "perms": [0], "language": language}

        roles_list = []
        role_mentions = roles.split()
        
        for role_mention in role_mentions:
            if role_mention.startswith('<@&') and role_mention.endswith('>'):
                try:
                    role_id = int(role_mention[3:-1])
                    role = interaction.guild.get_role(role_id)
                    if role and role.name.lower() not in ['everyone', '@everyone', 'here', '@here']:
                        roles_list.append(role.id)
                except ValueError:
                    pass
            else:
                try:
                    role_id = int(role_mention)
                    role = interaction.guild.get_role(role_id)
                    if role:
                        roles_list.append(role.id)
                except ValueError:
                    roles_by_name = [r.id for r in interaction.guild.roles if r.name.lower() == role_mention.lower()]
                    roles_list.extend(roles_by_name)

        if not roles_list:
            if language == "es":
                await interaction.response.send_message(
                    "No se encontraron roles válidos en tu mensaje. Asegúrate de mencionar roles o proporcionar IDs válidos.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "No valid roles found in your message. Make sure to mention roles or provide valid IDs.",
                    ephemeral=True
                )
            return
        
        current_perms = security_config.get("perms", [0])
        if current_perms == 0:
            current_perms = [0]

        if accion.lower() in ["añadir", "add"]:
            added_roles = []
            for role_id in roles_list:
                if role_id not in current_perms:
                    current_perms.append(role_id)
                    role = interaction.guild.get_role(role_id)
                    if role:
                        added_roles.append(f"<@&{role_id}>")
            
            if not added_roles:
                if language == "es":
                    await interaction.response.send_message(
                        "Todos los roles mencionados ya tienen permisos de seguridad.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "All mentioned roles already have security permissions.",
                        ephemeral=True
                    )
                return
                
            if language == "es":
                message = f"✅ Se han añadido los siguientes roles a los permisos de seguridad: {', '.join(added_roles)}"
            else:
                message = f"✅ The following roles have been added to security permissions: {', '.join(added_roles)}"
        
        elif accion.lower() in ["eliminar", "remove"]:
            removed_roles = []
            for role_id in roles_list:
                if role_id in current_perms and role_id != 0:
                    current_perms.remove(role_id)
                    role = interaction.guild.get_role(role_id)
                    if role:
                        removed_roles.append(f"<@&{role_id}>")
            
            if not removed_roles:
                if language == "es":
                    await interaction.response.send_message(
                        "Ninguno de los roles mencionados tenía permisos de seguridad.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "None of the mentioned roles had security permissions.",
                        ephemeral=True
                    )
                return
                
            if language == "es":
                message = f"✅ Se han eliminado los siguientes roles de los permisos de seguridad: {', '.join(removed_roles)}"
            else:
                message = f"✅ The following roles have been removed from security permissions: {', '.join(removed_roles)}"
        
        else:
            if language == "es":
                await interaction.response.send_message(
                    "Acción no válida. Las acciones permitidas son 'añadir' o 'eliminar'.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Invalid action. Allowed actions are 'add' or 'remove'.",
                    ephemeral=True
                )
            return

        if not current_perms:
            current_perms = [0]

        security_config["perms"] = current_perms
        
        if await update_server_data(server_id, "perms", current_perms):
            await interaction.response.send_message(message)
        else:
            if language == "es":
                await interaction.response.send_message(
                    "❌ Ha ocurrido un error al actualizar la configuración de seguridad.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ An error occurred while updating the security configuration.",
                    ephemeral=True
                )
    
    except Exception as e:
        print(f"Error en update_security_perms: {str(e)}")
        language = await get_server_language(interaction.guild.id)
        if language == "es":
            await interaction.response.send_message(
                f"❌ Ha ocurrido un error: {str(e)}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )