import time
import random
import input_utils as iu
from rf4_state import state
from datetime import datetime

BIG_REST_BASE_HOURS = 7
BIG_REST_RANDOM_HOURS = 0.5


def is_weekend():
    """判断是否周末：周六(5)、周日(6)"""
    return datetime.now().weekday() in (5, 6)


def is_peak_hour():
    """
    判断是否游戏高峰时段（可自行修改时段）
    示例：每日 18:00 ~ 23:00 为高峰
    """
    now = datetime.now()
    hour = now.hour
    # 工作日/周末统一 18点~23点为高峰，按需自行改区间
    return 18 <= hour <= 23


def take_small_rest(rest_min, rest_max, reason="随机休息"):
    """小休息（分钟级）"""
    rest_min_sec = rest_min * 60
    rest_max_sec = rest_max * 60
    rest_sec = iu.randomize_value(random.uniform(rest_min_sec, rest_max_sec))
    rest_end = time.time() + rest_sec

    print(f"\n🛌 {reason}，开始小休息：{int(rest_sec // 60)}分{int(rest_sec % 60)}秒")

    # 倒计时循环
    while time.time() < rest_end and state.is_running:
        remaining = int(rest_end - time.time())
        # 每30秒打印一次剩余时间
        if remaining % 30 == 0:
            print(f"\r⏳ 剩余休息时间：{int(remaining // 60)}分{remaining % 60}秒", end="")
        time.sleep(1)

    if not state.is_running:
        print("\n🛑 脚本停止，中断小休息")
    else:
        print("\n✅ 小休息结束，恢复操作！")


def take_big_rest(reason="单日时长超限"):
    """大休息（小时级，模拟离线挂机）"""
    big_rest_h = random.uniform(
        BIG_REST_BASE_HOURS - BIG_REST_RANDOM_HOURS,
        BIG_REST_BASE_HOURS + BIG_REST_RANDOM_HOURS
    )
    big_rest_sec = big_rest_h * 3600
    big_rest_end = time.time() + big_rest_sec
    end_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(big_rest_end))

    print(f"\n🛌 {reason}，开始大休息（模拟真人离线）：{big_rest_h:.1f}小时，结束时间：{end_time_str}")

    # 长休息循环，每分钟检测一次
    while time.time() < big_rest_end and state.is_running:
        time.sleep(60)

    if not state.is_running:
        print("\n🛑 脚本停止，中断大休息")
    else:
        print("\n✅ 大休息结束，准备重新登录游戏！")


def check_need_rest(max_continuous_h=None, max_daily_h=None, rest_min=None, rest_max=None):
    """
    检测是否需要休息
    返回值：
        big_rest      : 单日时长超限，大休息
        small_rest    : 连续运行时长超限，小休息
        random_small_rest : 随机小休息
        None          : 无需休息
    """
    # 缺参则从全局state读取
    if max_continuous_h is None:
        max_continuous_h = state.continuous_max_hours
    if max_daily_h is None:
        max_daily_h = state.daily_max_hours
    if rest_min is None:
        rest_min = state.rest_min_minutes
    if rest_max is None:
        rest_max = state.rest_max_minutes

    max_continuous_sec = max_continuous_h * 3600
    max_daily_sec = max_daily_h * 3600

    current_time = time.time()
    # 累加本次连续运行时长
    delta = current_time - state.last_continuous_check_time
    state.continuous_running_seconds += delta
    state.last_continuous_check_time = current_time

    # 1. 单日总时长超限 → 大休息
    if state.daily_running_seconds >= max_daily_sec:
        state.daily_running_seconds = 0
        return "big_rest"

    # 2. 连续运行时长超限 → 小休息
    if state.continuous_running_seconds >= max_continuous_sec:
        # 高峰/周末 休息时长翻倍
        if is_peak_hour() or is_weekend():
            rest_min *= 2
            rest_max *= 2
        state.continuous_running_seconds = 0
        return "small_rest"

    # 3. 随机触发小休息（概率10%）
    if random.random() < 0.1:
        return "random_small_rest"

    # 4. 无需休息
    return