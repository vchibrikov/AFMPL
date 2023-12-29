# Import libraries
import pandas as pd
import numpy as np
import heapq
import pySPM
from skimage.morphology import binary_erosion, disk
import os
import glob
import timeout_decorator
import matplotlib.pyplot as plt

# Set the input and output folders
input_image_folder = '/Users/...'
input_coordinates_folder = '/Users/...'
output_path_folder = '/Users/vadymchibrikov/...'

# Set a timeout for the A* pathfinding function
@timeout_decorator.timeout(10)

# A* pathfinding algorithm with a timeout.

# Parameters:
# - grid: 2D DataFrame representing the terrain.
# - start: Tuple (y, x) representing the starting point.
# - goal: Tuple (y, x) representing the goal point.

# Returns:
# - List of tuples representing the path from start to goal.

def astar_pathfinding_timeout(grid, start, goal, visualize = False):

    open_set = [(0, start)]
    heapq.heapify(open_set)
    came_from = {start: None}
    cost_so_far = {start: 0}

    while open_set:
        current_cost, current_node = heapq.heappop(open_set)

        if current_node == goal:
            break

        neighbors = [(current_node[0] + 1, current_node[1]),
                    (current_node[0] - 1, current_node[1]),
                    (current_node[0], current_node[1] + 1),
                    (current_node[0], current_node[1] - 1)]

        for neighbor in neighbors:
            if 0 <= neighbor[0] < grid.shape[0] and 0 <= neighbor[1] < grid.shape[1]:
                try:
                    if grid.iat[neighbor[0], neighbor[1]] > 0:
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
            return []

    path.reverse()

    if visualize:

        # Visualize the grid and path
        fig, ax = plt.subplots(figsize=(12, 7))
        cax = ax.matshow(grid, cmap='gray')

        for i in range(len(path) - 1):
            y, x = path[i]
            next_y, next_x = path[i + 1]
            plt.plot([x, next_x], [y, next_y], marker='o', markersize=3, color='red')

        plt.show()  # Display the visualization

    return path

# Heuristic function for the A* algorithm.

# Parameters:
# - a: Tuple (y, x) representing the current point.
# - b: Tuple (y, x) representing the goal point.
# - distance_weight: Weight for distance in the heuristic calculation.
# - value_weight: Weight for terrain value in the heuristic calculation.

# Returns:
# - Heuristic value.

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

# Calculate the contour length of a path.

# Parameter:
# - path: List of tuples representing the path.

# Returns:
# - Contour length.

def calculate_contour_length(path):
    return np.sum([np.sqrt((path[i][0] - path[i + 1][0])**2 + (path[i][1] - path[i + 1][1])**2) for i in range(len(path) - 1)])

# Calculate the shortest distance between start and end points

# Parameters:
# - start: Tuple (y, x) representing the starting point.
# - end: Tuple (y, x) representing the end point.

# Returns:
# - Shortest distance.

def calculate_shortest_distance(start, end):
    return np.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)

# Function to calculate angles between three consecutive points

# Calculate angles between three consecutive points in a path.

# Parameter:
# - path: List of tuples representing the path.

# Returns:
# - List of angles in degrees.

def calculate_angles(path):
    angles = []
    for i in range(1, len(path) - 1):
        prev_point = np.array(path[i - 1])
        current_point = np.array(path[i])
        next_point = np.array(path[i + 1])

        vector1 = prev_point - current_point
        vector2 = next_point - current_point

        norm_product = np.linalg.norm(vector1) * np.linalg.norm(vector2)

        if norm_product == 0:
            # Handle the case when the vectors have zero norm
            angle = 0
        else:
            # Calculate angle using dot product and arccosine
            dot_product = np.clip(np.dot(vector1, vector2) / norm_product, -1.0, 1.0)
            angle = np.arccos(dot_product)

        # Convert angle to degrees and append to the list
        angles.append(np.degrees(angle))

    return angles

# Initialize empty lists to store data
all_data_values = []
contour_lengths = []
shortest_distances = []
all_path_angles = []
all_base_filenames = []  # Added to store base filenames

# Initialize arrays for different purposes
data_filenames = []
metrics_filenames = []
angles_filenames = []

# Initialize a list to store all path coordinates
all_coordinates = []

# Iterate over image files in the specified input folder
for subdir, _, files in os.walk(input_image_folder):
    for file in files:

        # Construct the full path for each image
        image_path = os.path.join(subdir, file)
        base_filename = os.path.basename(image_path)
        all_base_filenames.append(base_filename)

        # Load and process the AFM image
        image = pySPM.Bruker(image_path)
        height = image.get_channel("Height Sensor")
        top = height.correct_lines(inline=False)
        top = top.correct_plane(inline=False)
        top = top.filter_scars_removal(.7, inline=False)
        top = top.correct_plane(inline=False)
        top = top.corr_fit2d(inline=False).offset([[10, 0, 10, 511]]).filter_scars_removal()
        mask0 = top.get_bin_threshold(.5, high=False)
        mask1 = binary_erosion(mask0, disk(3))
        top = top.corr_fit2d(mask=mask1, inline=False).offset([[10, 0, 10, 511]]).filter_scars_removal().correct_plane().correct_lines().zero_min()
        top = top.correct_lines(inline=False)
        top = top.correct_plane(inline=False)
        grid = pd.DataFrame(top.pixels)

        # Find the corresponding CSV file for the image
        csv_files = glob.glob(os.path.join(input_coordinates_folder, f'{base_filename}_coordinates.csv'))

        if not csv_files:
            print(f"No CSV file found for {base_filename}")
            continue

        csv_file_path = csv_files[0]
        print(f"Found CSV file: {csv_file_path}")

        try:
            df_points = pd.read_csv(csv_file_path)
        except FileNotFoundError:
            print(f"CSV file not found: {csv_file_path}")
            continue

        # Add a new column to the CSV file with filename
        df_points['image_filename'] = [f"{base_filename}_{i+1:06d}" for i in range(len(df_points))]

        # Iterate over the coordinates in the CSV file
        for index, row in df_points.iterrows():
            start = (row['start_y'], row['start_x'])
            goal = (row['end_y'], row['end_x'])

            # Perform A* pathfinding with timeout
            try:
                path = astar_pathfinding_timeout(grid, start, goal)

                if path:
                    print(f"Found path from {start} to {goal}")

                    # Append coordinates to the list
                    coordinates_df = pd.DataFrame({
                        'image_filename': [f"{base_filename}_{index:06d}" for _ in path],
                        'x': [coord[1] for coord in path],
                        'y': [coord[0] for coord in path]
                    })
                    all_coordinates.append(coordinates_df)

                    # Calculate angles for the path
                    path_angles = calculate_angles(path)
                    all_path_angles.extend(path_angles)

                    # Extract the data values for each coordinate in the path
                    path_data_values = [grid.iloc[y, x] for y, x in path]
                    all_data_values.extend(path_data_values)

                    # Calculate contour length and shortest distance
                    contour_length = calculate_contour_length(path)
                    shortest_distance = calculate_shortest_distance(start, goal)
                    contour_lengths.append(contour_length)
                    shortest_distances.append(shortest_distance)

                    # Append filenames with path numbers to arrays
                    path_number = index
                    filename_with_path = f"{base_filename}_{path_number:06d}"

                    data_filenames.extend([filename_with_path] * len(path_data_values))
                    metrics_filenames.append(filename_with_path)
                    angles_filenames.extend([filename_with_path] * len(path_angles))

            except timeout_decorator.timeout_decorator.TimeoutError:
                print(f"A* pathfinding timed out for {start} to {goal}. Skipping...")
                continue

# Print lengths for troubleshooting
print(f"Length of all_data_values: {len(all_data_values)}")
print(f"Length of contour_lengths: {len(contour_lengths)}")
print(f"Length of shortest_distances: {len(shortest_distances)}")

# Save data values to a CSV file with modified image_filename
output_data_df = pd.DataFrame({
    'image_filename': data_filenames,
    'data_values': all_data_values
})
output_data_df.to_csv(os.path.join(output_path_folder, base_filename + '_height_nm.csv'), index = False)

# Save lengths and distances to separate CSV files
output_metrics_df = pd.DataFrame({
    'image_filename': metrics_filenames,
    'contour_length': contour_lengths
})
output_metrics_df.to_csv(os.path.join(output_path_folder, base_filename + '_contour_length_pixels.csv'), index = False)

output_distances_df = pd.DataFrame({
    'image_filename': metrics_filenames,
    'shortest_distance': shortest_distances
})
output_distances_df.to_csv(os.path.join(output_path_folder, base_filename + '_shortest_distance_pixels.csv'), index = False)

# Save angles to a CSV file
output_angles_df = pd.DataFrame({
    'image_filename': angles_filenames,
    'path_angle_degrees': all_path_angles
})
output_angles_df.to_csv(os.path.join(output_path_folder, base_filename + '_path_angles.csv'), index = False)

# Save all coordinates to a CSV file
all_coordinates_df = pd.concat(all_coordinates, ignore_index=True)
all_coordinates_df.to_csv(os.path.join(output_path_folder, base_filename + '_path_coordinates.csv'), index=False)
