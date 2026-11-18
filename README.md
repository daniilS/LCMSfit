# LCMSfit
Script for simple baseline correction and deconvolution of LCMS traces, used by the Hunter Group.

## Installation
1. Right click [this link](https://raw.githubusercontent.com/daniilS/LCMSfit/refs/heads/main/LCMSfit.py) and download the script.
2. Wherever you saved the file, run:
   
   `python3 -m pip install --requirements-from-script LCMSfit.py` (macOS, Linux)
   
   `pip install --requirements-from-script LCMSfit.py` (Windows)
3. If the above doesn't work, you may need to [update pip](https://pip.pypa.io/en/stable/installation/#upgrading-pip), or failing that, manually specify the dependencies as
  
   `(python3 -m) pip install numpy scipy pybaselines matplotlib`

## Usage
1. Export your LCMS trace to a CSV. First column: time, second column: intensity. No header row.
2. Run using `python3 LCMSfit.py` (`python LCMSfit.py` on Windows)
3. Drag the slider to fit the appropriate baseline.
4. Click on each peak to add an initial guess for a peak location. Right click to remove points.
5. Press the `Fit` button. Add or remove peak locations and repeat the fitting until you're satisfied with it.
6. Press the `Save` buttons to export the peak locations and areas, or the baseline-corrected trace.
