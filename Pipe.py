import multiprocessing as mp
import dearpygui.dearpygui as dpg
import math
import random
import time
from collections import deque

# Sender
def gui_A(conn):                                           
    dpg.create_context()
    data_sending = False
    data_interval = 0.01  # seconds between data points
    t = 0.0  # Time variable for sine waves
    dt = 0.05  # Time increment per data point
    wave_params = [None] * 3  # Store frequency, amplitude, phase for each wave

    def toggle_data_sending():
        nonlocal data_sending, t, wave_params
        data_sending = not data_sending
        if data_sending:
            wave_params = [
                {
                    'freq': random.uniform(0.5, 2.0),
                    'amp': random.uniform(30, 50),
                    'phase': random.uniform(0, 2 * math.pi) 
                } for _ in range(3)
            ]
            t = 0.0
        dpg.set_item_label("toggle_btn", "Stop" if data_sending else "Start")

    with dpg.window(tag="window_a", no_title_bar=True, no_move=True, no_scrollbar=True):
        dpg.add_button(label="Start", tag="toggle_btn", callback=toggle_data_sending)
        dpg.add_text("Generating 3 randomized sine waves")

    dpg.create_viewport(title="Viewport A", width=420, height=180, resizable=True)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    random.seed(time.time())

    while dpg.is_dearpygui_running():
        if data_sending:
            waves = [
                params['amp'] * math.sin(2 * math.pi * params['freq'] * t + params['phase']) + 50
                for params in wave_params
            ]
            conn.send(waves)  # Send list of three values through pipe
            t += dt  # Increment time
            time.sleep(data_interval)  # Control data generation rate
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
    conn.close()

# Receiver
def gui_B(conn):                                            
    dpg.create_context()
    max_points = 100 

    data1 = deque(maxlen=max_points)
    data2 = deque(maxlen=max_points)
    data3 = deque(maxlen=max_points)
    x_data = deque(maxlen=max_points)
    counter = 0

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

    while dpg.is_dearpygui_running():
        while conn.poll():  # Check if data is available in the pipe
            values = conn.recv()  # Receive list of three values
            data1.append(values[0])
            data2.append(values[1])
            data3.append(values[2])
            x_data.append(counter)
            counter += 1

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

    dpg.destroy_context()
    conn.close()

def main():
    mp.freeze_support()
    parent_conn, child_conn = mp.Pipe()  # Create a Pipe

    p1 = mp.Process(target=gui_A, args=(parent_conn,))
    p2 = mp.Process(target=gui_B, args=(child_conn,))
    p1.start()
    p2.start()

    p1.join()
    p2.join()

if __name__ == "__main__":
    main()
