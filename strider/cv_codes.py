import argparse
import cv2


class CalibrateAction(argparse.Action):
    # calibrate action
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', argparse.SUPPRESS)
        super().__init__(*args, **kwargs)

    def __call__(self, parser_, namespace, values, option_string=None):
        ret = ['__codes__ = Codes()']
        cv2.imshow('calibration', 0)

        if values == 'all':
            print('enter backspace')
            backspace_code = cv2.waitKeyEx()
            if backspace_code != Codes.backspace:
                ret.append(f'custom_codes.backspace = {backspace_code}')
            print('enter esc')
            esc_code = cv2.waitKeyEx()
            if esc_code != Codes.esc:
                ret.append(f'__codes__.esc = {esc_code}')
        else:
            backspace_code = Codes.backspace
            esc_code = Codes.esc

        for name, v in Codes.__dict__.items():
            if name.startswith('_'):
                continue
            if (not values == 'all') and v < 128:
                continue

            print(f'enter code for {name}, backspace to not register this key, or esc to quit and save calibration')
            code = cv2.waitKeyEx()
            if code == backspace_code:
                continue
            elif code == esc_code:
                break
            if code == v:
                print(f'{name} = {code!r}, same as default')
            else:
                ret.append(f'__codes__.{name}= {code!r}')
                print(f'{name} = {code!r}')
        with open('__calibration__.py', 'w') as w:
            w.write('\n'.join(ret))
        print('calibration saved to __calibration__.py')
        exit()


class Codes:
    # a static class containing all the key codes the program needs. These values can be overridden
    # by the calibration file
    right = 2555904
    left = 2424832
    home = 2359296
    end = 2293760

    # everything below here is ascii
    esc = 27
    backspace = 8
    space = ord(' ')
    enter = ord('\r')
    tab = ord('\t')

    a = ord('a')
    c = ord('c')
    d = ord('d')
    g = ord('g')
    h = ord('h')
    i = ord('i')
    n = ord('n')
    p = ord('p')
    q = ord('q')
    r = ord('r')
    s = ord('s')
    t = ord('t')
    u = ord('u')
    w = ord('w')
    z = ord('z')

    shift_g = ord('G')
    shift_q = ord('Q')
    shift_z = ord('Z')


code_keys = [key for key in Codes.__dict__ if not key.startswith('_')]
