import discord
from discord.ext import commands
from .mongo_utils import update_server_data, get_server_language

async def change_language(interaction, language):
    try:
        if not interaction.user.guild_permissions.administrator:
            if language == "es":
                await interaction.response.send_message(
                    "No tienes permisos para usar este comando. Se requiere ser Administrador del servidor.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "You don't have permissions to use this command. You need to be a Server Administrator.",
                    ephemeral=True
                )
            return
        
        server_id = interaction.guild.id
        
        if language.lower() not in ["español", "english", "es", "en"]:
            current_lang = await get_server_language(server_id)
            if current_lang == "es":
                await interaction.response.send_message(
                    "Idioma no válido. Opciones disponibles: 'Español' o 'English'.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Invalid language. Available options: 'Español' or 'English'.",
                    ephemeral=True
                )
            return
        
        language_code = "es" if language.lower() in ["español", "es"] else "en"
        
        if await update_server_data(server_id, "language", language_code):
            language_name = "Español" if language_code == "es" else "English"
            
            embed = discord.Embed(
                title="✅ Idioma Actualizado" if language_code == "es" else "✅ Language Updated",
                color=discord.Color.green()
            )
            
            if language_code == "es":
                embed.description = f"El idioma del bot ha sido configurado a **{language_name}**."
            else:
                embed.description = f"Bot language has been set to **{language_name}**."
                
            await interaction.response.send_message(embed=embed)
        else:
            current_lang = await get_server_language(server_id)
            if current_lang == "es":
                await interaction.response.send_message(
                    "Ha ocurrido un error al actualizar el idioma.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "An error occurred while updating the language.",
                    ephemeral=True
                )
    
    except Exception as e:
        print(f"Error en change_language: {str(e)}")
        await interaction.response.send_message(
            f"Error: {str(e)}",
            ephemeral=True
        )