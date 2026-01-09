# Vizio SmartCast TV Control

A Python-based remote control for Vizio SmartCast TVs with both command-line and GUI interfaces.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Command-line control** for automation and scripting
- **Beautiful GUI remote** built with Pygame
- **Full remote control**: Power, volume, channels, navigation, and more
- **Input switching**: Easily switch between HDMI inputs
- **App launching**: Launch Netflix, Hulu, Prime Video, and more
- **Auto-pairing**: Pairs with your TV once and saves credentials
- **Network-based**: Controls TV over your local network

## Screenshots
![Screenshot](gui.png)

The GUI provides an intuitive touch-style remote interface with:
- Power control
- D-Pad navigation (up/down/left/right/OK)
- Volume and mute controls
- Channel controls
- Input and app selection dialogs
- Status messages

## Requirements

- Python 3.7 or higher
- Vizio SmartCast TV (2016+ models)
- TV and computer on the same network

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install requests pygame
```

## Quick Start

### First Time Setup (Pairing)

1. Make sure your TV is on and connected to your network

2. Find your TV's IP address (check your router or TV's network settings, or try `viziocasttv.local`)

3. Run the pairing command:
```bash
python vizio_control.py 192.168.1.0
```

4. Enter the 4-digit PIN displayed on your TV screen

5. Your pairing credentials will be saved to `vizio_config.json`

### Command Line Usage

After pairing, you can control your TV from the command line:

```bash
# Power control
python vizio_control.py on
python vizio_control.py off
python vizio_control.py toggle

# Volume
python vizio_control.py vol_up
python vizio_control.py vol_down
python vizio_control.py mute

# Change inputs
python vizio_control.py inputs          # List available inputs
python vizio_control.py input HDMI-1    # Switch to HDMI-1

# Launch apps
python vizio_control.py apps            # List available apps
python vizio_control.py app Netflix     # Launch Netflix

# Navigation
python vizio_control.py up
python vizio_control.py down
python vizio_control.py left
python vizio_control.py right
python vizio_control.py ok
python vizio_control.py back
python vizio_control.py home

# Channels
python vizio_control.py ch 125          # Go to channel 125
python vizio_control.py ch_up
python vizio_control.py ch_down

# Help
python vizio_control.py help
```

### GUI Remote Control

Launch the graphical remote after you pair the cli tool:

```bash
python vizio_gui.py
```

The GUI provides:
- Click buttons to control your TV
- Pop-up menus for input and app selection
- Visual feedback for all actions
- Clean, modern interface

## Available Commands

### Power
- `on` - Turn TV on
- `off` - Turn TV off  
- `toggle` - Toggle power state

### Volume
- `vol_up` - Volume up
- `vol_down` - Volume down
- `mute` - Toggle mute

### Navigation
- `up`, `down`, `left`, `right` - D-Pad arrows
- `ok` - OK/Select
- `back` - Back button
- `exit` - Exit button
- `menu` - Menu button
- `home` - Home/SmartCast button
- `info` - Info button

### Inputs
- `inputs` - List all available inputs
- `input <name>` - Switch to input (e.g., HDMI-1, HDMI-2)

### Apps
- `apps` - List available apps
- `app <name>` - Launch app

Supported apps:
- Netflix
- Hulu
- Prime Video / Amazon
- YouTube TV
- Pluto TV
- XUMO
- Vudu
- Disney+
- Crackle
- Plex
- Redbox
- CBS
- WatchFree

### Channels
- `ch <number>` - Go to specific channel
- `ch_up` - Channel up
- `ch_down` - Channel down

### Misc
- `status` - Show TV status
- `pair` - Re-pair with TV
- `help` - Show help

## Configuration File

After pairing, your TV's IP address and authentication token are saved in `vizio_config.json`:

```json
{
  "ip": "192.168.1.0",
  "auth_token": "Abc123Def456"
}
```

This file allows you to control your TV without entering credentials each time.

## Automation Examples

### Shell Script
```bash
#!/bin/bash
# Morning TV routine
python vizio_control.py on
sleep 2
python vizio_control.py input "HDMI-1"
python vizio_control.py app "YouTube TV"
```

### Python Script
```python
from vizio_control import VizioTV, load_config

config = load_config()
tv = VizioTV(config['ip'], config['auth_token'])

# Turn on TV and launch Netflix
tv.power_on()
time.sleep(2)
tv.launch_app("Netflix")
```

## Discovering and Adding New Apps

The built-in app database includes common streaming apps, but Vizio TVs support many more apps. To add support for apps not in the default list, you need to discover their configuration settings.

### How App Discovery Works

Each app on your Vizio TV has three key parameters:
- **APP_ID** - Unique identifier for the app
- **NAME_SPACE** - API namespace (typically 3, 4, or 5)
- **MESSAGE** - URL or identifier string (may be empty)

These values can change between firmware versions, so you need to capture them directly from your TV.

### Step-by-Step App Discovery Process

1. **Use your physical remote** to navigate to the app you want to add (e.g., HBO Max, Peacock, etc.)

2. **Launch the app** using your physical remote

3. **Run the discovery command** while the app is running:
```bash
   python vizio_control.py 192.168.4.31 discover_app
```

4. **Note the output** - it will show something like:
```
   Captured Local Settings:
   APP_ID: 74
   NAME_SPACE: 4
   MESSAGE: https://app.example.com/vizio/index.html
```

5. **Add the app to the database** in `vizio_control.py`:
   
   Open `vizio_control.py` and find the `launch_app()` function. Add your app to the `apps` dictionary:
```python
   apps = {
       # ... existing apps ...
       "hbo max": {"name_space": 4, "app_id": "74", "message": "https://app.example.com"},
       "your app": {"name_space": X, "app_id": "Y", "message": "your_message"},
   }
```

6. **Update the app list** in `list_available_apps()`:
```python
   def list_available_apps(self):
       """List apps that can be launched"""
       apps = [
           # ... existing apps ...
           "HBO Max",
           "Your App Name",
       ]
       return apps
```

7. **Test your new app**:
```bash
   python vizio_control.py 192.168.4.31 app "HBO Max"
```

### Important Notes

- **Firmware matters**: App IDs and namespaces can change with TV firmware updates
- **Empty messages**: Some apps have an empty MESSAGE field - use `None` in the dictionary
- **Case insensitive**: App names are matched case-insensitively (e.g., "netflix" = "Netflix" = "NETFLIX")
- **Contribute back**: If you discover settings for popular apps, consider sharing them via pull request

### Troubleshooting App Launch

If an app fails to launch:

1. **Verify the settings** by running discovery while the app is active
2. **Check the debug output** - the script shows exactly what it's sending and receiving
3. **Try different MESSAGE values** - some apps are picky about the exact URL format
4. **Update firmware** - ensure your TV has the latest firmware
5. **Manual test** - use curl to test the exact payload:
```bash
   curl -k -H "Content-Type: application/json" -H "AUTH: YOUR_TOKEN" \
     -X PUT -d '{"VALUE":{"APP_ID":"74","NAME_SPACE":4,"MESSAGE":"https://app.example.com"}}' \
     https://192.168.4.31:7345/app/launch
```

### Common App Namespaces

Based on testing across multiple firmware versions:

- **NAME_SPACE 3**: Netflix, older built-in apps
- **NAME_SPACE 4**: Most modern streaming apps (Disney+, Hulu, Prime Video, etc.)
- **NAME_SPACE 5**: YouTube TV, Google-related apps
- **NAME_SPACE 0**: Legacy apps, some SmartCast features

If an app isn't working, try changing the NAME_SPACE value while keeping the APP_ID the same.

## Troubleshooting

### Can't connect to TV
- Ensure TV is on and connected to network
- Verify IP address is correct
- Check that your computer and TV are on the same network
- Try using hostname `viziocasttv.local` instead of IP

### Authentication failed
- Re-pair with your TV: `python vizio_control.py <ip> pair`
- Delete `vizio_config.json` and pair again

### TV doesn't wake from sleep
- Wake-on-LAN may not work if TV is in Eco mode
- Try changing TV power settings

### Commands not working
- Verify pairing: `python vizio_control.py <ip> status`
- Check for error messages in output
- Ensure auth token is valid

## API Details

This project uses the Vizio SmartCast API which runs on:
- Port **7345** (firmware 4.0+)
- Port **9000** (older firmware)
- HTTPS with self-signed certificate

The API supports:
- Device pairing and authentication
- Remote control key commands
- Input selection
- App launching
- Power management
- Settings access

## Credits and Resources

This project was inspired by and built upon the following resources:

### Primary Inspiration
- **[homebridge-vizio](https://github.com/JohnWickham/homebridge-vizio)** by [JohnWickham](https://github.com/JohnWickham) - The Homebridge plugin that showed this was possible and pointed to the core API library

### Core API Library
- **[vizio-smart-cast](https://github.com/heathbar/vizio-smart-cast)** by [Heath Paddock](https://github.com/heathbar) - JavaScript library that implements the SmartCast API

### API Documentation
- **[Vizio_SmartCast_API](https://github.com/exiva/Vizio_SmartCast_API)** by [exiva](https://github.com/exiva) - Comprehensive API documentation for Vizio SmartCast TVs

### Python Implementation
- **[pyvizio](https://github.com/vkorn/pyvizio)** by [vkorn](https://github.com/vkorn) - Python library for Vizio SmartCast (referenced for API patterns)

## Technical Notes

- Uses HTTPS with self-signed certificates (SSL verification disabled)
- Requires pairing to obtain authentication token
- Pairing displays 4-digit PIN on TV screen
- All commands require authentication header
- TV must be powered on for API to respond (except power-on via WoL)

## License

MIT License - Feel free to use and modify

## Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## Disclaimer

This is an unofficial project and is not affiliated with or endorsed by Vizio. Use at your own risk.
