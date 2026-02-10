import pandas as pd
import numpy as np
import heapq
import pySPM
from skimage.morphology import binary_erosion, disk
import os
import glob
import timeout_decorator
import matplotlib.pyplot as plt
import xlsxwriter
import time

# Set threshold
lower_threshold = 
higher_threshold = 
a_path_tolerance = 

# Set input
input_image_folder = '/path/to/input/image/folder/'
input_coordinates_folder = '/path/to/input/coordinates/folder/'

# Set output folders
output_path_folder = '/path/to/output/path/folder/'
output_image_folder = '/path/to/output/image/folder/'

# Set a timeout for the A* pathfinding function
@timeout_decorator.timeout(10)
def astar_pathfinding_timeout(grid, start, goal, visualize=True, tolerance = a_path_tolerance):
    print(f"Running A* pathfinding from {start} to {goal}.")
    open_set = [(0, start)]
    heapq.heapify(open_set)
    came_from = {start: None}
    cost_so_far = {start: 0}

    while open_set:
        current_cost, current_node = heapq.heappop(open_set)

        if current_node == goal:
            print(f"Goal reached: {current_node}")
            break

        neighbors = [(current_node[0] + 1, current_node[1]),
                     (current_node[0] - 1, current_node[1]),
                     (current_node[0], current_node[1] + 1),
                     (current_node[0], current_node[1] - 1)]

        for neighbor in neighbors:
            if lower_threshold <= neighbor[0] < grid.shape[0] and lower_threshold <= neighbor[1] < grid.shape[1]:
                try:
                    # Apply tolerance for small deviations in pixel value
                    if grid.iat[neighbor[0], neighbor[1]] > (lower_threshold - tolerance):
                        new_cost = cost_so_far[current_node] + grid.iloc[neighbor]
                        if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                            cost_so_far[neighbor] = new_cost
                            priority = new_cost + heuristic(goal, neighbor)
                            heapq.heappush(open_set, (priority, neighbor))
                            came_from[neighbor] = current_node
                except IndexError:
                    print(f"IndexError: {neighbor} is out of bounds")
                    continue

    path = []
    current = goal
    while current is not None:
        path.append(current)
        if current in came_from:
            current = came_from[current]
        else:
            print(f"KeyError: {current} not found in came_from dictionary")
            return [], False  # Return empty path and indicate no image was saved

    path.reverse()

    # Variable to track if the image is successfully saved
    image_saved = False

    if visualize:
        fig, ax = plt.subplots(figsize=(18, 10))
        cax = ax.matshow(grid, cmap='gray')

        for i in range(len(path) - 1):
            y, x = path[i]
            next_y, next_x = path[i + 1]
            plt.plot([x, next_x], [y, next_y], marker='o', markersize=3, color='red')

        min_x = min([coord[1] for coord in path]) - 10
        max_x = max([coord[1] for coord in path]) + 10
        min_y = min([coord[0] for coord in path]) - 10
        max_y = max([coord[0] for coord in path]) + 10

        min_x = max(0, min_x)
        max_x = min(grid.shape[1] - 1, max_x)
        min_y = max(0, min_y)
        max_y = min(grid.shape[0] - 1, max_y)

        plt.xlim(min_x, max_x)
        plt.ylim(max_y, min_y)

        image_filename = f"{base_filename}_{index}_zoomed_path.png"
        image_path = os.path.join(output_image_folder, image_filename)

        try:
            plt.savefig(image_path, bbox_inches='tight', dpi=300)
            print(f"Image saved to: {image_path}")
            image_saved = True
        except Exception as e:
            print(f"Error saving image: {e}")

        plt.close(fig)

    return path, image_saved

def heuristic(a, b, distance_weight=1, value_weight=1):
    manhattan_distance = abs(a[0] - b[0])**2 + abs(a[1] - b[1])**2
    value_a = grid.iloc[a]
    value_b = grid.iloc[b]

    if value_a < 0 or value_b < 0:
        return float('inf')

    if value_a > 2 * value_b or (value_a < 2 * value_b and value_b < 0.5):
        value_penalty = 1000 * (value_a - value_b)
    else:
        value_penalty = abs(value_a - value_b)

    return distance_weight * manhattan_distance + value_weight * value_penalty

def calculate_contour_length(path):
    return np.sum([np.sqrt((path[i][0] - path[i + 1][0])**2 + (path[i][1] - path[i + 1][1])**2) for i in range(len(path) - 1)])

def calculate_shortest_distance(start, end):
    return np.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)

def find_possible_reconnects(goal, grid, threshold=0.25):
    # Find nearby points to the goal to try reconnecting
    neighbors = [(goal[0] + 1, goal[1]), (goal[0] - 1, goal[1]),
                 (goal[0], goal[1] + 1), (goal[0], goal[1] - 1)]
    valid_neighbors = []
    for neighbor in neighbors:
        if 0 <= neighbor[0] < grid.shape[0] and 0 <= neighbor[1] < grid.shape[1]:
            if grid.iloc[neighbor[0], neighbor[1]] > threshold:
                valid_neighbors.append(neighbor)
    return valid_neighbors

all_data_values = []
contour_lengths = []
shortest_distances = []
all_base_filenames = []

data_filenames = []
metrics_filenames = []
angles_filenames = []

all_coordinates = []

for subdir, _, files in os.walk(input_image_folder):
    for file in files:
        # Skip .DS_Store files
        if file == '.DS_Store':
            continue

        image_path = os.path.join(subdir, file)
        base_filename = os.path.basename(image_path)
        all_base_filenames.append(base_filename)

        # Load the image
        image = pySPM.Bruker(image_path)
        height = image.get_channel("Height")
        top = height.correct_lines(inline=False)
        top = top.correct_plane(inline=False)
        top = top.filter_scars_removal(.7, inline=False)
        top = top.correct_plane(inline=False)
        top = top.corr_fit2d(inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal()
        mask0 = top.get_bin_threshold(.5, high=False)
        mask1 = binary_erosion(mask0, disk(3))
        top = top.corr_fit2d(mask=mask1, inline=False).offset([[10, 0, 10, 255]]).filter_scars_removal().correct_plane().correct_lines().zero_min()
        top = top.correct_lines(inline=False)
        top = top.correct_plane(inline=False)
        grid = pd.DataFrame(top.pixels)

        # Search for the matching coordinates file in input_coordinates_folder
        coordinates_filename = f"{base_filename}_coordinates.csv"
        coordinates_file_path = os.path.join(input_coordinates_folder, coordinates_filename)

        if not os.path.exists(coordinates_file_path):
            print(f"No corresponding coordinates file found for {base_filename}")
            continue

        try:
            df_points = pd.read_csv(coordinates_file_path, delimiter=',')
        except FileNotFoundError:
            print(f"Coordinates file not found: {coordinates_file_path}")
            continue

        df_points['image_filename'] = [f"{base_filename}_{i+1:06d}" for i in range(len(df_points))]

        # Before accessing 'start_y' and 'start_x', print the columns to debug
        print(f"Columns in df_points: {df_points.columns}")

        # Check if 'start_y' and 'start_x' exist in the columns
        if 'start_y' not in df_points.columns or 'start_x' not in df_points.columns:
            print(f"Warning: 'start_y' or 'start_x' columns are missing in {coordinates_filename}. Skipping this file.")
            continue

        # Now you can safely access 'start_y', 'start_x', etc.
        for index, row in df_points.iloc[1:].iterrows():
            start = (row['start_y'], row['start_x'])
            goal = (row['end_y'], row['end_x'])
            # Further processing...

        # Inside your main loop (where you iterate over the coordinates):
        for index, row in df_points.iloc[1:].iterrows():
            start = (row['start_y'], row['start_x'])
            goal = (row['end_y'], row['end_x'])

            try:
                # Start timer for the A* pathfinding
                pathfinding_start_time = time.time()

                path, image_saved = astar_pathfinding_timeout(grid, start, goal)

                # End timer for pathfinding
                pathfinding_end_time = time.time()
                pathfinding_duration = pathfinding_end_time - pathfinding_start_time
                print(f"A* pathfinding from {start} to {goal} took {pathfinding_duration:.2f} seconds.")

                # If pathfinding fails, attempt to reconnect the path
                if not path:
                    print(f"A* failed. Attempting to reconnect path from {start} to {goal}.")
                    possible_reconnects = find_possible_reconnects(goal, grid)
                    for reconnect in possible_reconnects:
                        path, image_saved = astar_pathfinding_timeout(grid, start, reconnect, visualize=False)
                        if path:
                            print(f"Path successfully reconnected through {reconnect}")
                            break

                # Timer for the image-saving part
                if path and image_saved:
                    image_save_start_time = time.time()

                    coordinates_df = pd.DataFrame({
                        'image_filename': [f"{base_filename}_{index:06d}" for _ in path],
                        'x': [coord[1] for coord in path],
                        'y': [coord[0] for coord in path]
                    })
                    all_coordinates.append(coordinates_df)

                    path_data_values = [grid.iloc[y, x] for y, x in path]
                    all_data_values.extend(path_data_values)

                    contour_length = calculate_contour_length(path)
                    shortest_distance = calculate_shortest_distance(start, goal)
                    contour_lengths.append(contour_length)
                    shortest_distances.append(shortest_distance)

                    path_number = index
                    filename_with_path = f"{base_filename}_{path_number:06d}"

                    data_filenames.extend([filename_with_path] * len(path_data_values))
                    metrics_filenames.append(filename_with_path)

                    # Now save the Excel file since the image was saved
                    output_excel_path = os.path.join(output_path_folder, f"{base_filename}_results.xlsx")

                    with pd.ExcelWriter(output_excel_path, engine='xlsxwriter') as writer:
                        output_data_df = pd.DataFrame({
                            'image_filename': data_filenames,
                            'height_nm': all_data_values
                        })
                        output_data_df.to_excel(writer, sheet_name='height_nm', index=False)

                        output_metrics_df = pd.DataFrame({
                            'image_filename': metrics_filenames,
                            'contour_length_px': contour_lengths
                        })
                        output_metrics_df.to_excel(writer, sheet_name='contour_length_px', index=False)

                        output_distances_df = pd.DataFrame({
                            'image_filename': metrics_filenames,
                            'end_to_end_distance_px': shortest_distances
                        })
                        output_distances_df.to_excel(writer, sheet_name='end_to_end_distance_px', index=False)

                        if all_coordinates:
                            all_coordinates_df = pd.concat(all_coordinates, ignore_index=True)
                            all_coordinates_df.to_excel(writer, sheet_name='path_coordinates', index=False)

                    # print(f"Results saved to: {output_excel_path}")

                    # End timer for image-saving
                    image_save_end_time = time.time()
                    image_save_duration = image_save_end_time - image_save_start_time
                    # print(f"Image saving for {base_filename} took {image_save_duration:.2f} seconds.")

                else:
                    print(f"No valid path found or image not saved for {base_filename} at index {index}, skipping results saving.")

            except timeout_decorator.timeout_decorator.TimeoutError:
                print(f"A* pathfinding timed out for {start} to {goal}. Skipping...")
                continue
