import discord
from discord.ext import commands, tasks
import os
import glob
import asyncio
import webserver
import sys
import datetime
from commands.security.mongo_utils import update_server_data
from commands.security.mongo import mongo_report_storage

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='%', intents=intents)

bot.remove_command('help')
server_invites = {}

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.offline
    )
    print(f"Estamos dentro! {bot.user}")
    
    await load_extensions(["commands"])

    try:
        await bot.tree.sync()
        print("Slash commands sincronizados correctamente")
    except Exception as e:
        print(f"Error sincronizando slash commands: {e}")

async def get_server_invite(guild):
    if guild.id in server_invites:
        try:
            invite = await bot.fetch_invite(server_invites[guild.id])
            if invite:
                return invite
        except:
            pass
    
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).create_instant_invite:
            try:
                invites = await channel.invites()
                for invite in invites:
                    if invite.inviter == bot.user and invite.max_age == 0:
                        server_invites[guild.id] = invite.url
                        return invite
            except:
                continue
            
            try:
                invite = await channel.create_invite(max_age=0, max_uses=0, unique=False, reason="MC Blacklist Bot - Servidor nuevo")
                server_invites[guild.id] = invite.url
                return invite
            except:
                continue
    
    return None

@bot.event
async def on_guild_join(guild):
    try:   
        blocked_servers = await mongo_report_storage.get_blocked_servers()
        
        if guild.id in blocked_servers:
            await guild.leave()
            return
            
        server_id = guild.id
        await update_server_data(server_id, "language", "es")
        
        log_channel_id = 1359542831122743417
        
        log_channel = bot.get_channel(log_channel_id)
        
        if log_channel:
            try:
                creation_timestamp = int(guild.created_at.timestamp())
                
                admin_users = []
                
                for member in guild.members:
                    if member.guild_permissions.administrator:
                        admin_users.append(f"  - `{member.name}` (ID: {member.id})")
                
                
                embed = discord.Embed(
                    title="Nuevo Servidor",
                    description=(
                        f"El bot ha sido añadido al servidor `{guild.name}` (ID: {guild.id}). \n"
                        f"- El servidor fue creado el <t:{creation_timestamp}:D>\n"
                        f"- Tiene `{guild.member_count}` usuarios\n"
                        f"- El owner es `{guild.owner.name if guild.owner else 'Desconocido'}` "
                        f"(ID: {guild.owner.id if guild.owner else 'Desconocido'})\n"
                        f"- Los usuarios con permisos de **Administrador** son:\n"
                        f"{chr(10).join(admin_users) if admin_users else '  - Ninguno'}"
                    ),
                    color=0xFEF6,
                )
                
                embed.set_image(url="https://i.imgur.com/VMbCHbF.png")
                
                if guild.icon:
                    embed.set_thumbnail(url=guild.icon.url)
                
                view = None
                invite = await get_server_invite(guild)
                
                if invite:
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label="Unirse al Servidor",
                        url=invite.url
                    ))
                    
                    embed.add_field(
                        name="Invitación",
                        value=f"[Click aquí para unirse al servidor]({invite.url})",
                        inline=False
                    )
                
                await log_channel.send(embed=embed, view=view)
            except Exception as e:
                print(f"Error al crear o enviar el embed: {str(e)}")
        else:
            print(f"No se pudo encontrar el canal de logs con ID {log_channel_id}")
    except Exception as e:
        print(f"Error general en on_guild_join: {str(e)}")
        import traceback
        traceback.print_exc()

@bot.event
async def on_guild_remove(guild):
    try:
        blocked_servers = await mongo_report_storage.get_blocked_servers()
        
        if guild.id in blocked_servers:
            return
        
        log_channel_id = 1359542831122743417
        log_channel = bot.get_channel(log_channel_id)
        
        if log_channel:
            embed = discord.Embed(
                title="Servidor Abandonado",
                description=f"El bot ha salido del servidor `{guild.name}` - ID: {guild.id}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
                
            await log_channel.send(embed=embed)
        else:
            print(f"No se pudo encontrar el canal de logs con ID {log_channel_id}")
    except Exception as e:
        print(f"Error en on_guild_remove: {str(e)}")
        import traceback
        traceback.print_exc()

async def load_extensions(directories):
    total_extensions = 0
    main_extensions = 0
    subdir_extensions = 0
    
    for directory in directories:
        main_files = [f for f in glob.glob(f"{directory}/*.py") 
                     if "__pycache__" not in f]
        
        subdir_files = [f for f in glob.glob(f"{directory}/**/*.py", recursive=True) 
                       if "__pycache__" not in f]
        
        subdir_files = [f for f in subdir_files if f not in main_files]
        
        all_files = main_files + subdir_files
        
        for file in all_files:
            if file.endswith(".py"):
                extension = file[:-3].replace("\\", ".").replace("/", ".")
                
                try:
                    await bot.load_extension(extension)
                    print(f"Extensión cargada: {extension}")
                    total_extensions += 1
                    if file in main_files:
                        main_extensions += 1
                    else:
                        subdir_extensions += 1
                except Exception as e:
                    print(f"Error cargando {extension}: {e}")
    
    print(f"\nTotal de extensiones cargadas: {total_extensions}")
    print(f"Extensiones en directorios principales: {main_extensions}")
    print(f"Extensiones en subdirectorios: {subdir_extensions}")

async def main():
    try:
        print("Iniciando proceso principal...")
        print(f"Python version: {sys.version}")
        print(f"Discord.py version: {discord.__version__}")

        print("Iniciando bot de Discord...")
        try:
            await bot.start(DISCORD_TOKEN)
        except discord.LoginFailure as e:
            print(f"Error de login: {e}")
        except Exception as e:
            print(f"Error inesperado: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"Error en main: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("Iniciando servidor web...")
    web_thread = webserver.keep_alive()
    print("Servidor web iniciado en segundo plano")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Cerrando por interrupción del usuario...")
    except Exception as e:
        print(f"Error crítico: {type(e).__name__}: {e}")
    finally:
        loop.close()