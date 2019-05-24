import numpy as np
import subprocess
import cv2
import time
import os
import json

def touch(pos):
  x, y = pos
  cmd = 'adb shell input touchscreen tap {0} {1}'.format(x, y)
  os.system(cmd)

def click(x1, y1):
  touch((x1, y1))

def swipe_rel(pos, dx, dy, duration=500):
  cmd = 'adb shell input touchscreen swipe {} {} {} {} {}'.format(
      pos[0], pos[1], int(dx + pos[0]), int(dy + pos[1]), duration)
  os.system(cmd)

def swipe_abs(pos0, pos1, duration=500):
  swipe_rel(pos0, pos1[0] - pos0[0], pos1[1] - pos0[1], duration=duration)

def swipe(x1, y1, x2, y2, duration=500):
  swipe_abs((x1, y1), (x2, y2), duration=duration)

def locate(screen, want, rescale=1, verbose=False):
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
    if verbose:
      cv2.circle(screen, (x, y), 10, (0, 0, 255), 3)

    x, y = int(x), int(y)

    if rescale > 1:
      x, y = x * rescale, y * rescale
    loc_pos.append([x, y])

  if verbose > 1 and len(loc_pos) == 0:
    print(c_name, 'not found')

  return loc_pos

def cut(screen, upleft, downright):

  a, b = upleft
  c, d = downright
  screen = screen[b:d, a:c]

  return screen

def cheat(p, w=10, h=10):
  a, b = p
  c, d = np.random.randint(-w, w), np.random.randint(-h, h)
  e, f = a + c, b + d
  y = [e, f]
  return y

def wait(x=0.1, y=0.3, base=0.):
  t = np.random.uniform(x, y) + base
  time.sleep(t)

def save_screen(screen):
  cv2.imwrite(
    './screen/{}.png'
    .format(int(time.time())), screen)

def load_imgs(path='png'):
  img_dict = {}

  path = os.path.join(os.getcwd(), path)
  file_list = os.listdir(path)

  for f in file_list:
    name = f.split('.')[0]
    file_path = path + '/' + f
    a = [cv2.imread(file_path), 0.85, name]
    img_dict[name] = a

  return img_dict

def load_config(path='config.json'):
  path = os.path.join(os.getcwd(), path)
  with open(path) as json_file:  
    data = json.load(json_file)

  return data