import RPi.GPIO as GPIO
import subprocess
import time
import threading
import random
import os

# ---------------- GPIO SETUP ----------------
GPIO.setmode(GPIO.BOARD)  # using BOARD layout
PAIR_BTN = 29
START_BTN = 26
PLAY_BTN = 31  # new backup audio button

GPIO.setup(PAIR_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(START_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PLAY_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ---------------- CONFIG ----------------
DEVICE_MAC = "{MAC_ADRESS}"
CONNECTED_SOUND = "/usr/share/sounds/alsa/Front_Center.wav"
SENSOR_SCRIPT = "/opt/sensor/sensor.py"
AUDIO_DIR = "/home/{USER}"  # where your audio files are stored

# ---------------- FUNCTION TO CONNECT SPEAKER ----------------
def connect_speaker():
    print("Connecting Bluetooth speaker...")
    try:
        subprocess.run(["bluetoothctl", "connect", DEVICE_MAC], check=True)
        time.sleep(2)  # wait for A2DP to initialize

        sinks_output = subprocess.check_output(["pactl", "list", "short", "sinks"]).decode()
        sink_name = None
        for line in sinks_output.splitlines():
            if "bluez_output" in line:
                sink_name = line.split()[1]
                break

        if not sink_name:
            print("No Bluetooth sink found!")
            return

        subprocess.run(["pactl", "suspend-sink", sink_name, "0"])
        subprocess.run(["pactl", "set-default-sink", sink_name])
        time.sleep(1)

        subprocess.run(["aplay", CONNECTED_SOUND])
        print("Speaker connected and ready.")
    except subprocess.CalledProcessError as e:
        print("Error connecting speaker:", e)

# ---------------- FUNCTION TO START SENSOR SCRIPT ----------------
sensor_process = None
def start_sensor_script():
    global sensor_process
    if sensor_process and sensor_process.poll() is None:
        print("Sensor script already running.")
        return
    print("Starting sensor script...")
    sensor_process = subprocess.Popen(["python3", SENSOR_SCRIPT])
    print("Sensor script started.")

# ---------------- FUNCTION TO PLAY RANDOM AUDIO ----------------
def play_random_audio():
    supported = (".wav", ".ogg")
    files = [f for f in os.listdir(AUDIO_DIR) if f.lower().endswith(supported)]
    if not files:
        print("No audio files found in", AUDIO_DIR)
        return

    audio_file = os.path.join(AUDIO_DIR, random.choice(files))
    print(f"Playing (manual trigger): {os.path.basename(audio_file)}")
    subprocess.run(["aplay", audio_file])  # blocking, but in thread → safe

# ---------------- BUTTON CALLBACKS ----------------
def pair_button_pressed(channel):
    threading.Thread(target=connect_speaker, daemon=True).start()

def start_button_pressed(channel):
    threading.Thread(target=start_sensor_script, daemon=True).start()

def play_button_pressed(channel):
    threading.Thread(target=play_random_audio, daemon=True).start()

# ---------------- SETUP EVENTS ----------------
GPIO.add_event_detect(PAIR_BTN, GPIO.FALLING, callback=pair_button_pressed, bouncetime=300)
GPIO.add_event_detect(START_BTN, GPIO.FALLING, callback=start_button_pressed, bouncetime=300)
GPIO.add_event_detect(PLAY_BTN, GPIO.FALLING, callback=play_button_pressed, bouncetime=300)

print("Button listener running. Press buttons to connect speaker, start sensor, or play audio.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    if sensor_process:
        sensor_process.terminate()
    print("Exiting.")