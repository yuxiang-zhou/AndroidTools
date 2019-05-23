import utils
import cv2
import time


def main():
    before = time.time()
    control = utils.Control()
    screen = control.screenshot()
    print(screen.shape)
    after = time.time()

    cv2.imwrite(
        './screen_{}.png'
        .format(int(time.time())), screen)

    print('Elapse: {}'.format(after - before))


# Run our main function if we're in the default scope
if __name__ == "__main__":
    main()
