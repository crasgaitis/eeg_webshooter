import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify
import threading

# Import functions from the utils module
from utils import update_buffer, get_last_data, compute_band_powers
from pylsl import StreamInlet, resolve_byprop

import serial

def init_serial():
    global esc_control
    try:
        esc_control = serial.Serial("COM3", 9600)
        print("Serial port opened successfully.")
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
        esc_control = None

app = Flask(__name__)

ESC_ON = True
esc_control=None

score = 0.0
score_lock = threading.Lock()
recording_thread = None
recording_started = False

start_time = None      # for continuous timing
total_focus_time = 0   # for cumulative timing
last_time = time.time()

BUFFER_LENGTH = 5
EPOCH_LENGTH = 1
OVERLAP_LENGTH = 0
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH
INDEX_CHANNEL = [1]

def do_min_rec():
    """
    Record a 20s interval of EEG data in a min_bandpowers.csv file.
    """
    print("Recording minimum focus.")
    record(20, 'min_bandpowers.csv')
    return "You clicked the first button."

def do_max_rec():
    """
    Record a 20s interval of EEG data in a max_bandpowers.csv file.
    """
    print("Recording maximum focus.")
    record(60 * 5, 'max_bandpowers.csv')
    return "You clicked the second button."

@app.route('/start', methods=['POST'])
def spiderman_go():
    """
    Trigger live recordings with terminal printouts.
    """
    print("Running spiderman detection.")
    global recording_thread, recording_started
    if not recording_started:
        recording_started = True
        recording_thread = threading.Thread(target=record_live, daemon=True)
        recording_thread.start()
        return jsonify({'status': 'recording started'})
    else:
        return jsonify({'status': 'already running'})
    
def compute_focus_score(rule_matrix):
    """
    Compute a normalized weighted focus score between 0 and 1 based on multiple variables.

    Each variable is defined by a 4-element list:
        [value, lower_bound, upper_bound, weight]

    - If upper_bound > lower_bound:
        The score increases as the value moves from lower_bound to upper_bound.
    - If upper_bound < lower_bound:
        The score increases as the value moves from upper_bound to lower_bound.
    - If upper_bound == lower_bound:
        The score is 1.0 if value == bound, otherwise 0.0.

    The final score is the weighted sum of the individual normalized scores.
    All weights are assumed to sum to 1.0 (but this is not enforced).

    Parameters:
        rule_3d (list of list): A list of [value, lower_bound, upper_bound, weight].

    Returns:
        float: A single focus score between 0 and 1.
    """
    total = 0
    for var, low, high, weight in rule_matrix:
        if high != low:
            if high > low:
                score = (var - low) / (high - low)
            else:
                score = (low - var) / (low - high)
            score = max(0, min(1, score))  # clamp between 0 and 1
        else:
            score = 1.0 if var == low else 0.0

        total += score * weight
        print(total)
        
    return total

def check_focus_continuous(rule_matrix, continuous, time_data):
    """
    Compute a blended focus score based on rule-based heuristics and focus time.
    
    Parameters:
        rule_matrix (list of list): A list of [value, lower_bound, upper_bound, weight].
        continuous (bool): If True, require uninterrupted focus; else accumulate over time.
        time_data (list): [time_min, time_max, time_weight]
            - time_min: score is 0 at or below this time
            - time_max: score is 1 at or above this time
            - time_weight: how much the time contributes to the final score (0 to 1)

    Returns:
        float: Final focus score between 0 and 1.
    """       
    global focus_start_time, focus_total_time, last_check_time

    focus_start_time = None
    focus_total_time = 0
    last_check_time = time.time()

    curr_time = time.time()
    delta_time = curr_time - last_check_time
    last_check_time = curr_time

    time_min, time_max, time_weight = time_data
    rule_weight = 1.0 - time_weight

    rule_score = compute_focus_score(rule_matrix)

    if rule_score >= 1.0:
        if continuous:
            if focus_start_time is None:
                focus_start_time = curr_time
            time_focused = curr_time - focus_start_time
        else:
            focus_total_time += delta_time
            time_focused = focus_total_time
    else:
        if continuous:
            focus_start_time = None
        time_focused = 0

    if time_max != time_min:
        time_score = (time_focused - time_min) / (time_max - time_min)
        time_score = max(0.0, min(1.0, time_score))
    else:
        time_score = 1.0 if time_focused >= time_min else 0.0

    total = rule_weight * rule_score + time_weight * time_score
    print(total)
    return total
    
def check_focus_discrete(focus_rule):
    global start_time, total_focus_time, last_time
    
    condition, continuous, time_min = focus_rule
    curr_time = time.time()
    delta_time = curr_time - last_time
    last_time = curr_time

    if condition:
        print('wow focus')
        if continuous:
            if start_time is None:
                start_time = curr_time
            time_focus = curr_time - start_time
        else:
            total_focus_time += delta_time
            time_focus = total_focus_time
    else:
        print('no focus')
        if continuous:
            start_time = None
        time_focus = 0

    if time_focus >= time_min:
        print(f'wowowo {time_focus}')
        
@app.route('/score')
def get_score():
    global score
    return jsonify({'score': float(score) })
        
def record_live():
    global score 
    if ESC_ON and esc_control is None:
        init_serial()
    # Search for active LSL streams
    print('Looking for an EEG stream...')
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        raise RuntimeError('Can\'t find EEG stream.')
    else:
        print('Found it!')

    # Set active EEG stream to inlet and apply time correction
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Get the stream info
    info = inlet.info()
    fs = int(info.nominal_srate())

    # Initialize raw EEG data buffer
    eeg_buffer = np.zeros((int(fs * BUFFER_LENGTH), 1))
    filter_state = None  # for use with the notch filter

    # Compute the number of epochs in "buffer_length"
    n_win_test = int(np.floor((BUFFER_LENGTH - EPOCH_LENGTH) /
                                SHIFT_LENGTH + 1))

    while True:
        # Obtain EEG data from the LSL stream
        eeg_data, timestamp = inlet.pull_chunk(
            timeout=1, max_samples=int(SHIFT_LENGTH * fs))
        if len(eeg_data) == 0:
            continue

        # Only keep the channel we're interested in
        ch_data = np.array(eeg_data)[:, INDEX_CHANNEL]

        # Update EEG buffer with the new data
        eeg_buffer, filter_state = update_buffer(
            eeg_buffer, ch_data, notch=True,
            filter_state=filter_state)

        # Get newest samples from the buffer
        data_epoch = get_last_data(eeg_buffer,
                                   EPOCH_LENGTH * fs)

        # Compute band powers
        band_powers = compute_band_powers(data_epoch, fs)
        delta, theta, alpha, beta = band_powers
        
        max_bands = pd.read_csv('iq_max_bandpowers.csv')
        min_bands = pd.read_csv('iq_min_bandpowers.csv')
        
        max_val = max_bands['beta'].quantile(0.2)
        min_val = min_bands['beta'].quantile(0.10)
        
        # check_focus((condition, True, 5))  # for continuous
        # check_focus_discrete((condition, False, 5))  # for cumulative
        with score_lock:
            score = check_focus_continuous( [[beta, 0, max_val, min_val]], False, [2, 2, 0.2]) * 10
            print(score)
            
            if ESC_ON:
                cmd = f"{score}\n"
                esc_control.write(cmd.encode())
                esc_control.flush()
                print("Sent: " + cmd)

            # score = check_focus_continuous( [[beta, 0, max_val, min_val]], False, [2, 3, 0.5])

            
def record(duration_seconds=10, output_file='eeg_bandpowers.csv'):
    # Search for active LSL streams
    print('Looking for an EEG stream...')
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        raise RuntimeError('Can\'t find EEG stream.')
    else:
        print('Found it!')

    # Set active EEG stream to inlet and apply time correction
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Get the stream info
    info = inlet.info()
    fs = int(info.nominal_srate())

    # Initialize raw EEG data buffer
    eeg_buffer = np.zeros((int(fs * BUFFER_LENGTH), 1))
    filter_state = None  # for use with the notch filter

    # Compute the number of epochs in "buffer_length"
    n_win_test = int(np.floor((BUFFER_LENGTH - EPOCH_LENGTH) /
                                SHIFT_LENGTH + 1))

    # Initialize storage for band power time series
    data_log = []

    print(f'Recording for {duration_seconds} seconds...')

    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        # Obtain EEG data from the LSL stream
        eeg_data, timestamp = inlet.pull_chunk(
            timeout=1, max_samples=int(SHIFT_LENGTH * fs))
        if len(eeg_data) == 0:
            continue

        # Only keep the channel we're interested in
        ch_data = np.array(eeg_data)[:, INDEX_CHANNEL]

        # Update EEG buffer with the new data
        eeg_buffer, filter_state = update_buffer(
            eeg_buffer, ch_data, notch=True,
            filter_state=filter_state)

        # Get newest samples from the buffer
        data_epoch = get_last_data(eeg_buffer,
                                   EPOCH_LENGTH * fs)

        # Compute band powers
        band_powers = compute_band_powers(data_epoch, fs)
        delta, theta, alpha, beta = band_powers
        timestamp_now = time.time() - start_time

        # Log band powers with timestamp
        data_log.append({
            'time': timestamp_now,
            'alpha': alpha,
            'beta': beta,
            'theta': theta,
            'delta': delta
        })

    df = pd.DataFrame(data_log)
    df.to_csv(output_file, index=False)
    print(f'Data saved to {output_file}')

    return df

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'button1' in request.form:
            return do_min_rec()
        elif 'button2' in request.form:
            return do_max_rec()
        elif 'button3' in request.form:
            return spiderman_go()
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)