from typing import Self
import requests
import asyncio
from twitchio.ext import commands
from datetime import datetime, timedelta
import pytz
import logging

# Set your Twitch token and channel name
TWITCH_TOKEN = '' # Generate a token here: https://twitchtokengenerator.com
TWITCH_CLIENT_ID = ''
CHANNEL_NAME = ''

# ATIS API URL
ATIS_URL = 'https://api.flybywiresim.com/atis/KPDX?source=vatsim'  # change back to 'VATSIM' # Change this to whatever airport ICAO you need (IE: KSAN, KPHX)

# Log To File
logging.basicConfig(filename='ATIS-BOT.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_and_print(message, level='info'):
    """
    Logs and prints a message simultaneously.
    :param message: The message to log and print.
    :param level: The logging level ('info', 'warning', 'error', etc.).
    """
    if level == 'info':
        logging.info(message)
    elif level == 'warning':
        logging.warning(message)
    elif level == 'error':
        logging.error(message)
    elif level == 'debug':
        logging.debug(message)
    else:
        logging.log(logging.INFO, message)
    
    print(message)


class ATISBot(commands.Bot):

    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, client_id=TWITCH_CLIENT_ID, prefix='!', initial_channels=[CHANNEL_NAME])
        self.last_update_time = datetime.min
        self.last_atis_info = None

    async def startup(self):
        await self.update_atis()  # Start updating ATIS data

    async def event_ready(self):
        log_and_print(f'Logged in as | {self.nick}')
        log_and_print(f'User id is | {self.user_id}')
        await self.startup()  # Start the startup process

    async def event_error(self, error, *args, **kwargs):
        log_and_print(f"An error occurred: {error}, data: {args}")

    async def update_atis(self):
        while True:
            try:
                current_time = datetime.now()
                current_time_utc = current_time - (current_time.utcoffset() or timedelta())
                if current_time_utc is not None and current_time_utc - self.last_update_time > timedelta(minutes=10):
                    log_and_print("Fetching ATIS data...")
                    response = requests.get(ATIS_URL)
                    if response.status_code == 200:
                        atis_data = response.json()
                        log_and_print(f"ATIS data response: {atis_data}")  # Debug print to show the entire response
                        atis_info = atis_data.get('combined')
                        if atis_info:
                            log_and_print("Fetched ATIS data successfully.")
                            if atis_info != self.last_atis_info:
                                print(f"Original ATIS info length: {len(atis_info)}")
                                await self.post_atis_to_chat(atis_info)
                                self.last_atis_info = atis_info
                            self.last_update_time = current_time_utc
                        else:
                            log_and_print("No ATIS information found in response.")
                            await self.post_atis_to_chat("No ATIS information available.")
                    else:
                        log_and_print("Failed to fetch ATIS data.")
                await asyncio.sleep(600)  # Check for updates every 10 minutes
            except Exception as e:
                log_and_print(f"Error in update_atis: {e}")

    async def post_atis_to_chat(self, atis_info):
        try:
            channel = self.get_channel(CHANNEL_NAME)
            if channel:
                message = f"ATIS Update: \n{atis_info}"
                if len(message) > 500:
                    logging.warning(f"ATIS info exceeds 500 characters. Length: {len(message)}")
                    message = message[:497] + "..."  # Truncate and add ellipsis
                    print(f"Truncated message length: {len(message)}")
                else:
                    logging.info(f"ATIS info length: {len(message)}")
                await channel.send(message)
                log_and_print("Posted ATIS update to chat.")
            else:
                log_and_print(f"Failed to get channel: {CHANNEL_NAME}")
        except Exception as e:
            log_and_print(f"Error in post_atis_to_chat: {e}")

    async def event_message(self, message):
        if message is not None and message.author is not None and message.author.name is not None:
            if message.author.name.lower() == self.nick.lower():
                return
            await self.handle_commands(message)

bot = ATISBot()
try:
    log_and_print("Starting bot...")
    bot.run()
except Exception as e:
    log_and_print(f"Error: {e}")
    with open("error_log.txt", "w") as log_file:
        log_file.write(str(e))
bot.run()
