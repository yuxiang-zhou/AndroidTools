import subprocess
import cv2
import numpy as np
import time
from cStringIO import StringIO
from PIL import Image

def main():
  before = time.time()
  pipe = subprocess.Popen(
      "adb shell screencap -p",
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      shell=True)
  image_bytes = pipe.stdout.read()


  file_bytes = np.fromstring(image_bytes, np.uint8)
  screen = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

  after = time.time()

  cv2.imshow('we get', screen)
  cv2.waitKey(0)
  cv2.destroyAllWindows()

  print('Elapse: {}'.format(after - before))

# Run our main function if we're in the default scope
if __name__ == "__main__":
  main()
