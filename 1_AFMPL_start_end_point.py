# Import packages - These lines import necessary libraries and packages 
# for file operations (os), data manipulation (pandas), AFM image processing (pySPM),
# plotting (matplotlib.pyplot), and image morphology operations (skimage.morphology).
import os
import pandas as pd
import pySPM
import matplotlib.pyplot as plt
from skimage.morphology import binary_erosion, disk
import cv2

# This function is a callback for mouse click events. It handles left mouse button clicks (event.button == 1). 
# It prints the selected point coordinates, plots a red dot at that point, and saves the coordinates to a list
# (selected_coordinates). If there are more than one point, it also sets the "end_x" and "end_y" values for the
# prior-to-last point. Finally, it saves the coordinates to a CSV file immediately after each click.
def on_click(event):
    global ax, selected_coordinates, current_image_filename, output_filename

    if event.button == 1:
        x, y = int(event.xdata), int(event.ydata)
        print(f"Selected point: ({x}, {y})")

        ax.plot(x, y, 'ro', markersize = 5)
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

        # Check if the last point has all values present

        # Save selected coordinates to a CSV file immediately after each click
        df = pd.DataFrame(selected_coordinates)  # Exclude the last point from the DataFrame
        df = df.dropna()
        df["start_x"] = df["start_x"].astype(int)
        df["start_y"] = df["start_y"].astype(int)
        df["end_x"] = df["end_x"].astype(int)
        df["end_y"] = df["end_y"].astype(int)

        df.to_csv(output_filename, index=False)

# This function is a callback for mouse wheel scroll events. It adjusts the plot limits for zooming based
# on the direction of the scroll (event.button == 'up' or event.button == 'down').
def on_scroll(event):
    global ax

    x, y = event.xdata, event.ydata
    current_xlim = ax.get_xlim()
    current_ylim = ax.get_ylim()

    if current_xlim is not None and current_ylim is not None:
        if event.button == 'up':
            ax.set_xlim(x - (x - current_xlim[0]) / 1.1, x + (current_xlim[1] - x) / 1.1)
            ax.set_ylim(y - (y - current_ylim[0]) / 1.1, y + (current_ylim[1] - y) / 1.1)
        elif event.button == 'down':
            ax.set_xlim(x - (x - current_xlim[0]) * 1.1, x + (current_xlim[1] - x) * 1.1)
            ax.set_ylim(y - (y - current_ylim[0]) * 1.1, y + (current_ylim[1] - y) * 1.1)

        plt.draw()

# This block initializes a list (selected_coordinates) to store point coordinates and specifies input and output folders.
selected_coordinates = []

# This block iterates over the image files in the specified input folder. It constructs the full path for each image, sets 
# the current image filename, and determines the output CSV filename.
input_folder = '/Users/...'
output_folder = '/Users/...'

# This block iterates over the image files in the specified input folder. It constructs the full path for each image, sets 
# the current image filename, and determines the output CSV filename.
for subdir, _, files in os.walk(input_folder):
    for file in files:
        # Concatenate path of each image
        image_path = os.path.join(subdir, file)

        # Store the current image filename
        current_image_filename = file

        # Output CSV filename
        output_filename = os.path.join(output_folder, f"{current_image_filename}_coordinates.csv")

        # This part of the code imports the Bruker AFM image, processes it, and creates a heatmap
        # using Matplotlib for visualization.
        image = pySPM.Bruker(image_path)

        # Separate channels of datafile
        height = image.get_channel("Height Sensor")
        # height.show(cmap = 'gray')

        # Basic data correction
        top = height.correct_lines(inline = False)
        top = top.correct_plane(inline = False)
        top = top.filter_scars_removal(.7, inline = False)
        top = top.correct_plane(inline = False)
        top = top.corr_fit2d(inline=False).offset([[10, 0, 10, 511]]).filter_scars_removal()
        mask0 = top.get_bin_threshold(.1, high=False)
        mask1 = binary_erosion(mask0, disk(3))
        top = top.corr_fit2d(mask=mask1, inline=False).offset([[10, 0, 10, 511]]).filter_scars_removal().correct_plane().correct_lines().zero_min()
        top = top.correct_lines(inline=False)
        top = top.correct_plane(inline=False)

        height_dataframe = pd.DataFrame(top.pixels)

        # Create a heatmap with Matplotlib
        fig, ax = plt.subplots(figsize=(10, 7))
        im = ax.imshow(height_dataframe, cmap='gray')
        plt.colorbar(im)

        # Connect the callback function to the canvas for point clicks
        fig.canvas.mpl_connect('button_press_event', on_click)

        # Connect the callback function to the canvas for mouse wheel (zoom)
        fig.canvas.mpl_connect('scroll_event', on_scroll)

        # Remove the default Matplotlib toolbar
        plt.rcParams['toolbar'] = 'None'

        # This block displays the plot without blocking the code execution. 
        # A short pause allows immediate response after each click.
        plt.show(block=False)

        # Pause for a short duration to allow immediate response after each click
        plt.pause(0.01)

# This line ensures that the final plot is displayed without waiting for user input after clicking points.
plt.show()
