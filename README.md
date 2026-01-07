# Smart Door Lock System

An intelligent IoT door lock system that integrates ESP32 microcontrollers, a Python Flask server, and an iOS mobile application. The system features motion detection, face recognition, password authentication, and voice-controlled remote access.

## Getting Started

### Prerequisites

- Python 3.7 or later
- MicroPython firmware for ESP32
- Xcode 14.0 or later (for iOS app)
- Google Gemini API key (for voice recognition)
- WiFi network (all devices must be on the same network)

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install flask opencv-python numpy requests
   ```

2. **Configure Python server (`server_image_email.py`):**
   ```python
   IMAGE_URL = "http://YOUR_CAMERA_IP"  # ESP32 camera IP
   SMTP_USER = "your_email@gmail.com"
   SMTP_PASSWORD = "your_app_password"  # Gmail app password
   EMAIL_TO = "recipient@email.com"
   ```

3. **Configure ESP32 client (`esp32_keypad_client.py`):**
   ```python
   WIFI_SSID = "Your_WiFi_SSID"
   WIFI_PASSWORD = "Your_WiFi_Password"
   ```

4. **Setup iOS app:**
   - Open `aiot_door/aiot_door.xcodeproj` in Xcode
   - Get Gemini API key from: https://makersuite.google.com/app/apikey

### Running

1. **Start Python server:**
   ```bash
   python server_image_email.py
   ```
   Note the server IP address displayed.

2. **Run ESP32 client:**
   - Upload `esp32_keypad_client.py` to ESP32
   - Enter server IP when prompted

3. **Launch iOS app:**
   - Build and run in Xcode
   - Enter server IP and Gemini API key in settings

## System Overview

This project implements a three-tier distributed architecture:

- **ESP32 Main Board**: Hardware control hub with sensors and I/O devices
- **ESP32 Camera Module**: Independent camera device serving images via HTTP
- **PC Server**: Central processing unit handling AI/ML tasks and coordination
- **iOS Mobile App**: User interface for remote control and monitoring
- **WiFi Network**: Communication backbone connecting all devices

## Features

### Core Functionality

1. **Motion Detection & Face Recognition**
   - PIR sensor detects motion
   - Server captures 3 images (1 per second) from ESP32 camera
   - OpenCV face detection using Haar Cascade
   - Email notification sent if at least 2 images contain faces

2. **Password Authentication**
   - Global master password (default: "123")
   - Temporary password generation (6-digit, one-time use)
   - Password verification via keypad input
   - Visual feedback on OLED display
   - Audio feedback via buzzer

3. **Mobile Control**
   - Remote lock/unlock commands
   - Password change functionality
   - Photo capture and display
   - Custom text display on OLED
   - Voice command recognition using Google Gemini API

## Project Structure

```
fproject/
├── esp32_keypad_client.py      # ESP32 main board client code
├── server_image_email.py        # Python Flask server
├── aiot_door/                   # iOS mobile application
│   └── aiot_door/
│       └── ViewController.swift # Main iOS app controller
├── CameraWebServer/            # ESP32 camera web server code
└── README.md                    # This file
```

## Usage

### System Operation

**Password Unlock:** Press "A" on keypad → Enter password → Press "#" → System verifies and unlocks

**Motion Detection:** PIR detects motion → ESP32 sends trigger → Server fetches 3 images → Face detection → Email sent if ≥2 faces detected

**Mobile Control:** Tap button in iOS app → Server queues command → ESP32 polls and executes

**Voice Command:** Record audio → Gemini transcribes → Command parsed and executed

## API Endpoints

### Server Endpoints

- `POST /trigger` - PIR motion trigger (from ESP32)
- `POST /generate_temp_password` - Generate temporary password
- `POST /verify_temp_password` - Verify temporary password
- `POST /mobile_command` - Receive mobile command (JSON)
- `GET /get_mobile_command` - ESP32 polls for commands
- `GET /health` - Health check

### Command Queue System

Commands are queued on the server and retrieved by ESP32 via polling:
- ESP32 polls every 1 second
- Commands are FIFO (first in, first out)
- Queue stores up to 10 commands

## Troubleshooting

- **Connection issues:** Ensure all devices are on the same WiFi network
- **Camera images:** Verify camera IP in `IMAGE_URL` and test in browser
- **Email:** Use Gmail app password (not account password)
- **Face detection:** Check lighting and camera focus

## License

This project is developed for educational purposes.

## Authors

- Lizhong Wang (lw3225@columbia.edu)
- Zhenghang Zhao (zz3410@columbia.edu)
- Yankun Li (yl6022@columbia.edu)
- Zhang Shurong (sz3397@columbia.edu)

Team 3 - Columbia University

## Acknowledgments

- Flask Development Team
- OpenCV Development Team
- MicroPython Development Team
- Google AI (Gemini API)
- Apple Inc. (iOS Development Tools)

