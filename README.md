[![DOI](https://zenodo.org/badge/661665175.svg)](https://zenodo.org/doi/10.5281/zenodo.10646763)

# Multi-pad Agarose Plate (MAP) imaging

This repository contains all the information you need to get up and running with imaging using the multipad agarose plate (MAP).

1. CAD information and instructions for building the MAP.
2. Detailed protocol for loading the pads with agar, including code and setup instructions for doing so using the Opentrons OT-2 pipetting robot.
3. Example of how to use the PadImaging package we developed to analyse sample images from our agar pad imaging captured on the MAP platform. There are three notebooks, one outlining how to compress z-stacks, one outlining how to segment the images and one outlining how to segment and extract the data from time-series of images.

## Getting started with the analysis code

- Clone this repository.
- Make a Python virtual environment.
- Install the requirements with `pip install -r requirements.txt` into that environment.
- Open one of the Jupyter Notebooks to see how this can be used. Get started right away with example images included in this repository.

