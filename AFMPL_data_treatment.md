# AFMPL v.1.0
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Setup is highly inspired by the FiberApp script, described previously in paper: 
Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.
Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).
- Visual Studio Code version: 1.85.1
- Python version: 3.12.1.
- RStudio version: 2022.07.1 Build 554

## AFMPL_astat_path.py
The script imports Bruker AFM images, processes them, and creates heatmaps using Matplotlib for visualization (optionally). With 'astar_pathfinding_timeout' script performs A* pathfinding algorithm with a timeout, returning list of tuples representing the path from start to goal. With 'heuristic' script calculates contour length of a path, returning list of tuples representing the path. 'calculate_shortest_distance' allows to calculate the shortest distance between start and end points of each path. 'calculate_angles' allow to calculate angles between three consecutive points in a path, resulting list of angles in degrees as an output.
Script allows to extracts various metrics, such as fiber height, fiber contour length, fiber tangent angles, fiber contour coordinates, etc. to csv files.
