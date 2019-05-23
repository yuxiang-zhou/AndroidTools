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
import Queue as queue


if __name__ == '__main__':
  control = utils.Control()
  while True:
    control.touch((2574, 1067))
    control.wait(np.random.random() * 5)

