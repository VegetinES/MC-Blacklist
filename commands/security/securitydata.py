import discord
from discord.ext import commands
from .mongo_utils import get_server_data, get_specific_field, get_server_language

async def show_security_data(interaction):
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

        security_config = await get_specific_field(server_id, "security")

        if language == "es":
            embed = discord.Embed(
                title="📊 Configuración de Seguridad",
                color=discord.Color.blue(),
                description="Información de la configuración actual de seguridad para este servidor."
            )

            if not security_config:
                embed.description = "No hay configuración de seguridad establecida para este servidor. Utiliza los comandos `/security perms` y `/security alert` para configurarla."
                await interaction.response.send_message(embed=embed)
                return

            channel_id = security_config.get("channel", 0)
            channel = interaction.guild.get_channel(channel_id) if channel_id != 0 else None
            
            if channel:
                embed.add_field(
                    name="Canal de Alertas",
                    value=f"✅ Configurado: {channel.mention} (ID: {channel_id})",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Canal de Alertas",
                    value="❌ No configurado. Usa `/security alert` para establecer un canal.",
                    inline=False
                )

            message = security_config.get("message", "")
            if message:
                embed.add_field(
                    name="Mensaje de Alerta",
                    value=f"✅ Configurado:\n```\n{message}\n```",
                    inline=False
                )

                example_message = message.replace("{user}", "@Usuario").replace("{usertag}", "Usuario").replace("{userid}", "123456789012345678")
                
                embed.add_field(
                    name="Ejemplo",
                    value=f"{example_message}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Mensaje de Alerta",
                    value="❌ No configurado. Usa `/security alert` para establecer un mensaje.",
                    inline=False
                )

            perms = security_config.get("perms", [0])
            
            if perms == 0 or perms == [0]:
                embed.add_field(
                    name="Roles con Permisos de Seguridad",
                    value="❌ No hay roles configurados. Solo los administradores pueden usar los comandos de seguridad.",
                    inline=False
                )
            else:
                role_mentions = []
                for role_id in perms:
                    if role_id != 0:
                        role = interaction.guild.get_role(role_id)
                        if role:
                            role_mentions.append(f"{role.mention} (ID: {role.id})")
                
                if role_mentions:
                    embed.add_field(
                        name="Roles con Permisos de Seguridad",
                        value="✅ Los siguientes roles pueden usar los comandos de seguridad:\n" + "\n".join(role_mentions),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Roles con Permisos de Seguridad",
                        value="❌ No hay roles válidos configurados. Solo los administradores pueden usar los comandos de seguridad.",
                        inline=False
                    )
            
            lang_value = security_config.get("language", "es")
            language_name = "Español" if lang_value == "es" else "English"
            embed.add_field(
                name="Idioma",
                value=f"✅ Configurado: **{language_name}**",
                inline=False
            )

            embed.add_field(
                name="📝 Nota",
                value="Utiliza `/blacklist help` para obtener más información sobre los comandos de seguridad.",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="📊 Security Configuration",
                color=discord.Color.blue(),
                description="Information about the current security configuration for this server."
            )

            if not security_config:
                embed.description = "No security configuration has been set for this server. Use the `/security perms` and `/security alert` commands to configure it."
                await interaction.response.send_message(embed=embed)
                return

            channel_id = security_config.get("channel", 0)
            channel = interaction.guild.get_channel(channel_id) if channel_id != 0 else None
            
            if channel:
                embed.add_field(
                    name="Alert Channel",
                    value=f"✅ Configured: {channel.mention} (ID: {channel_id})",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Alert Channel",
                    value="❌ Not configured. Use `/security alert` to set a channel.",
                    inline=False
                )

            message = security_config.get("message", "")
            if message:
                embed.add_field(
                    name="Alert Message",
                    value=f"✅ Configured:\n```\n{message}\n```",
                    inline=False
                )

                example_message = message.replace("{user}", "@User").replace("{usertag}", "User").replace("{userid}", "123456789012345678")
                
                embed.add_field(
                    name="Example",
                    value=f"{example_message}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Alert Message",
                    value="❌ Not configured. Use `/security alert` to set a message.",
                    inline=False
                )

            perms = security_config.get("perms", [0])
            
            if perms == 0 or perms == [0]:
                embed.add_field(
                    name="Roles with Security Permissions",
                    value="❌ No roles configured. Only administrators can use security commands.",
                    inline=False
                )
            else:
                role_mentions = []
                for role_id in perms:
                    if role_id != 0:
                        role = interaction.guild.get_role(role_id)
                        if role:
                            role_mentions.append(f"{role.mention} (ID: {role.id})")
                
                if role_mentions:
                    embed.add_field(
                        name="Roles with Security Permissions",
                        value="✅ The following roles can use security commands:\n" + "\n".join(role_mentions),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Roles with Security Permissions",
                        value="❌ No valid roles configured. Only administrators can use security commands.",
                        inline=False
                    )
            
            lang_value = security_config.get("language", "es")
            language_name = "Español" if lang_value == "es" else "English"
            embed.add_field(
                name="Language",
                value=f"✅ Configured: **{language_name}**",
                inline=False
            )

            embed.add_field(
                name="📝 Note",
                value="Use `/blacklist help` to get more information about security commands.",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    except Exception as e:
        print(f"Error en show_security_data: {str(e)}")
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