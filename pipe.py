import Queue as queue
import subprocess as sp
import threading
import time
import cv2
import numpy

q = queue.LifoQueue()
FFMPEG_BIN = 'ffmpeg'
command = [
    FFMPEG_BIN,
    '-i',
    'pipe:',  # fifo is the named pipe
    '-pix_fmt',
    'bgr24',  # opencv requires bgr24 pixel format.
    '-vcodec',
    'libx264',
    '-an',
    '-sn',  # we want to disable audio processing (there is no audio)
    '-f',
    'image2pipe',
    '-'
]
pipe_in = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)


def worker(pipe):
  while True:
    raw_image = pipe.stdout.read(1024 * 768 * 3)
    # transform the byte read into a numpy array
    image = numpy.fromstring(raw_image, dtype='uint8')
    if image is not None:
      image = image.reshape((768, 1024, 3))
      q.put(image)
    pipe.stdout.flush()


t = threading.Thread(target=worker, args=(pipe_in,))
t.start()

while True:
  # Capture frame-by-frame
  frame = q.get()
  cv2.imshow('Video', frame)
  time.sleep(0.1)
  q.queue[:] = []
  if cv2.waitKey(1) & 0xFF == ord('q'):
    break

t.join()
cv2.destroyAllWindows()

