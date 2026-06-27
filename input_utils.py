# Visit https://www.lddgo.net/string/pyc-compile-decompile for more information
# Version : Python 3.9

import ctypes
import time
import random
from ctypes import wintypes
import win32api
import win32con
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.SetFocus.argtypes = (wintypes.HWND,)
user32.SetFocus.restype = wintypes.HWND
user32.SwitchToThisWindow.argtypes = (wintypes.HWND, wintypes.BOOL)
user32.SwitchToThisWindow.restype = wintypes.BOOL
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
SCREEN_WIDTH = win32api.GetSystemMetrics(0)
SCREEN_HEIGHT = win32api.GetSystemMetrics(1)
MOUSEEVENTF_MOVE = 1
MOUSEEVENTF_LEFTDOWN = 2
MOUSEEVENTF_LEFTUP = 4
MOUSEEVENTF_RIGHTDOWN = 8
MOUSEEVENTF_RIGHTUP = 16
MOUSEEVENTF_MIDDLEDOWN = 32
MOUSEEVENTF_MIDDLEUP = 64
MOUSEEVENTF_WHEEL = 2048
MOUSEEVENTF_HWHEEL = 4096
MOUSEEVENTF_ABSOLUTE = 32768
VK_SHIFT = 16
VK_CONTROL = 17
VK_MENU = 18
VK_SPACE = 32
VK_ESCAPE = 27
VK_RETURN = 13
VK_TAB = 9
VK_BACK = 8
VK_DELETE = 46
VK_HOME = 36
VK_END = 35
VK_LEFT = 37
VK_UP = 38
VK_RIGHT = 39
VK_DOWN = 40
VK_F1 = 112
VK_F2 = 113
VK_F3 = 114
VK_F4 = 115
VK_F5 = 116
VK_F6 = 117
VK_F7 = 118
VK_F8 = 119
VK_F9 = 120
VK_F10 = 121
VK_F11 = 122
VK_F12 = 123

def pixel_to_mouse_unit(pixel):
    '''将像素值转换为Windows API鼠标移动的微位移单位'''
    return int(pixel * 65536 / SCREEN_WIDTH)


def get_current_cursor_pos():
    '''获取当前鼠标位置'''
    point = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return (point.x, point.y)


def set_cursor_pos_absolute(x, y):
    '''绝对定位鼠标位置'''
    user32.SetCursorPos(x, y)


def random_sleep(min_seconds, max_seconds=None):
    '''随机等待时间
    :param min_seconds: 固定延时 / 区间最小值
    :param max_seconds: 区间最大值，不传则为固定延时
    '''
    if max_seconds is None:
        # 单个值：固定延时
        time.sleep(min_seconds)
    else:
        # 两个值：区间随机延时
        time.sleep(random.uniform(min_seconds, max_seconds))
        


def randomize_value(base_val, range_pct = 15):
    '''统一数值随机化（和原有脚本逻辑一致，防检测核心）'''
    pct = range_pct / 100
    return base_val * random.uniform(1 - pct, 1 + pct)


def find_rf4_window():
    '''查找RF4游戏窗口句柄（适配窗口名：Russian Fishing 4）'''
    return user32.FindWindowA(None, b'Russian Fishing 4')


def activate_rf4_window():
    '''激活RF4游戏窗口（底层API，确保游戏获得输入焦点）'''
    hwnd = find_rf4_window()
    if not hwnd:
        print('❌ 未找到RF4游戏窗口，请确认游戏已启动')
        return False

    # 多层激活，强制拿到窗口+键盘焦点
    user32.SwitchToThisWindow(hwnd, True)
    user32.SetForegroundWindow(hwnd)
    user32.SetFocus(hwnd)  # 关键：强制设置键盘输入焦点

    # 阶梯延时，给系统完成切换
    time.sleep(0.2)
    random_sleep(0.3, 0.6)
    return True

def mouse_move_relative(dx_pixel, dy_pixel, step_size=1, step_delay=0.015):
    '''
    Windows API底层平滑移动鼠标（相对移动，适配RF4视角转向核心）
    :param dx_pixel: 水平移动像素（负=左移，正=右移）
    :param dy_pixel: 垂直移动像素（负=上移，正=下移）
    :param step_size: 每步移动像素，越小越平滑
    :param step_delay: 每步间隔时间
    '''
    total_steps_x = abs(dx_pixel) // step_size
    if abs(dx_pixel) % step_size != 0:
        total_steps_x += 1
    total_steps_y = abs(dy_pixel) // step_size
    if abs(dy_pixel) % step_size != 0:
        total_steps_y += 1
    total_steps = max(total_steps_x, total_steps_y)
    if total_steps == 0:
        return None

    # 修复：None 改为 dx_pixel
    step_dx = dx_pixel / total_steps
    step_dy = dy_pixel / total_steps

    for i in range(total_steps):
        dx_unit = pixel_to_mouse_unit(step_dx)
        dy_unit = pixel_to_mouse_unit(step_dy)
        if i % 3 == 0:
            dx_unit += random.randint(-10, 10)
            dy_unit += random.randint(-10, 10)
        user32.mouse_event(MOUSEEVENTF_MOVE, dx_unit, dy_unit, 0, 0)
        current_delay = step_delay * random.uniform(0.8, 1.2)
        time.sleep(current_delay)


def mouse_move_to(x, y, duration = (0.3,)):
    '''
    拟人化移动到绝对坐标（带贝塞尔曲线，适配按钮点击）
    :param x: 目标X坐标
    :param y: 目标Y坐标
    :param duration: 移动总时间（秒）
    '''
    (current_x, current_y) = get_current_cursor_pos()
    dx = x - current_x
    dy = y - current_y
    distance = (dx ** 2 + dy ** 2) ** 0.5
    if distance < 5:
        set_cursor_pos_absolute(x, y)
        return None
    base_time = max(0.1, min(0.5, distance / 1000))
    actual_duration = base_time * random.uniform(0.8, 1.2)
    control_x = (current_x + x) / 2 + random.randint(-20, 20)
    control_y = (current_y + y) / 2 + random.randint(-20, 20)
    steps = int(actual_duration * 50)
    for i in range(steps):
        t = i / steps
        curve_x = (1 - t) ** 2 * current_x + 2 * (1 - t) * t * control_x + t ** 2 * x
        curve_y = (1 - t) ** 2 * current_y + 2 * (1 - t) * t * control_y + t ** 2 * y
        set_cursor_pos_absolute(int(curve_x), int(curve_y))
        time.sleep(actual_duration / steps)


def mouse_click(button, x, y, double_click = ('left', None, None, False)):
    """
    鼠标点击（底层API实现，带随机按下时长，防检测）
    :param button: 'left', 'right', 'middle'
    :param x, y: 点击坐标，None则为当前位置
    :param double_click: 是否双击
    """
    if x is not None and y is not None:
        mouse_move_to(x, y)
    if button.lower() == 'left':
        down_event = MOUSEEVENTF_LEFTDOWN
        up_event = MOUSEEVENTF_LEFTUP
    elif button.lower() == 'right':
        down_event = MOUSEEVENTF_RIGHTDOWN
        up_event = MOUSEEVENTF_RIGHTUP
    else:
        down_event = MOUSEEVENTF_MIDDLEDOWN
        up_event = MOUSEEVENTF_MIDDLEUP
    if double_click:
        for _ in range(2):
            user32.mouse_event(down_event, 0, 0, 0, 0)
            random_sleep(0.03, 0.08)
            user32.mouse_event(up_event, 0, 0, 0, 0)
            random_sleep(0.05, 0.1)
    else:
        user32.mouse_event(down_event, 0, 0, 0, 0)
        random_sleep(0.03, 0.15)
        user32.mouse_event(up_event, 0, 0, 0, 0)
    random_sleep(0.05, 0.2)


def mouse_down(button = ('left',)):
    '''按下鼠标（不释放，适配收线、抬杆）'''
    if button.lower() == 'left':
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    elif button.lower() == 'right':
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)


def mouse_up(button = ('left',)):
    '''松开鼠标（不释放，适配收线、抬杆）'''
    if button.lower() == 'left':
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button.lower() == 'right':
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


def mouse_scroll(clicks, direction = (1, 'down')):
    '''鼠标滚轮滚动'''
    scroll_event = MOUSEEVENTF_WHEEL
    if direction.lower() == 'up':
        clicks = abs(clicks)
    else:
        clicks = -abs(clicks)
    for _ in range(abs(clicks)):
        user32.mouse_event(scroll_event, 0, 0, clicks * 120, 0)
        random_sleep(0.05, 0.15)


def key_press(key, press_duration = None):
    """
    按下并释放单个按键（底层API，带随机按住时长）
    :param key: 字符或虚拟键码（如'shift'、'd'、VK_SHIFT）
    :param press_duration: 按下持续时间（秒）
    """
    key_code = get_key_code(key)
    if key_code == 0:
        print(f'''❌ 无效按键：{key}''')
        return None
    user32.keybd_event(key_code, 0, 0, 0)
    if press_duration is None:
        hold_time = random.uniform(0.05, 0.2)
    else:
        hold_time = press_duration * random.uniform(0.8, 1.2)
    time.sleep(max(0.01, hold_time))
    user32.keybd_event(key_code, 0, 2, 0)
    random_sleep(0.05, 0.15)


def key_down(key):
    '''按下按键（不释放，适配SHIFT长按、方向键移动）'''
    key_code = get_key_code(key)
    if key_code == 0:
        print(f'''❌ 无效按键：{key}''')
        return
    user32.keybd_event(key_code, 0, 0, 0)
    random_sleep(0.02, 0.05)


def key_up(key):
    '''释放按键（适配长按后的释放，核心修复SHIFT失效）'''
    key_code = get_key_code(key)
    if key_code == 0:
        print(f'''❌ 无效按键：{key}''')
        return
    user32.keybd_event(key_code, 0, 2, 0)
    random_sleep(0.02, 0.05)


def key_combo(keys):
    """
    组合键（如Ctrl+A）
    :param keys: 键列表，如['ctrl', 'a']
    """
    for key in keys[:-1]:
        key_down(key)
        random_sleep(0.02, 0.05)
    key_press(keys[-1], press_duration=0.1)
    for key in reversed(keys[:-1]):
        key_up(key)
        random_sleep(0.02, 0.05)


def get_key_code(key):
    '''将字符/键名转换为Windows虚拟键码（修复SHIFT、长按键、单字符报错问题）'''
    # 本身是数字键码，直接返回
    if isinstance(key, int):
        return key

    key_lower = key.lower().strip()

    # 完整按键映射表（沿用你原有配置，修复shift=None问题）
    key_map = {
        'shift': VK_SHIFT,
        'ctrl': VK_CONTROL,
        'alt': VK_MENU,
        'space': VK_SPACE,
        'esc': VK_ESCAPE,
        'escape': VK_ESCAPE,
        'enter': VK_RETURN,
        'return': VK_RETURN,
        'tab': VK_TAB,
        'backspace': VK_BACK,
        'delete': VK_DELETE,
        'home': VK_HOME,
        'end': VK_END,
        'left': VK_LEFT,
        'right': VK_RIGHT,
        'up': VK_UP,
        'down': VK_DOWN,
        'w': ord('W'),
        'a': ord('A'),
        's': ord('S'),
        'd': ord('D'),
        'e': ord('E'),
        'f': ord('F'),
        'm': ord('M'),
        '1': ord('1'),
        '2': ord('2'),
        '3': ord('3'),
        '4': ord('4'),
        'f1': VK_F1,
        'f2': VK_F2,
        'f3': VK_F3,
        'f4': VK_F4,
        'f5': VK_F5,
        'f6': VK_F6,
        'f7': VK_F7,
        'f8': VK_F8,
        'f9': VK_F9,
        'f10': VK_F10,
        'f11': VK_F11,
        'f12': VK_F12,
        '.': 190,
        ',': 188,
        '-': 189,
        '=': 187,
        '[': 219,
        ']': 221,
        '\\': 220,
        ';': 186,
        "'": 222,
        '`': 192,
        '/': 191
    }

    # 1. 优先匹配功能键/长键名（shift/ctrl/space 等）
    if key_lower in key_map:
        return key_map[key_lower]

    # 2. 处理单个字符（字母、数字、符号）
    if len(key_lower) == 1:
        return ord(key_lower.upper())

    # 3. 未知按键，返回 0
    return 0
def release_all_keys():
    '''释放所有可能按下的键盘+鼠标按键（核心防键鼠卡死，修复SHIFT/左键残留）'''
    keys_to_release = [
        VK_SHIFT,
        VK_CONTROL,
        VK_MENU,
        ord('W'),
        ord('A'),
        ord('S'),
        ord('D'),
        ord('Q'),
        ord('E'),
        ord('R'),
        ord('F'),
        ord('M'),
        ord('\t'),
        VK_ESCAPE,
        ord('1'),
        ord('2'),
        ord('3'),
        ord('4'),
        VK_SPACE,
        VK_BACK]
# WARNING: Decompyle incomplete


def human_type_text(text, min_delay, max_delay = (0.05, 0.2)):
    '''
    拟人化打字（模拟人类打字速度和错误）
    :param text: 要输入的文本
    :param min_delay: 最小按键间隔
    :param max_delay: 最大按键间隔
    '''
    for char in text:
        if random.random() < 0.05:
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            key_press(wrong_char)
            random_sleep(0.1, 0.3)
            key_press('backspace')
            random_sleep(0.1, 0.3)
        key_press(char)
        delay = random.uniform(min_delay, max_delay)
        if char == ' ' and random.random() < 0.1:
            delay *= random.uniform(1.5, 3)
        time.sleep(delay)


def simulate_human_idle(min_seconds, max_seconds = (10, 120)):
    '''
    模拟人类空闲（随机移动鼠标，轻微操作）
    :param min_seconds: 最小空闲时间
    :param max_seconds: 最大空闲时间
    '''
    idle_time = random.randint(min_seconds, max_seconds)
    start_time = time.time()
    print(f'''🧍 模拟人类空闲，持续约{idle_time}秒''')
    if time.time() - start_time < idle_time:
        for _ in range(random.randint(1, 5)):
            dx = random.randint(-3, 3)
            dy = random.randint(-3, 3)
            mouse_move_relative(dx, dy, 1, 0.05, **('step_size', 'step_delay'))
            time.sleep(random.uniform(0.5, 2))
        if random.random() < 0.2:
            dx = random.randint(-50, 50)
            mouse_move_relative(dx, 0, 10, 0.01, **('step_size', 'step_delay'))
        if random.random() < 0.1:
            key_press(random.choice([
                'tab',
                'm',
                '4']))
        time.sleep(random.uniform(2, 10))
    # continue


def click(x, y, button = (None, None, 'left')):
    '''兼容PyAutoGUI的click函数'''
    mouse_click(button, x, y)


def moveTo(x, y, duration = (0.3,)):
    '''兼容PyAutoGUI的moveTo函数'''
    mouse_move_to(x, y, duration)


def press(keys):
    '''兼容PyAutoGUI的press函数'''
    if isinstance(keys, list):
        for key in keys:
            key_press(key)
    else:
        key_press(keys)


def hotkey(*args):
    '''兼容PyAutoGUI的hotkey函数'''
    key_combo(list(args))
    
    
# if __name__ == '__main__':
#     from rf4_config import CAST_HOLD_TIME, DETECT_INTERVAL, FISH_ICON_TEMPLATE, FISH_CATCHED_TEMPLATE, FISH_MATCH_THRESHOLD, READY_MATCH_THRESHOLD, CATCHED_MATCH_THRESHOLD, \
#         READY_TEXT_1_DETECT_INTERVAL, READY_TEXT_2_DETECT_INTERVAL, DEFAULT_MAX_FISH_COUNT, MIN_CUSTOM_MAX_FISH, MAX_CUSTOM_MAX_FISH, MIN_EAT_INTERVAL, MAX_EAT_INTERVAL, EAT_KEY, RELEASE_KEY, \
#         SPACE_KEY, SHIFT_KEY, ASSEMBLY_CHECK_INTERVAL, DEVICE_UNASSEMBLED_TEMPLATE, SELL_POINT_CONFIG_FILE, BIG_REST_BASE_HOURS, BIG_REST_RANDOM_HOURS, BIG_REST_WAIT_LOGIN
#
#     while True:
#          key_press(SPACE_KEY)
#         time.sleep(1)