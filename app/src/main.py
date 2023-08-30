import discord
import os
import random
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv(
    "DISCORD_TOKEN",
    "",
)

if TOKEN == "":
    logging.error("DISCORD_TOKEN not passed")
    quit(1)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

ROLES = ["Smokes", "Initiator", "Duelist", "Sentinel", "Free Pick"]
NECESSARY_ROLES = ["Smokes"]

MEMBERS_NEEDED = 5


@client.event
async def on_ready():
    logging.info(f"Server started. Logged in as {client.user}")


def assign_random_roles(members, channel_name):
    random.shuffle(ROLES)
    member_roles_dict = {}
    for i in range(0, len(members)):
        role = ROLES[i]
        member_roles_dict[members[i]] = role
        logging.info(f"{members[i]}: {role}")
    text = f"Player roles for `{channel_name}` Voice Channel:\n"
    for member in member_roles_dict:
        text += f"{member.mention} assigned to `{member_roles_dict[member]}`\n"
    return text.strip()


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!roles"):
        voice_channel_responses = {}
        for voice_channel in message.guild.voice_channels:
            voice_channel_members = voice_channel.members
            if len(voice_channel_members) == MEMBERS_NEEDED:
                logging.info(
                    f"{voice_channel} has {len(voice_channel_members)} memebers"
                )
                text = assign_random_roles(voice_channel_members, voice_channel.name)
                voice_channel_responses[voice_channel] = text
            else:
                logging.info(f"{voice_channel} does not have {MEMBERS_NEEDED} memebers")
        if voice_channel_responses:
            for voice_channel in voice_channel_responses:
                await message.channel.send(voice_channel_responses[voice_channel])
        else:
            await message.channel.send(
                f"Sorry, no channels currently have exactly {MEMBERS_NEEDED} members"
            )


client.run(TOKEN)
