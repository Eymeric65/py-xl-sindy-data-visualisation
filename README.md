# py-xl-sindy-data-visualisation
The visualisation website for the PY-XL-SINDY research paper

This is the main repository for data visualisation concerning the package `py-xl-sindy`. This package is shipped with some script for generating data using the main python library and a site using **Vite** on React and typescript.

The site is hosted on GitHub pages : https://eymeric65.github.io/py-xl-sindy-data-visualisation/ 

I am using singularity for debug using node:24

```sh
singularity shell docker://node:24-alpine
```

## Singularity image 

I use the following commands to pull the singularity images used for the site and for the rapids base image (generating with GPU).
```sh

singularity pull site_image.sif  docker://node:24-alpine

singularity pull rapids_base.sif docker://aidockorg/python-cuda:3.10-v2-cuda-12.4.1-cudnn-runtime-22.04

```