#This is from my repository https://github.com/DanielLSM/drl-agents
import time
import numpy as np

import gym
from gym import spaces

from drl.tools.misc_util import LinearSchedule
from drl.agents.dqn import DQNAgent
from drl.managers.base import Manager
from drl.core.memory import ReplayBuffer
from drl.tools.plotter_util import Plotter

#obs is from type numpy array
# array([ 0.04109495, -0.19198027,  0.05014294,  0.34569618])
#action is from type numpy array
# array([0])
#action[0] is from type numpy.int
# <class 'numpy.int64'>
# reward is from type float
# 1.0
# done is type boolean


# here module the binary scheduling tree as an RL environment
class TreeScheduleRL:
    def __init__(self, cp, obs_dim=11, act_dim=2):

        self.observation_space_shape = (obs_dim, )
        self.observation_space = spaces.Box(low=0,
                                            high=1,
                                            shape=self.observation_space_shape,
                                            dtype=np.float32)
        self.action_space = spaces.Discrete(act_dim)
        self.spec = "Tree RL"
        self.cp = cp

    def reward(self, done):
        #maybe include depth as well
        return -10 if done else 1

    def make_obs(self, node, depth):
        # includes top 5 ratios
        top_ratio_aircraft = list(node.fleet_state.keys())[0:5]
        ratios = []

        for aircraft in top_ratio_aircraft:
            ratios.append(node.fleet_state[aircraft]['TOTAL-RATIO'])

        # includes some info about depth... as in 6 stages
        if depth <= self.cp['a-checks']['beta_1']:
            stage = [0, 0, 0, 0, 0, 1]
        elif depth <= self.cp['a-checks']['beta_2']:
            stage = [0, 0, 0, 0, 1, 0]
        elif depth <= self.cp['a-checks']['beta_3']:
            stage = [0, 0, 0, 1, 0, 0]
        elif depth <= self.cp['a-checks']['beta_4']:
            stage = [0, 0, 1, 0, 0, 0]
        elif depth <= self.cp['a-checks']['beta_5']:
            stage = [0, 1, 0, 0, 0, 0]
        else:
            stage = [1, 0, 0, 0, 0, 0]

        obs = ratios + stage
        obs = np.array(obs)

        return obs

    def make_experience_tuple(self, parent, child, done, depth):
        # return obs, action[0], reward, next_obs, float(done)

        obs = self.make_obs(parent, depth)
        next_obs = self.make_obs(child, depth)
        reward = self.reward(done)
        action = child.action_maintenance

        # import ipdb
        # ipdb.set_trace()
        return obs, action, reward, next_obs, done


class DQNManager:
    def __init__(self,
                 env,
                 seed=None,
                 lr=5e-2,
                 gamma=1.0,
                 buffer_size=50000,
                 total_timesteps=100000,
                 exploration_fraction=0.05,
                 final_epsilon=0.1,
                 learning_starts=100,
                 train_freq=1,
                 batch_size=32,
                 target_network_update_freq=10,
                 max_steps_per_episode=10000,
                 render_freq=100,
                 **kwargs):
        Manager.__init__(**locals())
        self.env = env
        self.obs_space = env.observation_space
        self.action_space = env.action_space

        self.agent = DQNAgent(self.obs_space, self.action_space)
        self.memory = ReplayBuffer(self.buffer_size)
        self.plotter = Plotter(num_lines=1,
                               title=env.spec,
                               x_label='episodes',
                               y_label='total_reward',
                               smooth=True)
        #TODO: this should actually by smarter...
        # exploring linearly based on timesteps is really
        # not good, it should be related to the entropy...
        # for now ill do step exploration decrease but
        # in the future it shoudl be like...... by episode maybe
        self.exploration = LinearSchedule(schedule_timesteps=int(self.exploration_fraction *
                                                                 self.total_timesteps),
                                          initial_p=self.epsilon,
                                          final_p=self.final_epsilon)

    def add_experience(self, obs, action, reward, next_obs, done):
        self.memory.add(obs, action[0], reward, next_obs, float(done))

    def act(self, obs):
        argmax_q_values, action, new_epsilon = self.agent.act(obs, new_epsilon=self.epsilon)
        return argmax_q_values, action, new_epsilon

    def train(self):
        batch = self.memory.sample(self.batch_size)
        output = self.agent.train(batch)

    def is_training(self):
        return self.total_steps > self.learning_starts and \
                self.total_steps % self.train_freq == 0

    def is_updating_nets(self):
        return self.total_steps > self.learning_starts and \
                self.total_steps % self.target_network_update_freq == 0

    def pprint_episode(self, episode, steps, total_reward, t1, t0):
        tt = time.time()
        print("episode: {} finished in steps {} \ntotal reward: {}  episode took {}".format(
            episode, steps, total_reward, tt - t1))
        print("total elapsed time across episodes {}".format(tt - t0))
        print("% used for exploration {}".format(100 * self.epsilon))
        print("total steps of the entire simulation: {}".format(self.total_steps))
