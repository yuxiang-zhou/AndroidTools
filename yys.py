# pylint:disable=missing-docstring

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

def log(f):

  def wrap(*agrs, **kwagrs):
    try:
      ans = f(*agrs, **kwagrs)
      return ans
    except:
      traceback.print_exc()
      time.sleep(60)

  return wrap


class StateBase(utils.Control):
  name = 'abstract'
  count = 0

  def __init__(self, verbose=0):
    super(StateBase, self).__init__()
    self._verbose = verbose

  def step(self):
    print('State: ' + self.name, self.count)
    before = time.time()
    screen = self.screenshot()
    s = self._step(screen)
    self.wait()
    self.count += 1
    self.on_count()
    if s != self.name:
      self.on_change_state()

    after = time.time()
    print('Elapse: {}'.format(after - before))
    return s

  def on_count(self):
    if self.count > self._timeout_count:
      self.timeout = True

    if self.count >= 40 and self.count % 10 == 0:
      subprocess.call(['notify-send', 'yys', 'Count too large.'])
      if self.count >= 100:
        sys.exit(0)

  def on_change_state(self):
    self.count = 0
    self.timeout = False


class TargetTransformDict(StateBase):

  def __init__(self,
               name,
               target_transfer_dict,
               timeout_transfer_state=None,
               timeout_count=5,
               click_offset=None,
               **kwargs):
    self.name = name
    self.dict = target_transfer_dict
    self.timeout = False
    self._timeout_count = timeout_count
    self._timeout_transfer_state = timeout_transfer_state
    self._click_offset = click_offset
    self._touch_retry = 1
    self._touch_noise = 10

    super(TargetTransformDict, self).__init__(**kwargs)

  def _location_selection(self, unused_target_name, locs):
    pts = locs[-1]
    if self._click_offset is not None:
      pts = [pts[0] + self._click_offset[0], pts[1] + self._click_offset[1]]
    return pts

  def _action(self, target_name, locs):
    pts = self._location_selection(target_name, locs)

    touch_retry = self._touch_retry
    while touch_retry > 0:
      click_pos = self.cheat(pts, self._touch_noise, self._touch_noise)
      self.touch(click_pos)
      self.wait()
      touch_retry -= 1

  def _step(self, screen):

    next_state = self.name
    if self.timeout and self._timeout_transfer_state is not None:
      next_state = self._timeout_transfer_state

    for target_name, state_name in self.dict.items():
      if not isinstance(target_name, tuple):
        target_name = tuple([target_name])

      hit = False
      for n in target_name:
        target_img = IMAGES[n]
        pts = self.locate(screen, target_img, target_name=n)

        if len(pts):
          print('target found', target_name)
          self._action(n, pts)
          next_state = state_name
          hit = True
          break

      if hit:
        break

    return next_state


class GoliangMainState(TargetTransformDict):

  def __init__(self, *argv, **kwargs):
    super(GoliangMainState, self).__init__(*argv, **kwargs)
    self._touch_retry = 5
    self._touch_noise = 100

  def _location_selection(self, target_name, locs):

    if target_name == 'ep28':
      pts = (2518, 1196)
    else:
      pts = super(GoliangMainState, self)._location_selection(target_name, locs)

    return pts

  def on_count(self):
    super(GoliangMainState, self).on_count()
    # add random swipe

    self.swipe((1496, 674),
               np.random.choice([-800, -400, 800], 1)[0],
               0,
               duration=100)


class TargetTransformDictAbs(TargetTransformDict):

  def _location_selection(self, unused_target_name, locs):

    if self._click_offset is not None:
      pts = self._click_offset
    else:
      pts = super(TargetTransformDictAbs,
                  self)._location_selection(unused_target_name, locs)

    return pts


class GoliangSwapState(TargetTransformDictAbs):

  def __init__(self, *argv, **kwargs):
    super(GoliangSwapState, self).__init__(*argv, **kwargs)
    self._swipes = [
        [(588, 1068), (608, 738)],
        [(854, 1112), (1500, 706)],
    ]

  def _action(self, unused_target_name, locs):

    for pos0, pos1 in self._swipes:
      self.swipe_abs(pos0, pos1)
      self.wait()


def load_imgs():
  mubiao = {}

  control = utils.Control()
  screen = control.screenshot()

  path = os.getcwd() + '/png' + str(screen.shape[1])
  file_list = os.listdir(path)

  for f in file_list:
    name = f.split('.')[0]
    file_path = path + '/' + f
    a = [cv2.imread(file_path), 0.85, name]
    mubiao[name] = a

  return mubiao


IMAGES = load_imgs()
STATE = 'goliang'
PRE_STATE = STATE
STATE_LIB = {
    # state machine for goliang
    'goliang':
        GoliangMainState(
            'goliang', {
                ('boss', 'mobs', 'boss2'): 'goliangfullcheck',
                'ep28': 'goliang',
                'search': 'goliangsearch',
                'chest': 'goliangfinalreward',
            },
            verbose=0),
    'goliangsearch':
        GoliangMainState('goliangsearch', {
            ('boss', 'mobs', 'boss2'): 'goliangfullcheck',
        }),
    'goliangfullcheck':
        TargetTransformDictAbs(
            'goliangfullcheck',
            {
                'full': 'goliangselect',
                # ('boss', 'mobs', 'boss2'): 'goliangfullcheck'
            },
            timeout_transfer_state='goliangready',
            timeout_count=1,
            click_offset=(1198, 1042)),
    'goliangselect':
        TargetTransformDict(
            'goliangselect', {
                'select_all': 'goliangselect',
                'select_sc': 'goliangswap'
            },
            timeout_transfer_state='goliangfullcheck'),
    'goliangswap':
        GoliangSwapState('goliangswap', {'sc': 'goliangready'}),
    'goliangready':
        TargetTransformDict(
            'goliangready', {'ready': 'goliangreward'},
            timeout_transfer_state='goliangsearch',
            timeout_count=1),
    'goliangreward':
        TargetTransformDict(
            'goliangreward', {'reward': 'goliang'},
            timeout_transfer_state='goliangready'),
    'goliangfinalreward':
        TargetTransformDict(
            'goliangfinalreward', {'get_reward': 'goliang'},
            click_offset=(600, -100),
            timeout_transfer_state='goliang'),

    # state machine for event
    'event':
        TargetTransformDict('event', {
            'event_fight': 'event_ready',
        }, verbose=1),
    'event_ready':
        TargetTransformDict('event_ready', {
            'ready': 'event',
        }, timeout_count=5, timeout_transfer_state='event'),
}

if __name__ == '__main__':
  if len(sys.argv) > 1:
    STATE = sys.argv[1]

  start_time = time.time()
  print('started', time.ctime())

  while True:
    NEXT_STATE = STATE_LIB[STATE].step()
    if NEXT_STATE != PRE_STATE:
      PRE_STATE = STATE
    STATE = NEXT_STATE
