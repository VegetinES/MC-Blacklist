import discord
from discord import app_commands
from discord.ext import commands
from .mongo_utils import get_specific_field, get_server_language

class ServerListView(discord.ui.View):
    def __init__(self, pages, current_page=0, language="es"):
        super().__init__(timeout=300)
        self.pages = pages
        self.current_page = current_page
        self.total_pages = len(pages)
        self.language = language
        
        self.update_buttons()
    
    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page >= self.total_pages - 1
    
    @discord.ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            
            if self.language == "es":
                embed = discord.Embed(
                    title="📋 Lista de Servidores",
                    description=self.pages[self.current_page],
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Página {self.current_page+1}/{self.total_pages}")
            else:
                embed = discord.Embed(
                    title="📋 Server List",
                    description=self.pages[self.current_page],
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Page {self.current_page+1}/{self.total_pages}")
            
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Siguiente ▶️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            
            if self.language == "es":
                embed = discord.Embed(
                    title="📋 Lista de Servidores",
                    description=self.pages[self.current_page],
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Página {self.current_page+1}/{self.total_pages}")
            else:
                embed = discord.Embed(
                    title="📋 Server List",
                    description=self.pages[self.current_page],
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Page {self.current_page+1}/{self.total_pages}")
            
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        try:
            message = self.message
            if message:
                await message.edit(view=self)
        except:
            pass

class BlacklistInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.server_invites = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cargado correctamente")
    
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
    
    async def get_server_invite(self, guild):
        if guild.id in self.server_invites:
            try:
                invite = await self.bot.fetch_invite(self.server_invites[guild.id])
                if invite:
                    return invite
            except:
                pass
        
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).create_instant_invite:
                try:
                    invites = await channel.invites()
                    for invite in invites:
                        if invite.inviter == self.bot.user and invite.max_age == 0:
                            self.server_invites[guild.id] = invite.url
                            return invite
                except:
                    continue
                
                try:
                    invite = await channel.create_invite(max_age=0, max_uses=0, unique=False, reason="MC Blacklist Bot - Estadísticas")
                    self.server_invites[guild.id] = invite.url
                    return invite
                except:
                    continue
        
        return None
    
    async def info(self, interaction: discord.Interaction):
        if not await self.check_permissions(interaction):
            language = await get_server_language(interaction.guild.id)
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
        
        language = await get_server_language(interaction.guild.id)
        
        if language == "es":
            embed = discord.Embed(
                title="Información MC Blacklist",
                description="Este bot ha sido creado en Python, para avisar a servidores de Minecraft de usuarios maliciosos.",
                color=0x515F01
            )
            
            embed.add_field(
                name="Creadores",
                value="Mercu `mercurianoooo`\nVegetin `vegetines`",
                inline=True
            )
            
            embed.add_field(
                name="Enlaces de interés",
                value="[Repositorio público](https://github.com/VegetinES/MC-Blacklist)\n[Servidor de Soporte](https://discord.gg/RG4JM59bet)",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="MC Blacklist Information",
                description="This bot has been created in Python, to alert Minecraft servers about malicious users.",
                color=0x515F01
            )
            
            embed.add_field(
                name="Creators",
                value="Mercu `mercurianoooo`\nVegetin `vegetines`",
                inline=True
            )
            
            embed.add_field(
                name="Links of interest",
                value="[Public Repository](https://github.com/VegetinES/MC-Blacklist)\n[Support Server](https://discord.gg/RG4JM59bet)",
                inline=True
            )
        
        allowed_ids = [702934069138161835, 327157607724875776]
        if interaction.user.id in allowed_ids:
            await interaction.response.defer()
            
            total_servers = len(self.bot.guilds)
            total_users = sum(guild.member_count for guild in self.bot.guilds)
            
            if language == "es":
                embed.add_field(
                    name="Estadísticas del Bot",
                    value=f"**Servidores:** {total_servers}\n**Usuarios totales:** {total_users}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Bot Statistics",
                    value=f"**Servers:** {total_servers}\n**Total users:** {total_users}",
                    inline=False
                )
            
            server_info = []
            servers_per_page = 10
            
            for guild in self.bot.guilds:
                try:
                    invite = await self.get_server_invite(guild)
                    invite_link = f"[Link invitación]({invite.url})" if invite else "No disponible"
                    server_info.append(f"`{guild.name}` - ID: {guild.id} | Usuarios: `{guild.member_count}` - {invite_link}")
                except Exception as e:
                    print(f"Error al procesar servidor {guild.id}: {e}")
                    server_info.append(f"`{guild.name}` - ID: {guild.id} | Usuarios: `{guild.member_count}` - Error al generar invitación")
            
            server_pages = []
            for i in range(0, len(server_info), servers_per_page):
                server_pages.append("\n".join(server_info[i:i+servers_per_page]))
            
            if server_pages:
                view = ServerListView(server_pages, 0, language)
                
                if language == "es":
                    server_embed = discord.Embed(
                        title="📋 Lista de Servidores",
                        description=server_pages[0],
                        color=discord.Color.green()
                    )
                    server_embed.set_footer(text=f"Página 1/{len(server_pages)}")
                else:
                    server_embed = discord.Embed(
                        title="📋 Server List",
                        description=server_pages[0],
                        color=discord.Color.green()
                    )
                    server_embed.set_footer(text=f"Page 1/{len(server_pages)}")
                
                await interaction.followup.send(embed=embed)
                await interaction.followup.send(embed=server_embed, view=view)
            else:
                embed.set_image(url="https://i.imgur.com/VVoXfQO.png")
                await interaction.followup.send(embed=embed)
        else:
            embed.set_image(url="https://i.imgur.com/VVoXfQO.png")
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(BlacklistInfo(bot))