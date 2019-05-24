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
                 state_config, imgs, entry_state='main', verbose=0):
        self.current_state = entry_state
        self.states = state_config['state_config']
        self.count = 0
        self.img_dict = imgs
        self.timeout = False
        self._verbose = verbose

    def step(self, screen):
        if self._verbose:
            print('State: ' + self.current_state, self.count)
        before = time.time()
        s = self._step(screen)
        after = time.time()
        td = after - before
        if self._verbose:
            print('Elapse: {}'.format(td))
        self.count += td
        self.on_count()
        if s != self.current_state:
            self.on_change_state()

        self.current_state = s
        return s

    def on_count(self):
        if self.count > self.states[self.current_state].get('timeout_count', 10):
            self.timeout = True
            if "timeout_actions" in self.states[self.current_state]:
                for cmd, args in self.states[self.current_state]['timeout_actions']:
                    getattr(utils, cmd)(*args)
                    utils.wait(1)

        if self.count >= 40 and not hasattr(self, 'notifyed'):
            subprocess.call(['notify-send', 'yys', 'Count too large.'])
            self.notifyed = True

        if self.count >= 100 and hasattr(self, 'notifyed'):
            sys.exit(0)

    def on_change_state(self):
        self.count = 0
        self.timeout = False
        utils.wait(2)

    def _step(self, screen):

        next_state = self.current_state
        if self.timeout and 'timeout_transfer_state' in self.states[self.current_state]:
            next_state = self.states[self.current_state]['timeout_transfer_state']

        for target_name, transition in self.states[self.current_state]['transitions'].items():
            hit = False
            for n in target_name.split(','):
                target_img = self.img_dict[n]
                pts = utils.locate(screen, target_img, verbose=self._verbose)

            if len(pts):
                if self._verbose:
                    print('target found', target_name)
                pts = pts[np.random.randint(len(pts))]
                pts = (pts[0]*4, pts[1]*4)
                self._action(transition.get('actions', [['click', pts]]))
                next_state = transition['state']
                hit = True
                break

            if hit:
                break

        return next_state

    def _action(self, actions):
        utils.wait(0.5)
        for cmd, args in actions:
            getattr(utils, cmd)(*args)
            utils.wait(1)