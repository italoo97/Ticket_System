import discord
from discord.ext import commands
import asyncio
from config import TOKEN, Tickets
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import duckdb
import threading

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

api_app = Flask(__name__)
CORS(api_app) 
DB_PATH = "tickets.duckdb"

@api_app.route("/api/ticket/<token>")
def get_ticket_html(token):
    
    
@api_app.route("/view/ticket/<token>")
def ticket_view(token):
    

def run_api():
    api_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def start_api():
    thread = threading.Thread(target=run_api)
    thread.daemon = True
    thread.start()
    print("✅ API Flask iniciada na porta 8080")

async def load_extensions():
    extensions = {
        "tickets": Tickets,
    }
    
    for name, enabled in extensions.items():
        if enabled:
            try:
                await bot.load_extension(f"cogs.{name.lower().replace(' ', '')}")
                print(f"✅ Carregando módulo: {name}")
            except Exception as e:
                print(f"❌ Falha ao carregar {name}: {str(e)}")

@bot.event
async def on_ready():
    print(f"\n🤖 Bot online como {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"📅 Iniciado em: {discord.utils.utcnow()}\n")
    
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} comandos slash sincronizados")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")

async def main():
    start_api()  
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot encerrado pelo usuário")
    except Exception as e:

        print(f"\n❌ Erro fatal: {e}")

