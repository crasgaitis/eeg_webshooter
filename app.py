import pandas as pd
import time
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template, request

# Import functions from the utils module
from utils import update_buffer, get_last_data, compute_band_powers
from pylsl import StreamInlet, resolve_byprop

app = Flask(__name__)

BUFFER_LENGTH = 5
EPOCH_LENGTH = 1
OVERLAP_LENGTH = 0
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH
INDEX_CHANNEL = [0]

def do_min_rec():
    print("Recording minimum focus.")
    record(20, 'min_bandpowers.csv')
    return "You clicked the first button."

def do_max_rec():
    print("Recording maximum focus.")
    record(20, 'max_bandpowers.csv')
    return "You clicked the second button."

def spiderman_go():
    print("Running spiderman detection.")
    record_live()
    

def record_live():
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
        
        if beta > 0.5:
            print('wow focus')
        else:
            print('no focus') 

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
    app.run(debug=True)