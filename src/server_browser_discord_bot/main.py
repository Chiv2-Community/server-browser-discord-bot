import discord
import requests
import asyncio
import http.client
import json
import argparse
import logging
import tabulate

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

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
    result = requests.get(f"http://{API_HOST}{API_PATH}")
    if result.status_code != 200:
        print(f"Error fetching server info: {result.status_code}")
        return []

    return result.json()


@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    while not client.is_closed():
        channel = client.get_channel(CHANNEL_ID)
        server_info = get_server_info()

        servers = [[
            server['name'],
            server['current_map'],
            f"{server['ip_address']}:{server['ports']['game']}",
            server['player_count'],
        ] for server in server_info['servers']]

        new_message = '```\n'
        new_message += tabulate.tabulate(servers, headers=['Name', 'Current Map', 'Server Address', 'Player Count'], tablefmt="fancy_grid") 
        new_message += '```\n'
        new_message += 'Install the launcher to join private servers: https://github.com/Chiv2-Community/C2GUILauncher/releases/latest.\n'
        
        # Fetch last message in the channel
        last_message = None
        async for message in channel.history(limit=1):
            last_message = message


        # If the last message was sent by our bot, we'll edit it. If not, we'll send a new message.
        if last_message and last_message.author == client.user:
            print("Editing last message")
            await last_message.edit(content=new_message)
        else:
            print("Sending new message")
            await channel.send(new_message)

        print("Sleeping for 60 seconds")
        await asyncio.sleep(UPDATE_INTERVAL)  # Wait a minute before updating again

if __name__ == "__main__":
    print("Starting bot")
    asyncio.run(client.start(TOKEN))
