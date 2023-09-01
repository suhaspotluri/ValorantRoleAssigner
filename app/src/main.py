import discord
import os
import random
import logging
import requests_cache
from itertools import groupby
import re

logging.basicConfig(level=logging.INFO)

VERSION = os.getenv(
    "VERSION",
    "0.0.0",
)

ENV = os.getenv(
    "ENV",
    "dev",
)
TOKEN = os.getenv(
    "DISCORD_TOKEN",
    "",
)

if TOKEN == "":
    logging.error("DISCORD_TOKEN not passed")
    quit(1)
session = requests_cache.CachedSession(".cache/valorant-api", expire_after=120)
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


AGENTS = []

MEMBERS_NEEDED = 2


@client.event
async def on_ready():
    logging.info(f"Server started. Logged in as {client.user}")


def get_agent_roles():
    session = requests_cache.CachedSession(".cache/valorant-api", expire_after=120)
    params = {"isPlayableCharacter": True}
    agents = session.get("https://valorant-api.com/v1/agents", params=params).json()[
        "data"
    ]
    agents = sorted(agents, key=lambda x: x["role"]["displayName"])
    final_dict = {}
    for key, value in groupby(agents, lambda x: x["role"]["displayName"]):
        final_dict[key] = list(value)
    final_dict["Free Pick"] = agents
    return final_dict


def assign_random_roles(members, channel_name):
    roles = list(get_agent_roles().keys())
    random.shuffle(roles)
    member_roles_dict = {}
    for i in range(0, len(members)):
        role = roles[i]
        member_roles_dict[members[i]] = role
        logging.info(f"{members[i]}: {role}")
    text = f"Player roles for `{channel_name}` Voice Channel:\n"
    for member in member_roles_dict:
        text += f"{member.mention} assigned to `{member_roles_dict[member]}`\n"
    return text.strip()


def assign_random_agents(members, channel_name):
    agents = get_agent_roles()["Free Pick"]
    random.shuffle(agents)
    member_agents_dict = {}
    for i in range(0, len(members)):
        agent = agents[i]["displayName"]
        member_agents_dict[members[i]] = agent
        logging.info(f"!AGENTS: {members[i]}: {agent}")
    text = f"Player agents for `{channel_name}` Voice Channel:\n"
    for member in member_agents_dict:
        text += f"{member.mention} assigned to `{member_agents_dict[member]}`\n"
    return text.strip()


def parse_roles_message(text):
    lines = text.split(":")[1].strip().split("\n")
    print(f"LINES: {lines}")
    member_role_dict = {}
    for line in lines:
        matches = re.search("(<.+>).+(`.+`)", line)
        member = matches.group(1)
        role = matches.group(2)
        member_role_dict[member] = role.split("`")[1]
    print(member_role_dict)
    return member_role_dict


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!info"):
        await message.reply(f"version: {VERSION} env: {ENV}")
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

    if message.content.startswith("!agents"):
        voice_channel_responses = {}
        if message.type == discord.MessageType.reply:
            reply_message = await message.channel.fetch_message(
                message.reference.message_id
            )
            if (
                reply_message.author == client.user
                and reply_message.content.startswith("Player roles for")
            ):
                print(reply_message.content)
                print(reply_message)
                member_role_dict = parse_roles_message(reply_message.content)
                text = f"Player role specific agents:\n"
                for member in member_role_dict:
                    agents = get_agent_roles()[member_role_dict[member]]
                    random.shuffle(agents)
                    text += f"{member} assigned to `{member_role_dict[member]}`: `{agents[0]['displayName']}`\n"
                await reply_message.reply(text)
            elif (
                reply_message.author == client.user
                and reply_message.content.startswith(
                    "Sorry, no channels currently have exactly"
                )
            ):
                await reply_message.reply(
                    "Error, roles were not assigned. Please try again after roles are successfully assigned or try command without a reply to assign random agents"
                )
            else:
                await reply_message.reply(
                    "Please try command command again without replying to this message"
                )

        else:
            for voice_channel in message.guild.voice_channels:
                voice_channel_members = voice_channel.members
                if len(voice_channel_members) != 0:
                    text = assign_random_agents(
                        voice_channel_members, voice_channel.name
                    )
                    voice_channel_responses[voice_channel] = text
            if voice_channel_responses:
                for voice_channel in voice_channel_responses:
                    await message.reply(voice_channel_responses[voice_channel])
            else:
                await message.reply(f"Sorry, no channels currently have members")


client.run(TOKEN)
