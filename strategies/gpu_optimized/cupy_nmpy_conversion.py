import cupy as cp
import numpy as np

def calculate_rsi_numpy(close, rsi_window):
    # Calculate differences
    delta = close[1:] - close[:-1]
    gain = np.maximum(delta, 0)
    loss = np.maximum(-delta, 0)

    # Calculate rolling averages (simple moving average for RSI)
    avg_gain = np.convolve(gain, np.ones(rsi_window) / rsi_window, mode='valid')
    avg_loss = np.convolve(loss, np.ones(rsi_window) / rsi_window, mode='valid')
    print(avg_gain)
    print(avg_loss)

    # Handle zero division and calculate RS
    rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)  # Handle division by zero
    rsi = 100 - (100 / (1 + rs))

    # If RSI calculation results in NaN (due to division by zero), set those to 100 (no loss)
    rsi = np.where(np.isnan(rsi), 100, rsi)

    # Align output size with padding (like CuPy)
    pad_length = close.shape[0] - rsi.shape[0]
    rsi = np.concatenate([np.full(pad_length, np.nan), rsi])

    return rsi

def calculate_rsi_gpu(close_gpu, rsi_window):
    delta = close_gpu[1:] - close_gpu[:-1]
    gain = cp.maximum(delta, 0)
    loss = cp.maximum(-delta, 0)

    avg_gain = cp.convolve(gain, cp.ones(rsi_window) / rsi_window, mode='valid')
    avg_loss = cp.convolve(loss, cp.ones(rsi_window) / rsi_window, mode='valid')

    # Handle zero division and calculate RS
    rs = cp.where(avg_loss == 0, cp.inf, avg_gain / avg_loss)  # Handle division by zero
    rsi = 100 - (100 / (1 + rs))

    # If RSI calculation results in NaN (due to division by zero), set those to 100 (no loss)
    rsi = cp.where(cp.isnan(rsi), 100, rsi)

    pad_length = close_gpu.shape[0] - rsi.shape[0]
    rsi = cp.concatenate([cp.full(pad_length, cp.nan), rsi])
    return rsi

# Sample input data (close values)
close_gpu = cp.array([0,1,1,1,0,0,0,1,1,1,1,1,1,0,0,0], dtype=cp.float64)
rsi_window = 20

# Calculate RSI with CuPy
rsi_cupy = calculate_rsi_gpu(close_gpu, rsi_window).get()  # Get the result back to CPU

# Calculate RSI with NumPy
close_numpy = np.array([0,1,1,1,0,0,0,1,1,1,1,1,1,0,0,0], dtype=np.float64)
rsi_numpy = calculate_rsi_numpy(close_numpy, rsi_window)

# Print results and compare
print("RSI CuPy:", rsi_cupy)
print("RSI NumPy:", rsi_numpy)
print("Difference:", np.abs(rsi_cupy - rsi_numpy))
