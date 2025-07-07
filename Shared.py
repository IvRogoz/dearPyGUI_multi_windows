import multiprocessing as mp
import dearpygui.dearpygui as dpg
import math
import random
import time
import numpy as np
from collections import deque
import struct

from multiprocessing import shared_memory
print(shared_memory.__name__)

# Sender
def gui_A(shm_name, shm_size, shm_bool_name):
    dpg.create_context()
    data_interval = 0.01  # seconds between data points
    t = 0.0  # Time variable for sine waves
    dt = 0.05  # Time increment per data point
    wave_params = [None] * 3  # Store frequency, amplitude, phase for each wave

    # Access shared memory
    shm = mp.shared_memory.SharedMemory(name=shm_name, create=False, size=shm_size)
    shm_bool = mp.shared_memory.SharedMemory(name=shm_bool_name, create=False, size=1)
    data_array = np.ndarray((4,), dtype=np.float64, buffer=shm.buf)  # 3 waves + counter
    bool_array = np.ndarray((1,), dtype=np.uint8, buffer=shm_bool.buf)  # Boolean for data_sending

    def toggle_data_sending():
        nonlocal t, wave_params
        bool_array[0] = 1 - bool_array[0]  # Toggle boolean (0 or 1)
        if bool_array[0]:
            wave_params = [
                {
                    'freq': random.uniform(0.5, 2.0),
                    'amp': random.uniform(30, 50),
                    'phase': random.uniform(0, 2 * math.pi)
                } for _ in range(3)
            ]
            t = 0.0
        dpg.set_item_label("toggle_btn", "Stop" if bool_array[0] else "Start")

    with dpg.window(tag="window_a", no_title_bar=True, no_move=True, no_scrollbar=True):
        dpg.add_button(label="Start", tag="toggle_btn", callback=toggle_data_sending)
        dpg.add_text("Generating 3 randomized sine waves")

    dpg.create_viewport(title="Viewport A", width=420, height=180, resizable=True)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    random.seed(time.time())

    while dpg.is_dearpygui_running():
        if bool_array[0]:
            waves = [
                params['amp'] * math.sin(2 * math.pi * params['freq'] * t + params['phase']) + 50
                for params in wave_params
            ]
            data_array[0:3] = waves  # Write wave values to shared memory
            data_array[3] += 1  # Increment counter
            t += dt  # Increment time
            time.sleep(data_interval)  # Control data generation rate
        dpg.render_dearpygui_frame()

    shm.close()
    shm_bool.close()
    dpg.destroy_context()

# Receiver
def gui_B(shm_name, shm_size, shm_bool_name):
    dpg.create_context()
    max_points = 100

    data1 = deque(maxlen=max_points)
    data2 = deque(maxlen=max_points)
    data3 = deque(maxlen=max_points)
    x_data = deque(maxlen=max_points)

    # Access shared memory
    shm = mp.shared_memory.SharedMemory(name=shm_name, create=False, size=shm_size)
    shm_bool = mp.shared_memory.SharedMemory(name=shm_bool_name, create=False, size=1)
    data_array = np.ndarray((4,), dtype=np.float64, buffer=shm.buf)  # 3 waves + counter
    bool_array = np.ndarray((1,), dtype=np.uint8, buffer=shm_bool.buf)  # Boolean for data_sending

    with dpg.theme(tag="theme_red"):
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, [255, 0, 0, 255])
    with dpg.theme(tag="theme_green"):
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, [0, 255, 0, 255])
    with dpg.theme(tag="theme_blue"):
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, [0, 0, 255, 255])

    with dpg.window(tag="window_b", no_title_bar=True, no_move=True, no_scrollbar=True, no_resize=True):
        with dpg.plot(label="Three Randomized Sine Waves", tag="main_plot", width=-1, height=-1):
            dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag="x_axis")
            with dpg.plot_axis(dpg.mvYAxis, label="Value", tag="y_axis"):
                dpg.add_line_series([], [], label="Wave 1", tag="series_1")
                dpg.add_line_series([], [], label="Wave 2", tag="series_2")
                dpg.add_line_series([], [], label="Wave 3", tag="series_3")

                dpg.bind_item_theme("series_1", "theme_red")
                dpg.bind_item_theme("series_2", "theme_green")
                dpg.bind_item_theme("series_3", "theme_blue")

    dpg.create_viewport(title="Viewport B", width=800, height=600, resizable=True)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    last_counter = -1
    while dpg.is_dearpygui_running():
        if bool_array[0] and data_array[3] > last_counter:
            data1.append(float(data_array[0]))
            data2.append(float(data_array[1]))
            data3.append(float(data_array[2]))
            x_data.append(float(data_array[3]))
            last_counter = data_array[3]

            dpg.set_value("series_1", [list(x_data), list(data1)])
            dpg.set_value("series_2", [list(x_data), list(data2)])
            dpg.set_value("series_3", [list(x_data), list(data3)])

            dpg.fit_axis_data("x_axis")
            dpg.fit_axis_data("y_axis")

        viewport_width = dpg.get_viewport_client_width()
        viewport_height = dpg.get_viewport_client_height()
        dpg.configure_item("window_b", width=viewport_width, height=viewport_height, pos=[0, 0])
        dpg.configure_item("main_plot", width=viewport_width, height=viewport_height)

        dpg.render_dearpygui_frame()

    shm.close()
    shm_bool.close()
    dpg.destroy_context()

def main():
    mp.freeze_support()
    # Create shared memory for wave data (3 values + counter) and boolean
    shm_size = np.dtype(np.float64).itemsize * 4  # 3 waves + 1 counter
    shm_bool_size = np.dtype(np.uint8).itemsize * 1  # 1 boolean
    shm = mp.shared_memory.SharedMemory(create=True, size=shm_size)
    shm_bool = mp.shared_memory.SharedMemory(create=True, size=shm_bool_size)
    data_array = np.ndarray((4,), dtype=np.float64, buffer=shm.buf)
    data_array[:] = 0.0  # Initialize to zeros
    bool_array = np.ndarray((1,), dtype=np.uint8, buffer=shm_bool.buf)
    bool_array[0] = 0  # Initialize data_sending to False

    p1 = mp.Process(target=gui_A, args=(shm.name, shm_size, shm_bool.name))
    p2 = mp.Process(target=gui_B, args=(shm.name, shm_size, shm_bool.name))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

    # Clean up shared memory
    shm.close()
    shm.unlink()
    shm_bool.close()
    shm_bool.unlink()

if __name__ == "__main__":
    main()
