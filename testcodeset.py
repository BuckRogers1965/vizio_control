#!/usr/bin/env python3
"""
Vizio Code Finder
This script tests all possible codes for a given codeset.
"""
import time
import sys
from vizio_control import VizioTV, load_config

# --- CONFIGURATION ---
CODESET_TO_TEST = 13  # The codeset you want to scan
DELAY_BETWEEN_CODES = 5 # Seconds to wait. Gives you time to see what happens.
# --- END CONFIGURATION ---

def main():
    """Main entry point"""
    config = load_config()
    if not config.get('ip') or not config.get('auth_token'):
        print("ERROR: No pairing found. Run vizio_control.py first to pair.")
        sys.exit(1)

    tv = VizioTV(config['ip'], config['auth_token'])
    print(f"--- Vizio Code Finder ---")
    print(f"TV IP: {config['ip']}")
    print(f"Scanning Codeset: {CODESET_TO_TEST}")
    print(f"Press Ctrl+C to stop the scan.")
    print("--------------------------\n")

    # We will test codes from 0 to 255
    for code in range(256):
        try:
            print(f"Sending: CODESET={CODESET_TO_TEST}, CODE={code}")
            success = tv.send_key(CODESET_TO_TEST, code)
            
            if not success:
                print("  -> Failed to send command. Check TV connection.")

            time.sleep(DELAY_BETWEEN_CODES)

        except KeyboardInterrupt:
            print("\n\nScan stopped by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            sys.exit(1)
    
    print("\nScan complete.")

if __name__ == "__main__":
    main()
