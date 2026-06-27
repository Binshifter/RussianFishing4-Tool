# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'rf4_human_simulation.py'
# Bytecode version: 3.9.0beta5 (3425)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import time
import random
import input_utils as iu
from rf4_state import state
from rf4_config import VIEW_ROTATE_INTERVAL_MIN, VIEW_ROTATE_INTERVAL_MAX, VIEW_MOVE_RANGE_X, VIEW_RECORD_TIMES
def simulate_rotate_view():
    """模拟人类随机转动视角并定期精准回正（防检测）"""
    if not state.is_running or state.is_paused or state.is_resting or state.is_selling_fish or state.is_big_resting:
        state.last_rotate_view_time = time.time()
        return None
    else:
        current_time = time.time()
        interval = random.randint(VIEW_ROTATE_INTERVAL_MIN, VIEW_ROTATE_INTERVAL_MAX)
        if current_time - state.last_rotate_view_time < interval:
            return None
        else:
            try:
                if not state.is_view_aligning:
                    dx = random.randint(-VIEW_MOVE_RANGE_X, VIEW_MOVE_RANGE_X)
                    dy = 0
                    if dx == 0:
                        dx = random.choice([(-1), 1])
                    state.view_offset_records.append((dx, dy))
                    print(f'\n👀 模拟转动视角【随机偏移】：水平{dx}px | 垂直{dy}px（已记录{len(state.view_offset_records)}/{VIEW_RECORD_TIMES}次）')
                    iu.mouse_move_relative(dx, dy, step_size=1, step_delay=0.01)
                    if len(state.view_offset_records) >= VIEW_RECORD_TIMES:
                        state.is_view_aligning = True
                        print(f'\n📏 视角偏移已记录{VIEW_RECORD_TIMES}次，下次开始精准回正！')
                else:
                    dx, dy = state.view_offset_records.pop(0)
                    align_dx = -dx
                    align_dy = -dy
                    print(f'\n🎯 视角精准回正：水平{align_dx}px | 垂直{align_dy}px（剩余{len(state.view_offset_records)}次）')
                    iu.mouse_move_relative(align_dx, align_dy, step_size=1, step_delay=0.01)
                    if len(state.view_offset_records) == 0:
                        state.is_view_aligning = False
                        print('\n✅ 视角所有偏移已回正，恢复随机偏移模式！')
                state.last_rotate_view_time = current_time
            except Exception as e:
                print(f'\n⚠️  视角转动异常：{e}')
                state.last_rotate_view_time = current_time
def run_simulation_actions():
    """视角模拟线程入口"""
    while state.is_running:
        if not state.is_paused and (not state.is_resting) and (not state.is_selling_fish) and (not state.is_big_resting):
                        simulate_rotate_view()
        time.sleep(0.5)