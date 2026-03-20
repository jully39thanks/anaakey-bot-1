import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import os
from flask import Flask
from threading import Thread

# --- Render生存確認用 (cron-jobからのアクセスを受ける窓口) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- 設定（最強の権限設定） ---
# .default() ではなく .all() にすることで、ログインできない問題を回避します
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
JST = timezone(timedelta(hours=+9), 'JST')

# 【重要】ログを流したいチャンネルのIDを入れてください
LOG_CHANNEL_ID = 1481594264533209088 

class MyView(discord.ui.View):
    def __init__(self):
        # ボットが再起動してもボタンが動くように timeout=None
        super().__init__(timeout=None)

    async def handle_click(self, interaction: discord.Interaction, status_text, color):
        # 1. 【3秒ルール回避】まずDiscordに「考えてるよ」と即レス（defer）させる
        await interaction.response.defer(ephemeral=True)
        
        now = datetime.now(JST).strftime('%Y/%m/%d %H:%M')
        try:
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            
            # ログチャンネルが見つかった場合
            if log_channel:
                embed = discord.Embed(
                    title=f"{now} {status_text}", 
                    description=f"**{interaction.user.display_name}** さんが{status_text}しました。",
                    color=color,
                    timestamp=datetime.now(JST)
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await log_channel.send(embed=embed)
                
                # 送信完了後に「記録しました」に書き換える
                await interaction.followup.send(f"{status_text}を記録しました！", ephemeral=True)
            else:
                # チャンネルが見つからない場合のエラー表示
                await interaction.followup.send(f"⚠️エラー：ログ用チャンネル(ID:{LOG_CHANNEL_ID})が見つかりません。", ephemeral=True)
                
        except Exception as e:
            print(f"Error occurred: {e}")
            await interaction.followup.send(f"❌エラーが発生しました。ログを確認してください。", ephemeral=True)

    # ボタンのデザインとID設定（v5として新しく設定）
    @discord.ui.button(label="入室", style=discord.ButtonStyle.green, custom_id="entry_v5")
    async def entry(self, interaction, button):
        await self.handle_click(interaction, "入室", discord.Color.green())

    @discord.ui.button(label="退室", style=discord.ButtonStyle.red, custom_id="exit_v5")
    async def exit(self, interaction, button):
        await self.handle_click(interaction, "退室", discord.Color.red())

@bot.event
async def on_ready():
    # 起動時にボタンを有効化
    bot.add_view(MyView())
    print(f'ログイン成功: {bot.user.name} (ID: {bot.user.id})')

@bot.command()
async def setup(ctx):
    """ボタン付きメッセージを出すコマンド"""
    await ctx.send("【入退室管理】ボタンを押して記録してください", view=MyView())

if __name__ == "__main__":
    # Renderで落ちないようにWebサーバーを裏で動かす
    keep_alive()
    # 環境変数からトークンを読み込んで起動
    bot.run(os.getenv('DISCORD_TOKEN'))
