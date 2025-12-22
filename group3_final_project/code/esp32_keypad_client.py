"""
ESP32 client: Sends JSON request to PC server when PIR sensor detects person
Includes password unlock functionality
"""

import machine
import network
import urequests
import time
import json

# OLED configuration
PIN_SCL = 22
PIN_SDA = 20

# WiFi configuration
WIFI_SSID = "Columbia University"
WIFI_PASSWORD = ""

# Server configuration (will prompt user input at runtime)
SERVER_PORT = 8080
SERVER_IP = None  # Will be input at runtime
SERVER_URL = None

# PIR sensor pin
PIR_PIN = 26  # PIR sensor connected to GPIO26

# Buzzer pin
BUZZER_PIN = 15  # Buzzer connected to GPIO15

# Keypad pin definitions
ROW_PINS = [27, 33, 25, 19]  # Row pins (output)
COL_PINS = [32, 4, 8, 21]   # Column pins (input with pull-up)

# Keypad mapping
KEYS = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Password configuration (global variable, can be modified)
CORRECT_PASSWORD = "123"  # Default master password

def init_oled():
    """Initialize OLED display (128x32)"""
    try:
        from ssd1306 import SSD1306_I2C
        i2c = machine.I2C(0, scl=machine.Pin(PIN_SCL), sda=machine.Pin(PIN_SDA), freq=400000)
        oled = SSD1306_I2C(128, 32, i2c)
        oled.fill(0)  # Clear screen
        oled.text("System Ready", 0, 0)
        oled.text("Initializing...", 0, 12)
        oled.show()
        print("OLED initialized successfully")
        return oled
    except Exception as e:
        print("OLED initialization failed: {}".format(e))
        print("Please ensure ssd1306 library is installed: upip.install('micropython-ssd1306')")
        return None

def display_default_status(oled):
    """Display default status prompt"""
    if oled is None:
        return
    
    try:
        oled.fill(0)  # Clear screen
        oled.text("Press A to enter", 0, 0)
        oled.text("password", 0, 8)
        oled.text("# to finish", 0, 16)
        oled.text("B to back", 0, 24)
        oled.show()
    except Exception as e:
        print("OLED display error: {}".format(e))

def display_unlock_status(oled, status, password_type=""):
    """Display unlock status on OLED (automatically returns to default after 3 seconds)"""
    if oled is None:
        return
    
    try:
        oled.fill(0)  # Clear screen
        if status:
            oled.text("DOOR UNLOCKED", 0, 0)
            if password_type:
                oled.text("Type: " + password_type, 0, 12)
            oled.text("Access Granted", 0, 24)
        else:
            oled.text("DOOR LOCKED", 0, 0)
            oled.text("Access Denied", 0, 12)
        oled.show()
    except Exception as e:
        print("OLED display error: {}".format(e))

def display_command_status(oled, command):
    """Display command status on OLED"""
    if oled is None:
        return
    
    try:
        oled.fill(0)  # Clear screen
        oled.text(command.upper(), 0, 0)
        oled.text("From Mobile", 0, 12)
        oled.text("Processing...", 0, 24)
        oled.show()
    except Exception as e:
        print("OLED display error: {}".format(e))

def display_custom_text(oled, text):
    """Display custom text on OLED"""
    if oled is None:
        return
    
    try:
        oled.fill(0)  # Clear screen
        
        # Process text display (128x32 OLED, approximately 21 characters per line)
        # Split text into multiple lines
        lines = []
        current_line = ""
        
        for char in text:
            # If current line plus new character exceeds 21 characters, start a new line
            if len(current_line) >= 21:
                lines.append(current_line)
                current_line = char
            else:
                current_line += char
        
        if current_line:
            lines.append(current_line)
        
        # Display at most 3 lines (32 pixel height, approximately 10 pixels per line)
        display_lines = lines[:3]
        y_positions = [0, 11, 22]
        
        for i, line in enumerate(display_lines):
            if i < len(y_positions):
                oled.text(line[:21], 0, y_positions[i])  # Ensure no more than 21 characters
        
        oled.show()
    except Exception as e:
        print("OLED custom text display error: {}".format(e))

def display_password_input(oled, password_length):
    """Display password input on OLED (shown as asterisks)"""
    if oled is None:
        return
    
    try:
        oled.fill(0)  # Clear screen
        oled.text("Enter Password", 0, 0)
        # Display asterisks, at most 12 characters (128 pixel width limit)
        display_text = "*" * min(password_length, 12)
        if password_length > 12:
            display_text = "*" * 12  # Only show first 12
        oled.text(display_text, 0, 12)
        oled.text("Len: {}".format(password_length), 0, 24)
        oled.show()
    except Exception as e:
        print("OLED display error: {}".format(e))

def connect_wifi(ssid, password):
    """Connect to WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(ssid, password)
        
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="")
        
        if wlan.isconnected():
            print("\nWiFi connected successfully!")
            print("IP address:", wlan.ifconfig()[0])
            return True
        else:
            print("\nWiFi connection failed!")
            return False
    else:
        print("WiFi already connected")
        print("IP address:", wlan.ifconfig()[0])
        return True

def beep_buzzer(buzzer_pin, duration_ms=200, frequency=2000):
    """Make buzzer beep once, using PWM to increase volume"""
    try:
        # Use PWM to generate sound, louder volume
        buzzer_pwm = machine.PWM(buzzer_pin)
        buzzer_pwm.freq(frequency)  # Set frequency (Hz)
        buzzer_pwm.duty(512)  # Set duty cycle 50%, louder volume
        time.sleep_ms(duration_ms)
        buzzer_pwm.duty(0)  # Stop
        buzzer_pwm.deinit()  # Release PWM resources
    except:
        # If PWM fails, use simple high/low level
        buzzer_pin.value(1)
        time.sleep_ms(duration_ms)
        buzzer_pin.value(0)

def scan_keypad(rows, cols):
    """Scan keypad, return pressed key (improved version)"""
    key = None
    
    # Scan each row
    for i, row in enumerate(rows):
        row.value(0)  # Pull current row low
        time.sleep_us(20)
        
        # Check each column
        for j, col in enumerate(cols):
            if col.value() == 0:  # Column pulled low, key pressed
                key = KEYS[i][j]
                break
        
        row.value(1)  # Restore row
        if key:
            break
    
    return key

def verify_temp_password(server_url, password):
    """Verify temporary password with server"""
    try:
        request_data = {
            "password": password
        }
        
        headers = {"Content-Type": "application/json"}
        response = urequests.post(
            server_url + "/verify_temp_password",
            json=request_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json() if hasattr(response, 'json') else {}
            response.close()
            return result.get('valid', False)
        else:
            print("✗ Verification failed, status code: {}".format(response.status_code))
            response.close()
            return False
    except OSError as e:
        # Network errors in MicroPython
        error_code = e.args[0] if e.args else "unknown"
        print("✗ Network error during verification (code {}): {}".format(error_code, e))
        return False
    except Exception as e:
        print("✗ Error verifying temporary password: {}".format(e))
        return False

def generate_temp_password(server_url):
    """Request server to generate temporary password"""
    try:
        headers = {"Content-Type": "application/json"}
        full_url = server_url + "/generate_temp_password"
        print("Connecting to: {}".format(full_url))
        
        response = urequests.post(
            full_url,
            headers=headers,
            timeout=10
        )
        
        print("Response status code: {}".format(response.status_code))
        
        if response.status_code == 200:
            try:
                result = response.json() if hasattr(response, 'json') else {}
                response.close()
                temp_password = result.get('temp_password', '')
                if temp_password:
                    print("\n" + "=" * 40)
                    print("✓ Temporary password generated: {}".format(temp_password))
                    print("=" * 40)
                    return temp_password
                else:
                    print("✗ No temp_password in response")
                    print("Response content: {}".format(result))
            except Exception as json_error:
                print("✗ Error parsing JSON response: {}".format(json_error))
                print("Response text: {}".format(response.text))
                response.close()
        else:
            print("✗ Server returned status code: {}".format(response.status_code))
            try:
                response_text = response.text
                print("Response text: {}".format(response_text))
            except:
                pass
            response.close()
        return None
    except OSError as e:
        # Network errors in MicroPython
        error_code = e.args[0] if e.args else "unknown"
        print("✗ Network error (code {}): {}".format(error_code, e))
        print("Please check:")
        print("  1. Server is running on {}".format(server_url))
        print("  2. WiFi connection is stable")
        print("  3. Server IP address is correct")
        return None
    except Exception as e:
        error_type = type(e).__name__
        print("✗ Error generating temporary password ({}): {}".format(error_type, e))
        if hasattr(e, 'args') and e.args:
            print("  Error code/details: {}".format(e.args))
        return None

def check_password(rows, cols, buzzer, server_url, oled):
    """Check password input"""
    password_input = ""
    last_key = None
    input_timeout = 10  # 10 second timeout
    start_time = time.time()
    
    print("\n" + "=" * 40)
    print("Please enter password (Global password: {} or temporary password)".format(CORRECT_PASSWORD))
    print("Press # to confirm, * to cancel, B to backspace")
    print("=" * 40)
    print("Current input: ", end="")
    
    # Initial OLED display
    display_password_input(oled, 0)
    
    while True:
        # Check timeout
        if time.time() - start_time > input_timeout:
            print("\nInput timeout")
            display_default_status(oled)
            return False
        
        key = scan_keypad(rows, cols)
        
        if key and key != last_key:
            print("Key pressed: {}".format(key))  # Display key content
            if key == '#':
                # Confirm input
                print("\n" + "=" * 40)
                if password_input == CORRECT_PASSWORD:
                    # Global password correct
                    print("✓ Global password correct!")
                    beep_buzzer(buzzer, 500, 2500)  # Beep 0.5 seconds, frequency 2500Hz (higher pitch)
                    display_unlock_status(oled, True, "Global")
                    print("=" * 40)
                    # Return to default after 3 seconds
                    time.sleep(3)
                    display_default_status(oled)
                    return True
                else:
                    # Check if it's a temporary password
                    print("Checking temporary password...")
                    if verify_temp_password(server_url, password_input):
                        print("✓ Temporary password correct!")
                        beep_buzzer(buzzer, 500, 2500)  # Beep 0.5 seconds
                        display_unlock_status(oled, True, "Temp")
                        print("=" * 40)
                        # Return to default after 3 seconds
                        time.sleep(3)
                        display_default_status(oled)
                        return True
                    else:
                        print("✗ Password incorrect!")
                        beep_buzzer(buzzer, 2000, 1500)  # Beep 2 seconds, frequency 1500Hz (lower pitch)
                        display_unlock_status(oled, False)
                        print("=" * 40)
                        # Return to default after 3 seconds
                        time.sleep(3)
                        display_default_status(oled)
                        return False
            elif key == '*':
                # Cancel input
                print("\nInput cancelled")
                display_default_status(oled)
                return False
            elif key == 'B':
                # Backspace: delete last character
                if len(password_input) > 0:
                    password_input = password_input[:-1]
                    print("Backspace, current input: {}".format("*" * len(password_input) if password_input else "(empty)"))
                    display_password_input(oled, len(password_input))
                    start_time = time.time()  # Reset timeout
                else:
                    print("No characters to delete")
            elif key.isdigit():
                # Digit key
                password_input += key
                print("Input: {}".format("*" * len(password_input)))
                display_password_input(oled, len(password_input))  # Update OLED display
                start_time = time.time()  # Reset timeout
            last_key = key
            # Wait for key release
            while scan_keypad(rows, cols) == key:
                time.sleep_ms(50)
        elif not key:
            last_key = None
        
        time.sleep_ms(10)

def get_mobile_command(server_url):
    """Get mobile command from server (polling)"""
    try:
        response = urequests.get(server_url + "/get_mobile_command", timeout=5)
        
        if response.status_code == 200:
            result = response.json() if hasattr(response, 'json') else {}
            response.close()
            
            if result.get('has_command', False):
                return result.get('command', None)
            return None
        else:
            response.close()
            return None
    except Exception as e:
        # Silent failure, don't print error (avoid error messages during frequent polling)
        return None

def execute_mobile_command(command, buzzer, oled):
    """Execute mobile command"""
    print("\nStarting command execution: {}".format(command))
    
    if command == "unlock":
        print("✓ Executing unlock operation")
        # Buzzer beep once
        beep_buzzer(buzzer, 500, 2500)
        print("✓ Buzzer beeped")
        # OLED display unlock
        display_command_status(oled, "unlock")
        print("✓ OLED display: UNLOCK")
        # Return to default display after 3 seconds
        time.sleep(3)
        display_default_status(oled)
        print("✓ Operation completed")
        return True
    elif command == "lock":
        print("✓ Executing lock operation")
        # Buzzer beep once
        beep_buzzer(buzzer, 500, 2500)
        print("✓ Buzzer beeped")
        # OLED display lock
        display_command_status(oled, "lock")
        print("✓ OLED display: LOCK")
        # Return to default display after 3 seconds
        time.sleep(3)
        display_default_status(oled)
        print("✓ Operation completed")
        return True
    elif command.startswith("change_password:"):
        # Change global password
        new_password = command.split(":", 1)[1]  # Get password after colon
        global CORRECT_PASSWORD
        old_password = CORRECT_PASSWORD
        CORRECT_PASSWORD = new_password
        print("✓ Executing change_password operation")
        print("  Old password: {}".format(old_password))
        print("  New password: {}".format(CORRECT_PASSWORD))
        print("✓ Global password changed")
        return True
    elif command == "take_photo":
        print("✓ Executing take_photo operation")
        print("✓ Server is processing photo capture and email sending...")
        print("✓ Operation completed (server-side processing)")
        return True
    elif command.startswith("display_text:"):
        # Display custom text
        text = command.split(":", 1)[1]  # Get text after colon
        print("✓ Executing display_text operation")
        print("  Text content: {}".format(text))
        # OLED display text
        display_custom_text(oled, text)
        print("✓ OLED display: {}".format(text))
        # Return to default display after 3 seconds
        time.sleep(3)
        display_default_status(oled)
        print("✓ Operation completed")
        return True
    else:
        print("✗ Unknown command: {}".format(command))
        return False

def send_request_to_server(url):
    """Send PIR trigger request to server (server will perform face detection)"""
    # Build JSON data
    request_data = {
        "action": "pir_trigger_face_detection",
        "timestamp": time.time(),
        "device": "ESP32",
        "trigger": "PIR_sensor"
    }
    
    try:
        print("Sending PIR trigger request to server...")
        print("Server address: {}".format(url))
        print("Server will perform face detection (1 image per second, 3 seconds total)")
        
        # Send POST request
        headers = {"Content-Type": "application/json"}
        response = urequests.post(
            url + "/trigger",
            json=request_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json() if hasattr(response, 'json') else response.text
            print("✓ Server response successful!")
            print("Response:", result)
            response.close()
            return True
        else:
            print("✗ Server response failed, status code:", response.status_code)
            print("Response:", response.text)
            response.close()
            return False
            
    except Exception as e:
        print("✗ Request error:", e)
        return False


# Main program
print("=" * 40)
print("ESP32 PIR Sensor Client")
print("=" * 40)

# Connect to WiFi
if not connect_wifi(WIFI_SSID, WIFI_PASSWORD):
    print("Cannot connect to WiFi, program exiting")
else:
    # Prompt user to enter server IP address
    print("\n" + "=" * 40)
    print("Please enter server IP address:")
    print("(Check the IP address displayed when PC server starts)")
    print("=" * 40)
    
    # In MicroPython REPL, use input() to get user input
    try:
        user_input = input("Server IP: ").strip()
        if user_input:
            SERVER_IP = user_input
            SERVER_URL = "http://{}:{}".format(SERVER_IP, SERVER_PORT)
            print("\nServer address set to: {}".format(SERVER_URL))
        else:
            print("No IP address entered, using default configuration")
            SERVER_IP = "10.206.95.176"  # Default IP (if input is empty)
            SERVER_URL = "http://{}:{}".format(SERVER_IP, SERVER_PORT)
    except:
        # If input is not available, use default IP
        print("Cannot get input, using default IP")
        SERVER_IP = "10.206.95.176"
        SERVER_URL = "http://{}:{}".format(SERVER_IP, SERVER_PORT)
    
    print("\nInitializing hardware...")
    
    # Initialize OLED
    print("OLED initialization (SCL: GPIO {}, SDA: GPIO {})...".format(PIN_SCL, PIN_SDA))
    oled = init_oled()
    
    # Initialize PIR sensor
    print("PIR sensor connected to GPIO {}".format(PIR_PIN))
    pir = machine.Pin(PIR_PIN, machine.Pin.IN)
    
    # Initialize Buzzer
    print("Buzzer connected to GPIO {}".format(BUZZER_PIN))
    buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
    buzzer.value(0)  # Initially off
    
    # Initialize Keypad
    print("Keypad initialization...")
    rows = [machine.Pin(p, machine.Pin.OUT) for p in ROW_PINS]
    cols = [machine.Pin(p, machine.Pin.IN, machine.Pin.PULL_UP) for p in COL_PINS]
    for r in rows:
        r.value(1)
    
    print("\nSystem ready!")
    print("Features:")
    print("1. PIR detects person → trigger face detection (1 image per second, 3 seconds total)")
    print("   → Email sent only if face detected 3 times consecutively")
    print("2. Enter password {} → unlock (buzzer beeps)".format(CORRECT_PASSWORD))
    print("Press Ctrl+C to stop\n")
    
    last_pir_state = 0
    detection_count = 0
    last_trigger_time = 0
    TRIGGER_COOLDOWN = 5  # 5 second cooldown to avoid repeated triggers
    
    # PIR debounce related: multiple detections within 3 seconds treated as one trigger
    pir_detection_start_time = None  # Time of first person detection (None means no pending detection)
    DEBOUNCE_INTERVAL = 3  # 3 second stabilization interval
    
    # Password input related
    last_keypad_key = None
    
    # Mobile command polling related
    last_command_check_time = 0
    COMMAND_CHECK_INTERVAL = 1  # Check mobile commands once per second
    
    print("System running...")
    print("PIR detection: only displayed when motion detected")
    print("Keypad: displayed when key pressed")
    print("Press A to enter password (global password or temporary password)")
    print("Press D to generate temporary password")
    print("-" * 40)
    
    # Display default status
    display_default_status(oled)
    
    try:
        while True:
            current_time = time.time()
            
            # Read PIR sensor state
            pir_state = pir.value()
            
            # Detect state change: low to high (person detected)
            if pir_state == 1 and last_pir_state == 0:
                # Display person detected (only shown when motion detected)
                print("\n" + "=" * 40)
                print("⚠️  Person detected!")
                print("=" * 40)
                
                # If no pending detection, or more than 3 seconds since last detection, start new detection cycle
                if pir_detection_start_time is None:
                    pir_detection_start_time = current_time
                    print("Starting detection cycle (3 second stabilization period)...")
                else:
                    # New trigger detected within 3 seconds, reset timer
                    pir_detection_start_time = current_time
                    print("New trigger detected, resetting timer (3 second stabilization period)...")
            
            # Check if should trigger: if there's a pending detection and more than 3 seconds since last detection
            if pir_detection_start_time is not None:
                time_since_last_detection = current_time - pir_detection_start_time
                
                if time_since_last_detection >= DEBOUNCE_INTERVAL:
                    # No new trigger within 3 seconds, can execute trigger operation
                    # Check cooldown time
                    if current_time - last_trigger_time >= TRIGGER_COOLDOWN:
                        detection_count += 1
                        print("\n" + "=" * 40)
                        print("[{}] Stabilization period ended, triggering face detection process...".format(detection_count))
                        print("Server will capture one image per second, detect faces, for 3 seconds")
                        print("Email will be sent if face detected 3 times consecutively")
                        print("=" * 40)
                        
                        # Send PIR trigger request to server (server will perform face detection)
                        success = send_request_to_server(SERVER_URL)
                        
                        if success:
                            print("✓ PIR trigger request sent to server")
                        else:
                            print("✗ PIR trigger request failed")
                        
                        last_trigger_time = current_time
                    else:
                        remaining = TRIGGER_COOLDOWN - (current_time - last_trigger_time)
                        print("\nDetection cycle ended, but in cooldown (need {:.1f} more seconds)".format(remaining))
                        print("Skipping this trigger")
                    
                    # Reset detection state
                    pir_detection_start_time = None
            
            # Detect state change: high to low (person left) - not displayed, only shown when motion detected
            # elif pir_state == 0 and last_pir_state == 1:
            #     print("\nPerson left")
            
            # Scan keypad (for password input)
            keypad_key = scan_keypad(rows, cols)
            
            # Display key press
            if keypad_key and keypad_key != last_keypad_key:
                print("Key pressed: {}".format(keypad_key))
            
            # Detect password input (press A to start entering password)
            if keypad_key == 'A' and keypad_key != last_keypad_key:
                # Start password input mode
                password_correct = check_password(rows, cols, buzzer, SERVER_URL, oled)
                if password_correct:
                    print("Unlock successful!")
                else:
                    print("Unlock failed!")
                # Wait for key release
                while scan_keypad(rows, cols) == 'A':
                    time.sleep_ms(50)
            
            # Detect temporary password generation (press D to generate temporary password)
            if keypad_key == 'D' and keypad_key != last_keypad_key:
                print("\n" + "=" * 40)
                print("Generating temporary password...")
                print("=" * 40)
                temp_password = generate_temp_password(SERVER_URL)
                if temp_password:
                    print("Temporary password: {}".format(temp_password))
                else:
                    print("Generation failed")
                # Wait for key release
                while scan_keypad(rows, cols) == 'D':
                    time.sleep_ms(50)
            
            last_keypad_key = keypad_key
            
            # Check mobile commands (check once per second)
            current_time = time.time()
            if current_time - last_command_check_time >= COMMAND_CHECK_INTERVAL:
                mobile_command = get_mobile_command(SERVER_URL)
                if mobile_command:
                    print("\n" + "=" * 40)
                    print("📱 Mobile command received")
                    print("=" * 40)
                    print("Command: {}".format(mobile_command))
                    print("Time: {}".format(time.time()))
                    print("=" * 40)
                    execute_mobile_command(mobile_command, buzzer, oled)
                last_command_check_time = current_time
            
            last_pir_state = pir_state
            time.sleep_ms(100)  # Check every 100ms
            
    except KeyboardInterrupt:
        print("\nProgram stopped")
        print("Total detections: {} movements".format(detection_count))

