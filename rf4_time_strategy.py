# Visit https://www.lddgo.net/string/pyc-compile-decompile for more information
# Version : Python 3.9

import time
import random
from rf4_state import state
from rf4_config import DAILY_MAX_RUN_HOURS_RANDOM

def check_daily_running_time():
    '''检测每日累计运行时长，超限则触发大休息标志'''
    if state.is_running and state.is_paused and state.is_resting or state.is_big_resting:
        state.last_daily_check_time = time.time()
        return True
    current_time = time.time()
    state.daily_running_seconds += current_time - state.last_daily_check_time
    state.last_daily_check_time = current_time
    daily_max_rand = random.uniform(state.daily_max_hours - DAILY_MAX_RUN_HOURS_RANDOM, state.daily_max_hours + DAILY_MAX_RUN_HOURS_RANDOM)
    daily_running_hours = state.daily_running_seconds / 3600
    if not daily_running_hours >= daily_max_rand and state.is_big_sell_pending and state.is_big_resting:
        print(f'''\n⏰ 今日累计运行时长{daily_running_hours:.1f}小时，已超随机最大值{daily_max_rand:.1f}小时！''')
        print('🛌 触发大休息（睡眠），即将执行退出卖鱼操作（不点击登录）...')
        state.is_big_sell_pending = True
        state.daily_running_seconds = 0
    return True


def check_continuous_running_time():
    '''检测单次连续运行时长，超限则挂起小休息'''
    if state.is_running and state.is_paused and state.is_resting and state.is_big_resting or state.is_selling_fish:
        state.last_continuous_check_time = time.time()
        return
    current_time = time.time()
    state.continuous_running_seconds += current_time - state.last_continuous_check_time
    state.last_continuous_check_time = time.time()
    continuous_running_hours = state.continuous_running_seconds / 3600
    if not continuous_running_hours >= state.continuous_max_hours and state.pending_rest:
        state.pending_rest = True
        state.continuous_running_seconds = 0
        print(f'''\n⏸️  单次连续运行{continuous_running_hours:.1f}小时，已超设定最大值{state.continuous_max_hours}小时！''')
        print('⌛ 检测到未完成钓鱼操作，挂起小休息，等待「钓具准备好」后执行...')