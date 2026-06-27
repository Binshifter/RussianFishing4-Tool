# Visit https://www.lddgo.net/string/pyc-compile-decompile for more information
# Version : Python 3.9

import cv2
import time
import random
import numpy as np
import os
import input_utils as iu
TEMPLATE_ROOT = 'image'
LURE_TEMPLATE_FOLDER = os.path.join(TEMPLATE_ROOT, 'lure_templates')
LEADER_TEMPLATE_FOLDER = os.path.join(TEMPLATE_ROOT, 'leader_templates')
DEFAULT_LEADER_PARAM = '6.2'
DEFAULT_LURE_PARAM = '2 018'
MIN_RANDOM_WAIT = 0.5
MAX_RANDOM_WAIT = 1.5
MIN_CONFIRM_WAIT = 1
MAX_CONFIRM_WAIT = 1.5
TEMPLATE_THRESHOLD = {
    'device_unassembled': 0.75,
    'leader_option': 0.75,
    'lure_option': 0.4,
    'search_box': 0.6,
    'leader_template': 0.65,
    'lure_template': 0.65,
    'confirm_button': 0.7,
    'disappear_check': 0.75 }
CLICK_OFFSET_X_RANGE = (-2, 2)
CLICK_OFFSET_Y_RANGE = (-1, 1)
EXIT_RETRY_TIMES = 3
EXIT_RETRY_INTERVAL = 1
ESC_PRESS_BASE_DURATION = 0.1
os.makedirs(LURE_TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(LEADER_TEMPLATE_FOLDER, exist_ok=True)

def random_wait():
    '''随机等待（基础值MIN/MAX_RANDOM_WAIT，±15%随机）'''
    wait_time = iu.randomize_value(random.uniform(MIN_RANDOM_WAIT, MAX_RANDOM_WAIT))
    print(f'''⏳ 随机等待{wait_time:.2f}秒...''')
    iu.random_sleep(MIN_RANDOM_WAIT, MAX_RANDOM_WAIT)


def confirm_wait():
    '''操作后确认等待（基础值MIN/MAX_CONFIRM_WAIT，±15%随机）'''
    wait_time = iu.randomize_value(random.uniform(MIN_CONFIRM_WAIT, MAX_CONFIRM_WAIT))
    print(f'''⏳ 确认等待{wait_time:.2f}秒...''')
    iu.random_sleep(MIN_CONFIRM_WAIT, MAX_CONFIRM_WAIT)


def screen_capture():
    '''mss底层截图（复用卖鱼脚本逻辑，返回灰度图）'''
    import mss
# WARNING: Decompyle incomplete


def template_exists(template_path, threshold = (None,)):
    '''检测模板是否存在（保留原逻辑，替换为mss截图）'''
    if not threshold:
        pass
    threshold = TEMPLATE_THRESHOLD['disappear_check']
    if not os.path.exists(template_path):
        print(f'''❌ 模板文件不存在：{os.path.basename(template_path)}''')
        return False
    template = None.imread(template_path, 0)
    screen_gray = screen_capture()
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    max_val = cv2.minMaxLoc(res)[1]
    if max_val >= threshold:
        print(f'''🔍 检测到{os.path.basename(template_path)}（匹配度：{max_val:.2f}≥{threshold}）''')
        return True
    None(f'''🔍 未检测到{os.path.basename(template_path)}（匹配度：{max_val:.2f}<{threshold}）''')
    return False


def find_and_click_template(template_path, threshold):
    '''模板匹配+调用input_utils点击（修复Y轴偏移，精准点击）'''
    if not os.path.exists(template_path):
        print(f'''❌ 模板文件不存在：{os.path.basename(template_path)}''')
        return False
    template = None.imread(template_path, 0)
    screen_gray = screen_capture()
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    (min_val, max_val, min_loc, max_loc) = cv2.minMaxLoc(res)
# WARNING: Decompyle incomplete


def configure_single_leader(target_param = (DEFAULT_LEADER_PARAM,)):
    '''配置引线（保留原流程，完全调用input_utils函数）'''
    print('\n🔧 开始配置引线...')
    leader_option_path = os.path.join(TEMPLATE_ROOT, 'leader_option.png')
    search_box_path = os.path.join(TEMPLATE_ROOT, 'search_box.png')
    leader_template_path = os.path.join(LEADER_TEMPLATE_FOLDER, f'''leader_{target_param}kg.png''')
    confirm_button_path = os.path.join(TEMPLATE_ROOT, 'confirm.png')
    if not find_and_click_template(leader_option_path, TEMPLATE_THRESHOLD['leader_option']):
        return False
    if not None(search_box_path, TEMPLATE_THRESHOLD['search_box']):
        return False
    None.key_combo([
        'ctrl',
        'a'])
    iu.random_sleep(0.5, 1)
    iu.human_type_text(target_param, 0.1, 0.3, **('min_delay', 'max_delay'))
    print(f'''🔤 输入引线参数：{target_param}''')
    iu.random_sleep(1.2, 1.8)
    if not find_and_click_template(leader_template_path, TEMPLATE_THRESHOLD['leader_template']):
        return False
    if not None(confirm_button_path, TEMPLATE_THRESHOLD['confirm_button']):
        return False
    None(f'''✅ 引线{target_param}kg配置完成''')
    iu.random_sleep(0.5, 1)
    return True


def configure_single_lure(target_param = (DEFAULT_LURE_PARAM,)):
    '''配置拟饵（核心修复：文件名直接使用参数，如 2 018.png）'''
    print('\n🎣 开始配置拟饵...')
    lure_option_path = os.path.join(TEMPLATE_ROOT, 'lure_option.png')
    search_box_path = os.path.join(TEMPLATE_ROOT, 'search_box.png')
    lure_template_path = os.path.join(LURE_TEMPLATE_FOLDER, f'''{target_param}.png''')
    confirm_button_path = os.path.join(TEMPLATE_ROOT, 'confirm.png')
    if not find_and_click_template(lure_option_path, TEMPLATE_THRESHOLD['lure_option']):
        return False
    if not None(search_box_path, TEMPLATE_THRESHOLD['search_box']):
        return False
    None.key_combo([
        'ctrl',
        'a'])
    iu.random_sleep(0.5, 1)
    iu.human_type_text(target_param, 0.1, 0.3, **('min_delay', 'max_delay'))
    print(f'''🔤 输入拟饵参数：{target_param}''')
    iu.random_sleep(1.2, 1.8)
    if not find_and_click_template(lure_template_path, TEMPLATE_THRESHOLD['lure_template']):
        return False
    if not None(confirm_button_path, TEMPLATE_THRESHOLD['confirm_button']):
        return False
    None(f'''✅ 拟饵{target_param}配置完成''')
    iu.random_sleep(0.5, 1)
    return True


def detect_device_unassembled():
    '''检测「设备未组装」提示并点击（调用input_utils点击）'''
    template_path = os.path.join(TEMPLATE_ROOT, 'device_unassembled.png')
    return find_and_click_template(template_path, TEMPLATE_THRESHOLD['device_unassembled'])


def check_unconfigured_parts():
    '''检测未配置部件（保留原逻辑，返回leader/lure列表）'''
    print('\n🔍 检测未配置的部件...')
    unconfigured = []
    if template_exists(os.path.join(TEMPLATE_ROOT, 'leader_option.png'), TEMPLATE_THRESHOLD['leader_option']):
        unconfigured.append('leader')
    if template_exists(os.path.join(TEMPLATE_ROOT, 'lure_option.png'), TEMPLATE_THRESHOLD['lure_option']):
        unconfigured.append('lure')
    if unconfigured:
        print(f'''⚠️  检测到未配置部件：{unconfigured}''')
    else:
        print('✅ 所有部件已配置完成')
    return unconfigured


def repair_unconfigured_parts(unconfigured_parts, leader_param, lure_param = (DEFAULT_LEADER_PARAM, DEFAULT_LURE_PARAM)):
    '''修复未配置部件（保留原逻辑，按顺序配置引线→拟饵）'''
    repair_result = True
    if 'leader' in unconfigured_parts and repair_result:
        repair_result = configure_single_leader(leader_param)
    if 'lure' in unconfigured_parts and repair_result:
        repair_result = configure_single_lure(lure_param)
    return repair_result


def final_check_and_exit():
    '''最终检测装配状态并ESC退出（保留原重试逻辑）'''
    print(f'''\n🔍 最终检测装配状态（最多重试{EXIT_RETRY_TIMES}次）...''')
    for retry in range(EXIT_RETRY_TIMES):
        print(f'''\n📌 第{retry + 1}次检测：''')
        leader_ok = not template_exists(os.path.join(TEMPLATE_ROOT, 'leader_option.png'))
        lure_ok = not template_exists(os.path.join(TEMPLATE_ROOT, 'lure_option.png'))
        if leader_ok and lure_ok:
            print('✅ 所有部件配置完成，执行ESC退出配置界面')
            iu.release_all_keys()
            iu.key_press('esc', iu.randomize_value(ESC_PRESS_BASE_DURATION), **('press_duration',))
            random_wait()
            return True
        wait_int = None.randomize_value(EXIT_RETRY_INTERVAL)
        print(f'''⚠️  第{retry + 1}次检测未通过，{wait_int:.2f}秒后重试...''')
        time.sleep(wait_int)
    print(f'''❌ 经过{EXIT_RETRY_TIMES}次重试，仍有部件未配置完成，不退出界面''')
    return False


def main_repair_flow(leader_param, lure_param = (DEFAULT_LEADER_PARAM, DEFAULT_LURE_PARAM)):
    '''主修复流程（对外暴露核心函数）'''
    iu.release_all_keys()
    iu.mouse_up('left')
    iu.mouse_up('right')
    if not iu.activate_rf4_window():
        return False
    None.release_all_keys()
    detect_device_unassembled()
    print('\n🔧 按V键进入鱼竿配置主界面')
    iu.key_press('v', 0.2, **('press_duration',))
    random_wait()
    unconfigured_parts = check_unconfigured_parts()
    if unconfigured_parts:
        repair_success = repair_unconfigured_parts(unconfigured_parts, leader_param, lure_param)
        if not repair_success:
            print('❌ 部件配置修复失败')
            return False
        return None()

if __name__ == '__main__':
    print('========================================')
    print('🔧 RF4自动修复「设备未组装」【底层防检测版】')
    print('========================================')
    print('⚠️  请确保RF4游戏处于前台可见状态！')
    input('按Enter开始修复（按下后有3秒时间切换到游戏界面）...')
    print('\n⏳ 倒计时3秒后开始修复...')
    for i in range(3, 0, -1):
        print(f'''   {i}秒...''')
        time.sleep(1)
    if main_repair_flow():
        print('\n🎉 自动修复完成！回到正常钓鱼流程')
    else:
        print('\n❌ 自动修复失败，请手动处理')