import numpy as np
import subprocess
import cv2
import time


class Control(object):

  def screenshot_v2(self):

    pipe = subprocess.Popen(
        'adb shell screencap -p',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True)
    image_bytes = pipe.stdout.read()
    screen = cv2.imdecode(
        np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    return screen

  def screenshot(self):

    subprocess.Popen(
      "adb shell screencap -p /sdcard/.tmp-screen.png",
      shell=True)
    time.sleep(1)
    subprocess.Popen(
      "adb pull /sdcard/.tmp-screen.png",
      shell=True)
    time.sleep(2)
    screen = None
    while screen is None:
      screen = cv2.imread('.tmp-screen.png', cv2.IMREAD_COLOR)
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