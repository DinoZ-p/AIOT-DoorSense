"""
PC Server: Receives JSON requests from ESP32, fetches photos and sends emails
"""

from flask import Flask, request, jsonify
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
import threading
import socket
import random
import string
from datetime import datetime
import cv2
import numpy as np
from io import BytesIO
import base64

app = Flask(__name__)

# Temporary password storage (password: creation time)
temp_passwords = {}

# Mobile command queue (for ESP32 polling)
mobile_command_queue = []

# PIR face detection processing status lock (prevent duplicate processing)
face_detection_in_progress = False
face_detection_lock = threading.Lock()

# ESP32 website address
IMAGE_URL = "http://10.76.135.201"

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "shimuguoyuan@gmail.com"
SMTP_PASSWORD = "yfxgacvriyaafnpm"
EMAIL_TO = "tonyshtarkz@gmail.com"

# Common image paths to try
POSSIBLE_PATHS = [
    "",           # Direct root path access
    "/capture",   # Common path
    "/photo.jpg",
    "/image.jpg",
    "/snapshot",
    "/camera",
    "/jpg",
    "/photo",
]

def detect_faces_in_image(image_data):
    """Detect if there are faces in the image"""
    try:
        # Convert byte data to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print("✗ Cannot decode image")
            return False
        
        # Load face detector (Haar Cascade)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale (face detection requires grayscale)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,  # Image scale factor
            minNeighbors=5,    # Minimum neighbors
            minSize=(30, 30)   # Minimum face size
        )
        
        if len(faces) > 0:
            print("✓ Detected {} face(s)".format(len(faces)))
            return True
        else:
            print("✗ No face detected")
            return False
            
    except Exception as e:
        print("✗ Face detection error: {}".format(e))
        return False

def get_image_from_esp32(url, max_retries=3):
    """Get photo from ESP32 website"""
    for attempt in range(max_retries):
        for path in POSSIBLE_PATHS:
            full_url = url + path if path else url
            try:
                print("Trying to fetch photo from {}... (attempt {}/{})".format(full_url, attempt + 1, max_retries))
                response = requests.get(full_url, timeout=30, stream=True)
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Check if it's an image
                    if 'image' in content_type or path.endswith(('.jpg', '.jpeg', '.png')):
                        image_data = response.content
                        print("✓ Photo fetched successfully, size: {} bytes".format(len(image_data)))
                        response.close()
                        return image_data, full_url
                    else:
                        response.close()
                        
            except Exception as e:
                print("Error: {}, trying next path...".format(e))
                continue
        
        if attempt < max_retries - 1:
            print("Waiting 3 seconds before retry...")
            time.sleep(3)
    
    print("✗ All attempts failed")
    return None, None

def send_email_smtp(image_data, image_filename, to_email):
    """Send email using SMTP"""
    try:
        print("Sending email to {}...".format(to_email))
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = "ESP32 Photo"
        
        # Email body
        body = "This is a photo fetched from ESP32 website.\n\nPhoto file: {}".format(image_filename)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Add image attachment
        attachment = MIMEBase('image', 'jpeg')
        attachment.set_payload(image_data)
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=image_filename)
        msg.attach(attachment)
        
        # Connect to SMTP server and send
        print("Connecting to SMTP server {}:{}...".format(SMTP_SERVER, SMTP_PORT))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        print("Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("Sending email...")
        text = msg.as_string()
        server.sendmail(SMTP_USER, to_email, text)
        server.quit()
        
        print("✓ Email sent successfully!")
        return True
        
    except Exception as e:
        print("✗ Email sending failed: {}".format(e))
        return False

def process_request_with_face_detection():
    """Process request: Wait 0.5 seconds, then fetch one photo per second, detect faces, send email only if at least 2 photos have faces detected"""
    global face_detection_in_progress
    
    # Set processing flag
    with face_detection_lock:
        if face_detection_in_progress:
            print("\n⚠️  Face detection in progress, ignoring this request")
            return False, "Face detection in progress"
        face_detection_in_progress = True
    
    try:
        print("\n" + "=" * 50)
        print("Starting PIR trigger request processing...")
        print("Waiting 0.5 seconds before starting face detection")
        print("Will perform face detection (1 image per second, 3 seconds total)")
        print("New PIR trigger requests will be ignored during this period")
        print("=" * 50)
        
        # Wait 0.5 seconds before starting detection
        print("Waiting 0.5 seconds...")
        time.sleep(0.5)
        print("Starting face detection")
        
        face_detection_results = []  # Store face detection result for each image
        captured_images = []  # Store captured image data
        
        # Fetch one photo per second for 3 seconds
        for i in range(3):
            print("\n--- Detection {}/3 ---".format(i + 1))
            print("Fetching photo...")
            
            image_data, image_url = get_image_from_esp32(IMAGE_URL)
            
            if image_data:
                # Detect faces
                print("Detecting faces...")
                has_face = detect_faces_in_image(image_data)
                face_detection_results.append(has_face)
                captured_images.append((image_data, image_url))
                
                if has_face:
                    print("✓ Detection {}: Face detected".format(i + 1))
                else:
                    print("✗ Detection {}: No face detected".format(i + 1))
            else:
                print("✗ Detection {}: Photo fetch failed".format(i + 1))
                face_detection_results.append(False)
                captured_images.append((None, None))
            
            # If not the last time, wait 1 second
            if i < 2:
                print("Waiting 1 second before next detection...")
                time.sleep(1)
        
        # Count number of detections with faces
        face_detected_count = sum(face_detection_results)
        
        # Check if at least 2 photos have faces detected
        print("\n" + "=" * 50)
        print("Face detection results summary:")
        print("=" * 50)
        for i, result in enumerate(face_detection_results, 1):
            status = "✓ Face detected" if result else "✗ No face detected"
            print("Detection {}: {}".format(i, status))
        print("Faces detected: {}/3".format(face_detected_count))
        
        if face_detected_count >= 2:
            print("\n✓ At least 2 photos have faces detected!")
            
            # Find the last photo with face detected, if none use the 3rd photo
            photo_to_send_index = -1
            for i in range(len(face_detection_results) - 1, -1, -1):
                if face_detection_results[i]:
                    photo_to_send_index = i
                    break
            
            # If no photo with face found, use the 3rd photo
            if photo_to_send_index == -1:
                photo_to_send_index = 2
            
            print("Sending photo from detection {}...".format(photo_to_send_index + 1))
            
            # Send selected photo
            if captured_images[photo_to_send_index][0] is not None:
                filename = "esp32_image_{}.jpg".format(int(time.time()))
                email_success = send_email_smtp(captured_images[photo_to_send_index][0], filename, EMAIL_TO)
                
                if email_success:
                    print("\n" + "=" * 50)
                    print("✓ Processing completed!")
                    print("Photo URL: {}".format(captured_images[photo_to_send_index][1]))
                    print("Email sent to: {}".format(EMAIL_TO))
                    print("=" * 50)
                    return True, "At least 2 photos have faces detected, email sent"
                else:
                    return False, "At least 2 photos have faces detected, but email sending failed"
            else:
                return False, "At least 2 photos have faces detected, but photo fetch failed"
        else:
            print("\n✗ Only {} photo(s) have faces detected (need at least 2), not sending email".format(face_detected_count))
            return False, "Only {} photo(s) have faces detected, conditions not met".format(face_detected_count)
    finally:
        # Clear processing flag
        with face_detection_lock:
            face_detection_in_progress = False
            print("\n✓ Face detection processing completed, lock released, ready to receive new PIR trigger requests")

def process_request():
    """Process request: Fetch photo and send email (old version, kept for compatibility)"""
    print("\n" + "=" * 50)
    print("Starting request processing...")
    print("=" * 50)
    
    # 1. Fetch photo
    image_data, image_url = get_image_from_esp32(IMAGE_URL)
    
    if image_data:
        # 2. Send email
        filename = "esp32_image_{}.jpg".format(int(time.time()))
        email_success = send_email_smtp(image_data, filename, EMAIL_TO)
        
        if email_success:
            print("\n" + "=" * 50)
            print("✓ Processing completed!")
            print("Photo URL: {}".format(image_url))
            print("Email sent to: {}".format(EMAIL_TO))
            print("=" * 50)
            return True, "Photo fetched successfully, email sent"
        else:
            return False, "Photo fetched successfully, but email sending failed"
    else:
        return False, "Photo fetch failed"

@app.route('/trigger', methods=['POST'])
def trigger():
    """Receive ESP32 PIR trigger request (with face detection)"""
    try:
        data = request.get_json()
        print("\nReceived ESP32 PIR trigger request:")
        print("  Action: {}".format(data.get('action', 'unknown')))
        print("  Timestamp: {}".format(data.get('timestamp', 'unknown')))
        print("  Device: {}".format(data.get('device', 'unknown')))
        
        # Check if face detection is in progress
        with face_detection_lock:
            if face_detection_in_progress:
                print("⚠️  Face detection in progress, ignoring this PIR trigger request")
                return jsonify({
                    "status": "busy",
                    "message": "Face detection in progress, ignoring this request"
                }), 200
        
        # Process face detection and email sending in background thread to avoid blocking response
        thread = threading.Thread(target=process_request_with_face_detection)
        thread.daemon = True
        thread.start()
        
        # Return response immediately
        return jsonify({
            "status": "success",
            "message": "PIR trigger received, face detection in progress..."
        }), 200
        
    except Exception as e:
        print("Error processing request: {}".format(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "server": "running"
    }), 200

@app.route('/generate_temp_password', methods=['POST'])
def generate_temp_password():
    """Generate temporary password"""
    try:
        # Generate 6-digit temporary password
        temp_password = ''.join(random.choices(string.digits, k=6))
        temp_passwords[temp_password] = time.time()
        
        # Display temporary password in console
        print("\n" + "=" * 50)
        print("🔑 Temporary password generated")
        print("=" * 50)
        print("Temporary password: {}".format(temp_password))
        print("Current temporary password count: {}".format(len(temp_passwords)))
        print("=" * 50)
        
        return jsonify({
            "status": "success",
            "temp_password": temp_password,
            "message": "Temporary password generated"
        }), 200
    except Exception as e:
        print("Error generating temporary password: {}".format(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/verify_temp_password', methods=['POST'])
def verify_temp_password():
    """Verify temporary password"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({
                "status": "error",
                "message": "Password cannot be empty"
            }), 400
        
        # Check if it's a temporary password
        if password in temp_passwords:
            # Password exists, delete after use
            del temp_passwords[password]
            print("\n" + "=" * 50)
            print("✅ Temporary password verification successful")
            print("=" * 50)
            print("Password: {}".format(password))
            print("Password destroyed")
            print("Remaining temporary password count: {}".format(len(temp_passwords)))
            print("=" * 50)
            
            return jsonify({
                "status": "success",
                "valid": True,
                "message": "Temporary password correct, destroyed"
            }), 200
        else:
            print("\n❌ Temporary password verification failed: {}".format(password))
            return jsonify({
                "status": "success",
                "valid": False,
                "message": "Password incorrect or already used"
            }), 200
            
    except Exception as e:
        print("Error verifying temporary password: {}".format(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/list_temp_passwords', methods=['GET'])
def list_temp_passwords():
    """List all temporary passwords (for debugging)"""
    return jsonify({
        "status": "success",
        "temp_passwords": list(temp_passwords.keys()),
        "count": len(temp_passwords)
    }), 200

def add_command_to_queue(command):
    """Add command to queue (for ESP32 to fetch)"""
    command_data = {
        "command": command,
        "timestamp": time.time(),
        "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    mobile_command_queue.append(command_data)
    
    # Keep only the last 10 commands
    if len(mobile_command_queue) > 10:
        mobile_command_queue.pop(0)
    
    # Print received command
    print("\n" + "=" * 50)
    print("📱 Mobile command received")
    print("=" * 50)
    print("Command: {}".format(command))
    print("Time: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("=" * 50)

@app.route('/unlock', methods=['GET'])
def receive_unlock():
    """Receive unlock command (GET request)"""
    add_command_to_queue('unlock')
    return "Command received: unlock", 200

@app.route('/lock', methods=['GET'])
def receive_lock():
    """Receive lock command (GET request)"""
    add_command_to_queue('lock')
    return "Command received: lock", 200

@app.route('/change_password', methods=['GET'])
def receive_change_password():
    """Receive change password command (GET request)"""
    password = request.args.get('password', '')
    
    if not password:
        return "Error: missing password parameter", 400
    
    if not password.isdigit():
        return "Error: password must be numeric", 400
    
    # Send command and new password together to ESP32
    command_with_data = "change_password:{}".format(password)
    add_command_to_queue(command_with_data)
    return "Command received: change_password, new password: {}".format(password), 200

@app.route('/take_photo', methods=['GET'])
def receive_take_photo():
    """Receive take_photo command (GET request), execute photo capture and send email"""
    add_command_to_queue('take_photo')
    
    # Process photo capture and email sending in background thread
    thread = threading.Thread(target=process_request)
    thread.daemon = True
    thread.start()
    
    return "Command received: take_photo, processing...", 200

@app.route('/mobile_command', methods=['POST'])
def receive_mobile_command():
    """Receive command from mobile (JSON format)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "Request body is empty"
            }), 400
        
        command = data.get('command', '')
        
        if not command:
            return jsonify({
                "status": "error",
                "message": "Command cannot be empty"
            }), 400
        
        # Special handling for display_text command: needs text content
        if command == "display_text":
            text = data.get('text', '')
            if not text:
                return jsonify({
                    "status": "error",
                    "message": "Text content cannot be empty"
                }), 400
            
            # Send command and text content together to ESP32
            command_with_data = "display_text:{}".format(text)
            add_command_to_queue(command_with_data)
            
            print("\n" + "=" * 50)
            print("📱 Received display_text command")
            print("=" * 50)
            print("Text content: {}".format(text))
            print("=" * 50)
            
            return jsonify({
                "status": "success",
                "message": "Display text command received",
                "command": command,
                "text": text
            }), 200
        
        # Special handling for take_photo command: fetch photo and return to iOS app (no email)
        if command == "take_photo":
            print("\n" + "=" * 50)
            print("📱 Received take_photo command (from iOS app)")
            print("=" * 50)
            print("Fetching photo...")
            
            # Fetch photo
            image_data, image_url = get_image_from_esp32(IMAGE_URL)
            
            if image_data:
                # Encode image data as base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                print("✓ Photo fetched successfully, size: {} bytes".format(len(image_data)))
                print("=" * 50)
                
                return jsonify({
                    "status": "success",
                    "message": "Photo fetched successfully",
                    "command": command,
                    "image_base64": image_base64,
                    "image_size": len(image_data)
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Photo fetch failed"
                }), 500
        
        # Other commands added to queue for ESP32 to fetch
        add_command_to_queue(command)
        
        return jsonify({
            "status": "success",
            "message": "Command received",
            "command": command
        }), 200
        
    except Exception as e:
        print("Error processing mobile command: {}".format(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/get_mobile_command', methods=['GET'])
def get_mobile_command():
    """ESP32 gets mobile command (polling method)"""
    if mobile_command_queue:
        # Return earliest command and remove it
        command = mobile_command_queue.pop(0)
        return jsonify({
            "status": "success",
            "has_command": True,
            "command": command["command"],
            "timestamp": command["timestamp"]
        }), 200
    else:
        # No pending commands, return simple response (reduce log output)
        return jsonify({
            "status": "success",
            "has_command": False,
            "command": None
        }), 200

def get_local_ip():
    """Get local IP address"""
    try:
        # Create a UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # No need to actually connect, just use it to get local IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Fallback method: use hostname
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return "Unable to get IP"

if __name__ == '__main__':
    # Get local IP address
    local_ip = get_local_ip()
    
    print("=" * 50)
    print("ESP32 Photo Email Server")
    print("=" * 50)
    print("Starting server...")
    print("Local IP address: {}".format(local_ip))
    print("Listening address: http://0.0.0.0:8080")
    print("Server URL: http://{}:8080".format(local_ip))
    print("Trigger endpoint: POST /trigger")
    print("Health check: GET /health")
    print("Generate temp password: POST /generate_temp_password")
    print("Verify temp password: POST /verify_temp_password")
    print("Mobile commands: GET /unlock, GET /lock")
    print("Change password: GET /change_password?password=[digits]")
    print("Take photo: GET /take_photo")
    print("Mobile command (JSON): POST /mobile_command")
    print("ESP32 get command: GET /get_mobile_command")
    print("\nFeature description:")
    print("- PIR trigger: Wait 0.5 seconds, then capture one image per second, detect faces, for 3 seconds")
    print("- Email sent only if at least 2 photos have faces detected")
    print("\nWaiting for ESP32 and mobile requests...")
    print("Please enter the following IP address in ESP32 client:")
    print(">>> {}".format(local_ip))
    print("=" * 50)
    
    # Run Flask server
    app.run(host='0.0.0.0', port=8080, debug=False)

