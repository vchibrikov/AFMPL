import os
import pandas as pd
import pySPM
import matplotlib.pyplot as plt
from skimage.morphology import binary_erosion, disk
import cv2
from matplotlib.widgets import Slider

# Callback function for mouse click events
def on_click(event):
    global ax, selected_coordinates, current_image_filename, output_filename

    if event.inaxes != ax:
        return

    x, y = int(event.xdata), int(event.ydata)
    print(f"Selected point: ({x}, {y})")

    # Determine color based on index parity
    color = 'ro' if len(selected_coordinates) % 2 == 0 else 'bo'
    ax.plot(x, y, color, markersize=8)
    plt.draw()

    selected_coordinates.append({
        "Filename": f"{current_image_filename}",
        "start_x": None,
        "start_y": None,
        "end_x": None,
        "end_y": None,
    })

    if len(selected_coordinates) % 2 == 0:
        selected_coordinates[-2]["end_x"] = x
        selected_coordinates[-2]["end_y"] = y
    else:
        selected_coordinates[-1]["start_x"] = x
        selected_coordinates[-1]["start_y"] = y

    df = pd.DataFrame(selected_coordinates).dropna()
    df["start_x"] = df["start_x"].astype(int)
    df["start_y"] = df["start_y"].astype(int)
    df["end_x"] = df["end_x"].astype(int)
    df["end_y"] = df["end_y"].astype(int)
    df.to_csv(output_filename, index=False)

# Function to update the image when sliders change
def update_threshold(val):
    lower_threshold = slider_lower.val
    upper_threshold = slider_upper.val
    modified_image = height_dataframe.copy()
    
    # Apply thresholding: values outside the range turn white (255)
    modified_image[(modified_image < lower_threshold) | (modified_image > upper_threshold)] = 255
    
    # Rescale colormap to the new range while keeping data unchanged
    im.set_clim(lower_threshold, upper_threshold)
    im.set_data(modified_image)
    plt.draw()

# Callback function for zooming with the mouse wheel
def on_scroll(event):
    global ax
    x, y = event.xdata, event.ydata
    current_xlim = ax.get_xlim()
    current_ylim = ax.get_ylim()

    if current_xlim is not None and current_ylim is not None:
        if event.button == 'up':  # Zoom in
            ax.set_xlim(x - (x - current_xlim[0]) / 1.1, x + (current_xlim[1] - x) / 1.1)
            ax.set_ylim(y - (y - current_ylim[0]) / 1.1, y + (current_ylim[1] - y) / 1.1)
        elif event.button == 'down':  # Zoom out
            ax.set_xlim(x - (x - current_xlim[0]) * 1.1, x + (current_xlim[1] - x) * 1.1)
            ax.set_ylim(y - (y - current_ylim[0]) * 1.1, y + (current_ylim[1] - y) * 1.1)

        plt.draw()

# Initialize coordinate storage
selected_coordinates = []

# Define input and output directories
input_folder = '/Users/vadymchibrikov/Desktop/AFMPL/1_input_image/OPUS26/'
output_folder = '/Users/vadymchibrikov/Desktop/AFMPL/1_output_coordinates/'

files_in_input_folder = os.listdir(input_folder)
if not files_in_input_folder:
    print("No files found in the input folder.")
else:
    print(f"Found {len(files_in_input_folder)} files in the input folder:")
    for file in files_in_input_folder:
        print(file)

for subdir, _, files in os.walk(input_folder):
    for file in files:
        if file == '.DS_Store':
            continue
        
        image_path = os.path.join(subdir, file)
        current_image_filename = file
        output_filename = os.path.join(output_folder, f"{current_image_filename}_coordinates.csv")

        image = pySPM.Bruker(image_path)
        height = image.get_channel("Height")

        top = height.correct_lines(inline=False)
        top = top.correct_plane(inline=False)
        top = top.filter_scars_removal(.7, inline=False)
        top = top.correct_plane(inline=False)
        top = top.corr_fit2d(inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal()
        mask0 = top.get_bin_threshold(.1, high=False)
        mask1 = binary_erosion(mask0, disk(3))
        top = top.corr_fit2d(mask=mask1, inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal().correct_plane().correct_lines().zero_min()
        
        height_dataframe = pd.DataFrame(top.pixels)

        fig, ax = plt.subplots(figsize=(18, 9))
        plt.subplots_adjust(bottom=0.3)  # Leave space for two sliders
        im = ax.imshow(height_dataframe, cmap='gray')
        plt.colorbar(im)

        ax_slider_lower = plt.axes([0.2, 0.1, 0.65, 0.03], facecolor="lightgray")
        ax_slider_upper = plt.axes([0.2, 0.05, 0.65, 0.03], facecolor="lightgray")
        
        slider_lower = Slider(ax_slider_lower, "Lower Threshold", height_dataframe.min().min(), height_dataframe.max().max(), valinit=0.25)
        slider_upper = Slider(ax_slider_upper, "Upper Threshold", height_dataframe.min().min(), height_dataframe.max().max(), valinit=height_dataframe.max().max())
        
        slider_lower.on_changed(update_threshold)
        slider_upper.on_changed(update_threshold)

        fig.canvas.mpl_connect('button_press_event', on_click)
        fig.canvas.mpl_connect('scroll_event', on_scroll)
        plt.show()
