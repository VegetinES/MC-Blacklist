import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import datetime
from .mongo import mongo_report_storage
from .image_uploader import upload_image_to_imgbb
from .mongo_utils import get_specific_field, get_server_language

class BlacklistAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cargado correctamente")
    
async def check_user_in_guilds(bot, user_id, reason):
    try:
        try:
            user = await bot.fetch_user(user_id)
            user_name = user.name
            user_avatar = user.display_avatar.url if user.avatar else None
        except:
            user_name = f"Usuario con ID {user_id}"
            user_avatar = None

        for guild in bot.guilds:
            try:
                member = guild.get_member(user_id)
                if not member:
                    try:
                        member = await guild.fetch_member(user_id)
                    except discord.NotFound:
                        continue

                security_config = await get_specific_field(guild.id, "security")
                if not security_config or "channel" not in security_config or security_config["channel"] == 0:
                    continue
                
                alert_channel_id = security_config["channel"]
                alert_channel = guild.get_channel(alert_channel_id)
                
                if not alert_channel:
                    continue

                language = await get_server_language(guild.id)
                
                if language == "es":
                    embed = discord.Embed(
                        title="⚠️ Usuario añadido a la blacklist",
                        description=f"{member.mention} `{member.name}` (ID: {member.id}) ha sido añadido a la blacklist y se encuentra en este servidor.",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="Razón del reporte",
                        value=reason,
                        inline=False
                    )
                else:
                    embed = discord.Embed(
                        title="⚠️ User added to blacklist",
                        description=f"{member.mention} `{member.name}` (ID: {member.id}) has been added to the blacklist and is in this server.",
                        color=discord.Color.red()
                    )
                    
                    embed.add_field(
                        name="Report reason",
                        value=reason,
                        inline=False
                    )
                
                if user_avatar:
                    embed.set_thumbnail(url=user_avatar)
                
                await alert_channel.send(embed=embed)
                
                message_template = security_config.get("message", "")
                if message_template:
                    formatted_message = message_template.replace("{user}", member.mention) \
                                                      .replace("{usertag}", member.name) \
                                                      .replace("{userid}", str(member.id))
                    await alert_channel.send(formatted_message)
            
            except Exception as e:
                print(f"Error al verificar el usuario {user_id} en el servidor {guild.name}: {e}")
    
    except Exception as e:
        print(f"Error en check_user_in_guilds: {e}")

    async def add_to_blacklist(
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
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if interaction.user.id not in [327157607724875776, 702934069138161835]:
            return

        try:
            user_ids = []
            for user_id in usuarios.split():
                user_id = user_id.strip()
                if user_id.startswith("<@") and user_id.endswith(">"):
                    user_id = user_id[2:-1]
                    if user_id.startswith("!"):
                        user_id = user_id[1:]
                try:
                    user_ids.append(int(user_id))
                except ValueError:
                    continue
            
            if not user_ids:
                await interaction.followup.send("No se ha proporcionado ningún usuario válido para añadir a la blacklist.", ephemeral=True)
                return

            reported_users = []
            for user_id in user_ids:
                try:
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        reported_users.append(user)
                except:
                    pass
            
            if not reported_users:
                await interaction.followup.send("No se pudo encontrar ningún usuario válido para añadir a la blacklist.", ephemeral=True)
                return

            imagen_urls = []
            attachments = [imagen1, imagen2, imagen3, imagen4, imagen5, imagen6]
            
            for attachment in attachments:
                if attachment is not None:
                    try:
                        image_bytes = await attachment.read()
                        image_url = await upload_image_to_imgbb(image_bytes)
                        if image_url:
                            imagen_urls.append(image_url)
                    except Exception as e:
                        print(f"Error al procesar/subir el archivo adjunto: {e}")

            success_users = []
            error_users = []
            
            for user in reported_users:
                try:
                    report_id = await mongo_report_storage.store_report(
                        user_id=interaction.user.id,
                        server_id=interaction.guild.id,
                        reported_user_id=user.id,
                        reason=razon,
                        imagen_files=imagen_urls
                    )
                    
                    if report_id:
                        success_users.append(user)
                        await check_user_in_guilds(self.bot, user.id, razon)
                    else:
                        error_users.append(user)
                except Exception as e:
                    print(f"Error al añadir usuario {user.id} a la blacklist: {e}")
                    error_users.append(user)

            if success_users:
                user_mentions = ", ".join([f"{user.mention} (`{user.name}`) ID: {user.id}" for user in success_users])
                embed = discord.Embed(
                    title="✅ Usuarios añadidos a la blacklist",
                    description=f"Se han añadido correctamente los siguientes usuarios a la blacklist:\n{user_mentions}",
                    color=discord.Color.green()
                )
                
                if error_users:
                    error_mentions = ", ".join([f"{user.mention} (`{user.name}`) ID: {user.id}" for user in error_users])
                    embed.add_field(
                        name="⚠️ Errores",
                        value=f"No se pudieron añadir los siguientes usuarios:\n{error_mentions}",
                        inline=False
                    )
                
                embed.add_field(
                    name="📝 Razón",
                    value=razon,
                    inline=False
                )
                
                embed.add_field(
                    name="🖼️ Pruebas",
                    value=f"Se han adjuntado {len(imagen_urls)} imágenes como prueba.",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=False)
            else:
                await interaction.followup.send("❌ No se ha podido añadir ningún usuario a la blacklist.", ephemeral=True)
        
        except Exception as e:
            print(f"Error en comando add_to_blacklist: {e}")
            await interaction.followup.send(
                f"Ha ocurrido un error al procesar la solicitud: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(BlacklistAdd(bot))