import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional
import datetime
import urllib.parse
from .mongo_utils import get_specific_field, get_server_language

from .mongo import mongo_report_storage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)
logger = logging.getLogger(__name__)

class ReportsView(discord.ui.View):
    def __init__(self, reports, user_id, bot, original_interaction=None, language="es"):
        super().__init__()
        self.reports = reports
        self.user_id = user_id
        self.bot = bot
        self.original_interaction = original_interaction
        self.language = language

        has_evidence = any(
            report.get('imagen_urls') and len(report.get('imagen_urls', [])) > 0 
            for report in reports
        )

        if has_evidence:
            evidence_button = discord.ui.Button(
                style=discord.ButtonStyle.primary, 
                label="Ver Pruebas" if language == "es" else "View Evidence"
            )
            evidence_button.callback = self.show_evidence
            self.add_item(evidence_button)

    async def show_evidence(self, interaction: discord.Interaction):
        reports_with_images = [
            report for report in self.reports 
            if report.get('imagen_urls') and len(report.get('imagen_urls', [])) > 0
        ]

        logger.info(f"\n{'='*50}\nDEBUG - REPORTES CON IMÁGENES:\n"
                   f"Cantidad: {len(reports_with_images)}\n"
                   f"Contenido: {reports_with_images}\n"
                   f"{'='*50}\n")

        evidence_view = EvidenceView(
            user_id=self.user_id, 
            reports=reports_with_images,
            original_interaction=interaction,
            language=self.language
        )

        first_report = reports_with_images[0] if reports_with_images else None
        first_image_url = first_report['imagen_urls'][0] if first_report and first_report['imagen_urls'] else None

        if first_image_url:
            first_image_url = self.clean_image_url(first_image_url)

        logger.info(f"\n{'='*50}\nDEBUG - PRIMERA IMAGEN:\n"
                   f"Reporte: {first_report}\n"
                   f"URL: {first_image_url}\n"
                   f"{'='*50}\n")

        if self.language == "es":
            embed = discord.Embed(
                title=f"Pruebas de Reporte - Usuario {self.user_id}",
                description=f"Razón: {first_report.get('reason', 'Sin razón')}\n"
                            f"Fecha: <t:{int(first_report['timestamp'])}:R>" if first_report else "No hay reportes con imágenes",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title=f"Report Evidence - User {self.user_id}",
                description=f"Reason: {first_report.get('reason', 'No reason')}\n"
                            f"Date: <t:{int(first_report['timestamp'])}:R>" if first_report else "No reports with images",
                color=discord.Color.orange()
            )

        if first_image_url:
            embed.set_image(url=first_image_url)
            logger.info(f"URL de imagen establecida: {first_image_url}")

        await interaction.response.edit_message(
            content=None if first_image_url else "No hay imágenes para mostrar" if self.language == "es" else "No images to display",
            embed=embed, 
            view=evidence_view
        )

    def clean_image_url(self, url):
        if not url:
            return None

        if 'imgbb.com' in url:
            return url
            
        cleaned = url.strip()
        if '?' in cleaned:
            cleaned = cleaned.split('?')[0]
        cleaned = urllib.parse.quote(cleaned, safe=':/')
        return cleaned

class EvidenceView(discord.ui.View):
    def __init__(self, user_id, reports, current_report_index=0, current_page=0, original_interaction=None, language="es"):
        super().__init__()
        self.user_id = user_id
        self.reports = reports
        self.current_report_index = current_report_index
        self.current_page = current_page
        self.max_report_pages = len(reports)
        self.original_interaction = original_interaction
        self.language = language
        
        current_report = self.reports[self.current_report_index] if self.reports else None
        self.imagen_urls = [self.clean_image_url(url) for url in current_report.get('imagen_urls', [])] if current_report else []
        self.max_evidence_pages = len(self.imagen_urls)
        
        self.update_buttons()
    
    def clean_image_url(self, url):
        if not url:
            return None
            
        if 'imgbb.com' in url:
            return url
            
        cleaned = url.strip()
        if '?' in cleaned:
            cleaned = cleaned.split('?')[0]
        cleaned = urllib.parse.quote(cleaned, safe=':/')
        return cleaned

    def update_buttons(self):
        self.clear_items()
        
        if self.max_evidence_pages > 1:
            prev_evidence_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary, 
                label="◀️ Prueba anterior" if self.language == "es" else "◀️ Previous evidence", 
                disabled=self.current_page == 0,
                row=0
            )
            prev_evidence_button.callback = self.prev_evidence
            self.add_item(prev_evidence_button)
            
            evidence_indicator = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=f"Prueba {self.current_page + 1}/{self.max_evidence_pages}" if self.language == "es" else f"Evidence {self.current_page + 1}/{self.max_evidence_pages}",
                disabled=True,
                row=0
            )
            self.add_item(evidence_indicator)
            
            next_evidence_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary, 
                label="Siguiente prueba ▶️" if self.language == "es" else "Next evidence ▶️", 
                disabled=self.current_page >= self.max_evidence_pages - 1,
                row=0
            )
            next_evidence_button.callback = self.next_evidence
            self.add_item(next_evidence_button)
        
        if self.max_report_pages > 1:
            prev_report_button = discord.ui.Button(
                style=discord.ButtonStyle.primary, 
                label="◀️ Reporte anterior" if self.language == "es" else "◀️ Previous report",
                disabled=self.current_report_index == 0,
                row=1
            )
            prev_report_button.callback = self.prev_report
            self.add_item(prev_report_button)
            
            report_indicator = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label=f"Reporte {self.current_report_index + 1}/{self.max_report_pages}" if self.language == "es" else f"Report {self.current_report_index + 1}/{self.max_report_pages}",
                disabled=True,
                row=1
            )
            self.add_item(report_indicator)
            
            next_report_button = discord.ui.Button(
                style=discord.ButtonStyle.primary, 
                label="Siguiente reporte ▶️" if self.language == "es" else "Next report ▶️",
                disabled=self.current_report_index >= self.max_report_pages - 1,
                row=1
            )
            next_report_button.callback = self.next_report
            self.add_item(next_report_button)

        back_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary, 
            label="⬅️ Volver atrás" if self.language == "es" else "⬅️ Go back",
            row=2
        )
        back_button.callback = self.back_to_reports
        self.add_item(back_button)
    
    async def prev_evidence(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await self.update_message(interaction)
    
    async def next_evidence(self, interaction: discord.Interaction):
        if self.current_page < self.max_evidence_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await self.update_message(interaction)
    
    async def prev_report(self, interaction: discord.Interaction):
        if self.current_report_index > 0:
            self.current_report_index -= 1
            self.current_page = 0
            current_report = self.reports[self.current_report_index]
            self.imagen_urls = [self.clean_image_url(url) for url in current_report.get('imagen_urls', [])]
            self.max_evidence_pages = len(self.imagen_urls)
            self.update_buttons()
            await self.update_message(interaction)
    
    async def next_report(self, interaction: discord.Interaction):
        if self.current_report_index < self.max_report_pages - 1:
            self.current_report_index += 1
            self.current_page = 0
            current_report = self.reports[self.current_report_index]
            self.imagen_urls = [self.clean_image_url(url) for url in current_report.get('imagen_urls', [])]
            self.max_evidence_pages = len(self.imagen_urls)
            self.update_buttons()
            await self.update_message(interaction)
    
    async def back_to_reports(self, interaction: discord.Interaction):
        if self.original_interaction:
            user_reports = self.reports
            
            try:
                user = await interaction.client.fetch_user(self.user_id)
                user_name = f"{user.name} ({user.mention})"
                user_avatar = user.display_avatar.url
            except:
                user_name = f"Usuario con ID {self.user_id}" if self.language == "es" else f"User with ID {self.user_id}"
                user_avatar = None

            if self.language == "es":
                embed = discord.Embed(
                    title=f"📋 Reportes de {user_name}",
                    description=f"Se han encontrado {len(user_reports)} reportes para este usuario.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title=f"📋 Reports for {user_name}",
                    description=f"{len(user_reports)} reports have been found for this user.",
                    color=discord.Color.red()
                )

            if user_avatar:
                embed.set_thumbnail(url=user_avatar)

            for i, report in enumerate(user_reports, 1):
                if self.language == "es":
                    embed.add_field(
                        name=f"Reporte #{i}",
                        value=f"**Razón:** {report.get('reason', 'Sin razón')}\n"
                              f"**Fecha:** <t:{int(report['timestamp'])}:R>",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"Report #{i}",
                        value=f"**Reason:** {report.get('reason', 'No reason')}\n"
                              f"**Date:** <t:{int(report['timestamp'])}:R>",
                        inline=False
                    )

            reports_view = ReportsView(
                reports=user_reports, 
                user_id=self.user_id, 
                bot=interaction.client,
                original_interaction=self.original_interaction,
                language=self.language
            )

            await interaction.response.edit_message(embed=embed, view=reports_view)
        else:
            await interaction.response.send_message(
                "No se puede volver a la vista anterior." if self.language == "es" else "Cannot return to previous view.", 
                ephemeral=True
            )
    
    async def update_message(self, interaction: discord.Interaction):
        if not self.reports or self.current_report_index >= len(self.reports):
            if self.language == "es":
                embed = discord.Embed(
                    title="Error",
                    description="No se pudo cargar el reporte solicitado.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Could not load the requested report.",
                    color=discord.Color.red()
                )
            await interaction.response.edit_message(embeds=[embed], view=self)
            return
        
        report = self.reports[self.current_report_index]
        
        if not self.imagen_urls:
            if self.language == "es":
                embed = discord.Embed(
                    title=f"Pruebas - Reporte {self.current_report_index + 1}/{self.max_report_pages}",
                    description=f"**Razón del reporte:** {report['reason']}\n\n"
                                f"**No hay pruebas para este reporte.**",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title=f"Evidence - Report {self.current_report_index + 1}/{self.max_report_pages}",
                    description=f"**Report reason:** {report['reason']}\n\n"
                                f"**No evidence for this report.**",
                    color=discord.Color.orange()
                )
            await interaction.response.edit_message(embeds=[embed], view=self)
            return
        
        try:
            current_image = self.imagen_urls[self.current_page] if self.current_page < len(self.imagen_urls) else None
            
            if self.language == "es":
                embed = discord.Embed(
                    title=f"Pruebas - Reporte {self.current_report_index + 1}/{self.max_report_pages}",
                    description=f"**Razón del reporte:** {report['reason']}\n"
                                f"**Fecha:** <t:{int(report['timestamp'])}:R>",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title=f"Evidence - Report {self.current_report_index + 1}/{self.max_report_pages}",
                    description=f"**Report reason:** {report['reason']}\n"
                                f"**Date:** <t:{int(report['timestamp'])}:R>",
                    color=discord.Color.orange()
                )
            
            if current_image:
                embed.set_image(url=current_image)

                await interaction.response.edit_message(
                    content=f"**URL de la imagen:**\n{current_image}" if self.language == "es" else f"**Image URL:**\n{current_image}",
                    embed=embed,
                    view=self
                )
            else:
                if self.language == "es":
                    embed.description += "\n\n⚠️ No se pudo cargar la imagen"
                else:
                    embed.description += "\n\n⚠️ Could not load the image"
                await interaction.response.edit_message(embed=embed, view=self)
                
        except Exception as e:
            error_msg = f"Error al mostrar la imagen: {str(e)}" if self.language == "es" else f"Error displaying the image: {str(e)}"
            logger.error(error_msg, exc_info=True)
            embed = discord.Embed(
                title="Error",
                description=error_msg,
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=self)

class BlacklistUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    async def _handle_user_report(self, interaction: discord.Interaction, user_id: str):
        await interaction.response.defer(ephemeral=False)
        language = await get_server_language(interaction.guild.id)
        
        try:
            user_id_int = int(user_id)
            user_reports = await mongo_report_storage.get_user_reports(user_id_int)

            if not user_reports:
                try:
                    user = await self.bot.fetch_user(user_id_int)
                    if language == "es":
                        description = f"No hay reportes para {user.mention} ({user.name})"
                    else:
                        description = f"No reports for {user.mention} ({user.name})"
                except:
                    if language == "es":
                        description = f"No hay reportes para el usuario con ID {user_id}"
                    else:
                        description = f"No reports for the user with ID {user_id}"
                
                if language == "es":
                    embed = discord.Embed(
                        title="🔍 Consulta de Reportes",
                        description=description,
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="🔍 Reports Query",
                        description=description,
                        color=discord.Color.green()
                    )
                await interaction.followup.send(embed=embed)
                return

            await self._show_user_reports(interaction, user_id_int, user_reports, language)
            
        except ValueError:
            if language == "es":
                embed = discord.Embed(
                    title="❌ Error",
                    description="ID de usuario no válido",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Invalid user ID",
                    color=discord.Color.red()
                )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"Error en _handle_user_report: {str(e)}", exc_info=True)
            if language == "es":
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Error al procesar la consulta: {str(e)}",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Error processing the query: {str(e)}",
                    color=discord.Color.red()
                )
            await interaction.followup.send(embed=embed)

    async def _show_user_reports(self, interaction: discord.Interaction, user_id: int, user_reports: list, language="es"):
        try:
            user = await self.bot.fetch_user(user_id)
            user_name = f"{user.name} ({user.mention})"
            user_avatar = user.display_avatar.url
            logger.info(f"Información del usuario obtenida: {user_name}")
        except Exception as e:
            if language == "es":
                user_name = f"Usuario con ID {user_id}"
            else:
                user_name = f"User with ID {user_id}"
            user_avatar = None
            logger.warning(f"No se pudo obtener información del usuario: {str(e)}")

        if language == "es":
            embed = discord.Embed(
                title=f"📋 Reportes de {user_name}",
                description=f"Se han encontrado {len(user_reports)} reportes para este usuario.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title=f"📋 Reports for {user_name}",
                description=f"{len(user_reports)} reports have been found for this user.",
                color=discord.Color.red()
            )

        if user_avatar:
            embed.set_thumbnail(url=user_avatar)

        for i, report in enumerate(user_reports, 1):
            if language == "es":
                embed.add_field(
                    name=f"Reporte #{i}",
                    value=f"**Razón:** {report.get('reason', 'Sin razón')}\n"
                          f"**Fecha:** <t:{int(report['timestamp'])}:R>",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Report #{i}",
                    value=f"**Reason:** {report.get('reason', 'No reason')}\n"
                          f"**Date:** <t:{int(report['timestamp'])}:R>",
                    inline=False
                )

        reports_view = ReportsView(user_reports, user_id, self.bot, interaction, language)
        await interaction.followup.send(embed=embed, view=reports_view)

    async def blacklistuser(self, interaction: discord.Interaction, usuario: str):
        language = await get_server_language(interaction.guild.id)
        
        if not await self.check_permissions(interaction):
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
            
        await self._handle_user_report(interaction, usuario)

async def setup(bot):
    await bot.add_cog(BlacklistUser(bot))