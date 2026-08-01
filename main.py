import asyncio
import discord
from discord.ext import commands
import yt_dlp

# ==========================================
# ⚙️ إعدادات البوتات الثلاثة (تم تصحيحها)
# ==========================================
BOTS_CONFIG = [
    {
        "token": "MTEyODE2NDc1MDIwMzgxODAwNQ.GszbaJ.HvaxX84bb0CmBlwOZujuX3Q_QqFG6HEWit4h1E",
        "channel_id": 1491932399951417375
    },
    {
        "token": "MTEyODE3MzkwMTcyMjE1NzA5Ng.G8TmQx.onxcMkEE8RLtaBJWlGW5LqMN6sNVYuup7KPZ0g",
        "channel_id": 1491932491857264803
    },
    {
        "token": "MTEyODE3NjQyNjA1MTQzNjY2Ng.Gax3Cr.AwbUZ_HiLamAllxQFgpQ2QS84ODGpYUmL-MoCo",
        "channel_id": 1239993652902887428
    },
]

# ==========================================
# 🛠️ إعدادات المحرك وصوتيات يوتيوب
# ==========================================
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class Music247Bot(commands.Bot):
    def __init__(self, target_channel_id):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        
        super().__init__(command_prefix="!", intents=intents)
        self.target_channel_id = target_channel_id

    async def setup_hook(self):
        self.loop.create_task(self.maintain_voice_connection())

    async def on_ready(self):
        print(f"✅ تم تشغيل البوت: {self.user.name} (ID: {self.user.id})")

    async def maintain_voice_connection(self):
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                channel = self.get_channel(self.target_channel_id)
                if channel and isinstance(channel, discord.VoiceChannel):
                    guild = channel.guild
                    voice_client = guild.voice_client

                    if not voice_client or not voice_client.is_connected():
                        print(f"🔄 البوت ({self.user.name}) يدخل الروم الصوتي...")
                        await channel.connect(reconnect=True, timeout=30.0)

            except Exception as e:
                print(f"⚠️ تنبيه اتصال في البوت ({self.user.name}): {e}")

            await asyncio.sleep(3)

    async def on_voice_state_update(self, member, before, after):
        if member.id == self.user.id:
            if before.channel is not None and after.channel is None:
                print(f"⚡ تم فصل البوت ({self.user.name})! جاري إعادة الاتصال...")
                await asyncio.sleep(1)
                self.loop.create_task(self.maintain_voice_connection())

# ==========================================
# 🎵 أوامر التشغيل والتحكم
# ==========================================

@commands.command(name="play", aliases=["p"])
async def play(ctx, *, search: str):
    voice_client = ctx.guild.voice_client

    if not voice_client or not voice_client.is_connected():
        return await ctx.send("❌ البوت ليس متصلاً بروم صوتي حالياً!")

    if voice_client.is_playing():
        voice_client.stop()

    async with ctx.typing():
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))

            if 'entries' in data:
                data = data['entries'][0]

            url = data['url']
            title = data.get('title', 'مقطع صوتي')
            
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            voice_client.play(source)

            await ctx.send(f"🎶 **جاري تشغيل:** `{title}`")

        except Exception as e:
            await ctx.send(f"❌ حدث خطأ أثناء محاولة التشغيل: {e}")

@commands.command(name="stop")
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("⏹️ تم إيقاف التشغيل.")
    else:
        await ctx.send("❌ لا يوجد شيء يتم تشغيله حالياً.")

# ==========================================
# 🚀 تشغيل البوتات الثلاثة معاً
# ==========================================
async def main():
    tasks = []

    for config in BOTS_CONFIG:
        bot = Music247Bot(config["channel_id"])
        bot.add_command(play)
        bot.add_command(stop)
        tasks.append(bot.start(config["token"]))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ تم إيقاف جميع البوتات.")