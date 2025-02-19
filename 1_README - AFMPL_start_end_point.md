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
Raw Nanoscope image imported: 
(https://github.com/vchibrikov/AFMPL/assets/98614057/3830dba3-9d2c-4f05-b6b1-fc36164c2762)

Processed AFM height sensor data (with an implemented removal of polynomial background, scars, plane correction):
<img width="1728" alt="1" src="https://github.com/user-attachments/assets/fc86ce13-8e34-4798-84b3-9862528dd375" />

Slidebar threshold image filtering applied to raw data:
<img width="1728" alt="2" src="https://github.com/user-attachments/assets/2e840579-23fd-4385-8c41-b021594f0703" />

Region of interest zoomed in:
<img width="1728" alt="3" src="https://github.com/user-attachments/assets/64e2beae-3aa0-41c4-b4cb-4303daf56301" />

Interaction with a data - defining start and end points of a fiberlike object:
<img width="1728" alt="4" src="https://github.com/user-attachments/assets/733e8c63-a523-4d7b-9876-ddebe535826f" />

Example of an output data structure:
![5](https://github.com/user-attachments/assets/489e627a-2b01-41fb-b472-27664034a1fd)

## License
This project is licensed under the MIT License - see the LICENSE file for details.

> For any issues or feature requests, feel free to open an issue in this repository.
