==========================================================
### Experimental Reinforcement learning scheduling

In this branch a reinforcement learning heuristic is trained to reduce the search space complexity
of the scheduling problem. In this manner, we replace the heuristic mentioned in the report.

To run, you need two extra python modules in this specific versions: 
tensorflow==1.14.0
matplotlib==3.0.2

## Ubuntu 18.0
0) Open a terminal
1) Activate the environment
```
conda activate remap_d6_1
```
2) Move to the repository in your system
```
pip install tensorflow==1.14.0
```
3) Move to the repository in your system
```
pip install matplotlib==3.0.2
```
4) Then run main.py according to the default config file (which has only the rl flag enabled)
```
python main.py
```