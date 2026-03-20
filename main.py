import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import os

# --- 設定 ---
# メンバー管理やメッセージ取得が必要なため、Intentsを適切に設定
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# タイムゾーンとログ用チャンネル
JST = timezone(timedelta(hours=+9), 'JST')
LOG_CHANNEL_ID = 1459786701143670794  

# --- ボタンのクラス（永続化対応） ---
class MyView(discord.ui.View):
    def __init__(self):
        # timeout=None にすることで、ボットが再起動してもボタンが死なないようにします
        super().__init__(timeout=None) 

    async def send_log(self, interaction: discord.Interaction, status_text: str, color: discord.Color):
        """共通のログ送信処理"""
        now_str = datetime.now(JST).strftime('%Y/%m/%d %H:%M')
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        if log_channel:
            embed = discord.Embed(
                title=f"{now_str} {status_text}", 
                description=f"**{interaction.user.display_name}** さんが{status_text}しました。",
                color=color,
                timestamp=datetime.now(JST)
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            await log_channel.send(embed=embed)
        else:
            print(f"Error: Channel ID {LOG_CHANNEL_ID} not found.")

    @discord.ui.button(label="入室", style=discord.ButtonStyle.green, custom_id="persistent_entry_btn")
    async def entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 3秒ルール回避のため、最初に応答を保留
        await interaction.response.defer(ephemeral=True)
        await self.send_log(interaction, "入室", discord.Color.green())
        await interaction.followup.send("入室を記録しました。がんばってください！", ephemeral=True)

    @discord.ui.button(label="退室", style=discord.ButtonStyle.red, custom_id="persistent_exit_btn")
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.send_log(interaction, "退室", discord.Color.red())
        await interaction.followup.send("退室を記録しました。お疲れ様でした！", ephemeral=True)

# --- ボット起動時の処理 ---
@bot.event
async def on_ready():
    # 起動時にViewを登録することで、古いメッセージのボタンも反応し続ける
    bot.add_view(MyView())
    print(f'ログインしました: {bot.user.name}')

# --- ボタン設置コマンド ---
@bot.command()
@commands.has_permissions(administrator=True) # 管理者のみ実行可能にする（推奨）
async def setup(ctx):
    """ボタン付きメッセージを送信するコマンド"""
    await ctx.send("【入退室管理】ボタンを押して記録してください", view=MyView())

# --- 実行 ---
if __name__ == "__main__":
    # GCPでは環境変数からトークンを読み込む
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
