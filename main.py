import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import os
from flask import Flask
from threading import Thread

# --- Render生存確認用 (cron-job用) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# --- 設定 ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
JST = timezone(timedelta(hours=+9), 'JST')

# 【重要】ログチャンネルID
LOG_CHANNEL_ID = 1481594264533209088 

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_click(self, interaction: discord.Interaction, status_text, color):
        # ★ここが重要：まず「受け付けたよ」と即レスして3秒ルールを回避する
        await interaction.response.defer(ephemeral=True)
        
        now = datetime.now(JST).strftime('%Y/%m/%d %H:%M')
        try:
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = discord.Embed(
                    title=f"{now} {status_text}", 
                    description=f"**{interaction.user.display_name}** さんが{status_text}しました。",
                    color=color, timestamp=datetime.now(JST)
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                # ログを送信
                await log_channel.send(embed=embed)
                
                # 送信完了後にメッセージを更新
                await interaction.followup.send(f"{status_text}を記録しました！", ephemeral=True)
            else:
                await interaction.followup.send(f"⚠️エラー：ログ用チャンネルが見つかりません(ID:{LOG_CHANNEL_ID})", ephemeral=True)
        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send(f"❌エラーが発生しました: {e}", ephemeral=True)

    @discord.ui.button(label="入室", style=discord.ButtonStyle.green, custom_id="entry_v4")
    async def entry(self, interaction, button):
        await self.handle_click(interaction, "入室", discord.Color.green())

    @discord.ui.button(label="退室", style=discord.ButtonStyle.red, custom_id="exit_v4")
    async def exit(self, interaction, button):
        await self.handle_click(interaction, "退室", discord.Color.red())

@bot.event
async def on_ready():
    bot.add_view(MyView())
    print(f'ログイン完了: {bot.user.name}')

@bot.command()
async def setup(ctx):
    await ctx.send("【入退室管理】ボタンを押して記録してください", view=MyView())

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
