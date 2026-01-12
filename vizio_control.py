#!/usr/bin/env python3
"""
Simple Vizio SmartCast TV Control Script
Requires: requests library (pip install requests)
"""
import warnings
import os

# 1. Quiet environment warnings immediately
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources.*")
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import requests
import json
import sys

CONFIG_FILE = "vizio_config.json"

class VizioTV:
    def __init__(self, ip_address, auth_token=None, ip_mac=None):
        self.ip = ip_address
        self.port = 7345
        self.mac = ip_mac
        self.base_url = f"https://{self.ip}:{self.port}"
        self.auth_token = auth_token
        self.headers = {
            "Content-Type": "application/json"
        }
        if auth_token:
            self.headers["AUTH"] = auth_token
    
    def _make_request(self, method, endpoint, data=None):
        """Make HTTP request to TV"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method, 
                url, 
                headers=self.headers,
                json=data,
                verify=False,
                timeout=5
            )
            return response
        except requests.exceptions.ConnectTimeout:
            print(f"ERROR: Connection timeout to {self.ip}. Is the TV on and connected to the network?")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"ERROR: Cannot connect to {self.ip}. Check IP address and network connection.")
            print(f"Details: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return None
    
    def pair_start(self, device_name="PythonRemote"):
        """Start pairing process"""
        data = {
            "DEVICE_NAME": device_name,
            "DEVICE_ID": device_name
        }
        response = self._make_request("PUT", "/pairing/start", data)
        if response is None:
            return None
        
        if response.status_code == 200:
            result = response.json()
            # Token is in ITEM.PAIRING_REQ_TOKEN
            item = result.get('ITEM', {})
            pairing_token = item.get('PAIRING_REQ_TOKEN')
            if pairing_token:
                print(f"✓ Pairing initiated. Check your TV for a 4-digit PIN.")
                return pairing_token
            else:
                print(f"ERROR: No pairing token in response: {result}")
                return None
        else:
            print(f"ERROR: Pairing failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def pair_finish(self, pairing_token, pin):
        """Complete pairing with PIN from TV"""
        data = {
            "DEVICE_ID": "PythonRemote",
            "PAIRING_REQ_TOKEN": int(pairing_token),
            "CHALLENGE_TYPE": 1,
            "RESPONSE_VALUE": str(pin)
        }
        response = self._make_request("PUT", "/pairing/pair", data)
        if response is None:
            return None
        
        if response.status_code == 200:
            result = response.json()
            # Token is in ITEM.AUTH_TOKEN
            item = result.get('ITEM', {})
            auth_token = item.get('AUTH_TOKEN')
            if auth_token:
                print(f"✓ Pairing successful!")
                return auth_token
            else:
                print(f"ERROR: No auth token in response: {result}")
                return None
        else:
            print(f"ERROR: Pairing failed with status {response.status_code}")
            print(f"Response: {response.text}")
            if "INVALID" in response.text:
                print("The PIN may be incorrect or expired. Try pairing again.")
            return None


    def get_power_state(self):
        """Check if TV is on or off"""
        response = self._make_request("GET", "/state/device/power_mode")
        if response is None:
            return None
        
        if response.status_code == 200:
            state = response.json()
            power_mode = state.get('ITEMS', [{}])[0].get('VALUE', 0)
            return power_mode == 1
        elif response.status_code == 401:
            print("ERROR: Authentication failed. Your auth token may be invalid or expired.")
            print("Try pairing again with: python vizio_control.py <tv_ip> pair")
            return None
        else:
            print(f"ERROR: Get power state failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    import time

    def power_on(self):
        """Turn TV on"""
        # First try Wake-on-LAN if MAC address is available
        if self.mac:
            print(f"Sending WoL magic packet to {self.mac}...")
            try:
                send_wol(self.mac)
                print("Waiting 5 seconds for TV to wake up...")
                #time.sleep(5)
            except Exception as e:
                print(f"WoL failed: {e}, trying API command...")
        
        # Now try the API command
        data = {
            "KEYLIST": [{
                "CODESET": 11,
                "CODE": 1,
                "ACTION": "KEYPRESS"
            }]
        }
        response = self._make_request("PUT", "/key_command/", data)
        if response is None:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("ERROR: Authentication failed. Your auth token is invalid.")
            return False
        else:
            print(f"ERROR: Power on failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    def power_on_old(self):
        """Turn TV on"""
        data = {
            "KEYLIST": [{
                "CODESET": 11,
                "CODE": 1,
                "ACTION": "KEYPRESS"
            }]
        }
        response = self._make_request("PUT", "/key_command/", data)
        if response is None:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("ERROR: Authentication failed. Your auth token is invalid.")
            return False
        else:
            print(f"ERROR: Power on failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def power_off(self):
        """Turn TV off"""
        data = {
            "KEYLIST": [{
                "CODESET": 11,
                "CODE": 0,
                "ACTION": "KEYPRESS"
            }]
        }
        response = self._make_request("PUT", "/key_command/", data)
        if response is None:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("ERROR: Authentication failed. Your auth token is invalid.")
            return False
        else:
            print(f"ERROR: Power off failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def power_toggle(self):
        """Toggle power state"""
        is_on = self.get_power_state()
        if is_on is None:
            print("ERROR: Could not determine power state")
            send_wol(self.mac)
            return False
        
        if is_on:
            print("TV is on, turning off...")
            return self.power_off()
        else:
            print("TV is off, turning on...")
            return self.power_on()
    
    def volume_up(self):
        """Increase volume"""
        data = {
            "KEYLIST": [{
                "CODESET": 5,
                "CODE": 1,
                "ACTION": "KEYPRESS"
            }]
        }
        response = self._make_request("PUT", "/key_command/", data)
        if response is None:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("ERROR: Authentication failed. Your auth token is invalid.")
            return False
        else:
            print(f"ERROR: Volume up failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def volume_down(self):
        """Decrease volume"""
        data = {
            "KEYLIST": [{
                "CODESET": 5,
                "CODE": 0,
                "ACTION": "KEYPRESS"
            }]
        }
        response = self._make_request("PUT", "/key_command/", data)
        if response is None:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("ERROR: Authentication failed. Your auth token is invalid.")
            return False
        else:
            print(f"ERROR: Volume down failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def mute(self):
        """Toggle mute"""
        data = {
            "KEYLIST": [{
                "CODESET": 5,
                "CODE": 4,
                "ACTION": "KEYPRESS"
            }]
        }
        response = self._make_request("PUT", "/key_command/", data)
        if response is None:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("ERROR: Authentication failed. Your auth token is invalid.")
            return False
        else:
            print(f"ERROR: Mute failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def get_current_input(self):
        """Get current input"""
        response = self._make_request("GET", "/menu_native/dynamic/tv_settings/devices/current_input")
        if response and response.status_code == 200:
            result = response.json()
            return result.get('ITEMS', [{}])[0].get('VALUE')
        return None
    
    def get_inputs_list(self):
        """Get list of available inputs"""
        response = self._make_request("GET", "/menu_native/dynamic/tv_settings/devices/name_input")
        if response and response.status_code == 200:
            result = response.json()
            return result.get('ITEMS', [])
        return []
    
    def set_input(self, input_name):
        """
        Change to a specific input
        Args:
            input_name: Input name like "HDMI-1", "HDMI-2", "CAST", etc.
        """
        # Get current input to get HASHVAL
        current_response = self._make_request("GET", "/menu_native/dynamic/tv_settings/devices/current_input")
        if not current_response or current_response.status_code != 200:
            print("ERROR: Could not get current input state")
            return False
        
        current_data = current_response.json()
        hashval = current_data.get('ITEMS', [{}])[0].get('HASHVAL')
        
        if not hashval:
            print("ERROR: Could not get HASHVAL from current input")
            return False
        
        # Set new input
        data = {
            "REQUEST": "MODIFY",
            "VALUE": input_name,
            "HASHVAL": hashval
        }
        response = self._make_request("PUT", "/menu_native/dynamic/tv_settings/devices/current_input", data)
        
        if response is None:
            return False
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:
            print("ERROR: Authentication failed")
            return False
        else:
            print(f"ERROR: Set input failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def send_key(self, codeset, code, action="KEYPRESS"):
        """
        Send a remote control key
        Args:
            codeset: Key codeset number
            code: Key code number
            action: KEYPRESS, KEYDOWN, or KEYUP
        """
        data = {
            "KEYLIST": [{
                "CODESET": codeset,
                "CODE": code,
                "ACTION": action
            }]
        }
        response = self._make_request("PUT", "/key_command/", data)
        if response is None:
            return False
        if response.status_code == 200:
            return True
        else:
            print(f"ERROR: Key command failed with status {response.status_code}")
            return False
    
    # Navigation keys (D-Pad)
    def key_up(self):
        """Press Up arrow"""
        return self.send_key(3, 8)
    
    def key_down(self):
        """Press Down arrow"""
        return self.send_key(3, 0)
    
    def key_left(self):
        """Press Left arrow"""
        return self.send_key(3, 1)
    
    def key_right(self):
        """Press Right arrow"""
        return self.send_key(3, 7)
    
    def key_ok(self):
        """Press OK/Select"""
        return self.send_key(3, 2)
    
    def key_back(self):
        """Press Back"""
        return self.send_key(4, 0)
    
    def key_exit(self):
        """Press Exit"""
        return self.send_key(4, 1)
    
    def key_menu(self):
        """Press Menu"""
        return self.send_key(4, 8)
    
    def key_home(self):
        """Press Home (SmartCast)"""
        return self.send_key(4, 3)
    
    def key_info(self):
        """Press Info"""
        return self.send_key(4, 6)
    
    # Channel keys
    def channel_up(self):
        """Channel up"""
        return self.send_key(8, 1)
    
    def channel_down(self):
        """Channel down"""
        return self.send_key(8, 0)
    
    def send_channel(self, channel_number):
        """
        Send channel number
        Args:
            channel_number: Channel number as string (e.g., "5", "125")
        """
        # Send each digit
        for digit in str(channel_number):
            if not digit.isdigit():
                print(f"ERROR: Invalid channel number: {channel_number}")
                return False
            
            # ASCII codes: 0=48, 1=49, 2=50, etc.
            code = 48 + int(digit)
            if not self.send_key(0, code):
                return False
        
        return True
    
    def get_current_app_settings(self):
        """
        Queries the local TV to see exactly what app is running 
        and what settings (ID, Namespace, Message) it uses.
        """
        response = self._make_request("GET", "/app/current")
        if response and response.status_code == 200:
            data = response.json().get("ITEM", {}).get("VALUE", {})
            print(f"Captured Local Settings:")
            print(f"APP_ID: {data.get('APP_ID')}")
            print(f"NAME_SPACE: {data.get('NAME_SPACE')}")
            print(f"MESSAGE: {data.get('MESSAGE')}")
            return data
        return None

    def launch_app(self, app_name):
        """
        Corrected Launch App function for 2026 Vizio firmware.
        Ensures correct NAME_SPACE (4) and valid string MESSAGE values.
        """
        # Updated database for 2026 compatibility
        apps = {
            "netflix": {"name_space": 3, "app_id": "1", "message": None},
            "youtube": {"name_space": 5, "app_id": "1", "message": None},
            "acorn tv": {"name_space": 4, "app_id": "74", "message": "https://app.rlje.net/vizio/index.html"},
            "watchfree": {"name_space": 4, "app_id": "3014", "message": "http://127.0.0.1:12345/scfs/sctv/main.html#/watchfreeplus"},
            "tubi": {"name_space": 4, "app_id": "61", "message": "https://ott-vizio.tubitv.com/?utm_source=AppRow&tracking=AppRow"},
            "free movies": {"name_space": 4, "app_id": "331", "message": "https://fmplus.unreel.me/tv/vizio"},
            "xumo": {"name_space": 4, "app_id": "62", "message": "https://xfinity-kabletown-app.xumo.com/prod/index.html?partner=smartcast"},
            "action": {"name_space": 4, "app_id": "298", "message": "https://vizio-prod.ottstudio.plus/vizio-apps/action"},
            "the archive": {"name_space": 4, "app_id": "577", "message": "https://blueprint.matchpoint.tv/thearchive/"},
        }

        self.get_current_app_settings()
        
        app_lower = app_name.lower()
        if app_lower not in apps:
            print(f"ERROR: Unknown app '{app_name}'")
            return False
        
        app_data = apps[app_lower]
        
        # CRITICAL FIX: Every key must be a string or integer exactly as the TV expects.
        # The MESSAGE field should be the string "None" if no specific URL is used.
        data = {
            "VALUE": {
                "APP_ID": str(app_data["app_id"]),
                "NAME_SPACE": int(app_data["name_space"]),
                "MESSAGE": str(app_data["message"]) if app_data["message"] else "None"
            }
        }
        
        response = self._make_request("PUT", "/app/launch", data)

        print()
 
        # --- RAW PRINT START ---
        import json
        print("--- DEBUG: SENDING PAYLOAD ---")
        print(json.dumps(data, indent=2))
        # --- RAW PRINT END ---
        print()
        # --- RAW PRINT START ---
        print("--- DEBUG: RECEIVING RESPONSE ---")
        if response is not None:
            print(f"Status Code: {response.status_code}")
            print(f"Raw Body: {response.text}")
        else:
            print("Response is None (Request Failed)")
        # --- RAW PRINT END ---
        
        if response and response.status_code == 200:
            return True
        
        print(f"ERROR: Failed with status {getattr(response, 'status_code', 'No Response')}")
        return False

    def list_available_apps(self):
        """List apps that can be launched"""
        apps = [
            "Netflix",
            "YouTube",
            "Acorn TV",
            "WatchFree",
            "Tubi", 
            "Free Movies",
            "XUMO",
            "Action",
            "The Archive",
        ]
        return apps

###  end of class VizioTV  ###
    
import os
import re

def get_mac_from_ip(ip_address):
    # Use system ARP command
    output = os.popen(f'arp -a {ip_address}').read()
    
    # Extract MAC address (matches patterns like AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)
    mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
    match = re.search(mac_pattern, output)
    
    if match:
        return match.group(0)
    return None

# Usage
#tv_ip = "192.168.1.100"
#tv_mac = get_mac_from_ip(tv_ip)
#print(f"MAC address: {tv_mac}")

import socket
import struct

def send_wol(mac_address, broadcast_ip='255.255.255.255'):
    # Remove separators from MAC address
    mac = mac_address.replace(':', '').replace('-', '')
    
    # Create magic packet: 6 bytes of FF + 16 repetitions of MAC
    data = b'FF' * 6 + (mac * 16).encode()
    packet = b''
    for i in range(0, len(data), 2):
        packet += struct.pack('B', int(data[i:i+2], 16))
    
    # Send to broadcast address on port 9
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(packet, (broadcast_ip, 9))
    sock.close()

# Usage
#send_wol('AA:BB:CC:DD:EE:FF')  # Your TV's MAC address

def load_config():
    """Load config from file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"WARNING: Could not load config file: {e}")
    return {}

def save_config(ip, auth_token, tv_mac):
    """Save config to file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)
    
    config = {
        "ip": ip,
        "auth_token": auth_token,
        "mac": tv_mac
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"ERROR: Could not save config: {e}")
        return False

def show_help():
    """Show help message"""
    print("Vizio TV Control")
    print("\nUsage:")
    print("  python vizio_control.py <tv_ip> <command> [args]")
    print("\nBasic Commands:")
    print("  ip_addr    - Pair with TV (first time setup)")
    print("  on         - Turn TV on")
    print("  off        - Turn TV off")
    print("  toggle     - Toggle power state")
    print("  status     - Show TV status")
    print("\nVolume Commands:")
    print("  vol_up     - Volume up")
    print("  vol_down   - Volume down")
    print("  mute       - Toggle mute")
    print("\nInput Commands:")
    print("  inputs     - List available inputs")
    print("  input <name> - Change to input (e.g., 'HDMI-1', 'Kodi')")
    print("\nNavigation Commands:")
    print("  up         - Arrow up")
    print("  down       - Arrow down")
    print("  left       - Arrow left")
    print("  right      - Arrow right")
    print("  ok         - OK/Select button")
    print("  back       - Back button")
    print("  exit       - Exit button")
    print("  menu       - Menu button")
    print("  home       - Home/SmartCast button")
    print("  info       - Info button")
    print("\nChannel Commands:")
    print("  ch_up      - Channel up")
    print("  ch_down    - Channel down")
    print("  ch <num>   - Go to channel (e.g., 'ch 5', 'ch 125')")
    print("\nExamples:")
    print("  python vizio_control.py 192.168.4.31")
    print("  python vizio_control.py on")
    print("  python vizio_control.py input HDMI-1")
    print("  python vizio_control.py input 'DISH Hopper'")
    print("  python vizio_control.py home")

def do_pairing(tv_ip):
    """Handle pairing process"""
    tv = VizioTV(tv_ip)
    
    print(f"Pairing with {tv_ip}...")
    pairing_token = tv.pair_start()
    
    if not pairing_token:
        print("\nPairing failed. Make sure:")
        print("  1. TV is on")
        print("  2. TV is connected to the network")
        print("  3. IP address is correct")
        return False
    
    pin = input("\nEnter the 4-digit PIN shown on your TV: ")
    auth_token = tv.pair_finish(pairing_token, pin)
    
    if auth_token:
        print(f"\nAuth Token: {auth_token}")

        tv_mac = get_mac_from_ip(tv_ip)
        print(f"\nMAC Address: {tv_mac}")

        save_config(tv_ip, auth_token, tv_mac)
        
        # Test the token
        print("\nTesting connection...")
        test_tv = VizioTV(tv_ip, auth_token)
        power_state = test_tv.get_power_state()
        if power_state is not None:
            print(f"✓ Connection successful! TV is {'ON' if power_state else 'OFF'}")
            return True
        else:
            print("WARNING: Pairing succeeded but couldn't verify connection")
            return False
    else:
        print("\nPairing failed.")
        return False


def main():
    """Main entry point"""
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    config = load_config()
    
    # Determine if first arg is IP or command
    if len(sys.argv) < 2:
        if not config.get('ip'):
            show_help()
            sys.exit(1)
        # No args, just show help
        show_help()
        sys.exit(0)
    
    first_arg = sys.argv[1]
    
    # Check if first arg looks like an IP address
    if '.' in first_arg or first_arg == 'viziocasttv.local':
        # First arg is IP
        tv_ip = first_arg
        command = sys.argv[2] if len(sys.argv) > 2 else "status"
        
        # Check if we need to pair for this IP
        if config.get('ip') != tv_ip or not config.get('auth_token'):
            print(f"No pairing found for {tv_ip}. Starting pairing process...\n")
            success = do_pairing(tv_ip)
            if not success:
                sys.exit(1)
            config = load_config()
    else:
        # First arg is command, use saved IP
        if not config.get('ip') or not config.get('auth_token'):
            print("ERROR: No saved config. Provide IP address first.")
            print("Usage: python vizio_control.py <tv_ip>")
            sys.exit(1)
        tv_ip = config['ip']
        command = first_arg
    
    if command == "help":
        show_help()
        sys.exit(0)
    
    auth_token = config['auth_token']
    
    tv = VizioTV(tv_ip, auth_token, config['mac'])
    
    # Execute command
    if command == "on":
        success = tv.power_on()
        if success:
            print("✓ TV turned on")
        sys.exit(0 if success else 1)
    
    elif command == "off":
        success = tv.power_off()
        if success:
            print("✓ TV turned off")
        sys.exit(0 if success else 1)
    
    elif command == "toggle":
        success = tv.power_toggle()
        sys.exit(0 if success else 1)
    
    elif command == "vol_up":
        success = tv.volume_up()
        if success:
            print("✓ Volume up")
        sys.exit(0 if success else 1)
    
    elif command == "vol_down":
        success = tv.volume_down()
        if success:
            print("✓ Volume down")
        sys.exit(0 if success else 1)
    
    elif command == "mute":
        success = tv.mute()
        if success:
            print("✓ Mute toggled")
        sys.exit(0 if success else 1)
    
    elif command == "status":
        is_on = tv.get_power_state()
        if is_on is not None:
            print(f"TV is {'ON' if is_on else 'OFF'}")
            current_input = tv.get_current_input()
            if current_input:
                print(f"Current input: {current_input}")
        sys.exit(0 if is_on is not None else 1)
    
    elif command == "inputs":
        inputs = tv.get_inputs_list()
        if inputs:
            print("Available inputs:")
            for inp in inputs:
                name = inp.get('VALUE', {}).get('NAME') if isinstance(inp.get('VALUE'), dict) else inp.get('VALUE')
                cname = inp.get('CNAME', '')
                print(f"  {cname}: {name}")
        else:
            print("ERROR: Could not get inputs list")
        sys.exit(0 if inputs else 1)
    
    elif command == "input":
        if len(sys.argv) < 4:
            print("ERROR: Input name required")
            print("Usage: python vizio_control.py <tv_ip> input <input_name>")
            print("Example: python vizio_control.py 192.168.4.31 input HDMI-1")
            sys.exit(1)
        
        input_name = sys.argv[3]
        success = tv.set_input(input_name)
        if success:
            print(f"✓ Changed to input: {input_name}")
        sys.exit(0 if success else 1)
    
    # Navigation commands
    elif command == "up":
        success = tv.key_up()
        if success:
            print("✓ Up")
        sys.exit(0 if success else 1)
    
    elif command == "down":
        success = tv.key_down()
        if success:
            print("✓ Down")
        sys.exit(0 if success else 1)
    
    elif command == "left":
        success = tv.key_left()
        if success:
            print("✓ Left")
        sys.exit(0 if success else 1)
    
    elif command == "right":
        success = tv.key_right()
        if success:
            print("✓ Right")
        sys.exit(0 if success else 1)
    
    elif command == "ok":
        success = tv.key_ok()
        if success:
            print("✓ OK")
        sys.exit(0 if success else 1)
    
    elif command == "back":
        success = tv.key_back()
        if success:
            print("✓ Back")
        sys.exit(0 if success else 1)
    
    elif command == "exit":
        success = tv.key_exit()
        if success:
            print("✓ Exit")
        sys.exit(0 if success else 1)
    
    elif command == "menu":
        success = tv.key_menu()
        if success:
            print("✓ Menu")
        sys.exit(0 if success else 1)
    
    elif command == "home":
        success = tv.key_home()
        if success:
            print("✓ Home")
        sys.exit(0 if success else 1)
    
    elif command == "info":
        success = tv.key_info()
        if success:
            print("✓ Info")
        sys.exit(0 if success else 1)
    
    elif command == "ch_up":
        success = tv.channel_up()
        if success:
            print("✓ Channel up")
        sys.exit(0 if success else 1)
    
    elif command == "ch_down":
        success = tv.channel_down()
        if success:
            print("✓ Channel down")
        sys.exit(0 if success else 1)
    
    elif command == "ch":
        if len(sys.argv) < 3:
            print("ERROR: Channel number required")
            print("Usage: python vizio_control.py ch <channel_number>")
            print("Example: python vizio_control.py ch 125")
            sys.exit(1)
        
        channel = sys.argv[2]
        success = tv.send_channel(channel)
        if success:
            print(f"✓ Changed to channel {channel}")
        sys.exit(0 if success else 1)
    
    elif command == "apps":
        apps = tv.list_available_apps()
        print("Available apps to launch:")
        for app in apps:
            print(f"  - {app}")
        print("\nUsage: python vizio_control.py <tv_ip> app <app_name>")
        print("Example: python vizio_control.py 192.168.4.31 app Netflix")
        sys.exit(0)
    
    elif command == "app":
        if len(sys.argv) < 4:
            print("ERROR: App name required")
            print("Usage: python vizio_control.py <tv_ip> app <app_name>")
            print("Run 'apps' command to see available apps")
            sys.exit(1)
        
        app_name = sys.argv[3]
        success = tv.launch_app(app_name)
        if success:
            print(f"✓ Launched app: {app_name}")
        sys.exit(0 if success else 1)
    
    else:
        print(f"ERROR: Unknown command '{command}'\n")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
