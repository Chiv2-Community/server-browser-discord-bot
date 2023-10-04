from ast import Dict
import colorsys
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

    await reset_channel()

    message_buffer: Dict[str, discord.Embed] = {}
    while not client.is_closed():
        try:
            print("Sleeping for " + str(UPDATE_INTERVAL) + " seconds")
            await asyncio.sleep(UPDATE_INTERVAL)  # Wait a minute before updating again

            channel = client.get_channel(CHANNEL_ID)

            server_info = get_server_info()
            if not server_info:
                continue

            print(f"Found {len(server_info['servers'])} servers")

            for server in server_info['servers']:
                unique_id = server['unique_id']
                name = server['name']
                current_map = server['current_map']
                player_count = server['player_count']
                max_players = server['max_players']
                password_protected = ":lock:" if server.get('password_protected', False) else ":unlock:"
                description = server['description']

                if current_map == "Unknown":
                    continue

                embed = discord.Embed(title=name, color=hash_to_color(hash(name)))
                embed.add_field(name="Map", value=current_map, inline=True)
                embed.add_field(name="Players", value=str(player_count) + " / " + str(max_players), inline=True)
                embed.add_field(name="Password Protected", value=password_protected, inline=True)
                embed.add_field(name="Description", value=description, inline=True)

                # Check if we've already posted about this server
                if unique_id in message_buffer:
                    # Update the message
                    await message_buffer[unique_id].edit(embed=embed)
                else:
                    # Otherwise, create a new message
                    sent_message = await channel.send(embed=embed, silent=True)
                    message_buffer[unique_id] = sent_message

            # Check for servers that no longer exist and delete their messages
            to_delete = []
            current_server_ids = {server['unique_id'] for server in server_info['servers']}
            for message_id, _ in message_buffer.items():
                if message_id not in current_server_ids:
                    to_delete.append(message_id)

            for message_id in to_delete:
                await message_buffer[message_id].delete()
                del message_buffer[message_id]

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

async def reset_channel():
    try:
        print("Resetting channel")
        channel = client.get_channel(CHANNEL_ID)
        messages = channel.history(limit=None)
        async for message in messages:
            print(f"Deleting message {message.id}")
            await message.delete()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

def hash_to_color(hash_int: int):
    # Convert the hash to an integer
    
    # Use the integer to get values between 0 and 1 for HSV components
    h = (hash_int & 0xFF) / 255.0
    s = ((hash_int >> 8) & 0xFF) / 255.0 * 0.5 + 0.5   # Ensuring saturation is vibrant
    v = ((hash_int >> 16) & 0xFF) / 255.0 * 0.5 + 0.5  # Ensuring value/brightness is vibrant
    
    # Convert HSV to RGB
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    # Convert RGB from 0-1 to 0-255
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    
    # Return in 0xRRGGBB format
    return (r << 16) | (g << 8) | b

if __name__ == "__main__":
    print("Starting bot")
    asyncio.run(client.start(TOKEN))
