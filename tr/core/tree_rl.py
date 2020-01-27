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

    def reward(self, action, done):
        #maybe include depth as well

        if not done:
            if action == 1:
                return 1
            else:
                return -1
        return -1

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
        action = child.action_maintenance
        reward = self.reward(action, done)

        # import ipdb
        # ipdb.set_trace()
        return obs, action, reward, next_obs, done


class DQNManager:
    def __init__(self,
                 env,
                 seed=None,
                 lr=5e-3,
                 gamma=1.0,
                 buffer_size=50000,
                 total_timesteps=1000000,
                 exploration_fraction=0.02,
                 final_epsilon=0.02,
                 learning_starts=1000,
                 train_freq=1,
                 batch_size=32,
                 target_network_update_freq=500,
                 max_steps_per_episode=10000,
                 render_freq=20,
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
        self.full_episodes = 0

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

    def _render_train_update(self, render=False, train=True):
        if render:
            self.env.render()
        if self._is_training() and train:
            self._train_agent()
        if self._is_updating_nets():
            self.agent.update_target_nets()

    def _train_agent(self):
        batch = self.memory.sample(self.batch_size)
        output = self.agent.train(batch)

    def _rollout(self, render=False, train=True):
        info = {}
        for _ in range(self.action_space.n):
            info[_] = 0
        obs = self.env.reset()
        total_reward = 0.
        steps = 0
        for _ in range(self.max_steps_per_episode):
            self.epsilon = self.exploration.value(self.total_steps)
            argmax_q_values, action, new_epsilon = self.agent.act(obs, new_epsilon=self.epsilon)
            # print("argmax {}, action{}".format(argmax_q_values, action))
            next_obs, reward, done, _info = self.env.step(action[0])
            info[action[0]] += 1
            self.memory.add(obs, action[0], reward, next_obs, float(done))
            obs = next_obs
            self._render_train_update(render, train)
            steps += 1
            self.total_steps += 1
            total_reward += reward
            if done:
                break
        return total_reward, steps, info

    def _pprint_episode(self, episode, steps, total_reward, t1, t0):
        tt = time.time()
        print("episode: {} finished in steps {} \ntotal reward: {}  episode took {}".format(
            episode, steps, total_reward, tt - t1))
        print("total elapsed time across episodes {}".format(tt - t0))
        print("% used for exploration {}".format(100 * self.epsilon))

    def _is_training(self):
        return self.total_steps > self.learning_starts and \
                self.total_steps % self.train_freq == 0

    def _is_updating_nets(self):
        return self.total_steps > self.learning_starts and \
                self.total_steps % self.target_network_update_freq == 0

    def run(self, episodes=1, render=False, train=True):
        t0 = time.time()
        for _ in range(episodes):
            print_render = not bool(_ % self.render_freq)
            t1 = time.time()
            total_reward, steps, info = self._rollout(render=print_render, train=train)
            # total_reward, steps = self._rollout(render=False)
            if print_render:
                # import ipdb
                # ipdb.set_trace()
                for key, value in info.items():
                    print("task: {} performed: {}".format(key, value))
            self._pprint_episode(self.full_episodes + _, steps, total_reward, t1, t0)
            self.plotter.add_points(self.full_episodes + _, total_reward)
            self.plotter.show()
        self.full_episodes = self.full_episodes + _

    def test(self):
        self.run(episodes=1, render=True, train=False)


if __name__ == "__main__":

    import gym
    env = gym.make("CartPole-v0")
    # parameteres_default_file = "/home/daniel/local-dev/schedule-sim/schedule_sim/envs/config/task_day_custom.yaml"
    # render_file = "/home/daniel/local-dev/schedule-sim/schedule_sim/envs/config/render_options.yaml"
    # env1 = TaskDay(
    #     parameters_file=parameteres_default_file,
    #     reward_scale=10,
    #     debug=1,
    #     rendering=True,
    #     render_file=render_file)
    experiment_config = {}
    # import ipdb
    # # ipdb.set_trace()
    # obs1 = env1.reset()
    obs2 = env.reset()
    manager = DQNManager(env, experiment_config)
    manager.run(episodes=400)
    import ipdb
    ipdb.set_trace()
    manager.test()

    # manager.save_agent()
    # manager.close()
