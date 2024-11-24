import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft
import time
import queue
import threading
import sys

# Set font for display
plt.rcParams['font.sans-serif'] = ['Arial']  # Use Arial
plt.rcParams['axes.unicode_minus'] = False  # Fix negative sign display issue

# Real-time audio stream parameters
FORMAT = pyaudio.paInt16  # 16-bit audio format
CHANNELS = 1  # Mono
RATE = 16000  # Sample rate 16kHz
CHUNK = 1024  # Audio chunk size

# Initialize PyAudio
p = pyaudio.PyAudio()

# Create a queue for inter-thread communication
audio_queue = queue.Queue()

# Start real-time audio stream and get input device information
def list_devices():
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        print(f"Device {i}: {device_info['name']}, Channels: {device_info['maxInputChannels']}")

# If you need to see device information, uncomment the line below
# list_devices()

# Real-time plotting function
def update_plot():
    plt.ion()  # Enable interactive mode
    fig, axs = plt.subplots(3, 1, figsize=(10, 8), facecolor='lightgray')  # 增加一个子图
    fig.patch.set_facecolor('whitesmoke')
    
    # Set the style of the charts
    for ax in axs:
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_xlim(0, 10)  # Set x-axis range to 10 seconds
        ax.set_ylim(-30000, 30000)  # Set y-axis range
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#39c5bb')  # 统一颜色
        ax.spines['bottom'].set_color('#39c5bb')  # 统一颜色
        ax.tick_params(axis='both', colors='#39c5bb')  # 统一颜色
        ax.set_title(ax.get_title(), fontsize=14, fontweight='bold', color='#39c5bb')  # 统一标题颜色并加粗

    # Create a color bar for dB scale
    cbar_ax = fig.add_axes([0.92, 0.15, 0.03, 0.7])  # Position for color bar
    norm = plt.Normalize(-100, 0)  # dB range for normalization
    sm = plt.cm.ScalarMappable(cmap='viridis', norm=norm)
    sm.set_array([])  # Only needed for older versions of matplotlib
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Decibels (dB)', rotation=270, labelpad=15)

    log_spectrum = np.zeros((4000, 10 * RATE // CHUNK))  # 10秒的长度

    while True:
        try:
            # Get audio data from the queue
            data = audio_queue.get(timeout=1)
            if data is None:
                break  # Exit the thread if `None` is received

            # Clear previous plots
            axs[0].cla()
            axs[1].cla()
            axs[2].cla()  # 清除对数图谱的绘图区域
            
            time_axis = np.arange(0, len(data)) * (1.0 / RATE)
            axs[0].plot(time_axis, data, color='#39c5bb', linewidth=1.5)  # 统一颜色
            axs[0].set_title("Real-time Voice Signal Time Domain Waveform", fontsize=14, fontweight='bold', color='#39c5bb')  # 统一标题颜色并加粗
            axs[0].set_xlabel("Duration (seconds)", fontsize=12, color='gray')
            axs[0].set_ylabel("Amplitude", fontsize=12, color='gray')

            # Calculate FFT and plot frequency domain spectrum
            ft = fft(data)
            magnitude = np.abs(ft)
            frequency = np.linspace(0, RATE, len(magnitude))
            axs[1].plot(frequency[:4000], magnitude[:4000], color='#39c5bb', linewidth=1.5)  # 统一颜色
            axs[1].set_title("Real-time Voice Signal Frequency Domain Spectrum", fontsize=14, fontweight='bold', color='#39c5bb')  # 统一标题颜色并加粗
            axs[1].set_xlabel("Frequency (Hz)", fontsize=12, color='gray')
            axs[1].set_ylabel("Magnitude", fontsize=12, color='gray')

            # 计算对数图谱并绘制
            log_magnitude = 10 * np.log10(magnitude[:CHUNK] + 1e-10)  # 使用 CHUNK 大小的数据
            # 确保 log_magnitude 的形状与 log_spectrum 的最后一列相匹配
            log_magnitude_resized = np.resize(log_magnitude, log_spectrum.shape[0])  # 调整形状

            # 更新对数图谱
            log_spectrum[:, :-1] = log_spectrum[:, 1:]  # 向左移动
            log_spectrum[:, -1] = log_magnitude_resized  # 添加新的数据

            # 只显示0-2000Hz的频谱对数
            axs[2].imshow(log_spectrum[:2000, :], aspect='auto', extent=[0, 10, 0, 2000], origin='lower', cmap='viridis')  # 修改纵轴范围为0-2000
            axs[2].set_title("Real-time Voice Signal Logarithmic Spectrum", fontsize=14, fontweight='bold', color='#39c5bb')  # 统一标题颜色并加粗
            axs[2].set_xlabel("Duration (seconds)", fontsize=12, color='gray')
            axs[2].set_ylabel("Frequency (Hz)", fontsize=12, color='gray')
            axs[2].set_ylim(0, 2000)  # 修正纵轴范围为0-2000

            plt.subplots_adjust(hspace=0.6)  # 增加图表之间的间距
            plt.draw()  # Update the figure
            plt.pause(0.01)  # Pause to allow the figure to update
        except queue.Empty:
            pass  # Continue waiting if the queue is empty

# Audio callback function
def audio_callback(in_data, frame_count, time_info, status):
    data = np.frombuffer(in_data, dtype=np.int16)
    # Put audio data into the queue
    audio_queue.put(data)
    return (None, pyaudio.paContinue)

# Start audio stream
def start_stream():
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=audio_callback)

    print("Starting real-time audio analysis...")
    stream.start_stream()

    # Start the plotting function here, ensuring it runs in the main thread
    update_plot()

    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping real-time audio analysis")
        stream.stop_stream()
        stream.close()
        plt.close()  # Close the figure
        sys.exit()  # Exit the program

if __name__ == '__main__':
    # Start audio stream and real-time analysis
    start_stream()

    # Keep the main thread active
    plt.show()
