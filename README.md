# Installation 
Instructions for kernel based Linux OS's (like ubuntu) and Windows are given bellow. The instructions and the code was tested on Ubuntu 18 and Windows 10. Since the instalation is made via Anaconda virtual environments, MAC OS is also an option, but it was not tested. At the end of the document there are instructions to run the code.

## Pre-requirements
The installation is made via Anaconda 3. So the installation of Anaconda 3 is required and Jupyter Notebook/Jupyter Lab

## Ubuntu 18.0
0) Open a terminal
1) Clone the repository 
```
cd ~
git clone [repo_link]
```
2) Move to the repository in your system
```
cd traces
```
3) Install the anaconda environment
```
conda env create -f remap_env_linux.yml
```
4) Load the anaconda environment
```
conda activate remap_d6_1
```
5) Install this package on the environment
```
pip install -e .
```

## Windows 10
0) Download the repository through a git software or by travelling to the website and download as a zip (unpack it afterwards)
1) Open a Anaconda 
2) On the left tab, click on "Environments"
3) On the bottom left click on import button.
4) Select the icon "folder", then travel to the downloaded repository directory and select the yaml file "remap_env_windows.yml" then click ok. 
4) Still on the "Environments" tab, click on "remap_d6_1" to load the environment
--------------------------------------------
### Installing our package in the Anaconda environment
5) Search on Windows for "Anaconda Prompt (Anaconda3)" this should open a command line/terminal.
6) Travel to the repository in your system, if you downloaded it and unpackaed it, it should be:
```
cd Downloads/traces-master
```
7) Activate our remap environment where we want to install this package:
```
conda activate remap_d6_1
```
8) Install this package (messages of successfully installed should appear at the end):
```
python setup.py install
```
you should be on a folder with a setup.py

9) Dowload the treelib repository and unpack https://github.com/DanielLSM/treelib
10) Travel to the repository in your system, if you downloaded it and unpackaed it, it should be:
```
cd Downloads/treelib-master
```
you should be on a folder with a setup.py
11) 
```
python setup.py install
```
installation is now complete
# Running the code
Here two alternatives (command-line interface and jupyter notebook/lab) for each OS are presented to run the code.

## Before running
The execution of the code is made from a config.yaml which controls the pace of the execution. Default parameters are given on the config.yaml, and a first run with this file is recommended. To turn off parts of the execution of the full program in terms of A-check/C-check and tasks planning, simply change the flags from True to False. The parameters for each planning algorithm were explained in the final report. 


## Ubuntu 18.0

### - command-line interface
1) Move the directory to the main.py
```
cd ~/traces/tr/core
```
2) Run with the pre-execution flag on (needed for the first run)
```
python main.py -pc True
```
3) Let the full program run, then find excel files for check and task planning on the created folders ~/traces/tr/core/check_planning and ~/traces/tr/core/task_planning respectively 
4) Additionally a metrics file can be run at the end to find some metrics computed for the final report
```
python metrics.py
```
A serious of figures presenting metrics should appear, feel free to terminate the program (it will loop through all checks for a total of about 500 figures)

### - Jupyter Notebook/Lab

1) Move the directory to the main.py
```
cd ~/traces/tr/core
```
2) Install jupyter lab/notebook
```
pip install jupyter
```
3) Run Jupyter
```
jupyter lab
```
or
```
jupyter notebook
```
4) Open the notebook "ReMAP D6.1.ipynb"
5) Run each cell from top to bottom
A series of figures presenting metrics should appear, feel free to terminate the program (it will loop through all checks for a total of about 500 figures)


## Windows 10

### - command-line interface

0) Search on Windows for "Anaconda Navigator (cmd)" this should open a command line/terminal.
1) Activate our remap environment where we want to install this package:
```
conda activate remap_d6_1
```
2) Move the directory to the main.py
```
cd Downloads/traces-master/tr/core
```
3) Run with the pre-execution flag on (needed for the first run)
```
python main.py -pc True
```
4) Let the full program run, then find excel files for check and task planning on the created folders "Downloads/traces/tr/core/check_planning" and "Downloads/traces/tr/core/task_planning" respectively 
5) Additionally a metrics file can be run at the end to find some metrics computed for the final report
```
python metrics.py
```
A serious of figures presenting metrics should appear, feel free to terminate the program (it will loop through all checks for a total of about 500 figures)

### - Jupyter Notebook/Lab

1) Open Anaconda GUI interface
2) On the left tab select "home" tab
3) Open Jupyter Lab or Jupyter Notebook
4) Open the notebook "ReMAP D6.1.ipynb"
5) Run each cell from top to bottom
