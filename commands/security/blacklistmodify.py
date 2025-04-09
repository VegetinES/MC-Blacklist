import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import random
import string
import time

from .mongo import mongo_report_storage
from .image_uploader import upload_image_to_imgbb

VALIDATION_CODES = {} 

class BlacklistModify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cargado correctamente")
        
        self.bot.loop.create_task(self.cleanup_expired_codes())
    
    async def cleanup_expired_codes(self):
        while True:
            try:
                current_time = time.time()
                expired_codes = []
                
                for code, data in VALIDATION_CODES.items():
                    if current_time - data['timestamp'] > 300:
                        expired_codes.append(code)
                
                for code in expired_codes:
                    del VALIDATION_CODES[code]
                    
                await asyncio.sleep(60)
            except Exception as e:
                print(f"Error en cleanup_expired_codes: {e}")
                await asyncio.sleep(60)
    
    async def modify_user(self, interaction: discord.Interaction, usuario: str):
        await interaction.response.defer(ephemeral=False)

        try:
            user_id = int(usuario)

            user_reports = await mongo_report_storage.get_user_reports(user_id)

            if not user_reports:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"No hay reportes registrados para el usuario con ID {user_id}.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return

            try:
                user = await self.bot.fetch_user(user_id)
                user_name = f"{user.name} ({user.mention})"
                user_avatar = user.display_avatar.url
            except:
                user_name = f"Usuario con ID {user_id}"
                user_avatar = None

            embed = discord.Embed(
                title="🛠️ Modificar Blacklist",
                description=f"Selecciona un reporte de {user_name} para modificar:",
                color=discord.Color.blue()
            )
            
            if user_avatar:
                embed.set_thumbnail(url=user_avatar)

            for i, report in enumerate(user_reports, 1):
                num_imagenes = len(report.get('imagen_urls', []))
                
                embed.add_field(
                    name=f"Reporte #{i}",
                    value=(
                        f"**Imágenes:** {num_imagenes}\n"
                        f"**Fecha:** <t:{int(report['timestamp'])}:R>"
                    ),
                    inline=True
                )

            view = ReportSelectorView(user_reports, user_id, self)
            await interaction.followup.send(embed=embed, view=view)
            
        except ValueError:
            await interaction.followup.send("Por favor, proporciona un ID de usuario válido.", ephemeral=True)
        except Exception as e:
            print(f"Error en comando blacklist modificar: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"Ocurrió un error al procesar la consulta: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
    
    async def check_admin_permissions(self, interaction):
        allowed_ids = [702934069138161835, 327157607724875776]
        return interaction.user.id in allowed_ids

class ReportSelectorView(discord.ui.View):
    def __init__(self, reports, user_id, parent_cog):
        super().__init__()
        self.reports = reports
        self.user_id = user_id
        self.parent_cog = parent_cog
        
        options = []
        for i, report in enumerate(reports, 1):
            options.append(
                discord.SelectOption(
                    label=f"Reporte #{i}",
                    value=str(i-1),
                    description=f"Fecha: {datetime.datetime.fromtimestamp(report['timestamp']).strftime('%d/%m/%Y')}"
                )
            )

        options = options[:25]
        
        self.report_select = discord.ui.Select(
            placeholder="Selecciona un reporte para modificar",
            options=options,
            row=0
        )
        self.report_select.callback = self.report_selected
        self.add_item(self.report_select)
        
        delete_user_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Eliminar Usuario de Blacklist",
            row=1
        )
        delete_user_button.callback = self.delete_user
        self.add_item(delete_user_button)
    
    async def report_selected(self, interaction: discord.Interaction):
        report_index = int(self.report_select.values[0])
        report = self.reports[report_index]
        
        embed = discord.Embed(
            title=f"Reporte",
            description=f"Selecciona qué acción realizar con este reporte:",
            color=discord.Color.blue()
        )

        num_imagenes = len(report.get('imagen_urls', []))
        
        embed.add_field(
            name="Información",
            value=(
                f"**Razón:** {report['reason']}\n"
                f"**Imágenes:** {num_imagenes}\n"
                f"**Fecha:** <t:{int(report['timestamp'])}:R>"
            ),
            inline=False
        )

        view = ReportModifyView(report, self.user_id, self.parent_cog, self.reports, report_index)
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def delete_user(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚠️ Confirmar Eliminación",
            description=f"¿Estás seguro de que deseas eliminar TODOS los reportes del usuario con ID {self.user_id}? Esta acción no se puede deshacer.",
            color=discord.Color.red()
        )
        
        view = ConfirmDeleteUserView(self.user_id, self.parent_cog)
        await interaction.response.edit_message(embed=embed, view=view)

class ConfirmDeleteUserView(discord.ui.View):
    def __init__(self, user_id, parent_cog):
        super().__init__()
        self.user_id = user_id
        self.parent_cog = parent_cog
    
    @discord.ui.button(label="Confirmar Eliminación", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        deleted = await mongo_report_storage.delete_user_reports(self.user_id)
        
        if deleted:
            embed = discord.Embed(
                title="✅ Usuario Eliminado",
                description=f"Todos los reportes del usuario con ID {self.user_id} han sido eliminados de la base de datos.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No se pudieron eliminar los reportes del usuario con ID {self.user_id}.",
                color=discord.Color.red()
            )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_reports = await mongo_report_storage.get_user_reports(self.user_id)
        view = ReportSelectorView(user_reports, self.user_id, self.parent_cog)
        
        embed = discord.Embed(
            title="🛠️ Modificar Blacklist",
            description=f"Operación cancelada. Selecciona un reporte para modificar:",
            color=discord.Color.blue()
        )

        for i, report in enumerate(user_reports, 1):
            num_imagenes = len(report.get('imagen_urls', []))
            
            embed.add_field(
                name=f"Reporte #{i}",
                value=(
                    f"**Imágenes:** {num_imagenes}\n"
                    f"**Fecha:** <t:{int(report['timestamp'])}:R>"
                ),
                inline=True
            )
        
        await interaction.response.edit_message(embed=embed, view=view)

class ReportModifyView(discord.ui.View):
    def __init__(self, report, user_id, parent_cog, reports, report_index):
        super().__init__()
        self.report = report
        self.user_id = user_id
        self.parent_cog = parent_cog
        self.reports = reports
        self.report_index = report_index
        
        reason_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Modificar Razón",
            row=0
        )
        reason_button.callback = self.modify_reason
        self.add_item(reason_button)
        
        images_button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Gestionar Imágenes",
            row=0
        )
        images_button.callback = self.manage_images
        self.add_item(images_button)
        
        delete_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Eliminar Reporte",
            row=1
        )
        delete_button.callback = self.delete_report
        self.add_item(delete_button)

        back_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Volver",
            row=2
        )
        back_button.callback = self.go_back
        self.add_item(back_button)
    
    async def modify_reason(self, interaction: discord.Interaction):
        modal = ReasonModal(self.report)
        await interaction.response.send_modal(modal)
    
    async def manage_images(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🖼️ Gestión de Imágenes",
            description="Selecciona una acción para gestionar las imágenes:",
            color=discord.Color.blue()
        )
        
        num_imagenes = len(self.report.get('imagen_urls', []))
        embed.add_field(
            name="Información",
            value=f"**Imágenes actuales:** {num_imagenes}",
            inline=False
        )
        
        view = ImageManagementView(self.report, self.user_id, self.parent_cog, self.reports, self.report_index)
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def delete_report(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚠️ Confirmar Eliminación",
            description=f"¿Estás seguro de que deseas eliminar este reporte? Esta acción no se puede deshacer.",
            color=discord.Color.red()
        )
        
        view = ConfirmDeleteReportView(self.report, self.user_id, self.parent_cog, self.reports, self.report_index)
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def go_back(self, interaction: discord.Interaction):
        view = ReportSelectorView(self.reports, self.user_id, self.parent_cog)
        
        embed = discord.Embed(
            title="🛠️ Modificar Blacklist",
            description=f"Selecciona un reporte para modificar:",
            color=discord.Color.blue()
        )

        try:
            user = await self.parent_cog.bot.fetch_user(self.user_id)
            user_name = f"{user.name} ({user.mention})"
            embed.description = f"Selecciona un reporte de {user_name} para modificar:"
            embed.set_thumbnail(url=user.display_avatar.url)
        except:
            pass
        
        for i, report in enumerate(self.reports, 1):
            num_imagenes = len(report.get('imagen_urls', []))
            
            embed.add_field(
                name=f"Reporte #{i}",
                value=(
                    f"**Imágenes:** {num_imagenes}\n"
                    f"**Fecha:** <t:{int(report['timestamp'])}:R>"
                ),
                inline=True
            )
        
        await interaction.response.edit_message(embed=embed, view=view)

class ConfirmDeleteReportView(discord.ui.View):
    def __init__(self, report, user_id, parent_cog, reports, report_index):
        super().__init__()
        self.report = report
        self.user_id = user_id
        self.parent_cog = parent_cog
        self.reports = reports
        self.report_index = report_index
    
    @discord.ui.button(label="Confirmar Eliminación", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        deleted = False
        if '_id' in self.report:
            deleted = await mongo_report_storage.delete_report(self.report['_id'])
        
        if deleted:
            updated_reports = await mongo_report_storage.get_user_reports(self.user_id)
            
            if not updated_reports:
                embed = discord.Embed(
                    title="✅ Reporte Eliminado",
                    description="El reporte ha sido eliminado. No hay más reportes para este usuario.",
                    color=discord.Color.green()
                )
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                view = ReportSelectorView(updated_reports, self.user_id, self.parent_cog)
                
                embed = discord.Embed(
                    title="✅ Reporte Eliminado",
                    description="El reporte ha sido eliminado. Selecciona otro reporte para modificar:",
                    color=discord.Color.green()
                )

                for i, report in enumerate(updated_reports, 1):
                    num_imagenes = len(report.get('imagen_urls', []))
                    
                    embed.add_field(
                        name=f"Reporte #{i}",
                        value=(
                            f"**Imágenes:** {num_imagenes}\n"
                            f"**Fecha:** <t:{int(report['timestamp'])}:R>"
                        ),
                        inline=True
                    )
                
                await interaction.response.edit_message(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo eliminar el reporte.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=f"Reporte",
            description=f"Selecciona qué acción realizar con este reporte:",
            color=discord.Color.blue()
        )

        num_imagenes = len(self.report.get('imagen_urls', []))
        
        embed.add_field(
            name="Información",
            value=(
                f"**Razón:** {self.report['reason']}\n"
                f"**Imágenes:** {num_imagenes}\n"
                f"**Fecha:** <t:{int(self.report['timestamp'])}:R>"
            ),
            inline=False
        )
        
        view = ReportModifyView(self.report, self.user_id, self.parent_cog, self.reports, self.report_index)
        await interaction.response.edit_message(embed=embed, view=view)

class ReasonModal(discord.ui.Modal, title="Modificar Razón del Reporte"):
    def __init__(self, report):
        super().__init__()
        self.report = report
        
        self.reason = discord.ui.TextInput(
            label="Nueva razón del reporte",
            style=discord.TextStyle.paragraph,
            placeholder="Escribe la nueva razón del reporte...",
            default=report['reason'],
            required=True,
            max_length=1000
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        old_reason = self.report['reason']
        new_reason = self.reason.value
        
        updated = await mongo_report_storage.update_report_reason(
            self.report['reported_user_id'],
            new_reason,
            self.report.get('_id', None)
        )
        
        if updated:
            self.report['reason'] = new_reason
            
            embed = discord.Embed(
                title="✅ Razón Actualizada",
                description=f"La razón del reporte ha sido actualizada.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Razón Anterior",
                value=old_reason,
                inline=False
            )
            
            embed.add_field(
                name="Nueva Razón",
                value=new_reason,
                inline=False
            )

            view = ReportModifyView(
                self.report, 
                self.report['reported_user_id'], 
                interaction.client.get_cog("BlacklistModify"),
                [], 
                0
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("No se pudo actualizar la razón del reporte.", ephemeral=True)

class ImageManagementView(discord.ui.View):
    def __init__(self, report, user_id, parent_cog, reports, report_index):
        super().__init__()
        self.report = report
        self.user_id = user_id
        self.parent_cog = parent_cog
        self.reports = reports
        self.report_index = report_index

        add_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Añadir Imágenes",
            row=0
        )
        add_button.callback = self.add_image
        self.add_item(add_button)

        num_imagenes = len(self.report.get('imagen_urls', []))
        if num_imagenes > 0:
            view_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="Ver y Eliminar Imágenes",
                row=0
            )
            view_button.callback = self.view_images
            self.add_item(view_button)

        back_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Volver",
            row=1
        )
        back_button.callback = self.go_back
        self.add_item(back_button)
    
    async def add_image(self, interaction: discord.Interaction):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        VALIDATION_CODES[code] = {
            'report_id': self.report.get('_id'),
            'user_id': self.user_id,
            'timestamp': time.time(),
            'interaction': interaction
        }
        
        embed = discord.Embed(
            title="🖼️ Añadir Imágenes",
            description=f"Para añadir imágenes a este reporte, usa el siguiente comando:\n\n"
                       f"```\n/blacklist image codigo:{code} imagen1:[adjunta imagen] (opcional: imagen2-imagen8)\n```\n\n"
                       f"Este código es válido durante 5 minutos.",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed)
    
    async def view_images(self, interaction: discord.Interaction):
        imagen_urls = self.report.get('imagen_urls', [])
        
        if not imagen_urls:
            await interaction.response.send_message("No hay imágenes para mostrar.", ephemeral=True)
            return

        embeds = []
        for i, image_url in enumerate(imagen_urls):
            embed = discord.Embed(
                title=f"Imagen {i+1} de {len(imagen_urls)}",
                color=discord.Color.blue()
            )
            embed.set_image(url=image_url)
            embeds.append(embed)

        view = ImageBrowserView(embeds, self.report, self.user_id, self.parent_cog, self.reports, self.report_index)
        await interaction.response.edit_message(embed=embeds[0], view=view)
    
    async def go_back(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Reporte",
            description=f"Selecciona qué acción realizar con este reporte:",
            color=discord.Color.blue()
        )

        num_imagenes = len(self.report.get('imagen_urls', []))
        
        embed.add_field(
            name="Información",
            value=(
                f"**Razón:** {self.report['reason']}\n"
                f"**Imágenes:** {num_imagenes}\n"
                f"**Fecha:** <t:{int(self.report['timestamp'])}:R>"
            ),
            inline=False
        )
        
        view = ReportModifyView(self.report, self.user_id, self.parent_cog, self.reports, self.report_index)
        await interaction.response.edit_message(embed=embed, view=view)

class ImageBrowserView(discord.ui.View):
    def __init__(self, embeds, report, user_id, parent_cog, reports, report_index):
        super().__init__()
        self.embeds = embeds
        self.report = report
        self.user_id = user_id
        self.parent_cog = parent_cog
        self.reports = reports
        self.report_index = report_index
        self.current_index = 0

        if len(embeds) > 1:
            self.prev_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="◀️ Anterior",
                disabled=True,
                row=0
            )
            self.prev_button.callback = self.prev_image
            self.add_item(self.prev_button)

            self.page_indicator = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label=f"1/{len(embeds)}",
                disabled=True,
                row=0
            )
            self.add_item(self.page_indicator)

            self.next_button = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Siguiente ▶️",
                disabled=len(embeds) <= 1,
                row=0
            )
            self.next_button.callback = self.next_image
            self.add_item(self.next_button)

        delete_button = discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Eliminar Imagen",
            row=1
        )
        delete_button.callback = self.delete_image
        self.add_item(delete_button)

        back_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Volver",
            row=1
        )
        back_button.callback = self.go_back
        self.add_item(back_button)
    
    async def prev_image(self, interaction: discord.Interaction):
        if self.current_index > 0:
            self.current_index -= 1
            await self.update_message(interaction)
    
    async def next_image(self, interaction: discord.Interaction):
        if self.current_index < len(self.embeds) - 1:
            self.current_index += 1
            await self.update_message(interaction)
    
    async def update_message(self, interaction: discord.Interaction):
        if hasattr(self, 'prev_button'):
            self.prev_button.disabled = self.current_index == 0
        if hasattr(self, 'next_button'):
            self.next_button.disabled = self.current_index >= len(self.embeds) - 1
        if hasattr(self, 'page_indicator'):
            self.page_indicator.label = f"{self.current_index + 1}/{len(self.embeds)}"

        await interaction.response.edit_message(embed=self.embeds[self.current_index], view=self)
    
    async def delete_image(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚠️ Confirmar Eliminación",
            description="¿Estás seguro de que deseas eliminar esta imagen? Esta acción no se puede deshacer.",
            color=discord.Color.red()
        )

        embed.set_image(url=self.report['imagen_urls'][self.current_index])
        
        view = ConfirmDeleteImageView(
            self.report, 
            self.user_id, 
            self.parent_cog, 
            self.reports, 
            self.report_index,
            self.current_index
        )
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def go_back(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🖼️ Gestión de Imágenes",
            description="Selecciona una acción para gestionar las imágenes:",
            color=discord.Color.blue()
        )
        
        num_imagenes = len(self.report.get('imagen_urls', []))
        embed.add_field(
            name="Información",
            value=f"**Imágenes actuales:** {num_imagenes}",
            inline=False
        )
        
        view = ImageManagementView(self.report, self.user_id, self.parent_cog, self.reports, self.report_index)
        await interaction.response.edit_message(embed=embed, view=view)

class ConfirmDeleteImageView(discord.ui.View):
    def __init__(self, report, user_id, parent_cog, reports, report_index, image_index):
        super().__init__()
        self.report = report
        self.user_id = user_id
        self.parent_cog = parent_cog
        self.reports = reports
        self.report_index = report_index
        self.image_index = image_index
    
    @discord.ui.button(label="Confirmar Eliminación", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        image_url = self.report['imagen_urls'][self.image_index]
        
        deleted = await mongo_report_storage.remove_image_from_report(
            self.report['reported_user_id'],
            self.image_index,
            self.report.get('_id', None)
        )
        
        if deleted:
            updated_reports = await mongo_report_storage.get_user_reports(self.user_id)
            updated_report = None
            
            for r in updated_reports:
                if str(r.get('_id')) == str(self.report.get('_id')):
                    updated_report = r
                    break
            
            if not updated_report:
                updated_report = self.report.copy()
                updated_report['imagen_urls'] = [url for i, url in enumerate(updated_report.get('imagen_urls', [])) if i != self.image_index]
            
            num_imagenes = len(updated_report.get('imagen_urls', []))
            
            if num_imagenes > 0:
                embeds = []
                for i, img_url in enumerate(updated_report['imagen_urls']):
                    embed = discord.Embed(
                        title=f"Imagen {i+1} de {num_imagenes}",
                        color=discord.Color.blue()
                    )
                    embed.set_image(url=img_url)
                    embeds.append(embed)

                new_index = min(self.image_index, num_imagenes - 1)
                
                view = ImageBrowserView(embeds, updated_report, self.user_id, self.parent_cog, updated_reports, self.report_index)
                view.current_index = new_index
                
                embed_to_show = embeds[new_index]
                await interaction.response.edit_message(embed=embed_to_show, view=view)
            else:
                embed = discord.Embed(
                    title="✅ Imagen Eliminada",
                    description="La imagen ha sido eliminada. No hay más imágenes que mostrar.",
                    color=discord.Color.green()
                )
                view = ImageManagementView(updated_report, self.user_id, self.parent_cog, updated_reports, self.report_index)
                await interaction.response.edit_message(embed=embed, view=view)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se pudo eliminar la imagen.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        embeds = []
        for i, image_url in enumerate(self.report['imagen_urls']):
            embed = discord.Embed(
                title=f"Imagen {i+1} de {len(self.report['imagen_urls'])}",
                color=discord.Color.blue()
            )
            embed.set_image(url=image_url)
            embeds.append(embed)
        
        view = ImageBrowserView(embeds, self.report, self.user_id, self.parent_cog, self.reports, self.report_index)
        view.current_index = self.image_index
        await interaction.response.edit_message(embed=embeds[self.image_index], view=view)

async def setup(bot):
    await bot.add_cog(BlacklistModify(bot))