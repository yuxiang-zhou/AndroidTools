import os, sys, time
import numpy as np

def touch(x,y):
    cmd = 'adb shell input touchscreen tap {0} {1}'.format(x, y)
    os.system(cmd)


if __name__ == "__main__":
    while True:
        touch(int(sys.argv[1]) + np.random.random()*10, int(sys.argv[2]) + np.random.random()*10)
        time.sleep(np.random.random() * 5)