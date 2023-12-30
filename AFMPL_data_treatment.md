# AFMPL v.1.0
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Setup is highly inspired by the FiberApp script, described previously in paper: 
Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.
Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).
- Visual Studio Code version: 1.85.1
- Python version: 3.12.1.
- RStudio version: 2022.07.1 Build 554

## AFMPL_astat_path.py
The script imports output data of AFMPL_astat_path.py script, processes them, routput and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.). Main accent in current code is focused on evaluation of persistence length by three methods - mean-squared end-to-end distance (MSED), bond correlation function (BCF), and mean-squared midpoint displacement (MSMD). Current methods on persistence length evaluation were previously show in paper:
Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c. Further method explanation is taken from the respected paper, and for more details, I strongly refer you to that paper.

## Mean-squared end-to-end distance (MSED)
One of the most practical and widely used methods for thepersistence length estimation is to calculate the mean-squaredend-to-end distance (MSED) between contour segments. This characteristic for a WLC model in 2D hasthe following theoretical dependence:
$⟨R^2⟩ = 4λ*(l−2*λ(1 − e^(−l/(2*λ)))$


## Bond correlation function (BCF)



## Mean-squared midpoint displacement (MSMD)
