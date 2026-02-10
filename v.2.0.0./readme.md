# AFMPL v.2.0.0.
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Code written for the project entitled "Studies on the conformation and rheological properties of pectins depending on the postharvest maturity of the plant source", supported by the National Science Center, Poland (grant nr - 2023/51/B/NZ9/02121). More information of project: https://projekty.ncn.gov.pl/index.php?projekt_id=591903

Setup is highly inspired by the FiberApp script, described previously in paper:

- Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.
Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).

Tools utilized:
- Visual Studio Code release: 1.109.0
- Python release: 3.9.7.

## Usage
1. Configure input/output: Open AFMPL v.2.0.0.py and modify the configuration section:
- INPUT_FOLDER = r'path/to/your/input/folder'
- OUTPUT_FOLDER = r'path/to/your/output/folder'

2. Run the tool.

3. Using the GUI:
- Sliders: adjust the height threshold manually to isolate fibers (Fig. 1.);
- Autotune: click to automatically find the best threshold based on the parameters set in the text boxes;
- Full update: click to run the heavy analysis (skeletonization) and see the green/blue fiber traces;
- Save & Next: exports the data and moves to the next file in the folder.
