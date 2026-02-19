from ctypes import POINTER, Structure, Union, byref, c_long, c_short, c_ulong, c_ushort, pointer, sizeof, windll

PUL = POINTER(c_ulong)


class KeyBdInput(Structure):
    _fields_ = [
        ("wVk", c_ushort),
        ("wScan", c_ushort),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", PUL),
    ]


class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong), ("wParamL", c_short), ("wParamH", c_ushort)]


class MouseInput(Structure):
    _fields_ = [
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", PUL),
    ]


class InputI(Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]


class Input(Structure):
    _fields_ = [("type", c_ulong), ("ii", InputI)]


class Point(Structure):
    _fields_ = [("x", c_ulong), ("y", c_ulong)]


def get_mouse_position():
    orig = Point()
    windll.user32.GetCursorPos(byref(orig))
    return int(orig.x), int(orig.y)


def set_mouse_position(pos):
    x, y = pos
    windll.user32.SetCursorPos(x, y)


def move_click(pos, move_back=False):
    origx, origy = get_mouse_position()
    set_mouse_position(pos)

    inputs_type = Input * 2
    extra = c_ulong(0)

    down = InputI()
    down.mi = MouseInput(0, 0, 0, 2, 0, pointer(extra))

    up = InputI()
    up.mi = MouseInput(0, 0, 0, 4, 0, pointer(extra))

    packet = inputs_type((0, down), (0, up))
    windll.user32.SendInput(2, pointer(packet), sizeof(packet[0]))

    if move_back:
        set_mouse_position((origx, origy))
        return origx, origy


def sendkey(scancode, pressed):
    if scancode is None:
        return

    inputs_type = Input * 1
    extra = c_ulong(0)

    key_input = InputI()
    key_input.ki = KeyBdInput(0, scancode, 0x8, 0, pointer(extra))

    if not pressed:
        key_input.ki.dwFlags |= 0x2

    packet = inputs_type((1, key_input))
    windll.user32.SendInput(1, pointer(packet), sizeof(packet[0]))
