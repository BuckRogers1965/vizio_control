# Extension Guide: Adding Closed Caption Button

This guide walks through the process of adding a Closed Caption (CC) button to control your Vizio TV's caption settings.

## Overview

Adding a CC button involves three main components:
1. **Finding the correct key code** for the CC button
2. **Adding the function** to the VizioTV class
3. **Adding the button** to both CLI and GUI interfaces

## Step 1: Understanding Vizio Remote Key Codes

Vizio TVs use a key command API with three parameters:
- **CODESET** - Category of the button (e.g., 5 = Audio, 7 = Input, 13 = CC)
- **CODE** - Specific button within that codeset
- **ACTION** - Type of press (KEYPRESS, KEYDOWN, KEYUP)

### Known Closed Caption Codes

According to the [Vizio SmartCast API documentation](https://github.com/exiva/Vizio_SmartCast_API):

```
Codeset 13 = CC (Closed Captions)
```

However, the specific CODE value within codeset 13 may vary by TV model and firmware version.

### Method 1: Try Known CC Codes

Based on the API documentation and similar remote implementations, the CC toggle is likely:

```python
CODESET: 13
CODE: 4  # or possibly 0, 1, 2, 3
ACTION: "KEYPRESS"
```

### Method 2: Discover the Correct Code

If the standard code doesn't work, you'll need to discover it:

1. **Use the Vizio SmartCast mobile app** and press the CC button
2. **Monitor network traffic** to see what key code is sent
3. **Try systematic testing** of codes 0-10 in codeset 13

Example test script:
```python
from vizio_control import VizioTV, load_config

config = load_config()
tv = VizioTV(config['ip'], config['auth_token'])

# Test different CC codes
for code in range(11):
    print(f"Testing CC codeset 13, code {code}")
    input(f"Press Enter to test code {code} (watch your TV)...")
    tv.send_key(13, code)
```

## Step 2: Add Function to VizioTV Class

Once you've identified the correct code, add it to `vizio_control.py`:

### Location
In the `VizioTV` class, after the channel methods (around line 250), add:

```python
def key_cc(self):
    """Toggle closed captions"""
    return self.send_key(13, 4)  # Use the code you discovered
```

### Alternative: Open CC Menu

Some TVs have separate codes for toggling CC on/off vs. opening the CC settings menu:

```python
def key_cc_toggle(self):
    """Toggle closed captions on/off"""
    return self.send_key(13, 4)

def key_cc_menu(self):
    """Open closed caption settings menu"""
    return self.send_key(13, 0)  # May vary by model
```

## Step 3: Add CLI Command

In the `main()` function of `vizio_control.py`, add the command handler:

### Location
After the other navigation commands (around line 450), add:

```python
elif command == "cc":
    success = tv.key_cc()
    if success:
        print("✓ CC toggled")
    sys.exit(0 if success else 1)
```

### Update Help Text

In the `show_help()` function, add to the navigation or misc section:

```python
print("\nMisc Commands:")
print("  cc         - Toggle closed captions")
```

### Test CLI Command

```bash
python vizio_control.py 192.168.4.31 cc
```

## Step 4: Add GUI Button

In `vizio_remote_gui.py`, add a CC button to the interface:

### Location
In the `RemoteGUI.create_buttons()` method, find a good spot for the button. Recommended placement is near the Info button or in a new row.

### Example: Add CC Button Next to Info

Around line 120-130, after the Info button:

```python
# Back/Exit/Menu/Info row
back_btn = Button(margin, y_pos, 80, btn_height, "BACK", 
                 lambda: self.execute_command("back"))
menu_btn = Button(margin + 90, y_pos, 80, btn_height, "MENU", 
                 lambda: self.execute_command("menu"))
exit_btn = Button(margin + 180, y_pos, 80, btn_height, "EXIT", 
                 lambda: self.execute_command("exit"))
info_btn = Button(margin + 270, y_pos, 80, btn_height, "INFO", 
                 lambda: self.execute_command("info"))
self.buttons.extend([back_btn, menu_btn, exit_btn, info_btn])

y_pos += btn_height + 10

# Add CC button on new row
cc_btn = Button(margin, y_pos, 80, btn_height, "CC", 
               lambda: self.execute_command("cc"), ACCENT_COLOR)
self.buttons.append(cc_btn)
```

### Add Command Handler

In the `execute_command()` method, add:

```python
elif command == "cc":
    success = self.tv.key_cc()
```

### Alternative: Dedicated Accessibility Section

For better UI organization, create an "Accessibility" section:

```python
# Accessibility section
accessibility_label_y = y_pos
y_pos += 25

cc_btn = Button(margin + 20, y_pos, 100, btn_height, "CC", 
               lambda: self.execute_command("cc"))
audio_desc_btn = Button(margin + 130, y_pos, 140, btn_height, "AUDIO DESC", 
                       lambda: self.execute_command("audio_desc"))
self.buttons.extend([cc_btn, audio_desc_btn])

# Store label position
self.accessibility_label_y = accessibility_label_y
```

Then in the `draw()` method, add the label:

```python
# Draw accessibility label
access_label = font_small.render("ACCESSIBILITY", True, TEXT_COLOR)
screen.blit(access_label, (SCREEN_WIDTH // 2 - access_label.get_width() // 2, 
                           self.accessibility_label_y))
```

## Step 5: Testing

### Test Sequence

1. **Test CLI first**:
   ```bash
   python vizio_control.py 192.168.4.31 cc
   ```
   - Watch TV to see if CC toggles or menu opens
   - If nothing happens, try different CODE values (0-10)

2. **Test GUI**:
   ```bash
   python vizio_remote_gui.py
   ```
   - Click the CC button
   - Verify behavior matches CLI

3. **Test different scenarios**:
   - CC off → press button → CC on
   - CC on → press button → CC off
   - Different inputs (HDMI vs apps)
   - During different content types

### Troubleshooting

**Button does nothing:**
- Wrong CODE value - try others in codeset 13
- Wrong CODESET - some older models may use different codesets
- TV model doesn't support CC via API - may require physical remote only

**Button opens menu instead of toggling:**
- This is normal on some models
- Add separate `cc_toggle` and `cc_menu` functions
- Document the behavior for users

**Inconsistent behavior:**
- Some apps handle CC differently
- Native TV tuner vs streaming apps may behave differently
- Add note to README about limitations

## Step 6: Documentation

Update `README.md` to include the new command:

```markdown
### Accessibility
- `cc` - Toggle closed captions (or open CC menu)
```

In the GUI section:
```markdown
- **Accessibility controls**: CC button for caption control
```

## Advanced: CC Settings Menu Navigation

If the CC button opens a settings menu instead of toggling, you can create a helper function:

```python
def enable_cc(self):
    """Navigate CC menu to enable captions"""
    self.key_cc()      # Open menu
    time.sleep(0.5)
    self.key_down()    # Navigate to "On"
    time.sleep(0.2)
    self.key_ok()      # Select
    time.sleep(0.2)
    self.key_back()    # Close menu
    return True

def disable_cc(self):
    """Navigate CC menu to disable captions"""
    self.key_cc()      # Open menu
    time.sleep(0.5)
    self.key_ok()      # Select "Off" (usually first option)
    time.sleep(0.2)
    self.key_back()    # Close menu
    return True
```

Then add CLI commands:
```bash
python vizio_control.py 192.168.4.31 cc_on
python vizio_control.py 192.168.4.31 cc_off
```

## Complete Code Reference

### vizio_control.py additions:

```python
# In VizioTV class
def key_cc(self):
    """Toggle closed captions"""
    return self.send_key(13, 4)

# In main() function
elif command == "cc":
    success = tv.key_cc()
    if success:
        print("✓ CC toggled")
    sys.exit(0 if success else 1)

# In show_help() function
print("  cc         - Toggle closed captions")
```

### vizio_remote_gui.py additions:

```python
# In create_buttons()
cc_btn = Button(margin, y_pos, 80, btn_height, "CC", 
               lambda: self.execute_command("cc"))
self.buttons.append(cc_btn)

# In execute_command()
elif command == "cc":
    success = self.tv.key_cc()
```

## Other Useful Extensions

Using the same pattern, you can add:

- **Audio Description** (codeset 13, various codes)
- **Picture Mode** (codeset 6, code 0)
- **Sleep Timer** (varies by model)
- **Aspect Ratio** (codeset 6, code 1 or 2)
- **Favorite Channels** (codeset varies)

The discovery and implementation process is identical for all these features.

## Resources

- [Vizio SmartCast API Docs](https://github.com/exiva/Vizio_SmartCast_API) - Complete API reference
- [Additional Remote Codes](https://github.com/exiva/Vizio_SmartCast_API#additional-remote-codes) - Full list of known codes
- [pyvizio](https://github.com/vkorn/pyvizio) - Python reference implementation

## Contributing

If you successfully add CC or other buttons:
1. Document the exact CODESET and CODE values that worked
2. Note your TV model and firmware version
3. Submit a pull request or issue with your findings
4. Help others by sharing your discovery process

This helps build a more complete database of working key codes across different Vizio TV models.
