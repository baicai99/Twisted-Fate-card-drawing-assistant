import threading
import time
import os  # 用于文件操作
from ctypes import *  # 获取屏幕上某个坐标的颜色

import pyWinhook  # 使用 pywinhook 库
import win32gui
import win32process
import psutil
import pythoncom

# <editor-fold desc="模拟点击部分">
PUL = POINTER(c_ulong)


class KeyBdInput(Structure):
    _fields_ = [("wVk", c_ushort),
                ("wScan", c_ushort),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong),
                ("wParamL", c_short),
                ("wParamH", c_ushort)]


class MouseInput(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_ulong),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(Structure):
    _fields_ = [("type", c_ulong),
                ("ii", Input_I)]


class POINT(Structure):
    _fields_ = [("x", c_ulong),
                ("y", c_ulong)]


def get_mpos():
    orig = POINT()
    windll.user32.GetCursorPos(byref(orig))
    return int(orig.x), int(orig.y)


def set_mpos(pos):
    x, y = pos
    windll.user32.SetCursorPos(x, y)


def move_click(pos, move_back=False):
    origx, origy = get_mpos()
    set_mpos(pos)
    FInputs = Input * 2
    extra = c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 2, 0, pointer(extra))
    ii2_ = Input_I()
    ii2_.mi = MouseInput(0, 0, 0, 4, 0, pointer(extra))
    x = FInputs((0, ii_), (0, ii2_))
    windll.user32.SendInput(2, pointer(x), sizeof(x[0]))
    if move_back:
        set_mpos((origx, origy))
        return origx, origy


def sendkey(scancode, pressed):
    FInputs = Input * 1
    extra = c_ulong(0)
    ii_ = Input_I()
    flag = 0x8
    ii_.ki = KeyBdInput(0, 0, flag, 0, pointer(extra))
    InputBox = FInputs((1, ii_))
    if scancode is None:
        return
    InputBox[0].ii.ki.wScan = scancode
    InputBox[0].ii.ki.dwFlags = 0x8

    if not pressed:
        InputBox[0].ii.ki.dwFlags |= 0x2

    windll.user32.SendInput(1, pointer(InputBox), sizeof(InputBox[0]))
# </editor-fold>


def getRgb(x, y):
    gdi32 = windll.gdi32
    user32 = windll.user32
    hdc = user32.GetDC(None)  # 获取颜色值
    pixel = gdi32.GetPixel(hdc, x, y)  # 提取RGB值
    r = pixel & 0x0000ff
    g = (pixel & 0x00ff00) >> 8
    b = pixel >> 16
    return [r, g, b]


def get_color(r, g, b):
    if r == g == b:
        return '灰'
    if (r <= 127 and g <= 127 and b >= 127):
        return "蓝"
    elif (r <= 127 and g >= 127 and b <= 127):
        return "绿"
    elif (r >= 127 and g <= 127 and b <= 127):
        return '红'
    elif (r >= 127 and g >= 127 and b <= 127):
        return "黄"
    elif (r >= 127 and g <= 127 and b >= 127):
        return "紫"
    elif (r <= 127 and g >= 127 and b >= 127):
        return "蓝"
    elif (r >= 127 and g >= 127 and b >= 127):
        return get_color(r - 1, g - 1, b - 1)
    elif (r <= 127 and g <= 127 and b <= 127):
        return get_color(r + 1, g + 1, b + 1)


# 全局变量
self_w = 0
req_color = "黄"
ctrl_press = False
last_R_time = 0
paused = False  # 添加暂停标志
x = 827  # 默认x坐标
y = 975  # 默认y坐标
process_time = time.time()
last_thread = threading.Thread(target=lambda: None)  # 初始化空线程
coordinate_file = 'color_coordinates.txt'  # 坐标文件名称
current_window_active = threading.Event()  # 使用 threading.Event 确保线程安全


target_process_name = "League of Legends.exe"  # 修改为您要检测的进程名称

def check_active_window():
    while True:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                # 打印当前活动进程名称
                # print(f"当前活动进程名称：{process_name}")
                if process_name.lower() == target_process_name.lower():
                    current_window_active.set()
                else:
                    current_window_active.clear()
            except psutil.NoSuchProcess:
                current_window_active.clear()
        else:
            current_window_active.clear()
        time.sleep(0.5)


def load_coordinates():
    """从文件中加载坐标"""
    global x, y
    if os.path.exists(coordinate_file):
        try:
            with open(coordinate_file, 'r') as f:
                data = f.read().split(',')
                if len(data) == 2:
                    x, y = int(data[0]), int(data[1])
                    print(f"已从文件加载取色坐标：{x}, {y}")
                else:
                    print("坐标文件格式错误，使用默认坐标")
        except Exception as e:
            print(f"加载坐标时发生错误：{e}，使用默认坐标")
    else:
        print("未找到坐标文件，使用默认坐标")


def save_coordinates():
    """将坐标保存到文件"""
    try:
        with open(coordinate_file, 'w') as f:
            f.write(f"{x},{y}")
        print(f"已将取色坐标保存到文件：{x}, {y}")
    except Exception as e:
        print(f"保存坐标时发生错误：{e}")


def down(event):
    global ctrl_press, self_w, last_R_time, paused

    key = event.Key
    print(f"按键按下：{key}, current_window_active: {current_window_active.is_set()}")

    if key == 'Return':
        paused = not paused
        if paused:
            print("功能已暂停")
        else:
            print("功能已恢复")
        return True  # 允许回车键的正常功能

    # 如果功能被暂停，或者当前窗口不是目标窗口，则不处理其他按键
    if paused or not current_window_active.is_set():
        return True

    if key == 'Lcontrol' or key == 'Rcontrol':
        ctrl_press = True
        return True
    # ctrl 按下中是升级技能操作，不响应抽牌
    if ctrl_press:
        return True

    if key == "E":
        tryLisCard('黄')
    elif key == "W":
        if self_w <= 0:
            # 是键盘按的W
            print(self_w, "w 键盘按的,拦截")
            tryLisCard('蓝')
            # 将这个事件拦截,软件会帮助按
            return False
        else:
            print(self_w, "w 程序按的")
            self_w = self_w - 1
    elif key == "A":
        tryLisCard('红')
    elif key == "R":
        # 是否距离上次按R过去了2秒
        if time.time() - last_R_time > 8:
            # 第一次R
            last_R_time = time.time()
        else:
            # 第二次R
            last_R_time = 0
            # 按第二次R开始抽牌
            tryLisCard('黄')
    return True


def up(event):
    global ctrl_press

    key = event.Key

    # 如果功能被暂停，或者当前窗口不是目标窗口，则不处理按键抬起事件
    if paused or not current_window_active.is_set():
        return True

    if key == 'Lcontrol' or key == 'Rcontrol':
        ctrl_press = False
    return True


def move(event):
    global x, y

    # 如果功能被暂停，或者当前窗口不是目标窗口，则不处理鼠标事件
    if paused or not current_window_active.is_set():
        return True

    x = event.Position[0]
    y = event.Position[1]
    print("当前取色坐标：", x, y, '祝您游戏愉快')
    r, g, b = getRgb(x, y)
    print("当前颜色：", get_color(r, g, b))
    save_coordinates()  # 保存坐标到文件
    return True


def tryLisCard(color):
    global self_w, req_color, process_time, last_thread
    # 按 w 开始选牌
    click_W()
    # 更新当前需求的颜色为最近一次按下需要的颜色
    req_color = color
    # 更新技能CD为最近按下的时间
    process_time = time.time()
    # 开始监听选牌，没启动则启动线程
    if not last_thread.is_alive():
        last_thread = threading.Thread(target=click)
        last_thread.start()


def click_W():
    global self_w
    # 标记是本软件按下的W
    self_w = self_w + 1
    sendkey(0x11, 1)
    sendkey(0x11, 0)


def click():
    global process_time, req_color, paused
    process_time = time.time()
    # 离上次按下的时间超过 3 秒还没选到牌，则选牌失败
    while time.time() - process_time < 3:
        # 如果功能被暂停，或者当前窗口不是目标窗口，则退出线程
        if paused or not current_window_active.is_set():
            print('功能已暂停或窗口未激活，停止抽牌')
            return
        if time.time() - process_time < 0.15:
            print("等待技能动画释放")
        else:
            # 开始抽牌
            r, g, b = getRgb(x, y)
            color = get_color(r, g, b)
            if color == req_color:
                click_W()
                print('抽牌成功', req_color)
                return
        # 刷新频率，按照每秒 30 帧刷新
        time.sleep(0.034)
    print('抽牌失败', req_color)


def action():
    hm = pyWinhook.HookManager()  # 使用 pywinhook 的 HookManager
    hm.KeyDown = down
    hm.KeyUp = up
    hm.MouseMiddleDown = move
    hm.HookKeyboard()
    hm.HookMouse()
    pythoncom.PumpMessages()


if __name__ == "__main__":
    load_coordinates()  # 程序启动时加载坐标

    # 启动检查活动窗口的线程
    window_thread = threading.Thread(target=check_active_window)
    window_thread.daemon = True  # 设置为守护线程，主程序退出时该线程自动退出
    window_thread.start()

    print('一切尽在卡牌中！光速抽牌，已经启动：E：黄牌，W：蓝牌，A：红牌，大招自动黄牌')
    print('按下 鼠标中间滑轮按键 确定卡牌取色位置，当前位置：', x, y)
    print('按下 回车键 可暂停/恢复 功能')
    print(f'只有当进程名称为 "{target_process_name}" 时，功能才会激活')
    action()
