import discord
from discord.ext import commands
from .mongo_utils import get_server_data, get_specific_field, get_server_language
from .mongo import mongo_report_storage

class CheckUsers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            if member.bot:
                return
                
            user_id = member.id
            
            user_reports = await mongo_report_storage.get_user_reports(user_id)
            
            if not user_reports:
                return
            
            server_id = member.guild.id
            security_config = await get_specific_field(server_id, "security")
            
            if not security_config:
                return
            
            channel_id = security_config.get("channel", 0)
            alert_message = security_config.get("message", "")
            
            if channel_id == 0 or not alert_message:
                return
            
            channel = member.guild.get_channel(channel_id)
            
            if not channel:
                return
            
            formatted_message = alert_message.replace("{user}", member.mention) \
                                           .replace("{usertag}", member.name) \
                                           .replace("{userid}", str(member.id))

            language = await get_server_language(server_id)
            
            if language == "es":
                embed = discord.Embed(
                    title="⚠️ Usuario malicioso detectado",
                    description=f"{member.mention} `{member.name}` (ID: {member.id})",
                    color=discord.Color.red()
                )

                embed.add_field(
                    name="Cantidad de reportes",
                    value=f"Este usuario tiene {len(user_reports)} reportes en la base de datos.",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Malicious user detected",
                    description=f"{member.mention} `{member.name}` (ID: {member.id})",
                    color=discord.Color.red()
                )

                embed.add_field(
                    name="Report count",
                    value=f"This user has {len(user_reports)} reports in the database.",
                    inline=False
                )

            report_info = ""
            for i, report in enumerate(user_reports[:3], 1):
                reason = report.get("reason", "Sin razón" if language == "es" else "No reason")
                timestamp = int(report.get("timestamp", 0))
                if language == "es":
                    report_info += f"**Reporte #{i}:** {reason}\n**Fecha:** <t:{timestamp}:R>\n\n"
                else:
                    report_info += f"**Report #{i}:** {reason}\n**Date:** <t:{timestamp}:R>\n\n"
            
            if len(user_reports) > 3:
                if language == "es":
                    report_info += f"*Y {len(user_reports) - 3} reportes más...*"
                else:
                    report_info += f"*And {len(user_reports) - 3} more reports...*"
                
            if report_info:
                if language == "es":
                    embed.add_field(
                        name="Detalles de reportes",
                        value=report_info,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="Report details",
                        value=report_info,
                        inline=False
                    )

            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
             
            if language == "es":
                embed.set_footer(text="Se recomienda verificar este usuario antes de permitirle acceso completo al servidor.")
            else:
                embed.set_footer(text="It's recommended to verify this user before granting full server access.")

            await channel.send(embed=embed)

            try:
                await channel.send(formatted_message)
            except Exception as e:
                print(f"Error al enviar mensaje formateado: {str(e)}")
            
        except Exception as e:
            print(f"Error en on_member_join: {str(e)}")

async def setup(bot):
    await bot.add_cog(CheckUsers(bot))