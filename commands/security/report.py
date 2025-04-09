import discord
from discord import app_commands
from discord.ext import commands
import datetime
from typing import Optional
import pytz
from .mongo_utils import get_specific_field, get_server_language
from .mongo import mongo_report_storage
from .image_uploader import upload_image_to_imgbb

class RejectReasonModal(discord.ui.Modal):
    def __init__(self, bot, usuario_reporter, servidor, usuario_reportado, message, embeds, files, report_reason):
        super().__init__(title="Razón de rechazo")
        self.bot = bot
        self.usuario_reporter = usuario_reporter
        self.servidor = servidor
        self.usuario_reportado = usuario_reportado
        self.message = message
        self.embeds = embeds
        self.files = files
        self.report_reason = report_reason
        
        self.reason = discord.ui.TextInput(
            label="¿Por qué rechazas este reporte?",
            style=discord.TextStyle.paragraph,
            placeholder="Escribe la razón del rechazo...",
            required=True,
            max_length=1000
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        rejection_reason = self.reason.value
        
        notification_view = discord.ui.View()
        notification_view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Servidor de Soporte",
            url="https://discord.gg/eQ9uZSrrfZ"
        ))
        
        notification_sent = False
        try:
            user = await self.bot.fetch_user(self.usuario_reporter.id)
            await user.send(
                f"🇪🇸 Tu reporte de usuario a `{self.usuario_reportado.name}` (ID: {self.usuario_reportado.id}) en el servidor `{self.servidor.name}` ha sido rechazado debido a:\n```\n{rejection_reason}\n```\n\n"
                f"🇬🇧 Your user report on `{self.usuario_reportado.name}` (ID: {self.usuario_reportado.id}) in the server `{self.servidor.name}` has been rejected due to:\n```\n{rejection_reason}\n```",
                view=notification_view
            )
            notification_sent = True
        except:
            try:
                security_config = await get_specific_field(self.servidor.id, "security")
                if security_config and "channel" in security_config:
                    alert_channel_id = security_config["channel"]
                    alert_channel = self.bot.get_channel(alert_channel_id)
                    
                    if alert_channel:
                        await alert_channel.send(
                            f"{self.usuario_reporter.mention}\n\n🇪🇸 Tu reporte de usuario a `{self.usuario_reportado.name}` (ID: {self.usuario_reportado.id}) en el servidor `{self.servidor.name}` ha sido rechazado debido a:\n```\n{rejection_reason}\n```\n\n"
                            f"🇬🇧 Your user report on `{self.usuario_reportado.name}` (ID: {self.usuario_reportado.id}) in the server `{self.servidor.name}` has been rejected due to:\n```\n{rejection_reason}\n```",
                            view=notification_view
                        )
                        notification_sent = True
            except:
                pass
        
        rejected_channel = self.bot.get_channel(1359190761635315953)
        
        if rejected_channel:
            self.embeds[1].add_field(
                name="Razón de rechazo",
                value=f"```\n{rejection_reason}\n```",
                inline=False
            )
            
            self.embeds[1].set_footer(
                text=f"Rechazado por: {interaction.user.name} • {datetime.datetime.now(pytz.timezone('Europe/Madrid')).strftime('%d/%m/%Y %H:%M')}",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            
            await rejected_channel.send(embeds=self.embeds, files=self.files)
            
            await self.message.delete()
        
        language = await get_server_language(interaction.guild.id)
        result_message = "Reporte rechazado ❌" if language == "es" else "Report rejected ❌"
        if notification_sent:
            if language == "es":
                result_message += "\nEl usuario ha sido notificado."
            else:
                result_message += "\nThe user has been notified."
        
        await interaction.followup.send(result_message)

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

class ReportButtonView(discord.ui.View):
    def __init__(self, bot, usuario_reporter, servidor, usuario_reportado, report_reason):
        super().__init__(timeout=None)
        self.bot = bot
        self.usuario_reporter = usuario_reporter
        self.servidor = servidor
        self.usuario_reportado = usuario_reportado
        self.thread = None
        self.report_reason = report_reason
    
    @discord.ui.button(label="Aceptar", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        
        await interaction.response.defer(ephemeral=True)
        
        uploaded_urls = []
        for attachment in interaction.message.attachments:
            try:
                image_bytes = await attachment.read()
                image_url = await upload_image_to_imgbb(image_bytes)
                if image_url:
                    uploaded_urls.append(image_url)
            except Exception as e:
                print(f"Error al subir imagen: {e}")

        usuarios_reportados = []
        if len(interaction.message.embeds) > 1:
            embed = interaction.message.embeds[1]
            for field in embed.fields:
                if field.name == "Usuarios reportados":
                    usuarios_texto = field.value.strip('```').strip()
                    lines = usuarios_texto.split('\n')
                    
                    current_id = None
                    for line in lines:
                        if line.startswith("ID: "):
                            current_id = int(line[4:])
                            usuarios_reportados.append(current_id)

        if not usuarios_reportados:
            usuarios_reportados = [self.usuario_reportado.id]

        for reported_user_id in usuarios_reportados:
            await mongo_report_storage.store_report(
                user_id=0,
                server_id=0,
                reported_user_id=reported_user_id,
                reason=self.report_reason,
                imagen_files=uploaded_urls
            )

            await check_user_in_guilds(self.bot, reported_user_id, self.report_reason)
        
        notification_view = discord.ui.View()
        notification_view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Servidor de Soporte",
            url="https://discord.gg/eQ9uZSrrfZ"
        ))
        
        notification_sent = False
        try:
            user = await self.bot.fetch_user(self.usuario_reporter.id)
            await user.send(
                f"🇪🇸 Tu reporte contra {self.usuario_reportado.name} en el servidor {self.servidor.name} ha sido **aceptado**. Gracias por ayudarnos a mantener la comunidad segura.\n\n"
                f"🇬🇧 Your report against {self.usuario_reportado.name} in the server {self.servidor.name} has been **accepted**. Thank you for helping us keep the community safe.",
                view=notification_view
            )
            notification_sent = True
        except:
            try:
                security_config = await get_specific_field(self.servidor.id, "security")
                if security_config and "channel" in security_config:
                    alert_channel_id = security_config["channel"]
                    alert_channel = self.bot.get_channel(alert_channel_id)
                    
                    if alert_channel:
                        await alert_channel.send(
                            f"{self.usuario_reporter.mention}\n\n🇪🇸 Tu reporte contra {self.usuario_reportado.name} en el servidor {self.servidor.name} ha sido **aceptado**. Gracias por ayudarnos a mantener la comunidad segura.\n\n"
                            f"🇬🇧 Your report against {self.usuario_reportado.name} in the server {self.servidor.name} has been **accepted**. Thank you for helping us keep the community safe.",
                            view=notification_view
                        )
                        notification_sent = True
            except:
                pass
        
        accepted_channel = self.bot.get_channel(1359190746896535903)
        
        if accepted_channel:
            message = interaction.message
            embeds = message.embeds.copy()
            
            files = []
            for attachment in message.attachments:
                file = await attachment.to_file()
                files.append(file)
            
            if len(embeds) > 1:
                embeds[1].set_footer(
                    text=f"Aprobado por: {interaction.user.name} • {datetime.datetime.now(pytz.timezone('Europe/Madrid')).strftime('%d/%m/%Y %H:%M')}",
                    icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                )
            
            await accepted_channel.send(embeds=embeds, files=files)
            
            await message.delete()
        
        language = await get_server_language(interaction.guild.id)
        result_message = "Reporte aceptado ✅" if language == "es" else "Report accepted ✅"
        if notification_sent:
            if language == "es":
                result_message += "\nEl usuario ha sido notificado."
            else:
                result_message += "\nThe user has been notified."
        
        await interaction.followup.send(result_message)
    
    @discord.ui.button(label="Rechazar", style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        embeds = message.embeds.copy()
        
        files = []
        for attachment in message.attachments:
            file = await attachment.to_file()
            files.append(file)
        
        modal = RejectReasonModal(
            self.bot, 
            self.usuario_reporter, 
            self.servidor, 
            self.usuario_reportado, 
            message,
            embeds, 
            files,
            self.report_reason
        )
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Consultar", style=discord.ButtonStyle.primary)
    async def query_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        dm_sent = False
        try:
            usuarios_datos = []
            if len(interaction.message.embeds) > 1:
                embed = interaction.message.embeds[1]
                for field in embed.fields:
                    if field.name == "Usuarios reportados":
                        usuarios_texto = field.value.strip('```').strip()
                        lines = usuarios_texto.split('\n')
                        
                        user_id = None
                        user_name = None
                        for i, line in enumerate(lines):
                            if line.startswith("ID: "):
                                user_id = line[4:]
                            elif line.startswith("Nombre: ") and user_id is not None:
                                user_name = line[8:]
                                usuarios_datos.append((user_id, user_name))
                                user_id = None

            if not usuarios_datos:
                usuarios_datos = [(str(self.usuario_reportado.id), self.usuario_reportado.global_name or self.usuario_reportado.name)]

            mensaje_usuarios = ""
            for i, (user_id, user_name) in enumerate(usuarios_datos):
                if i == 0:
                    mensaje_usuarios += f"`{user_name}` (ID: {user_id})"
                else:
                    mensaje_usuarios += f", `{user_name}` (ID: {user_id})"
            
            user = await self.bot.fetch_user(self.usuario_reporter.id)
            await user.send(
                f"🇪🇸 El equipo de seguridad del bot quiere hablar con usted por el reporte a {mensaje_usuarios} en el servidor `{self.servidor.name}` por `{self.report_reason}`. Para hablar con ellos, utilizaremos este chat privado.\n\n"
                f"🇬🇧 The bot security team wants to talk to you about your report against {mensaje_usuarios} in the server `{self.servidor.name}` for `{self.report_reason}`. We will use this private chat to communicate with you."
            )
            dm_sent = True
        except:
            try:
                security_config = await get_specific_field(self.servidor.id, "security")
                if security_config and "channel" in security_config:
                    alert_channel_id = security_config["channel"]
                    alert_channel = self.bot.get_channel(alert_channel_id)
                    
                    if alert_channel:
                        invite_button = discord.ui.View()
                        invite_button.add_item(discord.ui.Button(
                            style=discord.ButtonStyle.link,
                            label="Unirse al Servidor de Soporte",
                            url="https://discord.gg/eQ9uZSrrfZ"
                        ))

                        await alert_channel.send(
                            f"{self.usuario_reporter.mention}\n\n🇪🇸 El equipo de seguridad del bot quiere hablar con usted por su reporte. Por favor, únase al servidor de Discord y contacte con el soporte.\n\n"
                            f"🇬🇧 The bot security team wants to talk to you about your report. Please join the Discord server and contact support.",
                            view=invite_button
                        )
                        
                        try:
                            server_invite = await interaction.channel.create_invite(max_age=86400)
                            await interaction.channel.send(f"Enlace de invitación al servidor donde se reportó: {server_invite.url}")
                        except:
                            pass
                        
                        language = await get_server_language(interaction.guild.id)
                        if language == "es":
                            await interaction.followup.send("No se pudo enviar MD al usuario, pero se ha enviado un mensaje al canal de alertas del servidor.", ephemeral=True)
                        else:
                            await interaction.followup.send("Could not send DM to the user, but a message has been sent to the server's alert channel.", ephemeral=True)
                        return
            except:
                pass
            
            support_link = discord.ui.View()
            support_link.add_item(discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Unirse al Servidor de Soporte",
                url="https://discord.gg/eQ9uZSrrfZ"
            ))
            
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.followup.send(
                    "No se pudo contactar al usuario. Por favor, proporcione este enlace para que el usuario pueda unirse al servidor de soporte.",
                    view=support_link,
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "Could not contact the user. Please provide this link so the user can join the support server.",
                    view=support_link,
                    ephemeral=True
                )
            
            return
        
        if dm_sent:
            thread = await interaction.channel.create_thread(
                name=f"Consulta-Reporte-{self.usuario_reportado.name}",
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread
            )
            self.thread = thread
            
            mod = interaction.guild.get_member(702934069138161835)
            if mod:
                await thread.add_user(mod)
            
            mod = interaction.guild.get_member(327157607724875776)
            if mod:
                await thread.add_user(mod)
            
            close_view = CloseThreadView(self.thread, self.usuario_reporter)
            await thread.send(f"🇪🇸 Mensaje enviado al usuario\n🇬🇧 Message sent to the user", view=close_view)
            
            cog = self.bot.get_cog("ReportCommand")
            if cog:
                cog.dm_listeners[self.usuario_reporter.id] = {
                    "thread": thread,
                    "reported_user": self.usuario_reportado,
                    "server": self.servidor
                }
            
            language = await get_server_language(interaction.guild.id)
            if language == "es":
                await interaction.followup.send(f"Hilo de consulta creado: {thread.mention}", ephemeral=True)
            else:
                await interaction.followup.send(f"Consultation thread created: {thread.mention}", ephemeral=True)

class CloseThreadView(discord.ui.View):
    def __init__(self, thread, usuario_reporter=None):
        super().__init__(timeout=None)
        self.thread = thread
        self.usuario_reporter = usuario_reporter
    
    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.secondary)
    async def close_thread(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("ReportCommand")
        user_id_to_notify = None
        
        if cog:
            for user_id, data in list(cog.dm_listeners.items()):
                if data["thread"].id == self.thread.id:
                    user_id_to_notify = user_id
                    del cog.dm_listeners[user_id]
                    break
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        await self.thread.send("🇪🇸 Hilo cerrado.\n🇬🇧 Thread closed.")
        
        if user_id_to_notify or self.usuario_reporter:
            try:
                user_id = user_id_to_notify or self.usuario_reporter.id
                user = await interaction.client.fetch_user(user_id)
                
                support_view = discord.ui.View()
                support_view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label="Servidor de Discord de Soporte",
                    url="https://discord.gg/eQ9uZSrrfZ"
                ))

                await user.send(
                    "🇪🇸 La conversación sobre tu reporte ha sido cerrada. Si tienes más preguntas, por favor entra al servidor de Discord de Soporte\n\n"
                    "🇬🇧 The conversation about your report has been closed. If you have more questions, please join the Support Discord server",
                    view=support_view
                )
            except Exception as e:
                await self.thread.send(f"No se pudo notificar al usuario: {e}")
        
        await self.thread.archive(locked=True)

class ReportCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_channel_id = 1359190727950860288
        self.dm_listeners = {}
        
        bot.add_listener(self.handle_reporter_dm, 'on_message')
        bot.add_listener(self.handle_thread_message, 'on_message')
    
    async def handle_reporter_dm(self, message):
        if message.author.bot:
            return
            
        if not isinstance(message.channel, discord.DMChannel):
            return
            
        report_data = self.dm_listeners.get(message.author.id)
        if not report_data:
            return
            
        thread = report_data["thread"]
        
        try:
            if message.attachments:
                files = []
                for attachment in message.attachments:
                    file = await attachment.to_file()
                    files.append(file)
                
                await thread.send(
                    content=f"**{message.author}** envió: {message.content if message.content else ''}",
                    files=files
                )
            else:
                await thread.send(f"**{message.author}** envió: {message.content}")
        except Exception as e:
            print(f"Error al reenviar mensaje al hilo: {e}")
    
    async def handle_thread_message(self, message):
        if message.author.bot:
            return
            
        if not isinstance(message.channel, discord.Thread):
            return
            
        user_id = None
        for uid, data in self.dm_listeners.items():
            if data["thread"].id == message.channel.id:
                user_id = uid
                break
                
        if not user_id:
            return
                
        try:
            user = await self.bot.fetch_user(user_id)
            
            if message.attachments:
                files = []
                for attachment in message.attachments:
                    file = await attachment.to_file()
                    files.append(file)
                
                await user.send(
                    content=f"**Staff**: {message.content if message.content else ''}",
                    files=files
                )
            else:
                await user.send(f"**Staff**: {message.content}")
                
            await message.add_reaction("✅")
        except Exception as e:
            print(f"Error al reenviar mensaje al usuario: {e}")
            await message.channel.send(f"Error al enviar mensaje al usuario: {e}")
            await message.add_reaction("❌")
    
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
        await interaction.response.defer(ephemeral=True, thinking=True)
        language = await get_server_language(interaction.guild.id)
        
        try:
            report_channel = self.bot.get_channel(self.report_channel_id)
            if not report_channel:
                if language == "es":
                    await interaction.followup.send("No se pudo encontrar el canal de reportes.", ephemeral=True)
                else:
                    await interaction.followup.send("Could not find the reports channel.", ephemeral=True)
                return

            servidor = interaction.guild
            
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
                if language == "es":
                    await interaction.followup.send("No se ha proporcionado ningún usuario válido para reportar.", ephemeral=True)
                else:
                    await interaction.followup.send("No valid user has been provided to report.", ephemeral=True)
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
                if language == "es":
                    await interaction.followup.send("No se pudo encontrar ningún usuario válido para reportar.", ephemeral=True)
                else:
                    await interaction.followup.send("Could not find any valid user to report.", ephemeral=True)
                return
            
            files = []
            imagen_urls = []
            attachments = [imagen1, imagen2, imagen3, imagen4, imagen5, imagen6]
            
            for attachment in attachments:
                if attachment is not None:
                    try:
                        file = await attachment.to_file()
                        files.append(file)
                        if hasattr(attachment, 'url'):
                            imagen_urls.append(attachment.url)
                    except Exception as e:
                        print(f"Error al procesar el archivo adjunto: {e}")
            
            embeds = []
            
            madrid_tz = pytz.timezone('Europe/Madrid')
            timestamp_madrid = datetime.datetime.now(madrid_tz)
            
            reporte_embed = discord.Embed(
                title="Nuevo reporte",
                description=f"### Razón reporte:\n```ansi\n{razon}\n```\n",
                color=0xEB3737,
                timestamp=timestamp_madrid
            )
            reporte_embed.set_image(url="https://i.imgur.com/usPSOmX.png")
            embeds.append(reporte_embed)
            
            datos_embed = discord.Embed(
                title="Datos",
                color=0xEBD513
            )

            usuarios_texto = ""
            for user in reported_users:
                user_name = user.global_name or user.name
                usuarios_texto += f"ID: {user.id}\nNombre: {user_name}\n\n"
            
            datos_embed.add_field(
                name="Usuarios reportados",
                value=f"```\n{usuarios_texto.strip()}\n```",
                inline=False
            )
            
            datos_embed.add_field(
                name="Servidor donde se reporta",
                value=f"```\nID: {servidor.id}\nNombre: {servidor.name}\n```",
                inline=False
            )
            
            datos_embed.add_field(
                name="Usuario que reporta",
                value=f"```\nID: {interaction.user.id}\nNombre: {interaction.user.name}\n```",
                inline=False
            )
            
            datos_embed.set_image(url="https://i.imgur.com/VVoXfQO.png")
            embeds.append(datos_embed)

            primary_reported_user = reported_users[0]
            view = ReportButtonView(self.bot, interaction.user, servidor, primary_reported_user, razon)

            file_copies = []
            for attachment in attachments:
                if attachment is not None:
                    try:
                        file = await attachment.to_file()
                        file_copies.append(file)
                    except Exception as e:
                        print(f"Error al procesar archivo adjunto: {e}")
            
            await report_channel.send(content="hola, esto es un reporte.", embeds=embeds, files=file_copies, view=view)
            
            user_mentions = ", ".join([user.mention for user in reported_users])
            if language == "es":
                await interaction.followup.send(
                    f"✅ Reporte enviado correctamente contra {user_mentions}.", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"✅ Report successfully sent against {user_mentions}.", 
                    ephemeral=True
                )
        
        except Exception as e:
            print(f"Error en el comando report: {e}")
            if language == "es":
                await interaction.followup.send(
                    "Ha ocurrido un error al procesar tu reporte. Por favor, inténtalo de nuevo o contacta con un administrador.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An error occurred while processing your report. Please try again or contact an administrator.",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(ReportCommand(bot))