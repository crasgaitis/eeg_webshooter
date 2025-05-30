# eeg_webshooter

# Instructions:

0. Plug in Arduino.
1. Open device manager to check which com port is in use. (i.e. COM3)
2. Open the Arduino IDE to (1) compile and (2) upload the code in arduino.cpp file. Make sure you're using the right port. Make sure the serial monitor is closed.
3. Turn on the Muse EEG. Open Petal Metrics and click stream. Wait until it says "streaming."
4. Go to the app.py file and set the ESC_ON flag to `True`.
5. Activate the webshooter environment with `conda activate eeg_webshooter`.
6. Run the application with `python app.py`.
7. Go to `https://127.0.0.1.:5000` in your preferred browser.

# Project Overview:
![image](https://github.com/user-attachments/assets/eb3bc7a3-c32d-4d51-acd3-e73279b86535)

The Spiderman EEG-Controlled Web Shooter project aims to create a functional prototype of Spiderman's iconic web shooters, controlled by EEG (electroencephalogram) signals. This project integrates mechanical design, signal processing, and neural control to allow users to operate the web shooters using brain waves. Commands will include launching the web, adjusting the length of the web, and reloading the shooter.

# Key Components

# Mechanical Design
Shooter Mechanism: Develop a mechanism for propelling the web, including the flywheel system.

Reloading Mechanism: Design and implement a system for reloading the shooter with new web projectiles.

Ball and Web Design for Release: Determine the design of the ball/web that is fired from the shooter, ensuring it is lightweight and aerodynamic.

# Neural Control
EEG Recording System: Set up an EEG system to capture brain activity signals, which will control the web shooter.

Signal Processing & Feature Engineering: Process EEG signals to extract meaningful features for user intent detection.

EEG to Commands: Translate the processed EEG data into commands such as launching the web, adjusting web length, and reloading.
