import cv2
import time
import os
import random
import threading
import traceback
import sys
import subprocess
import numpy as np
import utils


class StateMachine(object):
    def __init__(self,
                 state_config, 
                 imgs, 
                 entry_state='main', 
                 verbose=0):
        self.current_state = entry_state
        self.states = state_config['state_config']
        self.config = state_config
        self.timer = 0
        self.img_dict = imgs
        self.timeout = False
        self._verbose = verbose
        self._action_queue = []
        self.entry_time = time.time()
        self.step_time = time.time()

    def get_current_state(self):
        return self.states[self.current_state]

    def step(self, screen):
        # Update State Timer
        self.timer = time.time() - self.entry_time
        self.on_timer_count()

        # Executing Queued Actions
        new_queue = []
        for (cmd, args), delay in self._action_queue:
            if delay <= time.time():
                getattr(utils, cmd)(*args)
            else:
                new_queue.append([(cmd, args), delay])

        self._action_queue = new_queue

        # State Transition Delay
        if self.timer < self.get_current_state().get("start_delay", self.config.get('default_start_delay', 1)):
            if self._verbose:
                print('{}: {:02.2f} - Delay'.format(self.current_state, self.timer))
            return self.current_state

        # Print State
        if self._verbose:
            print('{}: {:02.2f}'.format(self.current_state, self.timer))

        # Execute State Step
        s = self._step(screen)

        # Executing Transition Logic
        if s != self.current_state:
            self.on_change_state()
        self.current_state = s


        self.step_time = time.time()
        return s

    def on_timer_count(self):
        if self.timer > self.get_current_state().get('timeout_count', self.config.get('default_timeout_count', 10)):
            self.timeout = True
            if "timeout_actions" in self.get_current_state():
                action_delay = 0.
                for act in self.get_current_state()['timeout_actions']:
                    self._queue_action(act, delay=action_delay)
                    action_delay += 1.

        if self.timer >= 40 and not hasattr(self, 'notifyed'):
            subprocess.call(['notify-send', 'yys', 'Count too large. Stucked in state: %s'%self.current_state])
            self._verbose = 2
            self.notifyed = True

        if self.timer >= 100 and hasattr(self, 'notifyed'):
            sys.exit(0)

    def on_change_state(self):
        self.timer = 0
        self.timeout = False
        self.entry_time = time.time()

    def _step(self, screen):

        if self._verbose > 1:
            utils.save_screen(screen)

        next_state = self.current_state
        if self.timeout and 'timeout_transfer_state' in self.get_current_state():
            next_state = self.get_current_state()['timeout_transfer_state']

        for target_name, transition in self.get_current_state()['transitions'].items():
            hit = False
            for n in target_name.split(','):
                target_img = self.img_dict[n]
                pts = utils.locate(screen, target_img, verbose=self._verbose)

                if len(pts):
                    if self._verbose > 1:
                        print('target found', target_name)
                    pts = pts[np.random.randint(len(pts))]
                    pts = (pts[0]*4, pts[1]*4)
                    self._action_list(transition.get('actions', [['click', pts]]))
                    next_state = transition['state']
                    hit = True
                    break

            if hit:
                break

        return next_state

    def _action_list(self, actions):
        action_delay = 0.
        for act in actions:
            self._queue_action(act, delay=action_delay)
            action_delay += 1.

    def _queue_action(self, act, delay=0):
        self._action_queue.append([act, time.time() + delay])