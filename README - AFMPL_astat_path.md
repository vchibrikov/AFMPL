# AFMPL v.1.0
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Setup is highly inspired by the FiberApp script, described previously in paper: 
Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.
Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).
Visual Studio Code version: 1.85.1
Python version: 3.12.1.
RStudio version: 2022.07.1 Build 554

## AFMPL_astat_path.py
The script imports Bruker AFM images, processes them, and creates heatmaps using Matplotlib for visualization (optionally). With 'astar_pathfinding_timeout' script performs A* pathfinding algorithm with a timeout, returning list of tuples representing the path from start to goal. With 'heuristic' script calculates contour length of a path, returning list of tuples representing the path. 'calculate_shortest_distance' allows to calculate the shortest distance between start and end points of each path. 'calculate_angles' allow to calculate angles between three consecutive points in a path, resulting list of angles in degrees as an output.
Script allows to extracts various metrics, such as fiber height, fiber contour length, fiber tangent angles, fiber contour coordinates, etc. to csv files.

## Examples
Several examples of A* pathfinding algorithm: 
![Figure_1](https://github.com/vchibrikov/AFMPL/assets/98614057/77ff4e29-8cf7-4e0b-b5e4-15aa46085276)
![Figure_2](https://github.com/vchibrikov/AFMPL/assets/98614057/33f6dd7e-a4be-4723-b381-89ad1c4bf463)
![Figure_3](https://github.com/vchibrikov/AFMPL/assets/98614057/da7cf4c3-c71d-48f5-a8c6-01ebbf86eb19)
![Figure_4](https://github.com/vchibrikov/AFMPL/assets/98614057/a698c1e7-07c9-4ff7-b3fc-c5912868a0c5)

Example of a contour length (in pixels) evaluation output:
![Screenshot 2023-12-29 at 22 11 11](https://github.com/vchibrikov/AFMPL/assets/98614057/e4265385-5a01-4029-9c89-44e53a3537fe)

Example of a shortest distance (in pixels) evaluation output:
![Screenshot 2023-12-29 at 22 12 44](https://github.com/vchibrikov/AFMPL/assets/98614057/5726edd5-b89a-4d4b-ad0f-8d329d0fa521)

Example of a path heigth (in nm) evaluation output:
![Screenshot 2023-12-29 at 22 11 38](https://github.com/vchibrikov/AFMPL/assets/98614057/277c21a4-7f23-4a56-9e76-f6a3672e033c)

Example of a path angle (in deg.) evaluation output:
![Screenshot 2023-12-29 at 22 12 04](https://github.com/vchibrikov/AFMPL/assets/98614057/9cc0a78c-1849-4edc-a0d3-8009d2dcf970)

Example of a path coordinates (x;y) evaluation output:
![Screenshot 2023-12-29 at 22 12 30](https://github.com/vchibrikov/AFMPL/assets/98614057/c7e557ae-e44a-45d9-a381-874e29c7cedc)

