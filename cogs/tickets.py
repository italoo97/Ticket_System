# -*- coding: utf-8 -*-
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from discord import app_commands, ui
from discord.ui import Modal, TextInput, Button, View
from config import DB_TICKETS, ARQUIVO_JSON, ID_DEVOLUCAO, CARGOS_SLASH, CATEGORIAS_PERMITIDAS, CANAL_TICKET, LOG_TICKET, SUPORTE_ID, DENUNCIA_ID, DONATE_ID, REGRAS_TICKETS, STREAMER_ID, ALINHAMENTO_ID, POLICIA_ID, STAFF_ID
import json
import os
import io
import asyncio
import random
import string
from dateutil.parser import parse
import pytz
import duckdb
import uuid

def save_transcript_to_db(code: str, html: str, token: str):
    conn = duckdb.connect(DB_TICKETS)
    conn.execute("""
        UPDATE ticket_html
        SET html_content = ?, token = ?
        WHERE ticket_id = ?
    """, (html, token, code))
    conn.close()

def get_local_time():
    # Define o fuso horário de Brasília (GMT-3)
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

def init_db():
    conn = duckdb.connect(DB_TICKETS)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS devolucoes (
        message_id BIGINT PRIMARY KEY,
        usuario_id BIGINT,
        status TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        channel_id BIGINT PRIMARY KEY,
        ticket_id TEXT,
        author_id BIGINT,
        claimed_by BIGINT,
        added_users TEXT, -- JSON string de lista
        created_at TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS claimed_stats (
        staff_id BIGINT PRIMARY KEY,
        count BIGINT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS ticket_html (
        token TEXT PRIMARY KEY,
        ticket_id TEXT,
        user_id BIGINT,
        html_content TEXT
    )
    """)
    conn.close()

def load_ticket_data():
    conn = duckdb.connect(DB_TICKETS)
    ticket_owners = {}
    claimed_stats = {}

    for row in conn.execute("SELECT * FROM tickets").fetchall():
            ticket_owners[str(row[0])] = {
                "ticket_id": row[1],
                "channel_id": row[0],
                "author_id": row[2],
                "claimed_by": row[3],
                "added_users": json.loads(row[4]),
                "created_at": row[5]
            }
    for row in conn.execute("SELECT * FROM claimed_stats").fetchall():
        claimed_stats[str(row[0])] = row[1]
    conn.close()
    return ticket_owners, claimed_stats
    
def save_ticket_data(ticket_owners, claimed_stats):
    conn = duckdb.connect(DB_TICKETS)
    for ch_id, info in ticket_owners.items():
        conn.execute("""
                INSERT OR REPLACE INTO tickets (channel_id, ticket_id, author_id, claimed_by, added_users, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
            int(ch_id),
            info["ticket_id"],
            info["author_id"],
            info.get("claimed_by"),
            json.dumps(info.get("added_users", [])),
            info["created_at"]
            ))
    for staff_id, count in claimed_stats.items():
        conn.execute("""
                INSERT OR REPLACE INTO claimed_stats (staff_id, count) VALUES (?, ?)
            """, (int(staff_id), count))
    conn.close()

class TicketButtonView(View):
    def __init__(self, ticket_channel):
        super().__init__(timeout=None)
        self.add_item(
            Button(
                label="Acessar Ticket",
                url=ticket_channel.jump_url,
                style=discord.ButtonStyle.link
            )
        )

class DevolucaoModal(ui.Modal, title="📦 Registrar Devolução"):

    def __init__(self, interaction: discord.Interaction, usuario: discord.Member):
        super().__init__()
        self.interaction = interaction
        self.usuario = usuario

    id_field = ui.TextInput(label="ID de quem vai devolver os itens", placeholder="Ex: 12345", required=True, max_length=30)
    itens_field = ui.TextInput(label="Itens a serem devolvidos", style=discord.TextStyle.paragraph, placeholder="Descreva os itens aqui...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        canal = interaction.client.get_channel(ID_DEVOLUCAO)

        if not canal:
            await interaction.response.send_message("❌ Canal de devolução não encontrado. Verifique o ID.", ephemeral=True)
            return
        
        embed = 
        embed.timestamp = discord.utils.utcnow()

        view = DevolucaoView()

        msg = await canal.send(embed=embed, view=view)
        view.message = msg  

        await salvar_devolucao(msg.id, self.usuario.id)

        await interaction.response.send_message("✅ Pedido de devolução registrado com sucesso!", ephemeral=True)

async def atualizar_embed_status(message: discord.Message, status: str, aprovador: discord.Member):



class DevolucaoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.message = None  # Definido depois de enviar a mensagem

    @ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: ui.Button):
        

    @ui.button(label="❌ Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: ui.Button):


async def salvar_devolucao(message_id: int, usuario_id: int):
    conn = duckdb.connect(DB_TICKETS)
    conn.execute("""
        INSERT OR REPLACE INTO devolucoes (message_id, usuario_id, status)
        VALUES (?, ?, 'pendente')
    """, (message_id, usuario_id))
    conn.close()

async def atualizar_status_devolucao(message_id: int, status: str):
    conn = duckdb.connect(DB_TICKETS)
    conn.execute("""
        UPDATE devolucoes SET status = ? WHERE message_id = ?
    """, (status, message_id))
    conn.close()

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()
        self.ticket_owners, self.claimed_stats = load_ticket_data()

    @tasks.loop(seconds=10)
    async def auto_save(self):
        save_ticket_data(self.ticket_owners, self.claimed_stats)

    def save_ticket_data(self):
        save_ticket_data(self.ticket_owners, self.claimed_stats)

    def create_ticket_entry(self, channel_id: int, user_id: int, ticket_id: str):
        """Cria a entrada inicial de um ticket"""
        self.ticket_owners[str(channel_id)] = {
            "ticket_id": ticket_id,
            "channel_id": channel_id,
            "author_id": user_id,
            "claimed_by": None,
            "added_users": [],
            "created_at": get_local_time().isoformat()
        }
        save_ticket_data(self.ticket_owners, self.claimed_stats)

    def claim_ticket(self, channel_id: int, staff_id: int):
        """Marca quem assumiu o ticket e atualiza a contagem"""
        channel_id_str = str(channel_id)
        if channel_id_str in self.ticket_owners:

    def add_user_to_ticket(self, channel_id: int, user_id: int):
        """Adiciona um usuário ao ticket"""
        channel_id_str = str(channel_id)
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketButtons(self))  
        self.bot.add_view(TicketManagement(self))  
        print("Ticket System Cog carregado!")

        try:
            if os.path.exists(ARQUIVO_JSON):
                with open(ARQUIVO_JSON, "r") as f:
                    
            try:
                with open(ARQUIVO_JSON, "r") as f:
                    dados = json.load(f)

                for msg_id_str, info in dados.items():

            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"❌ Erro no on_ready do TicketSystem: {e}")
    
    async def on_guild_channel_delete(self, channel):
        if str(channel.id) in self.ticket_owners:
            
    async def on_guild_channel_create(self, channel):
        for prefix in self.ticket_count:
            if channel.name.startswith(prefix):
               
    @commands.command()
    async def setup_tickets(self, ctx):
        print(f"Procurando canal com ID: {CANAL_TICKET}")
        try:
            ticket_channel = self.bot.get_channel(CANAL_TICKET)
            print(f"Canal encontrado: {ticket_channel} ({type(ticket_channel)})")
            log_channel = self.bot.get_channel(LOG_TICKET) 
            
            if not ticket_channel:
                await ctx.send("Erro: Canal de tickets não encontrado. Verifique o ID.")
                return

            view = TicketButtons(self)

            bot_user = self.bot.user
            description_text = ()

            embed = 

            if log_channel:

        
        except Exception as e:
            print(f"Erro completo: {e}")

        msg = await ticket_channel.send(embed=embed, view=view)

        with open(ARQUIVO_JSON, "w") as f:
            json.dump({
                "canal_id": msg.channel.id,
                "mensagem_id": msg.id,
                "view_type": "TicketButtons"
            }, f)

class TicketTypeSelect(discord.ui.View):
    def __init__(self, cog, interaction_user):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction_user = interaction_user

        options = 

        self.add_item(TicketTypeDropdown(options, self))

class TicketButtons(discord.ui.View):
    def __init__(self, cog=None):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.secondary, custom_id="abrir_ticket")
    async def abrir_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            content="Escolha abaixo o tipo de atendimento:",
            view=TicketTypeSelect(self.cog, interaction.user),
            ephemeral=True
        )

class TicketTypeDropdown(discord.ui.Select):
    def __init__(self, options, parent_view):
        super().__init__(placeholder="Selecione o tipo de atendimento", options=options)
        self.custom_view = parent_view
        self.cog = parent_view.cog

    async def generate_unique_ticket_name(self, guild):
        def generate_code():
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        existing_codes = {
            channel.name.split("-")[-1] 
            for channel in guild.text_channels
            if "-" in channel.name and len(channel.name.split("-")[-1]) == 6
        }

        while True:
            code = generate_code()
            if code not in existing_codes:
                return code

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.custom_view.interaction_user:
            await interaction.response.send_message("Você não pode interagir com este menu.", ephemeral=True)
            return

        escolha = self.values[0]
        await interaction.response.defer(ephemeral=True)

        # Chamando a função apropriada com base na escolha
        if escolha.startswith("Suporte"):
            await self.create_ticket_sup(interaction, "📞・sup")

    async def check_open_ticket_sup(self, user):
        guild = user.guild
        for channel in guild.text_channels:
            if (
                channel.category and channel.category.id == SUPORTE_ID and
                channel.topic == str(user.id)
            ):
                return True
        return False
    
    async def create_ticket_sup(self, interaction: discord.Interaction, category_name: str):
            # Verificar se o usuário já tem um ticket aberto
            if await self.check_open_ticket_sup(interaction.user):
                await interaction.response.send_message("Você já tem um ticket aberto! Por favor, aguarde a resolução.", ephemeral=True)
                return
            
            guild = interaction.guild 
            category = discord.utils.get(guild.categories, id=SUPORTE_ID)
                
            overwrites = dict(category.overwrites)
            overwrites[interaction.user] = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        attach_files=True,
        read_message_history=True
    )

            overwrites[guild.me] = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        embed_links=True
    )
            code = await self.generate_unique_ticket_name(guild)
            channel_name = f"📞・sup-{code}"

            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=str(interaction.user.id)
                )
            
            if hasattr(self.cog, "create_ticket_entry"):
                self.cog.create_ticket_entry(ticket_channel.id, interaction.user.id, ticket_id=code)
                self.cog.save_ticket_data()

            
            embed = discord.Embed(
                )

            embed.set_footer(text="ByteShop © Todos os direitos reservados", icon_url=ticket_channel.guild.icon.url)
            
            view = TicketManagement(self.cog)
            await ticket_channel.send(embed=embed, view=view)
            embedresp = discord.Embed(
        title="🎫 Ticket Criado",
        description=f"Olá {interaction.user.mention}, seu ticket foi criado com sucesso!\n\nClique no botão abaixo para acessá-lo.",
        color=discord.Color.dark_teal()
    )
            view = TicketButtonView(ticket_channel)
            await interaction.followup.send(embed=embedresp, view=view, ephemeral=True)

def get_ticket_view(cog=None):
    return TicketButtons(cog=cog)

class RenameTicketModal(discord.ui.Modal, title="Renomear Ticket"):
    def __init__(self, channel_id: int, nome_atual: str):
        super().__init__()
        self.channel_id = channel_id
        self.novo_nome = discord.ui.TextInput()
        self.add_item(self.novo_nome)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.client.get_channel(self.channel_id)

        if not channel:

        try:
            await channel.edit(name=self.novo_nome.value)
            await interaction.response.send_message(
                f"✅ Ticket renomeado para `{self.novo_nome.value}` com sucesso!",
                ephemeral=True
            )
        except discord.Forbidden:
        
        except Exception as e:

class AcoesTicketView(discord.ui.View):
    def __init__(self, cog, interaction_user):
        super().__init__(timeout=60)
        self.cog = cog
        self.add_item(AcoesDropdown(cog, interaction_user))

class AcoesDropdown(discord.ui.Select):
    def __init__(self, cog, expected_user):
        options = []
        super().__init__(placeholder=, options=options)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.expected_user:
            return await interaction.response.send_message("Você não pode usar este menu.", ephemeral=True)

        if self.values[0] == :
            await interaction.response.send_modal(RenameTicketModal(interaction.channel.id, interaction.channel.name))
        elif self.values[0] == :
            view = discord.ui.View(timeout=60)
            await interaction.response.send_message("Escolha uma nova categoria:", view=view, ephemeral=True)

class CategoriaDropdown(discord.ui.Select):
    def __init__(self, cog, expected_user):
        options = [
            discord.SelectOption(label="Suporte", value=str(SUPORTE_ID), emoji="📞"),
            ]
        super().__init__(placeholder="Selecione uma nova categoria...", options=options)
        self.cog = cog
        self.expected_user = expected_user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.expected_user:
            return await interaction.response.send_message("Você não pode usar este menu.", ephemeral=True)

        categoria_id = int(self.values[0])
        nova_categoria = interaction.guild.get_channel(categoria_id)

        if not nova_categoria:
            return await interaction.response.send_message("❌ Categoria não encontrada.", ephemeral=True)

        try:
            await interaction.channel.edit(category=nova_categoria)
            await interaction.response.send_message(f"✅ Ticket movido para a categoria **{nova_categoria.name}**.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao mover categoria: {e}", ephemeral=True)


class TicketManagement(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.bot = cog.bot
    
    @discord.ui.button(label="❌ Cancelar Ticket", style=discord.ButtonStyle.danger, custom_id="ticket:cancelar")
    async def cancel_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Verifica se é o criador ou staff

            await interaction.response.defer()
            ticket_info = self.cog.ticket_owners.get(str(interaction.channel.id), {})
            try:
                await self.transcribe_ticket(interaction.channel, interaction.user)
            except Exception as e:
                print(f"Erro ao gerar transcript ao cancelar: {e}")

            # Remove o ticket do sistema

        except Exception as e:
            print(f"Erro ao cancelar ticket: {e}")
            await interaction.followup.send(
                "❌ Ocorreu um erro ao cancelar o ticket.",
                ephemeral=True
            )

    @discord.ui.button(label="👤 Poke", style=discord.ButtonStyle.secondary, custom_id="intimar:membro")
    async def int_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Verifica se é staff
           
    @discord.ui.button(label="⚙️ Ações Ticket", style=discord.ButtonStyle.secondary, custom_id="ticket:acoes")
    async def ticket_actions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.id in CARGOS_SLASH for role in interaction.user.roles):

    @discord.ui.button(label="🔄 Devolução", style=discord.ButtonStyle.secondary, custom_id="ticket:devolucao")
    async def devolver_user(self, interaction: discord.Interaction, button: Button):

    @discord.ui.button(label="👤 Adicionar Membro", style=discord.ButtonStyle.secondary, custom_id="add:membro")
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        
    @discord.ui.button(label="🚫 Remover Membro", style=discord.ButtonStyle.secondary, custom_id="intimar:remover")
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        
    @discord.ui.button(label="📝 Adicionar Observação", style=discord.ButtonStyle.primary, custom_id="obs")
    async def add_observation(self, interaction: discord.Interaction, button: discord.ui.Button):
       
    @discord.ui.button(label="✅ Fechar Ticket", style=discord.ButtonStyle.success, custom_id="ticket:fechar")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        token = str(uuid.uuid4())  # Gera o token uma única vez
        try:
           
    @discord.ui.button(label="🎯 Assumir Ticket", style=discord.ButtonStyle.secondary, custom_id="ticket:assumir")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar se o usuário tem permissão para assumir o ticket

        # Mensagem ephemeral confirmando

        # Alterar nome do canal
        
        # Desativar botão e alterar texto
       
        # Enviar mensagem de recepção no canal
       
        # Enviar DM para o criador do ticket
       
    @discord.ui.button(label="👤 Chamada de Voz", style=discord.ButtonStyle.secondary, custom_id="ticket:call")
    async def call_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        ticket_channel = interaction.channel
    
        # Criar o canal de voz com base no nome do canal atual

        # Esperar e monitorar a chamada por 5 minutos
            # Se ninguém estiver na call, deleta

                # Se alguém estiver na call, reinicia o contador

    async def transcribe_ticket(self, channel: discord.TextChannel, closed_by: discord.Member, token: str):
        ticket_info = self.cog.ticket_owners.get(str(channel.id), {})
        code = ticket_info.get("ticket_id", "DESCONHECIDO")
        author_id = ticket_info.get("author_id")

        creator = None
        
        if author_id:
        
        
        messages = []
        ticket_opened_at = None
        
        # Coleta o histórico de mensagens
        
            
            # Determina a cor da borda com base no tipo de usuário
            
        opened_at_str = ticket_opened_at.strftime("%d/%m/%Y %H:%M") if ticket_opened_at else "Desconhecido"

        html_content = f"""
        """
        transcript_bytes = html_content.encode()
        
        conn = duckdb.connect(DB_TICKETS)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_html (
                token TEXT PRIMARY KEY,
                ticket_id TEXT,
                user_id BIGINT,
                html_content TEXT
            )
        """)
        conn.execute("""
            INSERT OR REPLACE INTO ticket_html (token, ticket_id, user_id, html_content)
            VALUES (?, ?, ?, ?)
        """, (token, code, ticket_info.get("author_id"), html_content))
        conn.close()
        save_transcript_to_db(code, html_content, token)
        
        log_channel = self.bot.get_channel(LOG_TICKET)
        if log_channel:
            log_embed = 
            await log_channel.send(embed=log_embed, 
                                 file=discord.File(io.BytesIO(transcript_bytes), 
                                 filename=f"transcript-{channel.name}.html"))

            # Enviar mensagem privada ao criador
        if creator:
            try:    
                dm_embed = 
                view = View()
                view.add_item(
                    Button(
                        label="📄 Ver Transcript",
                        style=discord.ButtonStyle.link,
                        url=f"https://maliticket.discloud.app/api/ticket/{token}"  # usa o token do ticket
                    )
                )

                await creator.send(embed=dm_embed, view=view)

            except discord.Forbidden:
                await channel.send(

                )

            # Remover ticket dos owners


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketSystem(bot))