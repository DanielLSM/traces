#this was taken directly from the author (me)
# https://github.com/DanielLSM/drl-agents/
# from drl.tools.misc_util import LinearSchedule
from abc import ABC, abstractmethod


# ================================================================
# Exploration from OpenAI
# ================================================================
class LinearSchedule(object):
    def __init__(self, schedule_timesteps, final_p, initial_p=1.0):
        """Linear interpolation between initial_p and final_p over
        schedule_timesteps. After this many timesteps pass final_p is
        returned.
        Parameters
        ----------
        schedule_timesteps: int
            Number of timesteps for which to linearly anneal initial_p
            to final_p
        initial_p: float
            initial output value
        final_p: float
            final output value
        """
        self.schedule_timesteps = schedule_timesteps
        self.final_p = final_p
        self.initial_p = initial_p

    def value(self, t):
        """See Schedule.value"""
        fraction = min(float(t) / self.schedule_timesteps, 1.0)
        return self.initial_p + fraction * (self.final_p - self.initial_p)


# from drl.tools.plotter_util import Plotter

# We could see everything in tensorboard if we wanted, but what is the fun in that?
# Here we create a single threaded dynamic plotter with matplotlib
# For an interprocess plotter implementation go here: https://github.com/ctmakro/stanford-osrl/blob/master/plotter.py
#a base agent to remove the massive clutter of repeated variable
#assignments

class BaseAgent(ABC):

    #This is needed since locals() also passes self.
    def __init__(self, *args, **kwargs):
        """ Here we reduce the clutter for every agent, storing things hyperparameteres"""
        self._observation_space = kwargs['observation_space']
        self._action_space = kwargs['action_space']
        self._seed = kwargs['seed']
        self._lr = kwargs['lr']
        self._gamma = kwargs['gamma']
        self._batch_size = kwargs['batch_size']

        if self._seed:
            # from drl.tools.misc_util import set_seeds
            set_seeds(self._seed)

        #TODO:OpenAI baselines has helpers for the observation inputs..
        # this time we go ham on the class, but this could be made automatically
        #here

    @abstractmethod
    def act(self, observation):

        raise NotImplementedError

    @abstractmethod
    def train(self, batch_training=False):
        """ Train the agent according to a batch or a sample """
        raise NotImplementedError


# from drl.tools.plotter_util import Plotter
import matplotlib.pyplot as plot

colors = {'red': [1, 0, 0]}


class Plotter:
    def __init__(self,
                 num_lines=1,
                 color='blue',
                 x_label='x',
                 y_label='y',
                 title='custom plot',
                 smooth=False):

        self.x = []
        self.y = []
        self.num_lines = num_lines
        self.ys = [[] for i in range(num_lines)]

        self.colors = [[
            (i * i * 7.9 + i * 19 / 2.3 + 17 / 3.1) % 0.5 + 0.2,
            (i * i * 9.1 + i * 23 / 2.9 + 31 / 3.7) % 0.5 + 0.2,
            (i * i * 11.3 + i * 29 / 3.1 + 37 / 4.1) % 0.5 + 0.2,
        ] for i in range(num_lines)]

        self.smooth = smooth

        self.fig = plot.figure()
        self.axis = self.fig.add_subplot(1, 1, 1)
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        plot.show(block=False)

    def show(self):

        self.axis.clear()
        self.axis.grid(color='#f0f0f0', linestyle='solid', linewidth=1)

        #this is important if self.x changes during somewhere else
        x = self.x
        self.axis.set_xlabel(self.x_label)
        self.axis.set_ylabel(self.y_label)
        self.axis.set_title(self.title)

        for _ in range(len(self.ys)):
            y = self.ys[_]
            c = self.colors[_]
            self.axis.plot(x, y, color=tuple(c))

        # Putting if outside is O(2n) but putting inside is O(n) more ifs
        if self.smooth:
            self.plot_smooth()

        self.fig.canvas.draw()

    def add_points(self, x, y, *args):
        """ Adds points to our plotter, at least one x and one y, but can take multiple ys """
        assert len(args) + 1 == self.num_lines, "points without a line"
        self.x.append(x)
        args = list(args)
        args.insert(0, y)
        for _ in range(len(args)):
            self.ys[_].append(args[_])

    def plot_smooth(self, alpha=0.5):
        x = self.x
        for _ in range(len(self.ys)):
            y = self.ys[_]
            c = self.colors[_]
            init = 5
            if len(y) > init:
                ysmooth = [sum(y[0:init]) / init] * init
                for i in range(init, len(y)):  # first order
                    ysmooth.append(ysmooth[-1] * 0.9 + y[i] * 0.1)
                for i in range(init, len(y)):  # second order
                    ysmooth[i] = ysmooth[i - 1] * 0.9 + ysmooth[i] * 0.1

                self.axis.plot(x, ysmooth, lw=2, color=tuple([cp**0.3 for cp in c]), alpha=alpha)


# from drl.managers.base import Manager

class Manager(ABC):
    def __init__(self, *args, **kwargs):
        self.seed = kwargs['seed']
        self.lr = kwargs['lr']
        self.gamma = kwargs['gamma']
        self.buffer_size = kwargs['buffer_size']
        self.total_timesteps = kwargs['total_timesteps']
        self.exploration_fraction = kwargs['exploration_fraction']
        self.final_epsilon = kwargs['final_epsilon']
        self.learning_starts = kwargs['learning_starts']
        self.train_freq = kwargs['train_freq']
        self.batch_size = kwargs['batch_size']
        self.max_steps_per_episode = kwargs['max_steps_per_episode']
        self.target_network_update_freq = kwargs['target_network_update_freq']
        self.render_freq = kwargs['render_freq']
        self.total_steps = 0
        self.epsilon = 1.0

    @abstractmethod
    def run(self):
        raise NotImplementedError

    @abstractmethod
    def test(self):
        raise NotImplementedError

    @abstractmethod
    def save(self):
        raise NotImplementedError

    @abstractmethod
    def load(self):
        raise NotImplementedError

    @abstractmethod
    def save_agent(self):
        raise NotImplementedError

    @abstractmethod
    def load_agent(self):
        raise NotImplementedError

    @abstractmethod
    def save_memory(self):
        raise NotImplementedError

    @abstractmethod
    def load_memory(self):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError


# from drl.core.memory import ReplayBuffer

#code and authorship on https://github.com/openai/baselines

import numpy as np
import random


class ReplayBuffer(object):
    def __init__(self, size):
        """Create Replay buffer.
        Parameters
        ----------
        size: int
            Max number of transitions to store in the buffer. When the buffer
            overflows the old memories are dropped.
        """
        self._storage = []
        self._maxsize = size
        self._next_idx = 0

    def __len__(self):
        return len(self._storage)

    def add(self, obs_t, action, reward, obs_tp1, done):
        data = (obs_t, action, reward, obs_tp1, done)

        if self._next_idx >= len(self._storage):
            self._storage.append(data)
        else:
            self._storage[self._next_idx] = data
        self._next_idx = (self._next_idx + 1) % self._maxsize

    def _encode_sample(self, idxes):
        obses_t, actions, rewards, obses_tp1, dones = [], [], [], [], []
        for i in idxes:
            data = self._storage[i]
            obs_t, action, reward, obs_tp1, done = data
            obses_t.append(np.array(obs_t, copy=False))
            actions.append(np.array(action, copy=False))
            rewards.append(reward)
            obses_tp1.append(np.array(obs_tp1, copy=False))
            dones.append(done)
        return np.array(obses_t), np.array(actions), np.array(rewards), np.array(
            obses_tp1), np.array(dones)

    def sample(self, batch_size):
        """Sample a batch of experiences.
        Parameters
        ----------
        batch_size: int
            How many transitions to sample.
        Returns
        -------
        obs_batch: np.array
            batch of observations
        act_batch: np.array
            batch of actions executed given obs_batch
        rew_batch: np.array
            rewards received as results of executing act_batch
        next_obs_batch: np.array
            next set of observations seen after executing act_batch
        done_mask: np.array
            done_mask[i] = 1 if executing act_batch[i] resulted in
            the end of an episode and 0 otherwise.
        """
        idxes = [random.randint(0, len(self._storage) - 1) for _ in range(batch_size)]
        return self._encode_sample(idxes)


# from drl.agents.dqn import DQNAgent

import math
import random

import numpy as np
import tensorflow as tf
# from drl.core.memory import ReplayBuffer
# from drl.core.base import BaseAgent
# from drl.core.dqn_models import *

# from drl.tools.math_util import huber_loss


def lrelu(x, leak=0.2):
    f1 = 0.5 * (1 + leak)
    f2 = 0.5 * (1 - leak)
    return f1 * x + f2 * abs(x)


def huber_loss(x, delta=1.0):
    """Reference: https://en.wikipedia.org/wiki/Huber_loss"""
    return tf.where(tf.abs(x) < delta, tf.square(x) * 0.5, delta * (tf.abs(x) - 0.5 * delta))


# from drl.tools.misc_util import set_seeds


class DQNAgent(BaseAgent):
    def __init__(self,
                 observation_space,
                 action_space,
                 hiddens=[16, 16],
                 seed=None,
                 lr=5e-4,
                 gamma=1.0,
                 batch_size=None,
                 **kwargs):
        """ Setup of agent's variables and graph construction with useful
        pointers to nodes  """
        BaseAgent.__init__(**locals())

        # Declaring for readibility
        batch_size = self._batch_size
        obs_shape = self._observation_space.shape
        obs_dtype = self._observation_space.dtype

        act_shape = self._action_space.shape
        act_dtype = self._action_space.dtype
        num_actions = self._action_space.n

        # ================================================================
        # Input nodes of the graph, obervations, actions
        # and hyperparameters, aka tf.placeholders
        # ================================================================

        with tf.variable_scope('dqn_vars', reuse=None):
            self.obs_input_node = tf.placeholder(shape=(batch_size, ) + obs_shape,
                                                 dtype=obs_dtype,
                                                 name="observation_input")

            self.obs_input_node_target_net = tf.placeholder(shape=(batch_size, ) + obs_shape,
                                                            dtype=obs_dtype,
                                                            name="observation_input_target_net")

            #Tensorflow shapes XDDDDDDD
            # https://stackoverflow.com/questions/46940857/what-is-the-difference-between-none-none-and-for-the-shape-of-a-placeh
            self.action = tf.placeholder(shape=[None], dtype=tf.int64, name="action_input")
            self.reward = tf.placeholder(shape=[None], dtype=tf.float32, name="reward_input")

            self.done = tf.placeholder(tf.float32, [None], name="done")
            self.importance_sample_weights = tf.placeholder(tf.float32, [None], name="weights")

            # ================================================================
            # Here we construct our action-value function Q
            # this will be an MLP, no CNN needed
            # ================================================================

            self.q_values = q_mlp(hiddens,
                                  self.obs_input_node,
                                  num_actions,
                                  scope='action_value_function')

            self.q_mlp_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES,
                                                scope=tf.get_variable_scope().name +
                                                "/action_value_function")

            # ================================================================
            # Here we construct our target action-value function Q
            # ================================================================

            self.q_values_target = q_mlp(hiddens,
                                         self.obs_input_node_target_net,
                                         num_actions,
                                         scope='action_value_function_target')

            self.q_mlp_target_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES,
                                                       scope=tf.get_variable_scope().name +
                                                       "/action_value_function_target")

            # ================================================================
            # Bellman equation
            # old estimate
            # Q_old(s_t,a_t)
            # new estimate
            # Q_new(s_t,a_t) = R(s,a_t) + gamma * max_a(Q(s_{t+1},a_t))
            # Objective is to minimize the squared error of the difference
            # between the old and new estimates
            # the difference also mentioned in the literature as td_error(0)
            # the target q_function has 2 connotations, one is the target in
            # supervised learning, the second is the TD target to update the value
            # function for the old state (The TD target)
            # https://en.wikipedia.org/wiki/Temporal_difference_learning
            # ================================================================

            # old estimate
            # Q_old(s_t,a_t)
            self.q_value_old = tf.reduce_sum(self.q_values * tf.one_hot(self.action, num_actions),
                                             1)

            # new estimate
            # Q_new(s_t,a_t) = R(s,a_t) + max_a(Q(s_{t+1},a_t))

            # max_a(Q(s_{t+1},a_t)
            self.q_target_max = tf.reduce_max(self.q_values_target, 1)
            self.q_target_max = (1.0 - self.done) * self.q_target_max
            # Q_new(s_t,a_t) = R(s,a_t) + max_a(Q(s_{t+1},a_t))
            self.q_value_new = self.reward + self._gamma * self.q_target_max

            # td_error TD(0) = Q_old - Q_new
            self.td_error = self.q_value_old - tf.stop_gradient(self.q_value_new)
            self.errors = huber_loss(self.td_error)
            # self.errors = 0.5 * tf.square(self.td_error)
            # mean squared td_erors = (1/2) * (TD(0))

            #TODO: we could use huber_loss
            # we minimize the mean of these weights, unless weights are assigned
            # to this errors, for now, will not weight samples...
            # self.weighted_error = tf.reduce_mean(
            #     self.importance_sample_weights * self.errors)

            self.weighted_error = tf.reduce_mean(self.errors)

            #TODO: gradient normalization is left as an additional exercise
            optimizer = tf.train.AdamOptimizer(learning_rate=self._lr)
            self.optimize = optimizer.minimize(self.weighted_error, var_list=self.q_mlp_vars)

            # ================================================================
            # Pointer update q_mlp_target_vars with q_mlp_vars
            # ================================================================

            self.q_update_target_vars = q_target_update(self.q_mlp_vars, self.q_mlp_target_vars)
            # ================================================================
            # Action and exploration nodes
            # ================================================================
            # deterministic actions
            # yes, there is a difference between () and [None], [None] is for
            # 1-D arrays, () is for a single scalar value.
            # https://stackoverflow.com/questions/46940857/what-is-the-difference-between-none-none-and-for-the-shape-of-a-placeh
            # yes this is actually interesting
            self.argmax_q_values = tf.argmax(self.q_values, axis=1)
            self.stochastic = tf.placeholder(tf.bool, (), name="stochastic")
            self.new_epsilon = tf.placeholder(tf.float32, (), name="n_epsilon")
            self.epsilon = tf.get_variable("epsilon", (), initializer=tf.constant_initializer(0))
            self.size_obs_batch = tf.shape(self.obs_input_node)[0]

            self.random_actions = tf.random_uniform(tf.stack([self.size_obs_batch]),
                                                    minval=0,
                                                    maxval=num_actions,
                                                    dtype=tf.int64)
            self.chose_random = tf.random_uniform(
                tf.stack([self.size_obs_batch
                          ]), minval=0, maxval=1, dtype=tf.float32) < self.epsilon
            self.output_actions = tf.where(self.chose_random, self.random_actions,
                                           self.argmax_q_values)
            self.update_new_epsilon = self.epsilon.assign(
                tf.cond(self.new_epsilon >= 0, lambda: self.new_epsilon, lambda: self.epsilon))

            # ================================================================
            # Finalize graph and initiate all variables
            # ================================================================
            self.initializer = tf.initializers.global_variables()

        get_session().graph.finalize()
        get_session().run(self.initializer)
        print("### agent graph finalized and ready to use!!! ###")

    def act(self, observation, stochastic=True, new_epsilon=-1.):
        """ Agent acts by delivering an action from an observation """

        obs = adjust_shape(self.obs_input_node, observation)

        return get_session().run(
            [self.argmax_q_values, self.output_actions, self.update_new_epsilon],
            feed_dict={
                self.obs_input_node: obs,
                self.new_epsilon: new_epsilon,
                self.stochastic: stochastic
            })

    def train(self, batch, batch_training=False):
        """ Train the agent according a batch or step """

        obs, action, reward, next_obs, done = batch
        obs = adjust_shape(self.obs_input_node, obs)
        action = adjust_shape(self.action, action)
        new_obs = adjust_shape(self.obs_input_node_target_net, next_obs)
        reward = adjust_shape(self.reward, reward)
        done = adjust_shape(self.done, done)

        # print(done)
        feed_dict = {
            self.obs_input_node: obs,
            self.action: action,
            self.obs_input_node_target_net: new_obs,  #next observation
            self.reward: reward,
            self.done: done
        }
        return get_session().run([self.optimize, self.td_error, self.q_mlp_vars],
                                 feed_dict=feed_dict)

    def update_target_nets(self):
        get_session().run([self.q_update_target_vars])

    def save(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError


#code and authorship on https://github.com/openai/baselines
import os
import joblib
import multiprocessing

import numpy as np
import tensorflow as tf

# ================================================================
# Session related functions
# ================================================================


def get_session(config=None):
    """Get default session or create one with a given config"""
    sess = tf.get_default_session()
    if sess is None:
        sess = make_session(config=config, make_default=True)
    return sess


#TODO: This function as been changed from OpenAI baselines, I think config.gpu_options.allow_growth is deprecated
def make_session(config=None, num_cpu=None, make_default=False, graph=None):
    """Returns a session that will use <num_cpu> CPU's only"""
    if num_cpu is None:
        num_cpu = int(os.getenv('RCALL_NUM_CPU', multiprocessing.cpu_count()))
    if config is None:
        gpu_options = tf.GPUOptions(allow_growth=True)
        config = tf.ConfigProto(allow_soft_placement=True,
                                inter_op_parallelism_threads=num_cpu,
                                intra_op_parallelism_threads=num_cpu,
                                gpu_options=gpu_options)
        # from OpenAI baselines
        # config.gpu_options.allow_growth = True

    if make_default:
        return tf.InteractiveSession(config=config, graph=graph)
    else:
        return tf.Session(config=config, graph=graph)


def single_threaded_session():
    """Returns a session which will only use a single CPU"""
    return make_session(num_cpu=1)


# ================================================================
# Initialize graph functions
# ================================================================

ALREADY_INITIALIZED = set()


def initialize():
    """Initialize all the uninitialized variables in the global scope."""
    new_variables = set(tf.global_variables()) - ALREADY_INITIALIZED
    get_session().run(tf.variables_initializer(new_variables))
    ALREADY_INITIALIZED.update(new_variables)


def normc_initializer(std=1.0, axis=0):
    def _initializer(shape, dtype=None, partition_info=None):  # pylint: disable=W0613
        out = np.random.randn(*shape).astype(dtype.as_numpy_dtype)
        out *= std / np.sqrt(np.square(out).sum(axis=axis, keepdims=True))
        return tf.constant(out)

    return _initializer


# ================================================================
# Save and load graph variables
# ================================================================


def save_variables(save_path, variables=None, sess=None):
    sess = sess or get_session()
    variables = variables or tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES)

    ps = sess.run(variables)
    save_dict = {v.name: value for v, value in zip(variables, ps)}
    dirname = os.path.dirname(save_path)
    if any(dirname):
        os.makedirs(dirname, exist_ok=True)
    joblib.dump(save_dict, save_path)


def load_variables(load_path, variables=None, sess=None):
    sess = sess or get_session()
    variables = variables or tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES)

    loaded_params = joblib.load(os.path.expanduser(load_path))
    restores = []
    if isinstance(loaded_params, list):
        assert len(loaded_params) == len(
            variables), 'number of variables loaded mismatches len(variables)'
        for d, v in zip(loaded_params, variables):
            restores.append(v.assign(d))
    else:
        for v in variables:
            restores.append(v.assign(loaded_params[v.name]))

    sess.run(restores)


# ================================================================
# Tensorboard monitoring
# ================================================================


def launch_tensorboard_in_background(log_dir):
    '''
    To log the Tensorflow graph when using rl-algs
    algorithms, you can run the following code
    in your main script:
        import threading, time
        def start_tensorboard(session):
            time.sleep(10) # Wait until graph is setup
            tb_path = osp.join(logger.get_dir(), 'tb')
            summary_writer = tf.summary.FileWriter(tb_path, graph=session.graph)
            summary_op = tf.summary.merge_all()
            launch_tensorboard_in_background(tb_path)
        session = tf.get_default_session()
        t = threading.Thread(target=start_tensorboard, args=([session]))
        t.start()
    '''
    import subprocess
    subprocess.Popen(['tensorboard', '--logdir', log_dir])


# ================================================================
# Shape adjustment for feeding into tf placeholders
# ================================================================
def adjust_shape(placeholder, data):
    '''
    adjust shape of the data to the shape of the placeholder if possible.
    If shape is incompatible, AssertionError is thrown
    Parameters:
        placeholder     tensorflow input placeholder
        data            input data to be (potentially) reshaped to be fed into placeholder
    Returns:
        reshaped data
    '''

    if not isinstance(data, np.ndarray) and not isinstance(data, list):
        return data
    if isinstance(data, list):
        data = np.array(data)

    placeholder_shape = [x or -1 for x in placeholder.shape.as_list()]


    assert _check_shape(placeholder_shape, data.shape), \
        'Shape of data {} is not compatible with shape of the placeholder {}'.format(data.shape, placeholder_shape)

    # import ipdb
    # ipdb.set_trace()
    return np.reshape(data, placeholder_shape)


def _check_shape(placeholder_shape, data_shape):
    ''' check if two shapes are compatible (i.e. differ only by dimensions of size 1, or by the batch dimension)'''

    squeezed_placeholder_shape = _squeeze_shape(placeholder_shape)
    squeezed_data_shape = _squeeze_shape(data_shape)

    for i, s_data in enumerate(squeezed_data_shape):
        s_placeholder = squeezed_placeholder_shape[i]
        if s_placeholder != -1 and s_data != s_placeholder:
            return False

    return True


def _squeeze_shape(shape):
    return [x for x in shape if x != 1]


# ================================================================
# Observations from open AI
# ================================================================

# ================================================================
# My helper functions to create nodes in the tf.Graph
# ================================================================


def get_placeholder(batch_size, shape, dtype, name):
    placeholder = tf.placeholder(shape=(batch_size, ) + shape, dtype=dtype, name=name)

    #from input.py in baselines deepq, they recast the tensor to tf.float
    # placeholder = tf.to_float(placeholder)
    return placeholder


# from drl.core.dqn_models import q_mlp, q_target_update

from abc import ABC, abstractmethod





class SimpleAgent(BaseAgent):
    def __init__(self):
        pass

    def act(self, obs):
        pass

    def train(self, obs):
        pass

    #Some models can be found here: https://github.com/openai/baselines


import tensorflow as tf
import tensorflow.contrib.layers as layers


#TODO: inputting a different activation than tf.nn.relu would make sense
def q_mlp(hiddens, input_, num_actions, scope='action_value_function', reuse=None,
          layer_norm=False):
    with tf.variable_scope(scope, reuse=reuse):
        out = input_
        for hidden in hiddens:
            out = layers.fully_connected(out, num_outputs=hidden, activation_fn=None)
            # if layer_norm:
            #     out = layers.layer_norm(out, center=True, scale=True)
            out = tf.nn.relu(out)
        q_out = layers.fully_connected(out, num_outputs=num_actions, activation_fn=None)
        return q_out


def q_target_update(q_vars, qt_vars):
    update_target_expr = []
    for var, var_target in zip(sorted(q_vars, key=lambda v: v.name),
                               sorted(qt_vars, key=lambda v: v.name)):
        update_target_expr.append(var_target.assign(var))
    update_target_expr = tf.group(*update_target_expr)
    return update_target_expr

import os
import pickle
import zipfile
import random
import numpy as np
import tensorflow as tf

# ================================================================
# Seeding
# ================================================================


def set_global_seeds(i):
    try:
        import MPI
        rank = MPI.COMM_WORLD.Get_rank()
    except ImportError:
        rank = 0

    myseed = i + 1000 * rank if i is not None else None
    try:
        import tensorflow as tf
        tf.set_random_seed(myseed)
    except ImportError:
        pass
    np.random.seed(myseed)
    random.seed(myseed)


def set_seeds(seed):
    """ My simple seeds version without multiprocessing """
    tf.set_random_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


# ================================================================
# Pretty printings
# ================================================================


def pretty_eta(seconds_left):
    """Print the number of seconds in human readable format.
    Examples:
    2 days
    2 hours and 37 minutes
    less than a minute
    Paramters
    ---------
    seconds_left: int
        Number of seconds to be converted to the ETA
    Returns
    -------
    eta: str
        String representing the pretty ETA.
    """
    minutes_left = seconds_left // 60
    seconds_left %= 60
    hours_left = minutes_left // 60
    minutes_left %= 60
    days_left = hours_left // 24
    hours_left %= 24

    def helper(cnt, name):
        return "{} {}{}".format(str(cnt), name, ('s' if cnt > 1 else ''))

    if days_left > 0:
        msg = helper(days_left, 'day')
        if hours_left > 0:
            msg += ' and ' + helper(hours_left, 'hour')
        return msg
    if hours_left > 0:
        msg = helper(hours_left, 'hour')
        if minutes_left > 0:
            msg += ' and ' + helper(minutes_left, 'minute')
        return msg
    if minutes_left > 0:
        return helper(minutes_left, 'minute')
    return 'less than a minute'


# ================================================================
# Save and load compressed python objects
# ================================================================


def relatively_safe_pickle_dump(obj, path, compression=False):
    """This is just like regular pickle dump, except from the fact that failure cases are
    different:
        - It's never possible that we end up with a pickle in corrupted state.
        - If a there was a different file at the path, that file will remain unchanged in the
          even of failure (provided that filesystem rename is atomic).
        - it is sometimes possible that we end up with useless temp file which needs to be
          deleted manually (it will be removed automatically on the next function call)
    The indended use case is periodic checkpoints of experiment state, such that we never
    corrupt previous checkpoints if the current one fails.
    Parameters
    ----------
    obj: object
        object to pickle
    path: str
        path to the output file
    compression: bool
        if true pickle will be compressed
    """
    temp_storage = path + ".relatively_safe"
    if compression:
        # Using gzip here would be simpler, but the size is limited to 2GB
        with tempfile.NamedTemporaryFile() as uncompressed_file:
            pickle.dump(obj, uncompressed_file)
            uncompressed_file.file.flush()
            with zipfile.ZipFile(
                    temp_storage, "w",
                    compression=zipfile.ZIP_DEFLATED) as myzip:
                myzip.write(uncompressed_file.name, "data")
    else:
        with open(temp_storage, "wb") as f:
            pickle.dump(obj, f)
    os.rename(temp_storage, path)


def pickle_load(path, compression=False):
    """Unpickle a possible compressed pickle.
    Parameters
    ----------
    path: str
        path to the output file
    compression: bool
        if true assumes that pickle was compressed when created and attempts decompression.
    Returns
    -------
    obj: object
        the unpickled object
    """

    if compression:
        with zipfile.ZipFile(
                path, "r", compression=zipfile.ZIP_DEFLATED) as myzip:
            with myzip.open("data") as f:
                return pickle.load(f)
    else:
        with open(path, "rb") as f:
            return pickle.load(f)

