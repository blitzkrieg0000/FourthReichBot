import asyncio
import datetime as dt
import random
from enum import Enum

import discord
import wavelink
from wavelink.ext import spotify
from discord.ext import commands
from data.conts_data import *

OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}

class AlreadyConnectedToChannel(commands.CommandError):
    pass
class NoVoiceChannel(commands.CommandError):
    pass
class QueueIsEmpty(commands.CommandError):
    pass
class NoTracksFound(commands.CommandError):
    pass
class PlayerIsAlreadyPaused(commands.CommandError):
    pass
class NoMoreTracks(commands.CommandError):
    pass
class NoPreviousTracks(commands.CommandError):
    pass
class InvalidRepeatMode(commands.CommandError):
    pass
class VolumeTooLow(commands.CommandError):
    pass
class VolumeTooHigh(commands.CommandError):
    pass
class MaxVolume(commands.CommandError):
    pass
class MinVolume(commands.CommandError):
    pass
class NoLyricsFound(commands.CommandError):
    pass
class InvalidEQPreset(commands.CommandError):
    pass
class NonExistentEQBand(commands.CommandError):
    pass
class EQGainOutOfBounds(commands.CommandError):
    pass
class InvalidTimeString(commands.CommandError):
    pass

class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2

class Queue():
    def __init__(self):
        self._queue = []
        self.temp_queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE
	

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty
        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty
        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    @property
    def position_info(self):
        return self.position

    @position_info.setter
    def position_info(self, value):
        self.position = value

    @property
    def queue_value(self):
        return self._queue

    @queue_value.setter
    def queue_value(self, value):
        self._queue.pop(value)
        self._queue = self._queue
        
    def add(self, *args):
        self._queue.extend(args)

    def add_track_to_position(self, track):
        self._queue.insert(self.position_info, track)
        self.position_info = self.position - 1

    def pop_a_track(self):
        self.queue_value = self.position_info
        self.position_info = self.position - 1

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty
        self.position += 1

        if self.position < 0:
            return None

        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None
        return self._queue[self.position]

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "1":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "all":
            self.repeat_mode = RepeatMode.ALL

    def empty(self):
        self._queue.clear()
        self.position = 0

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        self.bot = kwargs['bot']
        kwargs.pop('bot')
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.seek_pos = 0
        self.soviet_activated = False

    @property
    def track_position(self):
        return self.seek_pos

    @track_position.setter
    def track_position(self, value):
        self.seek_pos = value

    @property
    def soviet_activ(self):
        return self.soviet_activated

    @soviet_activ.setter
    def soviet_activ(self, value):
        self.soviet_activated = value

    async def soviet(self):
        self.soviet_activ = True
        index = random.choice(ranges)
        track_query = soviet_marchs[index]
        
        track=None
        try:
            track = await wavelink.YouTubeTrack.search(query='rzAxoQkOKOY', return_first=True) #wOVMvmNugM4
        except Exception as e:
            print(e)

        if track is None:
            raise NoTracksFound

        if self.is_playing():
            self.track_position = self.position
            self.queue.add_track_to_position(track)
            await self.stop()

            await asyncio.sleep(11)

            await self.stop()
            await self.set_volume(100)
            self.queue.pop_a_track()
            await self.seek(int(self.track_position))
        else:
            #self.queue.add_track_to_position(track)
            self.queue.add(track)
            await self.start_playback()

            await asyncio.sleep(11)

            await self.stop()
            await self.set_volume(100)
            await self.disconnect()
        self.soviet_activ = False

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound

        if isinstance(tracks, wavelink.tracks.YouTubePlaylist) or isinstance(tracks, spotify.SpotifySearchType):
            self.queue.add(*tracks.tracks)
        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            await ctx.send(f"{tracks[0].title} sıraya eklendi.")
        else:
            track = await self.choose_track(ctx, tracks)
            if track is not None:
                self.queue.add(track)
                await ctx.send(f"{track.title} sıraya eklendi.")

        if not self.is_playing() and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == msg.id
            )

        embed = discord.Embed(
            title="Parça seçiniz:",
            description=(
                "\n".join(
                    f"**{i+1}.** {t.title} ({t.length//60000}:{str(t.length%60).zfill(2)})"
                    for i, t in enumerate(tracks[:5])
                )
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Arama Sonuçları")
        embed.set_footer(text=f"Ekleyen: {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def advance(self):
        try:
            track = self.queue.get_next_track()
            if track is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)

