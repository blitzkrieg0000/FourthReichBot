from pathlib import Path
import discord
from discord.ext import commands
from bot.consts import *

class FourthReich(commands.Bot):
    def __init__(self):
        self._cogs = [p.stem for p in Path(".").glob("bot/cogs/*.py")]
        print(f"Bulunan COGS: {self._cogs}")
        intents = discord.Intents.all()
        super().__init__(command_prefix=self.prefix, case_insensitive=True, intents=intents)

    #BOT INITIALIZE
    def setup(self):
        print("Eklentiler yükleniyor...")
        for cog in self._cogs:
            self.load_extension(f"bot.cogs.{cog}")
            print(f" Yüklenen: `{cog}` cog.")
        print("Yükleme tamamlandı!")

    def run(self):
        self.setup()
        #File Token
        # with open("./data/keys/token.0", "r", encoding="utf-8") as f:
        #     TOKEN = f.read()
        print("Bot Çalışıyor...")
        super().run(TOKEN, reconnect=True)

    async def info(self):
        bot_info = await self.application_info()
        return bot_info

    #EVENTS
    async def on_connect(self):
        await self.change_presence(activity=discord.Streaming(name=NAME_TWITCH, url=URL_TWITCH))
        
        #GET BOT ID
        bot_info = await self.info()
        print(f"Bot discorda bağlandı (server ping: {self.latency*1000:,.0f} ms).\nBOT_INFO: {bot_info}")

    async def on_resumed(self):
        print("Bot devam ediyor.")

    async def on_disconnect(self):
        print("Bot bağlantıyı kesti.")

    async def shutdown(self):
        print("Discord bağlantısı kesiliyor...")
        await super().close()

    async def close(self):
        print("Klavyeden kesinti (Ctrl+C) ile kapatılma...")
        await self.shutdown()

    async def on_error(self, err, *args, **kwargs):
        print(f"Bir hata oluştu: {err}")
        raise

    async def on_command_error(self, ctx, exc):
        raise getattr(exc, "original", exc)

    async def on_ready(self):
        print("Bot hazır ve nazır.")

    #COMMAND MANAGEMENT
    async def prefix(self, bot, msg):
        return commands.when_mentioned_or("+")(bot, msg)

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)
        if ctx.command is not None:
            await self.invoke(ctx)

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)