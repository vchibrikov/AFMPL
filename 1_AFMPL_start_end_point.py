# Import necessary packages
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

    # Ignore clicks outside the image plot
    if event.inaxes != ax:
        return

    if event.button == 1:  # Left mouse button click
        x, y = int(event.xdata), int(event.ydata)
        print(f"Selected point: ({x}, {y})")

        ax.plot(x, y, 'ro', markersize=8)  # Mark point with red dot
        plt.draw()

        selected_coordinates.append({
            "Filename": f"{current_image_filename}",
            "start_x": None,
            "start_y": None,
            "end_x": None,
            "end_y": None,
        })

        # Update the last point based on parity
        if len(selected_coordinates) % 2 == 0:
            selected_coordinates[-2]["end_x"] = x
            selected_coordinates[-2]["end_y"] = y
        else:
            selected_coordinates[-1]["start_x"] = x
            selected_coordinates[-1]["start_y"] = y

        # Save selected coordinates to CSV
        df = pd.DataFrame(selected_coordinates).dropna()
        df["start_x"] = df["start_x"].astype(int)
        df["start_y"] = df["start_y"].astype(int)
        df["end_x"] = df["end_x"].astype(int)
        df["end_y"] = df["end_y"].astype(int)
        df.to_csv(output_filename, index=False)

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
input_folder = '/Users/path/to/input/image/folder/'
output_folder = '/Users/path/to/output/coordinates/folder/'

# Check for files in input folder
files_in_input_folder = os.listdir(input_folder)
if not files_in_input_folder:
    print("No files found in the input folder.")
else:
    print(f"Found {len(files_in_input_folder)} files in the input folder:")
    for file in files_in_input_folder:
        print(file)

# Loop through images in the input folder
for subdir, _, files in os.walk(input_folder):
    for file in files:

    # Skip .DS_Store files
        if file == '.DS_Store':
            continue
            # Construct full image path
        image_path = os.path.join(subdir, file)

        # Store filename and output CSV filename
        current_image_filename = file
        output_filename = os.path.join(output_folder, f"{current_image_filename}_coordinates.csv")

        # Load Bruker AFM image
        image = pySPM.Bruker(image_path)

        # Extract "Height" channel
        height = image.get_channel("Height")
        print("Processing Height Channel...")

        # Data correction
        top = height.correct_lines(inline=False)
        top = top.correct_plane(inline=False)
        top = top.filter_scars_removal(.7, inline=False)
        top = top.correct_plane(inline=False)
        top = top.corr_fit2d(inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal()
        mask0 = top.get_bin_threshold(.1, high=False)
        mask1 = binary_erosion(mask0, disk(3))
        top = top.corr_fit2d(mask=mask1, inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal().correct_plane().correct_lines().zero_min()
        top = top.correct_lines(inline=False)
        top = top.correct_plane(inline=False)

        # Convert data to a DataFrame
        height_dataframe = pd.DataFrame(top.pixels)

        # Define initial threshold value
        initial_threshold = 0.25

        # Function to update the image when slider changes
        def update_threshold(val):
            threshold = slider.val
            modified_image = height_dataframe.copy()

            # Apply thresholding: values below threshold turn white (255)
            modified_image[modified_image < threshold] = 255

            im.set_data(modified_image)  # Update the image
            plt.draw()

        # Create Matplotlib figure
        fig, ax = plt.subplots(figsize=(18, 9))
        plt.subplots_adjust(bottom=0.2)  # Leave space for the slider
        im = ax.imshow(height_dataframe, cmap='gray')
        plt.colorbar(im)

        # Create slider for threshold selection
        ax_slider = plt.axes([0.2, 0.05, 0.65, 0.03], facecolor="lightgray")  # Position
        slider = Slider(ax_slider, "Threshold", height_dataframe.min().min(), height_dataframe.max().max(), valinit=initial_threshold)
        slider.on_changed(update_threshold)  # Attach event handler

        # Connect mouse events for clicks and zooming
        fig.canvas.mpl_connect('button_press_event', on_click)
        fig.canvas.mpl_connect('scroll_event', on_scroll)

        # Show the plot
        plt.show()
