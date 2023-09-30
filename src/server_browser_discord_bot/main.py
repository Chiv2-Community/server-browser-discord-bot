from ast import Dict
import traceback
from typing import Any, Optional
import discord
import requests
import asyncio
import http.client
import json
import argparse
import logging
import tabulate

# logging.basicConfig(level=logging.DEBUG, format="%(message)s")

args = argparse.ArgumentParser()
args.add_argument('--token', help='Discord bot token')
args.add_argument('--channel', help='Discord channel ID (integer)')
args.add_argument('--api-host', required=False, default="servers.polehammer.net", help='API host')
args.add_argument('--api-path', required=False, default="/api/v1/servers", help='API path')
args.add_argument('--update-interval', required=False, default=5, help='Update interval in seconds')
inputs = args.parse_args()

TOKEN = inputs.token  
CHANNEL_ID = int(inputs.channel)
API_HOST = inputs.api_host
API_PATH = inputs.api_path
UPDATE_INTERVAL = int(inputs.update_interval) # in seconds

INTENTS = discord.Intents.default()
client = discord.Client(intents=INTENTS)

def get_server_info():
    print(f"Fetching server info from http://{API_HOST}{API_PATH}")
    try:
        result = requests.get(f"http://{API_HOST}{API_PATH}")
        if result.status_code != 200:
            print(f"Error fetching server info: {result.status_code}")
            return None
        
        return result.json()
    except Exception as e:
        print(f"Error fetching server info: {e}")
        traceback.print_exc()
        return None


@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    while not client.is_closed():
        try:
            print("Sleeping for " + str(UPDATE_INTERVAL) + " seconds")
            await asyncio.sleep(UPDATE_INTERVAL)  # Wait a minute before updating again

            channel = client.get_channel(CHANNEL_ID)
            
            server_info = get_server_info()
            if not server_info:
                continue

            # Get all messages in the channel
            messages = await channel.history(limit=None).flatten()

            print(f"Found {len(server_info['servers'])} servers")

            servers = [[
                server['name'],
                server['current_map'],
                server['player_count'],
                ":reversecheckmark:" if server.get('password_protected', False) else ":x:",
                server['description']
            ] for server in server_info['servers']]

            new_embed = discord.Embed(
                title="Chivalry 2 Community Server List", 
                color=0x00ccff,
            )

            new_embed.set_footer(text="Install the launcher to join private servers: https://github.com/Chiv2-Community/UnchainedLauncher/releases/latest")

            servers.sort(key=lambda x: x[0])

            for [name, current_map, player_count, password_protected, description] in servers:
                current_server_message = filter(lambda x: x.embeds and x.embeds[0].title == name, messages)
                new_embed.add_field(
                    name=name, 
                    inline=True,
                    value=f"**Map:** {current_map}\n**Players:** {player_count}\n**Password Protected:** {password_protected}\n**Description:** {description}"
                )

            
            # Fetch last message in the channel
            last_message = None
            async for message in channel.history(limit=1):
                last_message = message


            # If the last message was sent by our bot, we'll edit it. If not, we'll send a new message.
            if last_message and last_message.author == client.user:
                print("Editing last message")
                await last_message.edit(content=None, embed=new_embed)
            else:
                print("Sending new message")
                await channel.send(new_embed)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    print("Starting bot")
    asyncio.run(client.start(TOKEN))
