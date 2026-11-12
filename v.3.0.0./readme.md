# AFMPL v3.0.0.
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Code written for the project entitled "Studies on the conformation and rheological properties of pectins depending on the postharvest maturity of the plant source", supported by the National Science Center, Poland (grant nr - 2023/51/B/NZ9/02121). More information of project: https://projekty.ncn.gov.pl/index.php?projekt_id=591903

Setup is highly inspired by the FiberApp script, described previously in paper:

- Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.
Current setup consist of two scripts:
001_afmpl_v3.0.0..py;
002_afmpl_v3.0.0..R.

Codes allow to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone/sidechain and aggregate recognition, output and analyse its main data (height, contour length, persistence length, contour coordinates, aggregate volume, degree of aggragstion, etc.).

Tools utilized:
- Visual Studio Code release: 1.145.3
- Python release: 3.12

## 001_afmpl_v3.0.0..py
## Usage
1. Configure input/output: Open 001_afmpl_v3.0.0..py and modify the configuration section:
INPUT_FOLDER = r'path/to/your/input/folder'
OUTPUT_FOLDER = r'path/to/your/output/folder'

2. Run the tool.Using the GUI:
- Sliders: adjust the height thresholds manually to isolate fibers and aggregates (Fig. 1). You can also adjust the minimum pixel size (Min Size px) to filter out small objects.
<img width="2560" height="1389" alt="image" src="https://github.com/user-attachments/assets/4c95ec46-d37b-41bf-bce3-ec51b8184eb5" />
<img width="2560" height="1389" alt="image" src="https://github.com/user-attachments/assets/7a31dae1-da1a-4ace-a70d-c411ba775b4a" />

- Autotune: click to automatically find the best thresholds based on the Sigma sensitivity parameters set in the text boxes (Fig. 2). This auto-tune relies on Median Absolute Deviation (MAD) to calculate robust thresholds.
<img width="2560" height="1389" alt="image" src="https://github.com/user-attachments/assets/bff874b8-effb-4c91-acbc-b257e228d740" />

- Full update: click to run the heavy analysis (skeletonization and exact volume calculation) and see the green/blue fiber traces alongside the aggregate detection.
- Navigation: Use < PREV to go back to the previous file, or SKIP > to bypass the current file without saving.
- Save & Next: exports the data to an Excel file and PNG visualizations, then moves to the next file in the folder.

## Examples
### Fig. 3. Fiber height .xlsx sheet. 
For the "structure_id" column those 1_, 2_, etc. values define molecule number; those _0 values define backbone values, while others (_1, _2, etc.) - sidechain values. height_nm is a difference of a raw_height_nm (meaning those of a fiber height laying on some non-zero background), while bg_median_nm is a median background height, subtracted from raw_height_nm. Additionally, if aggregates are detected, an "aggregates" sheet is generated containing the aggregate ID, area, mean height, maximum height, and exact volume data.   
<img width="1060" height="895" alt="image" src="https://github.com/user-attachments/assets/366aaf54-d761-4271-b73f-347b52fef0f4" />

### Fig. 4. Fiber path coordinates as a row sequence of x and y values.
For the "structure_id" column those 1_, 2_, etc. values define molecule number; those _0 values define backbone values, while others (_1, _2, etc.) - sidechain values.Additional notes
<img width="626" height="989" alt="image" src="https://github.com/user-attachments/assets/f0c85528-b4bc-4b15-960d-68d0dfa2f3e4" />

!Sometimes in Bruker, height sensor may be called either "Height Sensor" or "Sensor"LicenseThis project is licensed under the MIT 

## License 
See the LICENSE file for details.

