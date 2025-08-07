
from keep_alive import keep_alive
keep_alive()
import discord
from discord.ext import commands
from discord.utils import get
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ADMIN_ROLE_NAME = "admin"
TICKET_CATEGORY = "Tickets"

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Chiudi Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(role.name == ADMIN_ROLE_NAME for role in interaction.user.roles):
            await interaction.response.send_message("Solo gli admin possono chiudere il ticket.", ephemeral=True)
            return
        await interaction.channel.delete()

class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apri Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild

        category = get(guild.categories, name=TICKET_CATEGORY)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for role in guild.roles:
            if role.name == ADMIN_ROLE_NAME:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"ticket-{user.name}", category=category, overwrites=overwrites)

        await interaction.response.send_message(f"Ticket creato: {channel.mention}", ephemeral=True)

        await channel.send(f"{user.mention} Preparati a fornire le seguenti risposte:\n"
                           f"1️⃣ Il tuo **rank**?\n"
                           f"2️⃣ Il tuo **ruolo**?\n"
                           f"3️⃣ Le tue **esperienze in ambito gaming/competitivo**?\n\n"
                           f"Per favore rispondi in ordine ai messaggi.")

        answers = []

        def check(m):
            return m.channel == channel and m.author == user

        try:
            for i in range(3):
                msg = await bot.wait_for("message", check=check, timeout=180)
                answers.append(msg.content)

            embed = discord.Embed(title="Risposte del ticket", color=discord.Color.blurple())
            embed.add_field(name="Utente", value=user.mention, inline=False)
            embed.add_field(name="Rank", value=answers[0], inline=False)
            embed.add_field(name="Ruolo", value=answers[1], inline=False)
            embed.add_field(name="Esperienze", value=answers[2], inline=False)

            await channel.send(embed=embed, view=CloseTicketView())

        except Exception:
            await channel.send(f"{user.mention}, tempo scaduto. Ticket non completato.")
            await channel.send(view=CloseTicketView())

@bot.event
async def on_ready():
    print(f"{bot.user} è online.")
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="ticket")
        if channel:
            await channel.send("🎫 Clicca il pulsante per aprire un ticket:", view=OpenTicketView())
            break

bot.run(os.getenv("DISCORD_TOKEN"))
