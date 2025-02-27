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

## AFMPL_start_end_point.py
The script imports Bruker AFM images, processes them, and creates heatmaps using Matplotlib for visualization. With 'on_click(event)', script
handles mouse button clicks, allowing for determination of the coordinates of fiber ends, with its further storage. With 'on_scroll(event)', script adjusts the plot limits based on the direction of the scroll, allowing to zoom image in and out. Main script initializes a list (selected_coordinates) to store fiber ends coordinates and specifies input and output folders. In addition, script iterates over the image files in the specified input folder, processes each image, and creates a heatmap for visualization. Output CSV filenames with defined coordinates are generated based on the current image filename with the suffix _coordinates.csv. Input and processed AFM images, as well as output image interaction interface and file of fiber coordinates are given below.

## Examples

Processed AFM height sensor data (with an implemented removal of polynomial background, scars, plane correction):
<img width="1340" alt="Знімок екрана 2025-02-26 о 13 00 09" src="https://github.com/user-attachments/assets/90665b14-7502-46ea-a603-f996f8ea164c" />

Slidebar threshold image filtering applied to raw data:
<img width="1343" alt="Знімок екрана 2025-02-26 о 13 00 26" src="https://github.com/user-attachments/assets/bb92ee11-763b-4541-acac-1fcaa503d131" />
<img width="1337" alt="Знімок екрана 2025-02-26 о 13 00 57" src="https://github.com/user-attachments/assets/768ff8c6-52b7-456a-814e-87ded3b1c18b" />

Region of interest zoomed in, as well as interaction with a data - defining start and end points of a fiberlike object:
<img width="1346" alt="Знімок екрана 2025-02-26 о 13 01 26" src="https://github.com/user-attachments/assets/62b29ff9-86cc-4623-ad3f-08427367f856" />

Example of an output data structure:

![5](https://github.com/user-attachments/assets/489e627a-2b01-41fb-b472-27664034a1fd)

## License
This project is licensed under the MIT License - see the LICENSE file for details.

> For any issues or feature requests, feel free to open an issue in this repository.
