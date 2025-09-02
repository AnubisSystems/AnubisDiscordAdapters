# pip install discord.py

import base64
from typing import Callable, List
import discord
from discord import Message, Interaction, File
from discord.ext import commands
from discord.ui import View, Select, Button
from anubis_core.ports.bots import IConversationPort, IBotFlowPort

# Vistas para opciones
class OpcionesBotonesView(discord.ui.View):
    def __init__(self, opciones: list[str], on_response: Callable[[str], None]):
        super().__init__(timeout=None)
        for opcion in opciones:
            self.add_item(self.OpcionButton(opcion, on_response))

    class OpcionButton(discord.ui.Button):
        def __init__(self, label: str, on_response: Callable[[str], None]):
            super().__init__(label=label, style=discord.ButtonStyle.primary)
            self.on_response = on_response

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"✅ Seleccionaste: {self.label}", ephemeral=True)
            await self.on_response(self.label)


class OpcionesSelectView(discord.ui.View):
    def __init__(self, opciones: list[str], on_response: Callable[[str], None]):
        super().__init__(timeout=None)
        self.add_item(self.OpcionSelect(opciones, on_response))

    class OpcionSelect(discord.ui.Select):
        def __init__(self, opciones: list[str], on_response: Callable[[str], None]):
            options = [discord.SelectOption(label=op) for op in opciones]
            super().__init__(placeholder="Selecciona una opción...", options=options)
            self.on_response = on_response

        async def callback(self, interaction: discord.Interaction):
            seleccion = self.values[0]
            await interaction.response.send_message(f"✅ Seleccionaste: {seleccion}", ephemeral=True)
            await self.on_response(seleccion)


# Conversación
class DiscordConversation:
    def __init__(self, message: discord.Message, bot, modo_opciones: str = "botones"):
        self.message = message
        self.bot = bot
        self.modo_opciones = modo_opciones
        

    async def preguntar_texto(self, prompt: str, on_response: Callable[[str], None]):
        await self._send(prompt)
        self.bot.pending_callbacks[self.message.author.id] = on_response

    async def preguntar_opciones(self, prompt: str, opciones: list[str], on_response: Callable[[str], None]):
        if self.modo_opciones == "botones":
            view = OpcionesBotonesView(opciones, on_response)
        else:
            view = OpcionesSelectView(opciones, on_response)
        await self.message.channel.send(content=prompt, view=view)

    async def preguntar_imagen(self, prompt: str, on_response: Callable[[bytes], None]):
        await self._send(prompt)
        self.bot.pending_callbacks[self.message.author.id] = on_response
        self.bot.esperando_imagen.add(self.message.author.id)

    async def mostrar_texto(self, texto: str):
        await self._send(texto)

    async def mostrar_resumen(self, titulo: str, datos: dict):
        embed = discord.Embed(title=titulo, color=discord.Color.green())
        for k, v in datos.items():
            embed.add_field(name=k, value=str(v), inline=False)
        await self.message.channel.send(embed=embed)

    async def mostrar_error(self, mensaje: str):
        await self._send(f"⚠️ {mensaje}")

    async def obtener_imagen(self, image_bytes: bytes) -> str:
        import base64
        return base64.b64encode(image_bytes).decode("utf-8")

    async def _send(self, texto: str):
        await self.message.channel.send(texto)


class DiscordBotCommand:
    def __init__(self, discord_token: str, flow: IBotFlowPort, modo_opciones: str = "botones"):
        self.token = discord_token
        self.flow = flow
        self.bot = commands.Bot(command_prefix="/", intents=discord.Intents.all(),help_command=None)
        
        # 👇 Aquí guardamos los callbacks pendientes por usuario
        self.pending_callbacks: dict[int, Callable] = {}
        self.esperando_imagen: set[int] = set()

        # Configuración de modo para opciones (botones o select)
        self.modo_opciones = modo_opciones

        # --- Bind commands ---
        @self.bot.command(name="start")
        async def start(ctx: commands.Context):
            conv = DiscordConversation(message=ctx.message, bot=self)
            user_data = {}
            await self.flow.start(conv, user_data)

        @self.bot.command(name="help")
        async def help_cmd(ctx: commands.Context):
            conv = DiscordConversation(message=ctx.message)
            user_data = {}
            await self.flow.help(conv, user_data)

        @self.bot.command(name="cancel")
        async def cancel(ctx: commands.Context):
            await ctx.send("❌ Operación cancelada.")

        # --- Eventos ---
        @self.bot.event
        async def on_ready():
            print(f"✅ Bot conectado como {self.bot.user}")
            await self.bot.change_presence(
                activity=discord.Game(name="cuidando pollitos 🐣"),
                status=discord.Status.online
            )
            # Si quieres que avise en un canal concreto:
            # channel_id = 123456789012345678
            # channel = self.bot.get_channel(channel_id)
            # if channel:
            #     await channel.send("✅ El bot está online y listo para ayudarte 🐣")

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return

            user_id = message.author.id

            # 1️⃣ Imagen primero
            if user_id in self.esperando_imagen:
                if message.attachments:
                    self.esperando_imagen.remove(user_id)
                    cb = self.pending_callbacks.pop(user_id, None)
                    if cb:
                        file = message.attachments[0]
                        img_bytes = await file.read()
                        await cb(img_bytes)   # ✅ le mandamos bytes
                    return
                else:
                    await message.channel.send("⚠️ Por favor, envíame una imagen 📷")
                    return

            # 2️⃣ Texto después
            if user_id in self.pending_callbacks:
                cb = self.pending_callbacks.pop(user_id)
                await cb(message.content)   # ✅ aquí sí es str
                return

            await self.bot.process_commands(message)
        self.run()
    def run(self):
        self.bot.run(self.token)
