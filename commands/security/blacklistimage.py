import discord
from discord import app_commands
from discord.ext import commands
import time

from .mongo import mongo_report_storage
from .image_uploader import upload_image_to_imgbb
from .blacklistmodify import VALIDATION_CODES

class BlacklistImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cargado correctamente")
    
    async def image(
        self, 
        interaction: discord.Interaction, 
        codigo: str,
        imagen1: discord.Attachment,
        imagen2: discord.Attachment = None,
        imagen3: discord.Attachment = None,
        imagen4: discord.Attachment = None,
        imagen5: discord.Attachment = None,
        imagen6: discord.Attachment = None,
        imagen7: discord.Attachment = None,
        imagen8: discord.Attachment = None
    ):
        allowed_ids = [702934069138161835, 327157607724875776]
        if interaction.user.id not in allowed_ids:
            await interaction.response.send_message("No tienes permisos para usar este comando.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        if codigo not in VALIDATION_CODES:
            await interaction.followup.send("❌ El código proporcionado no es válido o ha expirado.", ephemeral=True)
            return
        
        validation_data = VALIDATION_CODES[codigo]
        current_time = time.time()
        
        if current_time - validation_data['timestamp'] > 300:
            del VALIDATION_CODES[codigo]
            await interaction.followup.send("❌ El código ha expirado. Por favor, solicita un nuevo código.", ephemeral=True)
            return

        report_id = validation_data.get('report_id')
        user_id = validation_data.get('user_id')

        attachments = [imagen1, imagen2, imagen3, imagen4, imagen5, imagen6, imagen7, imagen8]
        valid_attachments = [attachment for attachment in attachments if attachment is not None]
        
        if not valid_attachments:
            await interaction.followup.send("❌ No se proporcionaron imágenes válidas.", ephemeral=True)
            return

        for attachment in valid_attachments:
            if not attachment.content_type or not attachment.content_type.startswith('image/'):
                await interaction.followup.send(f"❌ El archivo '{attachment.filename}' no es una imagen válida.", ephemeral=True)
                return
        
        uploaded_urls = []
        for attachment in valid_attachments:
            try:
                image_bytes = await attachment.read()
                image_url = await upload_image_to_imgbb(image_bytes)
                if image_url:
                    uploaded_urls.append(image_url)
                else:
                    await interaction.followup.send(f"❌ Error al subir la imagen '{attachment.filename}' a ImgBB.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Error al procesar la imagen '{attachment.filename}': {e}", ephemeral=True)
                return
        
        if not uploaded_urls:
            await interaction.followup.send("❌ No se pudo subir ninguna imagen.", ephemeral=True)
            return

        success_count = 0
        for url in uploaded_urls:
            added = await mongo_report_storage.add_image_to_report(user_id, url, report_id)
            if added:
                success_count += 1
        
        original_interaction = validation_data.get('interaction')
        del VALIDATION_CODES[codigo]
        
        embed = discord.Embed(
            title="✅ Imágenes Añadidas",
            description=f"Se han añadido correctamente {success_count} de {len(uploaded_urls)} imágenes al reporte.",
            color=discord.Color.green()
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
        if original_interaction:
            try:
                user_reports = await mongo_report_storage.get_user_reports(user_id)
                report = None
                
                for r in user_reports:
                    if str(r.get('_id')) == str(report_id):
                        report = r
                        break
                
                if report:
                    from .blacklistmodify import ImageManagementView
                    
                    embed = discord.Embed(
                        title="🖼️ Gestión de Imágenes",
                        description="Las imágenes han sido añadidas correctamente. Selecciona una acción para gestionar las imágenes:",
                        color=discord.Color.blue()
                    )
                    
                    num_imagenes = len(report.get('imagen_urls', []))
                    embed.add_field(
                        name="Información",
                        value=f"**Imágenes actuales:** {num_imagenes}",
                        inline=False
                    )
                    
                    view = ImageManagementView(report, user_id, self.bot.get_cog("BlacklistModify"), user_reports, 0)
                    await original_interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                print(f"Error al actualizar el mensaje original: {e}")

async def setup(bot):
    await bot.add_cog(BlacklistImage(bot))