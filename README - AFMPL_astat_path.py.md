# AFMPL v.1.0
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Setup is highly inspired by the FiberApp script, described previously in paper: 
Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.
Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).
Visual Studio Code version: 1.85.1
Python version: 3.12.1.
RStudio version: 2022.07.1 Build 554

## AFMPL_astat_path.py
This Python script performs path planning on Atomic Force Microscopy (AFM) images using the A* algorithm. It analyzes the topography of AFM images, calculates paths between specified points, and extracts various metrics, such as height, contour length, fiber tangent angles, contour coordinates, etc.

## Usage
Set the input and output folders in the script.
Ensure the required libraries are installed (pip install pandas numpy pySPM scikit-image matplotlib timeout_decorator).
Run the script.

## Functions
### astar_pathfinding_timeout: A* pathfinding algorithm with a timeout.
### Parameters:
grid: 2D DataFrame representing the terrain.
start: Tuple (y, x) representing the starting point.
goal: Tuple (y, x) representing the goal point.
visualize: Boolean indicating whether to visualize the path.
Returns: List of tuples representing the path from start to goal.

### heuristic: Heuristic function for the A* algorithm.
### Parameters:
a: Tuple (y, x) representing the current point.
b: Tuple (y, x) representing the goal point.
distance_weight: Weight for distance in the heuristic calculation.
value_weight: Weight for terrain value in the heuristic calculation.
Returns: Heuristic value.

### calculate_contour_length: Calculate the contour length of a path.
### Parameters:
path: List of tuples representing the path.
Returns: Contour length.

### calculate_shortest_distance: Calculate the shortest distance between start and end points.
### Parameters:
start: Tuple (y, x) representing the starting point.
end: Tuple (y, x) representing the end point.
Returns: Shortest distance.

### calculate_angles: Calculate angles between three consecutive points in a path.
### Parameter: path: List of tuples representing the path.
Returns: List of angles in degrees.

## Data Output
The script generates several CSV files containing data values, contour lengths, shortest distances, and path angles.

## Examples
Several examples of A* pathfinding algorithm: 
![Figure_1](https://github.com/vchibrikov/AFMPL/assets/98614057/77ff4e29-8cf7-4e0b-b5e4-15aa46085276)
![Figure_2](https://github.com/vchibrikov/AFMPL/assets/98614057/33f6dd7e-a4be-4723-b381-89ad1c4bf463)
![Figure_3](https://github.com/vchibrikov/AFMPL/assets/98614057/da7cf4c3-c71d-48f5-a8c6-01ebbf86eb19)
![Figure_4](https://github.com/vchibrikov/AFMPL/assets/98614057/a698c1e7-07c9-4ff7-b3fc-c5912868a0c5)


