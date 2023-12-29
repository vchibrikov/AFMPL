# AFMPL v.1.0

AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Setup is highly inspired by the FiberApp script, described previously in paper: 
Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.
Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).

# AFMPL_start_end_point.py

The script imports Bruker AFM images, processes them, and creates heatmaps using Matplotlib for visualization. With 'on_click(event)', script
handles mouse button clicks, allowing for determination of the coordinates of fiber ends, with its further storage. With 'on_scroll(event)', script adjusts the plot limits based on the direction of the scroll, allowing to zoom image in and out. Main script initializes a list (selected_coordinates) to store fiber ends coordinates and specifies input and output folders. In addition, script iterates over the image files in the specified input folder, processes each image, and creates a heatmap for visualization. Output CSV filenames with defined coordinates are generated based on the current image filename with the suffix _coordinates.csv. Input and processed AFM images, as well as output image interaction interface and file of fiber coordinates are given below.

Raw AFM image imported: 
![Figure_0](https://github.com/vchibrikov/AFMPL/assets/98614057/3830dba3-9d2c-4f05-b6b1-fc36164c2762)

Processed AFM height sensor data (with an implemented removal of polynomial background, scars, plane correction):
![Figure_1](https://github.com/vchibrikov/AFMPL/assets/98614057/a577aee2-0a72-4118-9753-8e0a0511e4fe)

