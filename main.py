import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import os
from flask import Flask
from threading import Thread

# --- Renderの強制終了(Timed Out)を防ぐための偽装サーバー ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Renderがチェックしに来るポート(10000)で応答を返します
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Discordボットの設定 ---
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

JST = timezone(timedelta(hours=+9), 'JST')
LOG_CHANNEL_ID = 1459786701143670794  # ログ用チャンネルID

# --- ボタンのクラス（ボットが再起動しても有効） ---
class MyView(discord.ui.View):
    def __init__(self):
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

    @discord.ui.button(label="入室", style=discord.ButtonStyle.green, custom_id="persistent_entry_btn")
    async def entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_log(interaction, "入室", discord.Color.green())
        await interaction.response.send_message("入室を記録しました。がんばってください！", ephemeral=True)

    @discord.ui.button(label="退室", style=discord.ButtonStyle.red, custom_id="persistent_exit_btn")
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_log(interaction, "退室", discord.Color.red())
        await interaction.response.send_message("退室を記録しました。お疲れ様でした！", ephemeral=True)

# --- ボット起動時の処理 ---
@bot.event
async def on_ready():
    # ボット起動時に古いボタンを再認識させる
    bot.add_view(MyView())
    print(f'ログインしました: {bot.user.name}')

# --- ボタン設置コマンド ---
@bot.command()
async def setup(ctx):
    await ctx.send("【入退室管理】ボタンを押して記録してください", view=MyView())

# --- 実行 ---
if __name__ == "__main__":
    keep_alive()  # 偽装サーバーを起動
    token = os.getenv('DISCORD_TOKEN')
    bot.run(token)
