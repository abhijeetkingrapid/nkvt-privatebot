import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

allow_join_list = set()

def save_allowlist():
    with open("allowlist.txt", "w") as f:
        f.write("\n".join(allow_join_list))

def load_allowlist():
    global allow_join_list
    try:
        with open("allowlist.txt", "r") as f:
            allow_join_list = set(f.read().splitlines())
    except FileNotFoundError:
        allow_join_list = set()

@bot.event
async def on_ready():
    load_allowlist()
    await bot.tree.sync()  # Auto sync slash commands
    print(f'Logged in as NKVT CORPORATION - {bot.user}')

@bot.event
async def on_member_join(member):
    if str(member.id) not in allow_join_list:
        try:
            await member.send("You have been kicked from NKVT CORPORATION as you are not on the allowlist.")
        except:
            pass
        await member.kick(reason="Not in NKVT CORPORATION allowlist")
    else:
        try:
            await member.send("Welcome to NKVT CORPORATION! You have been approved.")
        except:
            pass

@bot.tree.command(name="allow", description="Add a user to the NKVT CORPORATION allow list")
@app_commands.checks.has_permissions(administrator=True)
async def allow_slash(interaction: discord.Interaction, user_id: str):
    allow_join_list.add(user_id)
    save_allowlist()
    try:
        user = await interaction.guild.fetch_member(int(user_id))
        await user.send("✅ You have been approved to join NKVT CORPORATION!")
    except:
        pass
    await interaction.response.send_message(f"✅ User <@{user_id}> added to NKVT CORPORATION allow list.", ephemeral=True)

class TicketModal(Modal):
    def __init__(self, label, user):
        super().__init__(title=f"{label} Ticket - NKVT CORPORATION")
        self.user = user
        self.panel_name = TextInput(label="Panel Name", required=True)
        self.add_item(self.panel_name)
    
    async def on_submit(self, interaction: discord.Interaction):
        panel_name = self.panel_name.value
        category = discord.utils.get(interaction.guild.categories, id=1354023929018187797)
        if not category:
            await interaction.response.send_message("⚠️ Ticket category not found. Please check the category ID.", ephemeral=True)
            return
        
        # Set permissions: Only the creator and admins can see the ticket
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for admin in interaction.guild.roles:
            if admin.permissions.administrator:
                overwrites[admin] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # Create ticket channel with permissions
        channel_name = f"panel-update-{self.user.name}-{panel_name}"
        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎫 Ticket Created - Custom Panel Update",
            description=f"**User:** {self.user.mention}\n**Panel Name:** {panel_name}\n\nOur team will assist you shortly!",
            color=discord.Color.green()
        )
        embed.set_footer(text="Managed by NKVT CORPORATION | Please wait for assistance.")
        close_button = CloseTicketView(channel)
        await channel.send(embed=embed, view=close_button)
        
        try:
            await self.user.send(f"✅ Your ticket has been created: {channel.mention}")
        except:
            pass
        
        await interaction.response.send_message(f"✅ Your Custom Panel Update ticket has been created: {channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛠 Custom Panel Update", style=discord.ButtonStyle.blurple)
    async def panel_update(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(TicketModal("Custom Panel Update", interaction.user))

class CloseTicketView(View):
    def __init__(self, channel):
        super().__init__(timeout=None)
        self.channel = channel

    @discord.ui.button(label="❌ Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        transcript = "\n".join([f"{msg.author}: {msg.content}" async for msg in self.channel.history(limit=100)])
        user = self.channel.name.split("-")[2]
        user_obj = discord.utils.get(self.channel.guild.members, name=user)
        if user_obj:
            try:
                await user_obj.send(f"📜 Your ticket transcript from NKVT CORPORATION:\n```{transcript}```")
            except:
                pass
        await self.channel.delete()

@bot.tree.command(name="ticket", description="Send the ticket embed to a specified channel")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_slash(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = discord.Embed(
        title="🎫 NKVT CORPORATION Ticket System",
        description="🔹 **Need a Custom Panel Update?** Click the button below and provide panel details.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Managed by NKVT CORPORATION | Click the button below to create a ticket.")
    await channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message(f"✅ Ticket embed sent to {channel.mention}", ephemeral=True)

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))
