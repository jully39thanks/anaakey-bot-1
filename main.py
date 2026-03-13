import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# --- 設定 ---
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

JST = timezone(timedelta(hours=+9), 'JST')
LOG_CHANNEL_ID = 1481594264533209088

# --- 常駐用Viewクラス ---
class MyView(discord.ui.View):
    def __init__(self):
        # timeout=None にすることで、Viewが内部的に終了しなくなります
        super().__init__(timeout=None) 

    async def send_log(self, interaction, status_text, color):
        now = datetime.now(JST).strftime('%Y/%m/%d %H:%M')
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        
        if log_channel:
            embed = discord.Embed(
                title=f"{now} {status_text}", 
                description=f"**{interaction.user.display_name}** さんが{status_text}しました。",
                color=color,
                timestamp=datetime.now(JST)
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await log_channel.send(embed=embed)

    # custom_id を必ず指定するのが常駐化の最大のポイントです
    @discord.ui.button(label="入室", style=discord.ButtonStyle.green, custom_id="persistent_entry_btn")
    async def entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_log(interaction, "入室", discord.Color.green())
        await interaction.response.send_message("入室を記録しました。がんばってください！", ephemeral=True)

    @discord.ui.button(label="退室", style=discord.ButtonStyle.red, custom_id="persistent_exit_btn")
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_log(interaction, "退室", discord.Color.red())
        await interaction.response.send_message("退室を記録しました。お疲れ様でした！", ephemeral=True)

# --- イベント処理 ---
@bot.event
async def on_ready():
    # 起動時に「このView（ボタンのセット）を常に監視してね」とボットに教え込みます
    bot.add_view(MyView())
    print(f'ログインしました: {bot.user.name}')

# --- ボタン設置コマンド ---
@bot.command()
async def setup(ctx):
    """チャンネルにボタンを1回だけ設置するコマンド"""
    await ctx.send("【入退室管理】ボタンを押して記録してください", view=MyView())

token = os.getenv('DISCORD_TOKEN')
bot.run(token)