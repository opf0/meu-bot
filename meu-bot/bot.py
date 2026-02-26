import discord
from discord.ext import commands
from discord import app_commands, Interaction
import os
import asyncio
from datetime import datetime

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
SUPPORT_ROLE_ID = None
TICKET_CATEGORY_ID = None
GUILD_ID = None


class TicketButtons(discord.ui.View):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        guild = interaction.guild
        support_role = guild.get_role(SUPPORT_ROLE_ID)

        if not support_role:
            await interaction.followup.send("❌ Support role not configured!", ephemeral=True)
            return

        ticket_channel = discord.utils.get(guild.channels, name=f"ticket-{interaction.user.id}")
        if ticket_channel:
            await interaction.followup.send(
                f"❌ You already have a ticket: {ticket_channel.mention}",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        category = guild.get_channel(TICKET_CATEGORY_ID)

        ticket = await guild.create_text_channel(
            f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket opened by {interaction.user} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        embed = discord.Embed(
            title="🎫 Ticket Created",
            description=f"Thank you for creating a ticket, {interaction.user.mention}!",
            color=discord.Color.green()
        )

        embed.add_field(name="User", value=interaction.user.mention, inline=False)
        embed.add_field(name="Created At", value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inline=False)

        await ticket.send(
            f"{interaction.user.mention} {support_role.mention}",
            embed=embed,
            view=TicketManagementButtons()
        )

        await interaction.followup.send(f"✅ Ticket created: {ticket.mention}", ephemeral=True)


class TicketManagementButtons(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.claimed_by = None

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.blurple)
    async def claim_ticket(self, interaction: Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        guild = interaction.guild
        support_role = guild.get_role(SUPPORT_ROLE_ID)

        if support_role not in interaction.user.roles:
            await interaction.followup.send("❌ You don't have permission!", ephemeral=True)
            return

        if self.claimed_by:
            await interaction.followup.send(
                f"❌ Already claimed by {self.claimed_by.mention}",
                ephemeral=True
            )
            return

        self.claimed_by = interaction.user

        embed = discord.Embed(
            title="🎫 Ticket Claimed",
            description=f"Claimed by {interaction.user.mention}",
            color=discord.Color.blue()
        )

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("✅ You claimed this ticket!", ephemeral=True)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: Interaction, button: discord.ui.Button):

        await interaction.response.defer()

        guild = interaction.guild
        support_role = guild.get_role(SUPPORT_ROLE_ID)

        user_id = int(interaction.channel.name.split("-")[1])

        if support_role not in interaction.user.roles and interaction.user.id != user_id:
            await interaction.followup.send("❌ No permission!", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎫 Ticket Closed",
            description=f"Closed by {interaction.user.mention}",
            color=discord.Color.red()
        )

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("⏳ Deleting in 5 seconds...", ephemeral=True)

        await asyncio.sleep(5)
        await interaction.channel.delete()


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")


@bot.tree.command(name="setup_tickets", description="Setup ticket system (Admin only)")
async def setup_tickets(interaction: Interaction, support_role: discord.Role, category: discord.CategoryChannel):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin only!", ephemeral=True)
        return

    global SUPPORT_ROLE_ID, TICKET_CATEGORY_ID, GUILD_ID

    SUPPORT_ROLE_ID = support_role.id
    TICKET_CATEGORY_ID = category.id
    GUILD_ID = interaction.guild.id

    embed = discord.Embed(
        title="🎫 Ticket System Setup",
        description="Configured successfully!",
        color=discord.Color.green()
    )

    embed.add_field(name="Support Role", value=support_role.mention)
    embed.add_field(name="Ticket Category", value=category.mention)

    ticket_channel = discord.utils.get(interaction.guild.channels, name="tickets")
    if not ticket_channel:
        ticket_channel = await interaction.guild.create_text_channel("tickets")

    embed_message = discord.Embed(
        title="🎫 Support Tickets",
        description="Click below to open a ticket.",
        color=discord.Color.blue()
    )

    await ticket_channel.send(embed=embed_message, view=TicketButtons(bot))
    await interaction.response.send_message(embed=embed, ephemeral=True)


# RUN BOT
if __name__ == "__main__":
        bot.run("MTQ3NjM0MjQyMjkxNjE2OTc4OQ.GiGEvT.W0-uqIr_4_yIg8HKBjhwWbg02n6Y1YjU5np2cM
