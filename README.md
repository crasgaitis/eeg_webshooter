# eeg_webshooter

# Instructions:

0. Plug in Arduino.
1. Open device manager to check which com port is in use. (i.e. COM3)
2. Open the Arduino IDE to (1) compile and (2) upload the code in arduino_code/combo.cpp file. Make sure you're using the right port. Make sure the serial monitor is closed.
3. Turn on the Muse EEG. Open Petal Metrics or Synaptech Metrics and click stream. Wait until it says "streaming."
4. Go to the app.py file and set the ESC_ON flag to `True`.
5. Activate the webshooter environment with `conda activate eeg_webshooter`.
6. Run the application with `python app.py`.
7. Go to `https://127.0.0.1.:5000` in your preferred browser.

# Project Overview:
![image](https://github.com/user-attachments/assets/eb3bc7a3-c32d-4d51-acd3-e73279b86535)

The Spiderman EEG-Controlled Web Shooter project aims to create a functional prototype of Spiderman's iconic web shooters, controlled by EEG (electroencephalogram) signals. This project integrates mechanical design, signal processing, and neural control to allow users to operate the web shooters using brain waves. Commands will include launching the web, adjusting the length of the web, and reloading the shooter.

## Key Components

### Neural Control
We convert raw voltage traces from EEG recordings into focus scores, by computing a power spectral density estimate using Welch's method. This allows us to extract beta band activity. Using data from the calibration stage, we automatically devise a custom thresholding system to group neural activity into (1) low, (2) medium, and (3) high focus categorizations. 

### Mechanical Design
These scores are sent via serial to the microcontroller as scaled values to modulate the electronic speed controller (ESC), which in turn, accelerates the motor, spinning the flywheel. When a score over 0 is sent, the reloading mechanism is also triggered. Reloading is achieved by using a servo arm to push discs through the magazine and next to the flywheel. The rotational energy from the wheel propels projectiles forward.

![image](https://github.com/user-attachments/assets/00014717-9bd6-4081-827a-8b1c1436a5c2)

### Your friendly neighborhood engineeers...


<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/cdc0b597-ac9a-44d7-bf40-8da04d7c2e27" alt="IMG_5433 (1)" width="250"/>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/850c89d1-7568-4277-a34f-16b4119d2406" alt="image" width="700"/>
    </td>
  </tr>
</table>





