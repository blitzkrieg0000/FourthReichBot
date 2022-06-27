import datetime as dt
import random
import re
import typing as t
import json
import aiohttp
import discord
import wavelink
from bot.modules.openai_chatbot import *
from bot.modules.player import *
from data.conts_data import *
from discord.ext import commands
from wavelink.ext import spotify


URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
LYRICS_URL = "https://some-random-api.ml/lyrics?title="
HZ_BANDS = (20, 40, 63, 100, 150, 250, 400, 450, 630, 1000, 1600, 2500, 4000, 10000, 16000)
TIME_REGEX = r"([0-9]{1,2})[:ms](([0-9]{1,2})s?)?"

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop = self.bot.loop.create_task(self.connect_nodes())
        self.openai_chat = openai_Chatbot()
        self.data = None
        self.get_settings()

    def get_settings(self):
        with open("data/settings.json") as json_data_file:
            self.data = json.load(json_data_file)
            json_data_file.close()

    def set_settings(self):
        with open("data/settings.json", "w") as outfile:
            json.dump(self.data, outfile)
            outfile.close()

    #Build-in
    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Müzik komutları DM lerde geçerli değildir.")
            return False
        return True
    
    #!LISTENERS-------------------------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        bot_info = await self.bot.application_info()
        bot_id = bot_info.id

        if (before.channel is not None) and (after.channel is None) and member.bot: #!Kanaldan Çıkan BOTLAR
            if member.id == bot_id: #Giden BİZİM botsa 
                voice_state = member.guild.voice_client
                if voice_state:
                    await voice_state.disconnect()

        elif (before.channel is not None) and (after.channel is None) and not member.bot: #!Kanaldan Çıkan İnsanoğulları
            pass

        elif (before.channel is None) and (after.channel is not None) and member.bot: #*Kanala Giren BOTLAR
            pass

        elif (before.channel is None) and (after.channel is not None) and not member.bot: #*Kanala Giren İnsanoğulları 
            if (member.id in [318085889408630785, 359083909100863488]) and (self.data["soviet"]["soviet_is_activated"]==1): #SEKO_ID #359083909100863488 - 318085889408630785
                vc = await self.get_player(after.channel)
                #TODO async içinde async olmuyor.
                if not vc.soviet_activ:
                    await vc.soviet()
                
        elif (before.channel is not None) and (after.channel is not None) and member.bot: #?Kanal Değiştiren BOTLAR
            if member.id == bot_id:
                vc = await self.get_player(after.channel)
                await vc.pause()

        elif (before.channel is not None) and (after.channel is not None) and not member.bot: #?Kanal Değiştiren İnsanoğulları
            pass


    #CONNECT LAVALINK
    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot,
                                    host='127.0.0.1',
                                    port=3000,
                                    password='youshallnotpass',
                                    region= "europe",
                                    identifier= "MAIN",
                                    spotify_client=spotify.SpotifyClient(client_id="117f2f7208e34d64b6fdb2de1a2fe66a", client_secret="e7b040095eef4dffb863b5180d85dc6c")
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'Node: <{node.identifier}> Hazır!')
    @commands.Cog.listener()
    
    async def on_wavelink_track_stuck(self, player: Player, track: wavelink.Track, threshold):
        print("on_wavelink_track_stuck")
        if player.queue.repeat_mode == RepeatMode.ONE:
            await player.repeat_track()
        else:
            await player.advance()
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: Player, track: wavelink.Track, reason):
        print("on_wavelink_track_end")
        if player.queue.repeat_mode == RepeatMode.ONE:
            await player.repeat_track()
        else:
            await player.advance()

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, player: Player, track: wavelink.Track, error):
        print("on_wavelink_track_exception")
        if player.queue.repeat_mode == RepeatMode.ONE:
            await player.repeat_track()
        else:
            await player.advance()


    #!HELPER FUNCTIONS------------------------------------------------------------------------------
    async def send_file(self, ctx, filename):
        with open(filename, "rb") as fh:
            f = discord.File(fh, filename=filename)
        await ctx.send(file=f)

    async def get_member_avatar_url(self, ctx, member_id):
        member = ctx.guild.get_member(member_id)
        if member is not None:
            userAvatarUrl = member.avatar_url
        else:
            userAvatarUrl = None
        return userAvatarUrl

    async def get_player(self, obj):
        """Context veya Guild den, varsa playeri döndürür yoksa player üretir ve kanala bağlar."""
        vc = None
        if isinstance(obj, commands.Context):
            #*FROM CONTEXT
            ctx = obj

            if obj.author.voice is not None:
                vc: wavelink.Player = ctx.voice_client

                if vc is None: 
                    channel = ctx.author.voice.channel
                    player = Player(bot=self.bot)
                    vc: Player = await channel.connect(cls=player)
                    
                print("CONTEXT: ", vc, type(vc))
                return vc

        elif isinstance(obj, discord.VoiceChannel):
            #*FROM GUILD
            channel = obj

            node = wavelink.NodePool.get_node(identifier="MAIN")
            vc = node.get_player(channel.guild)

            if vc is None:
                player = Player(bot=self.bot)
                vc: Player = await channel.connect(cls=player)
            
            print("GUILD: ", vc, type(vc))
            return vc


    #!COMMANDS-------------------------------------------------------------------------------------
    @commands.command(name="aycayce", aliases=["aycayçe", "ayçe", "ayce", "acelayce", "açelayçe"])
    async def aycayce(self, ctx):
        await ctx.send("Laptop kamerasından kendisini çekemeyen bir kız! 😈 ")
        userAvatarUrl = await self.get_member_avatar_url(ctx, member_id=659897460751073292) #AYCE_ID

        if userAvatarUrl is not None:
            await ctx.send(userAvatarUrl)
        else:
            await self.send_file(ctx, filename = "data/assets/gifs/eva_green.gif")

    @commands.command(name="vader", aliases=["darthvader", "dervader"])
    async def vader(self, ctx):
        await self.send_file(ctx, filename = "data/assets/images/darth-vader-star-wars.gif")
        await ctx.send(texts['vader'])
    
    @commands.command(name="blitzkrieg", aliases=["blitz"])
    async def blitzkrieg(self, ctx):
        await ctx.send(f"{soviet_images[0]}\n********Arbeit Macht Frei********")

    @commands.command(name="soviet", aliases=["sovyet", "russia", "rusya"])
    async def soviet(self, ctx, bool=None):

        if bool is not None:
            if isinstance(bool, str):
                try:
                    bool = int(bool)
                except:
                    return
                bool = abs(bool)%2
                bool = bool if bool == 0 else 1
                self.data["soviet"]["soviet_is_activated"] = bool
                self.set_settings()
                if bool==0:
                    await ctx.send("Remember, No Russian!")
                else:
                    await ctx.send("""Помните, без английского""")
            return

        restricted = [318085889408630785, 359083909100863488]
        id = ctx.author.id
        if id in restricted:
            
            await ctx.send(texts['soviet_march_lyrics_ru'])
            img_text = random.choice(soviet_images)
            await ctx.send(img_text)

            player = await self.get_player(ctx)
            await player.soviet()
        else:
            await ctx.send("Sadece Gerçek Sovyetler Kullanabilir!")

    @commands.command(name="soru", aliases=["sor", "ask", "soyle", "söyle", "cevapla"])
    async def soru(self, ctx, *, soru:str):
        cevap = self.openai_chat.ask(soru)
        if cevap is not None:
            await ctx.send(cevap)
        else:
            await ctx.send("...")

    @commands.command(name="connect", aliases=["join"])
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        try:
            channel = channel or ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('Uyarı: Bağlanılacak kanal yok. Lütfen bir tane kanal ses kanalına bağlanın.')

        vc = await self.get_player(ctx)
        if not vc:
            player = Player(bot=self.bot)
            vc: Player = await channel.connect(cls=player)
            await ctx.send(f"Bot {channel.name} a bağlandı!")
        return vc

    @connect.error
    async def connect_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            await ctx.send("BOT zaten bir ses kanalına bağlandı.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("Katılacak uygun ses kanalı bulunamadı!")

    @commands.command(name="disconnect", aliases=["leave"])
    async def disconnect(self, ctx):
        player = await self.get_player(ctx)
        await player.disconnect()
        await ctx.send("Bağlantı Kesildi!")

    #PLAY
    @commands.command(name="play", aliases=["oynat", "çal"])
    async def play_command(self, ctx, *, query: t.Optional[str]):
        
        player = await self.get_player(ctx)
        if query is None:
            if player.queue.is_empty:
                await ctx.send("Sıra Boş...")
                raise QueueIsEmpty
            await player.set_pause(False)
            await ctx.send("Parça devam ediyor...")
        else:
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                query = f"{query}"
            #track_list = await wavelink.Node.get_tracks(wavelink.NodePool.get_node(), cls=wavelink.abc.Playable, query=query)
            deneme = 0
            track_list = []
            while True:
                try:
                    track_list = await spotify.SpotifyTrack.search(query=str(query))
                except:
                    track_list = await wavelink.YouTubeTrack.search(query=str(query))

                print(f"tracklist:{track_list}")
                
                if len(track_list)<1:
                    deneme+=1
                    if deneme>10:
                        return
                else: 
                    break
            deneme = 0
            
            await player.add_tracks(ctx, track_list)


    @play_command.error
    async def play(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Oynatma listesi boş")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("Katılacak uygun ses kanalı bulunamadı!")
    
    @commands.command(name="pause")
    async def pause_command(self, ctx):
        player = await self.get_player(ctx)
        if player.is_paused():
            raise PlayerIsAlreadyPaused

        await player.set_pause(True)
        await ctx.send("Oynatma duraklatıldı.")

    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("Zaten duraklatılmış.")

    @commands.command(name="stop", aliases=["durdur"])
    async def stop_command(self, ctx):
        player = await self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.send("Oynatma durduruldu.")

    @commands.command(name="next", aliases=["skip","gec"])
    async def next_command(self, ctx):
        player = await self.get_player(ctx)

        if not player.queue.upcoming:
            raise NoMoreTracks

        await player.stop()
        await ctx.send("Bir sonraki parça oynatılıyor.")

    @next_command.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Listede yeterince şarkı olmadığından işlem gerçekleştirilmedi!")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("Listede parça yok!")

    @commands.command(name="previous", aliases=["önceki", "onceki"])
    async def previous_command(self, ctx):
        player = await self.get_player(ctx)

        if not player.queue.history:
            raise NoPreviousTracks

        player.queue.position -= 2
        await player.stop()
        await ctx.send("Bir önceki parça oynatılıyor...")

    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Listede yeterince şarkı olmadığından işlem gerçekleştirilmedi!")
        elif isinstance(exc, NoPreviousTracks):
            await ctx.send("Önceki sırada başka oynatılacak medya yok!")

    @commands.command(name="shuffle", aliases=["karistir"])
    async def shuffle_command(self, ctx):
        player = await self.get_player(ctx)
        player.queue.shuffle()
        await ctx.send("Liste Karıştırıldı.")

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Liste karıştırılamadı çünkü liste boş.")

    @commands.command(name="repeat", aliases=["tekrarla"])
    async def repeat_command(self, ctx, mode: str):
        if mode not in ("none", "1", "all"):
            raise InvalidRepeatMode

        player = await self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        await ctx.send(f"Tekrar modu ayarlandı: {mode}.")

    @commands.command(name="queue", aliases=["sira", "sıra", "liste"])
    async def queue_command(self, ctx, show: t.Optional[int] = 10):
        player = await self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        embed = discord.Embed(
            title="Liste",
            description=f"Sonraki şarkılar: {show}",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Arama Sonuçları")
        embed.set_footer(text=f"Kullanıcı {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.add_field(
            name="Şuan Oynatılan",
            value=getattr(player.queue.current_track, "title", "Şuan oynatılan bir içerik yok!"),
            inline=False
        )
        if upcoming := player.queue.upcoming:
            embed.add_field(
                name="Sonraki",
                value="\n".join(t.title for t in upcoming[:show]),
                inline=False
            )

        msg = await ctx.send(embed=embed)

    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Liste boş!")

    # Requests -----------------------------------------------------------------
    @commands.group(name="volume", aliases=["ses"], invoke_without_command=True)
    async def volume_group(self, ctx, volume: int):
        player = await self.get_player(ctx)

        if volume < 0:
            raise VolumeTooLow

        if volume > 120:
            raise VolumeTooHigh

        await player.set_volume(volume)
        await ctx.send(f"Ses seviyesi: {volume:,}%")

    @volume_group.error
    async def volume_group_error(self, ctx, exc):
        if isinstance(exc, VolumeTooLow):
            await ctx.send("Ses seviyesi 0% ya da daha yüksek olmalıdır.")
        elif isinstance(exc, VolumeTooHigh):
            await ctx.send("Ses seviyesi 120% ya da daha düşük olmalıdır.")

    @volume_group.command(name="up", aliases=["arttır"])
    async def volume_up_command(self, ctx):
        player = await self.get_player(ctx)

        if player.volume == 120:
            raise MaxVolume

        await player.set_volume(value := min(player.volume + 10, 120))
        await ctx.send(f"Ses seviyesi: {value:,}%")

    @volume_up_command.error
    async def volume_up_command_error(self, ctx, exc):
        if isinstance(exc, MaxVolume):
            await ctx.send("Ses En Yüksek Seviyede: 120")

    @volume_group.command(name="down", aliases=["azalt"])
    async def volume_down_command(self, ctx):
        player = await self.get_player(ctx)

        if player.volume == 0:
            raise MinVolume

        await player.set_volume(value := max(0, player.volume - 10))
        await ctx.send(f"Ses seviyesi: {value:,}%")

    @volume_down_command.error
    async def volume_down_command_error(self, ctx, exc):
        if isinstance(exc, MinVolume):
            await ctx.send("Ses En Düşük Seviyede: 0")

    @commands.command(name="lyrics", aliases=["sözler", "sozler", "soz"])
    async def lyrics_command(self, ctx, name: t.Optional[str]):
        player = await self.get_player(ctx)
        name = name or player.queue.current_track.title

        async with ctx.typing():
            async with aiohttp.request("GET", LYRICS_URL + name, headers={}) as r:
                if not 200 <= r.status <= 299:
                    raise NoLyricsFound

                data = await r.json()

                if len(data["lyrics"]) > 2000:
                    return await ctx.send(f"<{data['links']['genius']}>")

                embed = discord.Embed(
                    title=data["title"],
                    description=data["lyrics"],
                    colour=ctx.author.colour,
                    timestamp=dt.datetime.utcnow(),
                )
                embed.set_thumbnail(url=data["thumbnail"]["genius"])
                embed.set_author(name=data["author"])
                await ctx.send(embed=embed)

    @lyrics_command.error
    async def lyrics_command_error(self, ctx, exc):
        if isinstance(exc, NoLyricsFound):
            await ctx.send("Şarkı Sözü Bulunamadı.")

    @commands.command(name="eq", aliases=["ekolayzer", "equalizer"])
    async def eq_command(self, ctx, preset: str):
        player = await self.get_player(ctx)

        eq = getattr(wavelink.eqs.Equalizer, preset, None)
        if not eq:
            raise InvalidEQPreset

        await player.set_eq(eq())
        await ctx.send(f"Ekolayzer ayarlanıyor...: {preset}.")

    @eq_command.error
    async def eq_command_error(self, ctx, exc):
        if isinstance(exc, InvalidEQPreset):
            await ctx.send("Ekolayzer ayarları şunlar olabilir: 'flat', 'boost', 'metal', 'piano'.")

    @commands.command(name="adveq", aliases=["aeq"])
    async def adveq_command(self, ctx, band: int, gain: float):
        player = await self.get_player(ctx)

        if not 1 <= band <= 15 and band not in HZ_BANDS:
            raise NonExistentEQBand

        if band > 15:
            band = HZ_BANDS.index(band) + 1

        if abs(gain) > 10:
            raise EQGainOutOfBounds

        player.eq_levels[band - 1] = gain / 10
        eq = wavelink.eqs.Equalizer(levels=[(i, gain) for i, gain in enumerate(player.eq_levels)])
        await player.set_eq(eq)
        await ctx.send("Ekolayzer ayarlandı.")

    @adveq_command.error
    async def adveq_command_error(self, ctx, exc):
        if isinstance(exc, NonExistentEQBand):
            await ctx.send(
                "Bant numarası 1 ile 15 arasında veya aşağıdakilerden biri olmalıdır "
                "Frekanslar: " + ", ".join(str(b) for b in HZ_BANDS)
            )
        elif isinstance(exc, EQGainOutOfBounds):
            await ctx.send("Herhangi bir bant için EQ kazancı 10 dB ile -10 dB arasında olmalıdır.")

    @commands.command(name="playing", aliases=["info", "bilgi"])
    async def playing_command(self, ctx):
        player = await self.get_player(ctx)

        if not player.is_playing:
            raise PlayerIsAlreadyPaused

        embed = discord.Embed(
            title="Şuan Oynatılan:",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow(),
        )
        embed.set_author(name="Parça Bilgisi")
        embed.set_footer(text=f"Kullanıcı: {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.add_field(name="Parça başlığı", value=player.queue.current_track.title, inline=False)
        embed.add_field(name="Sanatçı", value=player.queue.current_track.author, inline=False)

        position = divmod(player.position, 60000)
        length = divmod(player.queue.current_track.length, 60000)
        embed.add_field(
            name="Position",
            value=f"{int(position[0])}:{round(position[1]/1000):02}/{int(length[0])}:{round(length[1]/1000):02}",
            inline=False
        )

        await ctx.send(embed=embed)

    @playing_command.error
    async def playing_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("Şuan oynatılan bir parça yok!")

    @commands.command(name="skipto", aliases=["playindex", "to", "sec", "degistir"])
    async def skipto_command(self, ctx, index: int):
        player = await self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not 0 <= index <= player.queue.length:
            raise NoMoreTracks

        player.queue.position = index - 2
        await player.stop()
        await ctx.send(f"Süre {index}.")

    @skipto_command.error
    async def skipto_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Listede şarkı yok!")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("Liste dışı bir numara!")

    @commands.command(name="restart", aliases=["yenidenbaslat", "tekrarbaslat", "tekrar"])
    async def restart_command(self, ctx):
        player = await self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        await player.seek(0)
        await ctx.send("Parça yeniden başlatıldı.")

    @restart_command.error
    async def restart_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Listede parça yok")

    @commands.command(name="seek",aliases=["sure", "süre", "süreyegit","gez"])
    async def seek_command(self, ctx, position: str):
        player = await self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not (match := re.match(TIME_REGEX, position)):
            raise InvalidTimeString

        if match.group(3):
            secs = (int(match.group(1)) * 60) + (int(match.group(3)))
        else:
            secs = int(match.group(1))

        await player.seek(secs * 1000)
        await ctx.send("...")

def setup(bot):
    bot.add_cog(Music(bot))

