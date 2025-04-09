import discord
from discord.ext import commands
from .mongo_utils import get_server_data, get_specific_field, update_server_data, get_server_language

async def set_security_alert(interaction, canal, mensaje):
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

        security_config["channel"] = canal.id
        security_config["message"] = mensaje

        if await update_server_data(server_id, "channel", canal.id) and await update_server_data(server_id, "message", mensaje):
            if language == "es":
                embed = discord.Embed(
                    title="✅ Configuración de Alertas Actualizada",
                    color=discord.Color.green(),
                    description=f"Se ha configurado correctamente el canal y mensaje de alertas de seguridad."
                )
                
                embed.add_field(
                    name="Canal",
                    value=f"{canal.mention} (ID: {canal.id})",
                    inline=False
                )
                
                embed.add_field(
                    name="Mensaje",
                    value=f"```\n{mensaje}\n```",
                    inline=False
                )
                
                embed.add_field(
                    name="Variables disponibles",
                    value="• `{user}` - Mención al usuario malicioso\n• `{usertag}` - Nombre del usuario malicioso\n• `{userid}` - ID del usuario malicioso",
                    inline=False
                )

                example_message = mensaje.replace("{user}", "@Usuario").replace("{usertag}", "Usuario").replace("{userid}", "123456789012345678")
                
                embed.add_field(
                    name="Ejemplo",
                    value=f"{example_message}",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="✅ Alert Configuration Updated",
                    color=discord.Color.green(),
                    description=f"The security alert channel and message have been successfully configured."
                )
                
                embed.add_field(
                    name="Channel",
                    value=f"{canal.mention} (ID: {canal.id})",
                    inline=False
                )
                
                embed.add_field(
                    name="Message",
                    value=f"```\n{mensaje}\n```",
                    inline=False
                )
                
                embed.add_field(
                    name="Available variables",
                    value="• `{user}` - Mention to the malicious user\n• `{usertag}` - Name of the malicious user\n• `{userid}` - ID of the malicious user",
                    inline=False
                )

                example_message = mensaje.replace("{user}", "@User").replace("{usertag}", "User").replace("{userid}", "123456789012345678")
                
                embed.add_field(
                    name="Example",
                    value=f"{example_message}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        else:
            if language == "es":
                await interaction.response.send_message(
                    "❌ Ha ocurrido un error al actualizar la configuración de alertas.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ An error occurred while updating the alert configuration.",
                    ephemeral=True
                )
    
    except Exception as e:
        print(f"Error en set_security_alert: {str(e)}")
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