# -*- coding: utf-8 -*-
import os
import time
import random
import pygame
import RPi.GPIO as GPIO

# --- SETTINGS ---
TRIG = 18
ECHO = 24
THRESHOLD_CM = 150           # trigger distance (1.5 m)
AUDIO_DIR = "/home/pi"       # folder with audio files
FADE_MS = 1000               # fade-in/out time in milliseconds

# --- OS Directory Setup ---
os.chdir("/opt/sensor")  # ensures relative paths work

# --- GPIO SETUP ---
GPIO.setmode(GPIO.BOARD)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# --- AUDIO SETUP ---
mixer_initialized = False

def init_mixer():
    """Initialize pygame mixer once."""
    global mixer_initialized
    if not mixer_initialized:
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(1.0)
            mixer_initialized = True
            print("Audio initialized")
        except Exception as e:
            print("Audio init failed:", e)

def entfernung():
    """Measure distance using HC-SR04"""
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start = time.time()
    while GPIO.input(ECHO) == 0:
        start = time.time()
    while GPIO.input(ECHO) == 1:
        stop = time.time()

    elapsed = stop - start
    return (elapsed * 34300) / 2  # cm

def get_random_audio():
    """Pick a random audio file from AUDIO_DIR"""
    supported = (".wav", ".ogg")
    files = [f for f in os.listdir(AUDIO_DIR) if f.lower().endswith(supported)]
    return os.path.join(AUDIO_DIR, random.choice(files)) if files else None

def play_audio():
    """Play random audio with fade-in if not already playing"""
    init_mixer()
    if not pygame.mixer.music.get_busy():
        audio_file = get_random_audio()
        if not audio_file:
            print("o audio files found in", AUDIO_DIR)
            return
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play(fade_ms=FADE_MS)
            print(f"laying: {os.path.basename(audio_file)}")
        except Exception as e:
            print("Playback failed:", e)
    else:
        print("Audio already playing, ignoring trigger")

# --- MAIN LOOP ---
try:
    print("Starting sensor loop...")
    init_mixer()  # initialize once right away
    while True:
        dist = entfernung()
        print(f"Entfernung: {dist:.1f} cm")

        if dist < THRESHOLD_CM:
            play_audio()

        time.sleep(0.5)

except KeyboardInterrupt:
    print("Beendet.")
finally:
    if mixer_initialized:
        pygame.mixer.music.fadeout(FADE_MS)
        time.sleep(1)
        pygame.mixer.quit()
    GPIO.cleanup()
    print("Clean exit.")