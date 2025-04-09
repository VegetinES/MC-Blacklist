import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from .mongo_utils import get_specific_field, get_server_language

from .mongo import mongo_report_storage

class BlacklistList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users_per_page = 30
        self.special_channel_id = 1359190774792716399
    
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
    
    async def execute_list_command(self, interaction: discord.Interaction):
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

        await interaction.response.defer()
        language = await get_server_language(interaction.guild.id)

        temp_message = None
        if interaction.channel_id == self.special_channel_id:
            if language == "es":
                temp_message = await interaction.followup.send("⏳ Obteniendo datos de la blacklist, esto puede tomar un momento...", wait=True)
            else:
                temp_message = await interaction.followup.send("⏳ Getting blacklist data, this may take a moment...", wait=True)
        
        try:
            all_reports = await mongo_report_storage.get_all_reports()

            if not all_reports:
                if language == "es":
                    embed = discord.Embed(
                        title="🔍 Lista de Usuarios en Blacklist",
                        description="No hay usuarios en la blacklist.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="🔍 Blacklisted Users List",
                        description="There are no users in the blacklist.",
                        color=discord.Color.green()
                    )
                if temp_message:
                    await temp_message.edit(content="", embed=embed, view=None)
                else:
                    await interaction.followup.send(embed=embed)
                return
        
            blacklisted_users = {}
            for report in all_reports:
                user_id = report.get('reported_user_id')
                if user_id is not None:
                    if user_id not in blacklisted_users:
                        blacklisted_users[user_id] = {}
                    
            
            if interaction.channel_id == self.special_channel_id:
                await self.send_full_list(interaction, blacklisted_users, temp_message, language)
            else:
                await self.send_server_list(interaction, blacklisted_users, language)
                
        except Exception as e:
            if language == "es":
                error_msg = f"❌ Ocurrió un error al procesar la blacklist: {str(e)}"
            else:
                error_msg = f"❌ An error occurred while processing the blacklist: {str(e)}"
            if temp_message:
                await temp_message.edit(content=error_msg, embed=None, view=None)
            else:
                await interaction.followup.send(error_msg)
            print(f"Error en execute_list_command: {e}")
    
    async def send_full_list(self, interaction: discord.Interaction, blacklisted_users, temp_message=None, language="es"):
        user_entries = []

        for i, (user_id, data) in enumerate(blacklisted_users.items()):
            if i < 150:
                try:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        user_name = user.name
                        user_entry = f"<@{user_id}> (`{user_name}`) ID: {user_id}"
                    else:
                        user_entry = f"ID: {user_id}"
                except:
                    user_entry = f"ID: {user_id}"
            else:
                user_entry = f"ID: {user_id}"
            
            user_entries.append(user_entry)
        
        pages = [user_entries[i:i+self.users_per_page] for i in range(0, len(user_entries), self.users_per_page)]
        if not pages:
            pages = [[]]
        
        current_page = 0

        view = PaginationView(pages, current_page, language)

        if language == "es":
            embed = discord.Embed(
                title="🚫 Lista Completa de Usuarios en Blacklist",
                description="\n".join(pages[current_page]) if pages[current_page] else "No hay usuarios en la blacklist.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Página {current_page+1}/{len(pages)} | Total: {len(user_entries)} usuarios")
        else:
            embed = discord.Embed(
                title="🚫 Complete List of Blacklisted Users",
                description="\n".join(pages[current_page]) if pages[current_page] else "There are no users in the blacklist.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Page {current_page+1}/{len(pages)} | Total: {len(user_entries)} users")
        
        if temp_message:
            await temp_message.edit(content="", embed=embed, view=view)
        else:
            await interaction.followup.send(embed=embed, view=view)
    
    async def send_server_list(self, interaction: discord.Interaction, blacklisted_users, language="es"):
        server_members = interaction.guild.members
        server_member_ids = [member.id for member in server_members]
        
        matching_users = []
        for user_id in blacklisted_users:
            try:
                if int(user_id) in server_member_ids:
                    member = interaction.guild.get_member(int(user_id))
                    if member:
                        matching_users.append(member)
            except (ValueError, TypeError):
                continue

        if language == "es":
            embed = discord.Embed(
                title="🔍 Análisis de Blacklist en el Servidor",
                color=discord.Color.red() if matching_users else discord.Color.green()
            )
            
            if matching_users:
                description = "**¡Atención! Se han encontrado los siguientes usuarios de la blacklist en este servidor:**\n\n"
                for member in matching_users:
                    description += f"{member.mention} (`{member.name}`) ID: {member.id}\n"
                
                embed.description = description
                embed.set_footer(text=f"Total: {len(matching_users)} usuarios de la blacklist encontrados en este servidor")
            else:
                embed.description = "✅ No se ha encontrado ningún usuario de la blacklist en este servidor."
                embed.color = discord.Color.green()
        else:
            embed = discord.Embed(
                title="🔍 Blacklist Analysis in the Server",
                color=discord.Color.red() if matching_users else discord.Color.green()
            )
            
            if matching_users:
                description = "**Warning! The following blacklisted users have been found in this server:**\n\n"
                for member in matching_users:
                    description += f"{member.mention} (`{member.name}`) ID: {member.id}\n"
                
                embed.description = description
                embed.set_footer(text=f"Total: {len(matching_users)} blacklisted users found in this server")
            else:
                embed.description = "✅ No blacklisted users have been found in this server."
                embed.color = discord.Color.green()
        
        await interaction.followup.send(embed=embed)

class PaginationView(discord.ui.View):
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
                    title="🚫 Lista Completa de Usuarios en Blacklist",
                    description="\n".join(self.pages[self.current_page]),
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Página {self.current_page+1}/{self.total_pages} | Total: {sum(len(p) for p in self.pages)} usuarios")
            else:
                embed = discord.Embed(
                    title="🚫 Complete List of Blacklisted Users",
                    description="\n".join(self.pages[self.current_page]),
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Page {self.current_page+1}/{self.total_pages} | Total: {sum(len(p) for p in self.pages)} users")
            
            self.update_buttons()
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Siguiente ▶️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            
            if self.language == "es":
                embed = discord.Embed(
                    title="🚫 Lista Completa de Usuarios en Blacklist",
                    description="\n".join(self.pages[self.current_page]),
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Página {self.current_page+1}/{self.total_pages} | Total: {sum(len(p) for p in self.pages)} usuarios")
            else:
                embed = discord.Embed(
                    title="🚫 Complete List of Blacklisted Users",
                    description="\n".join(self.pages[self.current_page]),
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Page {self.current_page+1}/{self.total_pages} | Total: {sum(len(p) for p in self.pages)} users")
            
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

async def setup(bot):
    await bot.add_cog(BlacklistList(bot))