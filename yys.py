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


def log(f):

  def wrap(*agrs, **kwagrs):
    try:
      ans = f(*agrs, **kwagrs)
      return ans
    except:
      traceback.print_exc()
      time.sleep(60)

  return wrap


class StateBase(object):
  name = 'abstract'
  count = 0

  def __init__(self, verbose=0):
    self._verbose = verbose

  def screen_shot(self):

    pipe = subprocess.Popen(
        'adb shell screencap -p',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True)
    image_bytes = pipe.stdout.read()
    screen = cv2.imdecode(
        np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    return screen

  def touch(self, pos):
    x, y = pos
    cmd = 'adb shell input touchscreen tap {0} {1}'.format(x, y)
    os.system(cmd)

  def swipe(self, pos, dx, dy, duration=500):
    cmd = 'adb shell input touchscreen swipe {} {} {} {} {}'.format(
        pos[0], pos[1], int(dx + pos[0]), int(dy + pos[1]), duration)
    os.system(cmd)

  def swipe_abs(self, pos0, pos1, duration=500):
    self.swipe(pos0, pos1[0] - pos0[0], pos1[1] - pos0[1], duration=duration)

  def locate(self, screen, want, rescale=1, **kwargs):
    loc_pos = []
    want, threshold, c_name = want[0], want[1], want[2]
    sh, sw, _ = screen.shape
    h, w = want.shape[:-1]
    if rescale > 1:
      screen = cv2.resize(screen, sw / rescale, sh / rescale)
      want = cv2.resize(want, w / rescale, h / rescale)
    result = cv2.matchTemplate(screen, want, cv2.TM_CCOEFF_NORMED)
    location = np.where(result >= threshold)

    _, ex, ey = 1, 0, 0
    for pt in zip(*location[::-1]):
      x, y = pt[0] + int(w / 2), pt[1] + int(h / 2)
      if (x - ex) + (y - ey) < 15:
        continue
      ex, ey = x, y
      if self._verbose:
        cv2.circle(screen, (x, y), 10, (0, 0, 255), 3)

      x, y = int(x), int(y)

      if rescale > 1:
        x, y = x * rescale, y * rescale
      loc_pos.append([x, y])

    if self._verbose:
      cv2.imwrite(
          '/usr/local/google/home/yuxiangzhou/Downloads/screen_{:d}_{}.png'
          .format(int(time.time()), kwargs.pop('target_name',
                                               self.name)), screen)

    if len(loc_pos) == 0:
      print(c_name, 'not found')

    return loc_pos

  def cut(self, screen, upleft, downright):

    a, b = upleft
    c, d = downright
    screen = screen[b:d, a:c]

    return screen

  def cheat(self, p, w=10, h=10):
    a, b = p
    c, d = random.randint(-w, w), random.randint(-h, h)
    e, f = a + c, b + d
    y = [e, f]
    return y

  def wait(self, x=0.1, y=0.3):
    t = random.uniform(x, y)
    time.sleep(t)

  def step(self):
    print('State: ' + self.name, self.count)
    before = time.time()
    screen = self.screen_shot()
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
  path = os.getcwd() + '/png'
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
        }),
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
