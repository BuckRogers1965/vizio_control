#!/usr/bin/env python3
"""
Vizio TV Remote Control Web Interface
Requires: flask, requests
Install: pip install flask requests
"""
from flask import Flask, render_template, jsonify, request
from vizio_control import VizioTV, load_config
import sys

app = Flask(__name__)

# Load config and initialize TV
config = load_config()
if not config.get('ip') or not config.get('auth_token'):
    print("ERROR: No pairing found. Run vizio_control.py first to pair.")
    sys.exit(1)

tv = VizioTV(config['ip'], config['auth_token'], config.get('mac'))

@app.route('/')
def index():
    return render_template('remote.html')

@app.route('/api/command/<command>', methods=['POST'])
def execute_command(command):
    """Execute a TV command"""
    try:
        if command == "toggle":
            success = tv.power_toggle()
        elif command == "on":
            success = tv.power_on()
        elif command == "off":
            success = tv.power_off()
        elif command == "vol_up":
            success = tv.volume_up()
        elif command == "vol_down":
            success = tv.volume_down()
        elif command == "mute":
            success = tv.mute()
        elif command == "ch_up":
            success = tv.channel_up()
        elif command == "ch_down":
            success = tv.channel_down()
        elif command == "up":
            success = tv.key_up()
        elif command == "down":
            success = tv.key_down()
        elif command == "left":
            success = tv.key_left()
        elif command == "right":
            success = tv.key_right()
        elif command == "ok":
            success = tv.key_ok()
        elif command == "back":
            success = tv.key_back()
        elif command == "exit":
            success = tv.key_exit()
        elif command == "menu":
            success = tv.key_menu()
        elif command == "home":
            success = tv.key_home()
        elif command == "info":
            success = tv.key_info()
        else:
            return jsonify({"success": False, "message": f"Unknown command: {command}"})
            
        if success:
            return jsonify({"success": True, "message": f"{command.upper()}"})
        else:
            return jsonify({"success": False, "message": f"Failed: {command}"})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/inputs', methods=['GET'])
def get_inputs():
    """Get list of available inputs"""
    try:
        inputs = tv.get_inputs_list()
        if inputs:
            input_list = [
                {
                    "name": inp.get('CNAME', ''),
                    "value": inp.get('VALUE', {}).get('NAME', '') if isinstance(inp.get('VALUE'), dict) else inp.get('VALUE', '')
                }
                for inp in inputs
            ]
            return jsonify({"success": True, "inputs": input_list})
        return jsonify({"success": False, "message": "No inputs found"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/apps', methods=['GET'])
def get_apps():
    """Get list of available apps"""
    try:
        apps = tv.list_available_apps()
        return jsonify({"success": True, "apps": apps})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/input/<input_name>', methods=['POST'])
def set_input(input_name):
    """Set TV input"""
    try:
        success = tv.set_input(input_name)
        if success:
            return jsonify({"success": True, "message": f"Input: {input_name}"})
        return jsonify({"success": False, "message": "Failed to change input"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/app/<app_name>', methods=['POST'])
def launch_app(app_name):
    """Launch app"""
    try:
        success = tv.launch_app(app_name)
        if success:
            return jsonify({"success": True, "message": f"Launched: {app_name}"})
        return jsonify({"success": False, "message": f"Failed to launch {app_name}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    print(f"\n🖥️  Vizio TV Remote Control Server")
    print(f"📺 TV: {config['ip']}")
    print(f"🌐 Access from any device on your network:")
    print(f"   http://localhost:5000")
    print(f"   http://<your-computer-ip>:5000")
    print(f"\n Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
