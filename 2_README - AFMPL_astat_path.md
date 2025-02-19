# AFMPL
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). 
Code written for the project entitled "Studies on the conformation and rheological properties of pectins depending on the postharvest maturity of the plant source", supported by the National Science Center, Poland (grant nr - 2023/51/B/NZ9/02121). More information of project: [https://projekty.ncn.gov.pl/index.php?projekt_id=591903](https://projekty.ncn.gov.pl/index.php?projekt_id=604538)

Setup is highly inspired by the FiberApp script, described previously in paper: 
- Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.

Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).
- Visual Studio Code release: 1.93.1
- Python release: 3.12.4. 64-bit
- RStudio version: 2022.07.1 Build 554

> Warning! There are no guaranties this code will run on your machine.

## AFMPL_astat_path.py
The script imports Bruker AFM images, and processes them in a way, similar to 1_AFMPL_sr=tart_to_end_point.py code. With 'astar_pathfinding_timeout' script performs A* pathfinding algorithm with a timeout, returning list of tuples representing the path from start to goal. With 'heuristic' script calculates contour length of a path, returning list of tuples representing the path. 'calculate_shortest_distance' allows to calculate the shortest distance between start and end points of each path.
Script allows to extracts various metrics, such as fiber height, fiber contour length, fiber contour coordinates, etc. to csv files.

## Examples
Several examples of A* pathfinding algorithm: 
![OPUS26_DASP_0 01_S1_A_S_3 054_284_zoomed_path](https://github.com/user-attachments/assets/55811d03-e4f9-46ca-9c76-8f3be4734083)
![OPUS26_DASP_0 01_S1_A_S_3 054_300_zoomed_path](https://github.com/user-attachments/assets/d79c4e89-e4c0-4466-8d04-9e546560217a)
![OPUS26_DASP_0 01_S1_A_S_3 055_198_zoomed_path](https://github.com/user-attachments/assets/b044ff77-79f8-4d2b-bd5d-629ec9a0762d)
![OPUS26_DASP_0 01_S1_A_S_3 054_167_zoomed_path](https://github.com/user-attachments/assets/3e621ed6-2442-48d3-a80f-a42bd632c827)

Example of a height output:

![1](https://github.com/user-attachments/assets/47de9f65-a59b-43d3-9f99-6c8eff57f658)

Example of a contour length (in pixels) evaluation output:

![2](https://github.com/user-attachments/assets/ee3192cc-d0dd-4b51-8c96-56123aed2f5c)

Example of a shortest distance (in pixels) evaluation output:

![3](https://github.com/user-attachments/assets/a35021f5-d2b6-4ce0-bcb9-5f3170de95d6)

Example of a path coordinates output:

![4](https://github.com/user-attachments/assets/63d27844-d3c0-4773-a42f-203e3109c7d1)


