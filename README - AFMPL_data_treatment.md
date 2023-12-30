# AFMPL v.1.0
AFMPL is a Python and R hardcode setup to perform image analysis of fiber-like objects, captured by means of atomic force microscopy (AFM). Setup is highly inspired by the FiberApp script, described previously in paper: 
- Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.

Current setup consist of three scripts - AFMPL_start_end_point.py, AFMPL_astat_path.py, and AFMPL_data_treatment.R - and allows to handle raw Nanoscope AFM images, perform its correction, conduct semi-automatic fiber backbone recognition with A* pathfinding algorithm, output and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.).
- Visual Studio Code version: 1.85.1
- Python version: 3.12.1.
- RStudio version: 2022.07.1 Build 554

## AFMPL_astat_path.py
The script imports output data of AFMPL_astat_path.py script, processes them, routput and analyse its main data (height, contour length, persistence length, fiber and segment tangent angles, contour coordinates, etc.). Main accent in current code is focused on evaluation of persistence length by three methods - mean-squared end-to-end distance (MSED), bond correlation function (BCF), and mean-squared midpoint displacement (MSMD). Current methods on persistence length evaluation were previously show in paper:
- Usov, I., & Mezzenga, R. (2015). FiberApp: an open-source software for tracking and analyzing polymers, filaments, biomacromolecules, and fibrous objects. Macromolecules, 48(5), 1269-1280. DOI: 10.1021/ma502264c.

Further method explanation is taken from the respected paper, and for more details, I strongly refer you to that paper.

## Mean-squared end-to-end distance (MSED)
One of the most practical and widely used methods for thepersistence length estimation is to calculate the mean-squaredend-to-end distance (MSED) between contour segments. This characteristic for a worm-like chains model in 2D has the following theoretical dependence:

$R^2 = 4 \lambda (l - 2 \lambda (1 - e^{-\frac{l}{2\lambda}}))$

where $λ$ is the persistence length and $R$ is the direct distance between any pair of segments along a contour separated by an arc length $l$.

Graphical respresentation of MSED method is provided on image below:
![PERSISTENCE_LENGTH_MSED_30 12 2023_VC](https://github.com/vchibrikov/AFMPL/assets/98614057/43bb5b27-5a6f-40f6-9592-8c982204e0eb)

## Bond correlation function (BCF)
The bond correlation function (BCF) is the most general way to evaluate the persistence length. For a worm-like chains in 2D, it corresponds to the following equation:

$\cos(\theta) = e^{-\frac{l}{2\lambda}}$

 where $λ$ is the persistence length, $θ$ is the angle (in rad) between tangent directions of any two segments along a fibril contour separated by an arc length $l$.

Graphical respresentation of BCF method is provided on image below:
![Copy of PERSISTENCE_LENGTH_BCF_30 12 2023_VC (1)](https://github.com/vchibrikov/AFMPL/assets/98614057/138936e0-6f3f-476f-afb0-3e3896e4d556)

## Mean-squared midpoint displacement (MSMD)

A different method thatcan be successfully applied only to very stiff fiber-like objects ($l < λ$) is the mean-squared midpoint displacement (MSMD). The equation, describing the behavior of a midpoint deviation has the following form:

$u^2 = \frac{l^3}{48\lambda}$

where $λ$ is the persistence length, $u^2$ is the mean-squared midpoint displacement between any pair of segments along a contour, separated by an arc length $l$. This expression is derived with an assumption that thesedeviations are small in comparison to the corresponding arclengths ($|u|≪l$).

Graphical respresentation of MSMD method is provided on image below:
![PERSISTENCE_LENGTH_MSMD_30 12 2023_VC](https://github.com/vchibrikov/AFMPL/assets/98614057/fa7e65e2-8c0f-4cf8-a390-f551b960e0fc)

