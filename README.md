# Self-driving-car-simulation-AI
First to install the required packages from the below command
```pip install requirements.txt```

To run the program , run this command from the root directory
```python3 src/main.py```


We have simulated a self driving car using NEAT algorithm
## Challenges Faced

### Reward Function 
+ Reward Function is based on the distance covered by the agent.
  + Oscillations
  + Vibration

### Updated reward function:
+ based on laps covered and distance travelled.



### Performance

### Elimination of Species

## Reward Function

$$Reward = D + \sum_{each frame} L * Lap Reward $$

## Inputs
1. Ray cast 1(Front)
2. Ray cast 2(Front-right)
3. Ray cast 3(Front-left)
4. Ray cast 4(Right)
5. Ray cast 5(Left)
6. Speed of the car
##outputs
1. Steering value
2. Acceleration value
