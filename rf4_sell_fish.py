# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'rf4_sell_fish.py'
# Bytecode version: 3.9.0beta5 (3425)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import cv2
import json
import time
import random
import numpy as np
import os
import mss
import input_utils as iu
from rf4_state import state
import rf4_rest_strategy as rest_strategy

JSON_CONFIG_PATH = 'map_config.json'
MATCH_THRESHOLD = 0.8
ROTATE_WAIT_TIME = 1.5
TEMPLATE_PATHS = {
    'exit': 'image/exit_button.png',
    'confirm': 'image/confirm_exit.png',
    'sell': 'image/sell_button_template.png'
}


def screen_capture():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)


def find_template(template_path, threshold=MATCH_THRESHOLD):
    if not os.path.exists(template_path):
        print(f'❌ 模板文件不存在：{template_path}')
        return (None, None)
    template = cv2.imread(template_path, 0)
    if template is None:
        print(f'❌ 模板文件读取失败：{template_path}')
        return (None, None)
    t_h, t_w = template.shape[:2]
    screen_gray = screen_capture()
    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        center_x = max_loc[0] + t_w // 2
        center_y = max_loc[1] + t_h // 2
        return (center_x, center_y)
    else:
        print(f'❌ 模板未识别：{os.path.basename(template_path)} | 匹配度：{max_val:.2f}/{threshold}')
        return (None, None)


def find_and_click_template(template_path, retry=2):
    iu.activate_rf4_window()
    iu.random_sleep(0.1, 0.2)
    for _ in range(retry):
        x, y = find_template(template_path, MATCH_THRESHOLD)
        if x and y:
            offset_x = random.randint(-4, 4)
            offset_y = random.randint(8, 11)
            final_x = x + offset_x
            final_y = y + offset_y
            iu.mouse_click(x=final_x, y=final_y)
            print(f'✅ 精准点击：{os.path.basename(template_path)} | 原坐标({x},{y}) | 偏移({offset_x},{offset_y})')
            return True
        iu.random_sleep(0.2, 0.4)
    return False


def wait_and_click_login_button(timeout=300):
    """
    循环检测登录按钮，找到后自动点击
    :param timeout: 最大等待时间（秒），默认5分钟
    :return: True/False
    """
    start_time = time.time()
    print('\n👀 开始检测登录按钮，找到后自动点击...')
    while time.time() - start_time < timeout and state.is_running:
        if find_and_click_template(state.login_button_template):
            load_wait = iu.randomize_value(state.login_load_wait)
            print(f'⏳ 登录成功，等待游戏加载：{load_wait:.1f}秒')
            iu.random_sleep(load_wait)
            return True
        time.sleep(2)
    if not state.is_running:
        print('🛑 脚本停止，中断登录等待')
    else:
        print(f'❌ 登录按钮检测超时（{timeout}秒），请手动点击！')
    return False


def playback_operations(record_file, precise_mode=True):
    if not state.is_running or not os.path.exists(record_file):
        print(f'🛑 脚本停止/操作文件不存在：{record_file}')
        return False
    try:
        with open(record_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        print(f"✅ 加载操作文件：{os.path.basename(record_file)} | 共{len(records)}个操作 | 模式：{'精准一致' if precise_mode else '防检测随机'}")
    except Exception as e:
        print(f'❌ 加载操作文件失败：{e}')
        return False

    playback_start = time.perf_counter()
    first_ts = records[0]['timestamp'] if records else 0.0
    key_name_map = {
        'key.shift': 'shift',
        'key.ctrl': 'ctrl',
        'key.alt': 'alt',
        'key.esc': 'esc',
        'key.space': 'space',
        'key.tab': 'tab',
        'key.w': 'w',
        'key.a': 'a',
        'key.s': 's',
        'key.d': 'd',
        'key.e': 'e',
        'key.f': 'f',
        'key.m': 'm'
    }

    for idx, record in enumerate(records):
        if not state.is_running:
            print(f'🛑 脚本停止，终止回放（第{idx + 1}操作）')
            return False
        try:
            target_elapsed = record['timestamp'] - first_ts
            actual_elapsed = time.perf_counter() - playback_start
            wait_time = max(0.0, target_elapsed - actual_elapsed)
            if wait_time > 0.001:
                if precise_mode:
                    time.sleep(wait_time)
                else:
                    iu.random_sleep(wait_time * 0.9, wait_time * 1.1)

            raw_key = record['key'].lower()
            raw_key = key_name_map.get(raw_key, raw_key)
            if record['type'] == 'key_press':
                iu.key_down(raw_key)
                if precise_mode:
                    time.sleep(0.02)
            else:
                iu.key_up(raw_key)
                if precise_mode:
                    time.sleep(0.02)
        except Exception as e:
            print(f'⚠️  第{idx + 1}操作失败：{e}，跳过')

    iu.release_all_keys()
    print(f"✅ 操作回放完成！已释放所有按键 | 模式：{'精准一致' if precise_mode else '防检测随机'}")
    return True


def rotate_by_mouse_slide(rotation):
    if not state.is_running:
        print('🛑 脚本停止，跳过转向')
        return False
    if rotation == 0:
        print('ℹ️  转向值为0，无需操作')
        return True

    direction = '👈 向左' if rotation < 0 else '👉 向右'
    move_pixel = abs(rotation)
    print(f'\n🖱️  底层API转向：{direction} | 移动{move_pixel}px | 屏幕{iu.SCREEN_WIDTH}x{iu.SCREEN_HEIGHT}')
    iu.random_sleep(0.4, 0.6)
    try:
        iu.mouse_move_relative(dx_pixel=rotation, step_size=8, step_delay=0.02)
        print('✅ 转向完成！')
        return True
    except Exception as e:
        print(f'❌ 转向失败：{str(e)}（请以管理员身份运行脚本）')
        return False


def simple_sell_operation():
    if not state.is_running:
        print('🛑 脚本停止，跳过卖鱼')
        return False
    print('\n===== 🐟 开始卖鱼操作 =====')
    try:
        iu.key_press('e', press_duration=0.1)
        iu.random_sleep(3.2, 4.2)
        iu.key_combo(['ctrl', 'a'])
        iu.random_sleep(0.9, 1.1)
        if not find_and_click_template(TEMPLATE_PATHS['sell'], retry=2):
            print('⚠️  卖鱼按钮点击失败，请手动确认！')
        iu.random_sleep(0.9, 1.1)
        iu.key_press('esc', press_duration=0.1)
        iu.random_sleep(0.9, 1.1)
        state.current_fish_count = 0
        print(f'✅ 卖鱼完成！渔户已重置为0/{state.max_fish_count}')
        return True
    except Exception as e:
        print(f'❌ 卖鱼操作失败：{e}')
        return False
    finally:
        iu.release_all_keys()


def relog_to_initial_pos(skip_login=False):
    if not state.is_running:
        print('🛑 脚本停止，跳过重登')
        return False
    print('\n===== 🚪 开始纯视觉重登回城 =====')
    try:
        iu.key_press('esc', press_duration=0.1)
        iu.random_sleep(0.7, 0.9)
        iu.key_down('shift')
        iu.random_sleep(0.04, 0.06)

        if not find_and_click_template(TEMPLATE_PATHS['exit']):
            iu.key_up('shift')
            raise Exception('未识别退出按钮')
        iu.random_sleep(0.04, 0.06)
        iu.key_up('shift')
        iu.random_sleep(0.3, 0.5)

        if not find_and_click_template(TEMPLATE_PATHS['confirm']):
            raise Exception('未识别确认退出按钮')
        iu.random_sleep(2.8, 3.2)

        print('\n===== ⏱️  运行状态检查（依赖主GUI时间统计） =====')
        rest_type = rest_strategy.check_need_rest()
        if rest_type == 'small_rest':
            rest_strategy.take_small_rest(state.rest_min_minutes, state.rest_max_minutes, reason='连续运行时长超限')
        elif rest_type == 'random_small_rest':
            rest_strategy.take_small_rest(state.rest_min_minutes // 2, state.rest_max_minutes // 2, reason='随机休息')

        if skip_login:
            print('⏸️  接收到跳过登录指令，执行大休息...')
            state.is_big_resting = True
            rest_strategy.take_big_rest(reason='单日运行时长超限')
            if not wait_and_click_login_button():
                raise Exception('大休息后登录失败')
            state.is_big_resting = False
        else:
            if not find_and_click_template(state.login_button_template):
                raise Exception('未识别登录按钮')
            load_wait = iu.randomize_value(state.login_load_wait)
            print(f'⏳ 等待游戏加载：{load_wait:.1f}秒')
            iu.random_sleep(load_wait)

        print('✅ 重登回城完成！' + ('已跳过登录按钮（大休息）' if skip_login else '已回到初始点位'))
        return True
    except Exception as e:
        print(f'❌ 重登回城失败：{e}')
        return False
    finally:
        iu.release_all_keys()


def relog_sell_process(target_map_id=16, target_point_id=1, skip_login=False):
    start_time = time.time()
    if not os.path.exists(JSON_CONFIG_PATH):
        print(f'❌ 配置文件不存在：{JSON_CONFIG_PATH}')
        state.is_selling_fish = False
        return None
    try:
        with open(JSON_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f'❌ 解析配置文件失败：{e}')
        state.is_selling_fish = False
        return None

    map_config = next((item for item in config_data if item.get('map_id') == target_map_id), None)
    point_config = None
    if map_config:
        point_config = next((p for p in map_config.get('points', []) if p.get('point_id') == target_point_id), None)

    if not map_config or not point_config:
        print(f'❌ 未找到配置：地图{target_map_id} | 点位{target_point_id}')
        state.is_selling_fish = False
        return None

    initial_rotation = map_config.get('initial_rotation', 0)
    water_rotation = point_config.get('water_rotation', 0)
    print('\n===== 🎮 RF4自动卖鱼流程启动 =====')
    print(f"📌 地图：{map_config['map_name']} | 点位：{target_point_id}号")
    print(f'📌 初始转向：{initial_rotation} | 钓点转向：{water_rotation}')
    print(f'📌 防检测配置：连续≤{state.continuous_max_hours}h | 单日≤{state.daily_max_hours}h | 休息{state.rest_min_minutes}-{state.rest_max_minutes}min')

    try:
        iu.release_all_keys()
        iu.activate_rf4_window()
        if not relog_to_initial_pos(skip_login=skip_login):
            raise Exception('重登回城失败')
        if not state.is_running:
            raise Exception('脚本已停止')

        move_initial_to_sell = map_config['files']['move_initial_to_sell']
        if not playback_operations(move_initial_to_sell, precise_mode=True):
            raise Exception('初始点→卖鱼点 移动失败')
        if not state.is_running:
            raise Exception('脚本已停止')

        iu.random_sleep(iu.randomize_value(ROTATE_WAIT_TIME))
        if not rotate_by_mouse_slide(initial_rotation):
            raise Exception('初始位置转向失败')
        if not state.is_running:
            raise Exception('脚本已停止')

        print('⏳ 转向完成，等待1秒后卖鱼...')
        iu.random_sleep(iu.randomize_value(1.0))
        if not simple_sell_operation():
            raise Exception('卖鱼操作失败')
        if not state.is_running:
            raise Exception('脚本已停止')

        move_sell_to_fishing = point_config['files']['move_sell_to_fishing']
        if not playback_operations(move_sell_to_fishing, precise_mode=True):
            raise Exception('卖鱼点→钓点 移动失败')
        if not state.is_running:
            raise Exception('脚本已停止')

        iu.random_sleep(iu.randomize_value(ROTATE_WAIT_TIME))
        if not rotate_by_mouse_slide(water_rotation):
            raise Exception('钓点水域转向失败')
        if not state.is_running:
            raise Exception('脚本已停止')

        run_dur = time.time() - start_time
        continuous_h = state.continuous_running_seconds / 3600
        daily_h = state.daily_running_seconds / 3600
        print('\n🎉 🎉 🎉 所有流程完成！🎉 🎉 🎉')
        print('💡 人物已对准水域，自动恢复钓鱼！')
        print(f'📊 运行统计：本次{run_dur:.1f}s | 连续{continuous_h:.1f}h | 今日{daily_h:.1f}h')

    except Exception as e:
        print(f'\n❌ 自动卖鱼流程失败：{e}')
        state.current_fish_count = state.max_fish_count
    finally:
        state.is_selling_fish = False
        iu.release_all_keys()