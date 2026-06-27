# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'rf4_fishing_gui.py'
# Bytecode version: 3.9.0beta5 (3425)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

global ctrl_pressed
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import time
import io
import os
import random
import json
import cv2
import numpy as np
from pynput import keyboard
import mss
import traceback
from datetime import datetime
try:
    import input_utils as iu
except ImportError:
    print('⚠️ 未找到 input_utils.py 文件，请确保该文件在同一目录下')
try:
    import rf4_sell_fish as sell_fish
except ImportError:
    print('⚠️ 未找到 rf4_sell_fish.py 文件，请确保该文件在同一目录下')
try:
    import ai_judgment
except ImportError:
    print('⚠️ 未找到 ai_judgment.py 文件，请确保该文件在同一目录下')
try:
    import rf4_assembly
except ImportError:
    print('⚠️ 未找到 rf4_assembly.py 文件，请确保该文件在同一目录下')
from rf4_state import state
from rf4_config import CAST_HOLD_TIME, DETECT_INTERVAL, FISH_ICON_TEMPLATE, FISH_CATCHED_TEMPLATE, FISH_MATCH_THRESHOLD, READY_MATCH_THRESHOLD, CATCHED_MATCH_THRESHOLD, READY_TEXT_1_DETECT_INTERVAL, READY_TEXT_2_DETECT_INTERVAL, DEFAULT_MAX_FISH_COUNT, MIN_CUSTOM_MAX_FISH, MAX_CUSTOM_MAX_FISH, MIN_EAT_INTERVAL, MAX_EAT_INTERVAL, EAT_KEY, RELEASE_KEY, SPACE_KEY, SHIFT_KEY, ASSEMBLY_CHECK_INTERVAL, DEVICE_UNASSEMBLED_TEMPLATE, SELL_POINT_CONFIG_FILE, BIG_REST_BASE_HOURS, BIG_REST_RANDOM_HOURS, BIG_REST_WAIT_LOGIN
from rf4_logger import LogRedirector
from rf4_time_strategy import check_daily_running_time, check_continuous_running_time
from rf4_human_simulation import simulate_rotate_view, run_simulation_actions
ctrl_pressed = False
def _get_leader_param_list():
    """扫描引线模板文件夹，返回参数列表（如 [\'6.2\', \'8.7\', \'17.3\']）"""
    folder = rf4_assembly.LEADER_TEMPLATE_FOLDER
    params = []
    try:
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith('.png'):
                name = f.rsplit('.', 1)[0]
                if name.startswith('leader_') and name.endswith('kg'):
                        param = name[len('leader_'):-len('kg')]
                        params.append(param)
    except FileNotFoundError:
        pass
    return params
def _get_lure_param_list():
    """扫描拟饵模板文件夹，返回参数列表（如 [\'2 018\', \'4-F006\', ...]）"""
    folder = rf4_assembly.LURE_TEMPLATE_FOLDER
    params = []
    try:
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith('.png'):
                name = f.rsplit('.', 1)[0]
                params.append(name)
    except FileNotFoundError:
        pass
    return params
MAP_NAME_MAP = {1: '马克羚诺也湖', 2: '埃尔克湖', 3: '惟有诺克河', 4: '旧奥斯特罗格湖', 5: '白河', 6: '廓里湖', 7: '梅德韦杰湖', 8: '沃尔霍夫河', 9: '北顿涅茨河', 10: '苏拉河', 11: '拉多加湖', 12: '琥珀湖', 13: '拉多加湖群岛', 14: '阿赫图巴河', 15: '铜湖', 16: '下通古斯卡河', 17: '亚马河', 18: '挪威海'}
def get_fish_judgment_result():
    if state.used_standard_multiplier == 0:
        print('⚡ 倍率设置为0，跳过AI判断，强制保留所有鱼（节省Token）')
        return {'judgment': '留下', 'reason': '倍率为0强制保留', 'grade': '倍率为0强制保留', 'fish_name': '未知（倍率0跳过AI）', 'converted_weight': 0.0}
    else:
        try:
            print('\n📡 开始调用AI判断（截图+API识别+本地倍数过滤）...')
            ai_result = ai_judgment.get_fish_judgment_result()
            print('✅ AI判断完成，结果已返回')
            return ai_result
        except Exception as e:
            print(f'❌ 调用AI判断失败：{e}，兜底保留鱼')
            return {'judgment': '留下', 'reason': f'AI调用异常：{str(e)}，兜底保留', 'grade': '识别失败默认入户', 'fish_name': '未知鱼（AI异常）', 'converted_weight': 0.0}
def set_standard_weight_multiplier(multiplier):
    if isinstance(multiplier, (int, float)) and multiplier >= 0:
        state.used_standard_multiplier = multiplier
        if 'ai_judgment' in sys.modules:
            ai_judgment.set_standard_weight_multiplier(multiplier)
    else:
        state.used_standard_multiplier = 0.0
        if 'ai_judgment' in sys.modules:
            ai_judgment.set_standard_weight_multiplier(0.0)
        print('⚠️  倍数输入不合法，默认使用0.0倍标准值')
def check_rest_status():
    if not state.is_resting or state.is_big_resting:
        state.last_small_rest_print_time = 0
        return None
    else:
        current_time = time.time()
        remaining_seconds = int(state.rest_end_time - current_time)
        if remaining_seconds <= 0:
            state.is_resting = False
            state.pending_rest = False
            state.last_small_rest_print_time = 0
            print('\n✅ 小休息时间结束，恢复自动钓鱼！')
            app.root.after(0, lambda: app.update_status_label('运行中'))
            app.root.after(0, lambda: app.status_label.config(foreground='green'))
            if state.is_sell_pending and state.pending_sell_info:
                    print('\n📦 处理休息期间挂起的卖鱼操作...')
                    app._execute_pending_sell()
                    state.is_sell_pending = False
                    state.pending_sell_info = {}
        else:
            if current_time - state.last_small_rest_print_time >= 60 or state.last_small_rest_print_time == 0:
                remaining_m = remaining_seconds // 60
                remaining_s = remaining_seconds % 60
                print(f'\n⏳ 小休息剩余：{remaining_m}分钟{remaining_s}秒')
                app.root.after(0, lambda: app.update_status_label(f'小休息中（剩余{remaining_m}分{remaining_s}秒）'))
                state.last_small_rest_print_time = current_time
def check_big_rest_status():
    if state.is_waiting_login:
        if not state.is_running:
            state.is_waiting_login = False
            return None
        else:
            if app._detect_target(state.login_button_template, 0.8):
                if state.is_running:
                    iu.activate_rf4_window()
                    app._find_and_click_template(state.login_button_template)
                    print('✅ 点击登录按钮，等待游戏加载...')
                    time.sleep(15)
                    print('✅ 上线成功，继续执行卖鱼流程，回到钓点！')
                    state.is_waiting_login = False
            else:
                current_time = time.time()
                if current_time - state.last_login_check_print_time >= 30 or state.last_login_check_print_time == 0:
                    print('⌛ 未检测到登录按钮，继续等待...')
                    state.last_login_check_print_time = current_time
            return None
    else:
        if not state.is_big_resting:
            state.last_big_rest_print_time = 0
            return None
        else:
            current_time = time.time()
            remaining_seconds = int(state.big_rest_end_time - current_time)
            if remaining_seconds <= 0:
                state.is_big_resting = False
                state.last_big_rest_print_time = 0
                print('\n✅ 大休息（睡眠）时间结束，准备上线恢复钓鱼！')
                print(f'👀 开始检测「登录按钮（{os.path.basename(state.login_button_template)}）」...')
                app.root.after(0, lambda: app.update_status_label('大休息结束，待登录'))
                app.root.after(0, lambda: app.status_label.config(foreground='green'))
                state.is_waiting_login = True
                state.last_login_check_print_time = 0
            else:
                if current_time - state.last_big_rest_print_time >= 600 or state.last_big_rest_print_time == 0:
                    remaining_h = remaining_seconds // 3600
                    remaining_m = remaining_seconds % 3600 // 60
                    remaining_s = remaining_seconds % 60
                    print(f'\n⏳ 大休息剩余：{remaining_h}小时{remaining_m}分钟{remaining_s}秒')
                    app.root.after(0, lambda: app.update_status_label(f'大休息中（剩余{remaining_h}h{remaining_m}m）'))
                    state.last_big_rest_print_time = current_time
class RF4FishingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('RF4钓鱼工具-免费学习交流 请勿付费购买')
        self.root.geometry('1000x1000')
        self.root.resizable(False, False)
        self.fishing_thread = None
        self.eat_thread = None
        self.keyboard_thread = None
        self.simulation_thread = None
        self.fast_reel_first_run = True
        self.fast_reel_start_time = 0
        self._is_holding_normal_reel = False
        self._last_catch_time = 0.0
        self._last_jig_print_time = 0.0
        self._consecutive_fast_reel_timeouts = 0
        self._sea_state = 'idle'
        self._sea_sink_start = 0.0
        self._sea_last_twitch = 0.0
        self._create_widgets()
        self.stdout_redirector = LogRedirector(self.log_text)
        sys.stdout = self.stdout_redirector
        self.update_status_label('未运行')
    def _create_widgets(self):
        config_frame = ttk.LabelFrame(self.root, text='基础配置', padding=8)
        config_frame.place(x=10, y=10, width=480, height=575)
        pad_y = 3
        ttk.Label(config_frame, text='初始渔户数量：').grid(row=0, column=0, sticky=tk.W, pady=pad_y)
        self.fish_count_var = tk.StringVar(value='0')
        ttk.Entry(config_frame, textvariable=self.fish_count_var, width=10).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='满户数量：').grid(row=1, column=0, sticky=tk.W, pady=pad_y)
        self.max_fish_count_var = tk.StringVar(value=str(DEFAULT_MAX_FISH_COUNT))
        self.max_fish_count_entry = ttk.Entry(config_frame, textvariable=self.max_fish_count_var, width=10)
        self.max_fish_count_entry.grid(row=1, column=1, sticky=tk.W)
        ttk.Label(config_frame, text=f'（{MIN_CUSTOM_MAX_FISH}-{MAX_CUSTOM_MAX_FISH}）').grid(row=1, column=2, sticky=tk.W)
        self.auto_eat_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text='开启自动进食', variable=self.auto_eat_var).grid(row=2, columnspan=3, sticky=tk.W, pady=pad_y)
        ttk.Label(config_frame, text='达标重量倍数：').grid(row=3, column=0, sticky=tk.W, pady=pad_y)
        self.multiplier_var = tk.StringVar(value='0.0')
        ttk.Entry(config_frame, textvariable=self.multiplier_var, width=10).grid(row=3, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='（1=标准，0=强制保留）').grid(row=3, column=2, sticky=tk.W)
        ttk.Label(config_frame, text='收线模式：').grid(row=4, column=0, sticky=tk.W, pady=pad_y)
        self.reel_mode_var = tk.StringVar(value='normal')
        ttk.Radiobutton(config_frame, text='平收', variable=self.reel_mode_var, value='normal', command=self._on_reel_mode_toggle).grid(row=4, column=1, sticky=tk.W)
        ttk.Radiobutton(config_frame, text='JIG状态', variable=self.reel_mode_var, value='jig', command=self._on_reel_mode_toggle).grid(row=4, column=2, sticky=tk.W)
        ttk.Radiobutton(config_frame, text='海钓', variable=self.reel_mode_var, value='sea', command=self._on_reel_mode_toggle).grid(row=4, column=3, sticky=tk.W)
        ttk.Label(config_frame, text='等待鱼饵落水时间(秒)：').grid(row=5, column=0, sticky=tk.W, pady=pad_y)
        self.bait_fly_var = tk.StringVar(value=str(state.bait_fly_time))
        self.bait_fly_entry = ttk.Entry(config_frame, textvariable=self.bait_fly_var, width=10)
        self.bait_fly_entry.grid(row=5, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='  └ JIG卷线时长(秒)：').grid(row=6, column=0, sticky=tk.W, pady=pad_y)
        self.reel_duration_var = tk.StringVar(value=str(state.reel_duration))
        self.reel_duration_entry = ttk.Entry(config_frame, textvariable=self.reel_duration_var, width=10, state=tk.DISABLED)
        self.reel_duration_entry.grid(row=6, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='  └ JIG停歇时长(秒)：').grid(row=7, column=0, sticky=tk.W, pady=pad_y)
        self.pause_duration_var = tk.StringVar(value=str(state.pause_duration))
        self.pause_duration_entry = ttk.Entry(config_frame, textvariable=self.pause_duration_var, width=10, state=tk.DISABLED)
        self.pause_duration_entry.grid(row=7, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='  └ 海钓抛竿(秒)：').grid(row=8, column=0, sticky=tk.W, pady=pad_y)
        self.sea_cast_duration_var = tk.StringVar(value=str(state.sea_cast_duration))
        self.sea_cast_entry = ttk.Entry(config_frame, textvariable=self.sea_cast_duration_var, width=8, state=tk.DISABLED)
        self.sea_cast_entry.grid(row=8, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='海钓沉底(秒)：').grid(row=8, column=2, sticky=tk.W, pady=pad_y)
        self.sea_sink_time_var = tk.StringVar(value=str(state.sea_sink_time))
        self.sea_sink_entry = ttk.Entry(config_frame, textvariable=self.sea_sink_time_var, width=8, state=tk.DISABLED)
        self.sea_sink_entry.grid(row=8, column=3, sticky=tk.W)
        ttk.Label(config_frame, text='  └ 挑动间隔(秒)：').grid(row=9, column=0, sticky=tk.W, pady=pad_y)
        self.sea_twitch_interval_var = tk.StringVar(value=str(state.sea_twitch_interval))
        self.sea_twitch_interval_entry = ttk.Entry(config_frame, textvariable=self.sea_twitch_interval_var, width=8, state=tk.DISABLED)
        self.sea_twitch_interval_entry.grid(row=9, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='挑动时长(秒)：').grid(row=9, column=2, sticky=tk.W, pady=pad_y)
        self.sea_twitch_duration_var = tk.StringVar(value=str(state.sea_twitch_duration))
        self.sea_twitch_duration_entry = ttk.Entry(config_frame, textvariable=self.sea_twitch_duration_var, width=8, state=tk.DISABLED)
        self.sea_twitch_duration_entry.grid(row=9, column=3, sticky=tk.W)
        self.auto_assemble_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text='开启自动装配引线/拟饵', variable=self.auto_assemble_var, command=self._on_auto_assemble_toggle).grid(row=10, columnspan=3, sticky=tk.W, pady=(10, pad_y))
        ttk.Label(config_frame, text='引线公斤数：').grid(row=11, column=0, sticky=tk.W, pady=pad_y)
        leader_values = _get_leader_param_list()
        self.leader_param_var = tk.StringVar(value=leader_values[0] if leader_values else '')
        self.leader_param_entry = ttk.Combobox(config_frame, textvariable=self.leader_param_var, values=leader_values, width=8, state=tk.DISABLED)
        self.leader_param_entry.grid(row=11, column=1, sticky=tk.W)
        ttk.Label(config_frame, text='kg').grid(row=11, column=2, sticky=tk.W)
        ttk.Label(config_frame, text='拟饵型号：').grid(row=12, column=0, sticky=tk.W, pady=pad_y)
        lure_values = _get_lure_param_list()
        self.lure_param_var = tk.StringVar(value=lure_values[0] if lure_values else '')
        self.lure_param_entry = ttk.Combobox(config_frame, textvariable=self.lure_param_var, values=lure_values, width=10, state=tk.DISABLED)
        self.lure_param_entry.grid(row=12, column=1, sticky=tk.W)
        self.auto_sell_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(config_frame, text='开启重登回城卖鱼', variable=self.auto_sell_var, command=self._on_auto_sell_toggle).grid(row=14, column=0, sticky=tk.W, pady=(10, pad_y))
        server_frame = ttk.Frame(config_frame)
        server_frame.grid(row=14, column=1, columnspan=2, sticky=tk.W, pady=(10, pad_y), padx=(10, 0))
        ttk.Label(server_frame, text='服务器:').pack(side=tk.LEFT)
        self.server_type_var = tk.StringVar(value='standalone')
        self.server_radio_standalone = ttk.Radiobutton(server_frame, text='独立端', variable=self.server_type_var, value='standalone', command=self._on_server_type_toggle)
        self.server_radio_standalone.pack(side=tk.LEFT, padx=(5, 0))
        self.server_radio_steam = ttk.Radiobutton(server_frame, text='Steam', variable=self.server_type_var, value='steam', command=self._on_server_type_toggle)
        self.server_radio_steam.pack(side=tk.LEFT, padx=(2, 0))
        self.server_radio_standalone.config(state=tk.DISABLED)
        self.server_radio_steam.config(state=tk.DISABLED)
        self.select_point_btn = ttk.Button(config_frame, text='选择卖鱼地图/点位', command=self._select_map_and_point, state=tk.DISABLED, width=20)
        self.select_point_btn.grid(row=15, columnspan=3, sticky=tk.W, pady=pad_y)
        ttk.Label(config_frame, text='已选点位：').grid(row=16, column=0, sticky=tk.W, pady=pad_y)
        self.selected_point_var = tk.StringVar(value='未选择')
        ttk.Label(config_frame, textvariable=self.selected_point_var, wraplength=350).grid(row=16, column=1, columnspan=2, sticky=tk.W)
        ttk.Label(config_frame, text='重登等待时间(秒)：').grid(row=17, column=0, sticky=tk.W, pady=(10, pad_y))
        self.login_load_wait_var = tk.StringVar(value=str(state.login_load_wait))
        self.login_load_wait_entry = ttk.Entry(config_frame, textvariable=self.login_load_wait_var, width=8)
        self.login_load_wait_entry.grid(row=17, column=1, sticky=tk.W, pady=(10, pad_y))
        ttk.Label(config_frame, text='（登录后等游戏加载）').grid(row=17, column=2, sticky=tk.W, pady=(10, pad_y))
        self.auto_relog_on_timeout_var = tk.BooleanVar(value=False)
        self.timeout_relog_check = ttk.Checkbutton(config_frame, text='大鱼超时自动重登卖鱼', variable=self.auto_relog_on_timeout_var, command=self._on_timeout_relog_toggle, state=tk.DISABLED)
        self.timeout_relog_check.grid(row=18, column=0, sticky=tk.W, pady=(10, pad_y))
        ttk.Label(config_frame, text='连续超时次数：').grid(row=18, column=1, sticky=tk.W, pady=(10, pad_y))
        self.max_timeout_count_var = tk.StringVar(value='3')
        self.max_timeout_count_entry = ttk.Entry(config_frame, textvariable=self.max_timeout_count_var, width=8, state=tk.DISABLED)
        self.max_timeout_count_entry.grid(row=18, column=2, sticky=tk.W, pady=(10, pad_y))
        ttk.Label(config_frame, text='次').grid(row=18, column=2, sticky=tk.W, padx=(50, 0), pady=(10, pad_y))
        time_frame = ttk.LabelFrame(self.root, text='时间策略配置（核心）', padding=8)
        time_frame.place(x=10, y=595, width=480, height=180)
        ttk.Label(time_frame, text='每日总运行时长(小时)：').grid(row=0, column=0, sticky=tk.W, pady=pad_y)
        self.daily_max_hours_var = tk.StringVar(value=str(state.daily_max_hours))
        ttk.Entry(time_frame, textvariable=self.daily_max_hours_var, width=10).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(time_frame, text='（建议≤14，自动±0.5h随机）').grid(row=0, column=2, sticky=tk.W)
        ttk.Label(time_frame, text='单次连续运行时长(小时)：').grid(row=1, column=0, sticky=tk.W, pady=pad_y)
        self.continuous_max_hours_var = tk.StringVar(value=str(state.continuous_max_hours))
        ttk.Entry(time_frame, textvariable=self.continuous_max_hours_var, width=10).grid(row=1, column=1, sticky=tk.W)
        ttk.Label(time_frame, text='（2-3，超了挂起小休息）').grid(row=1, column=2, sticky=tk.W)
        ttk.Label(time_frame, text='小休息时间范围(分钟)：').grid(row=2, column=0, sticky=tk.W, pady=pad_y)
        self.min_rest_var = tk.StringVar(value=str(state.rest_min_minutes))
        self.max_rest_var = tk.StringVar(value=str(state.rest_max_minutes))
        ttk.Entry(time_frame, textvariable=self.min_rest_var, width=8).grid(row=2, column=1, sticky=tk.W)
        ttk.Label(time_frame, text='~').grid(row=2, column=1, sticky=tk.E, padx=(40, 0))
        ttk.Entry(time_frame, textvariable=self.max_rest_var, width=8).grid(row=2, column=2, sticky=tk.W)
        ttk.Label(time_frame, text='（取值范围内随机）').grid(row=3, column=0, columnspan=4, sticky=tk.W)
        control_frame = ttk.LabelFrame(self.root, text='运行控制', padding=8)
        control_frame.place(x=500, y=10, width=480, height=490)
        self.start_btn = ttk.Button(control_frame, text='开始钓鱼', command=self.start_fishing, width=15)
        self.start_btn.grid(row=0, column=0, padx=5, pady=10)
        self.pause_btn = ttk.Button(control_frame, text='暂停', command=self.toggle_pause, width=15, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=1, padx=5, pady=10)
        self.stop_btn = ttk.Button(control_frame, text='停止钓鱼', command=self.stop_fishing, width=15, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5, pady=10)
        ttk.Label(control_frame, text='运行状态：').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value='未运行')
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground='red')
        self.status_label.grid(row=1, column=1, sticky=tk.W)
        stat_frame = ttk.LabelFrame(control_frame, text='鱼获统计', padding=5)
        stat_frame.grid(row=2, columnspan=3, sticky=tk.W + tk.E, pady=10)
        ttk.Label(stat_frame, text='总上鱼：').grid(row=0, column=0, sticky=tk.W)
        self.total_fish_var = tk.StringVar(value='0')
        ttk.Label(stat_frame, textvariable=self.total_fish_var).grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Label(stat_frame, text='上星鱼：').grid(row=0, column=2, sticky=tk.W, padx=10)
        self.star_fish_var = tk.StringVar(value='0')
        ttk.Label(stat_frame, textvariable=self.star_fish_var).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(stat_frame, text='上蓝鱼：').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.blue_fish_var = tk.StringVar(value='0')
        ttk.Label(stat_frame, textvariable=self.blue_fish_var).grid(row=1, column=1, sticky=tk.W, padx=10)
        ttk.Label(stat_frame, text='放生数：').grid(row=1, column=2, sticky=tk.W, padx=10, pady=5)
        self.released_fish_var = tk.StringVar(value='0')
        ttk.Label(stat_frame, textvariable=self.released_fish_var).grid(row=1, column=3, sticky=tk.W)
        ttk.Label(stat_frame, text='达标数：').grid(row=2, column=0, sticky=tk.W)
        self.qualified_fish_var = tk.StringVar(value='0')
        ttk.Label(stat_frame, textvariable=self.qualified_fish_var).grid(row=2, column=1, sticky=tk.W, padx=10)
        ttk.Label(stat_frame, text='运行时长：').grid(row=2, column=2, sticky=tk.W, padx=10)
        self.run_time_var = tk.StringVar(value='00:00:00')
        ttk.Label(stat_frame, textvariable=self.run_time_var).grid(row=2, column=3, sticky=tk.W)
        time_stat_frame = ttk.LabelFrame(control_frame, text='时间统计', padding=5)
        time_stat_frame.grid(row=3, columnspan=3, sticky=tk.W + tk.E, pady=10)
        ttk.Label(time_stat_frame, text='今日累计运行：').grid(row=0, column=0, sticky=tk.W)
        self.daily_run_time_var = tk.StringVar(value='00:00:00')
        ttk.Label(time_stat_frame, textvariable=self.daily_run_time_var).grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Label(time_stat_frame, text='本次连续运行：').grid(row=0, column=2, sticky=tk.W, padx=10)
        self.continuous_run_time_var = tk.StringVar(value='00:00:00')
        ttk.Label(time_stat_frame, textvariable=self.continuous_run_time_var).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(control_frame, text='本程序免费交流，仅供学习研究使用。付费购买的请立即退款！', foreground='red', font=('Arial', 9, 'bold')).grid(row=4, columnspan=3, sticky=tk.W, pady=(0, 5))
        log_frame = ttk.LabelFrame(self.root, text='运行日志', padding=10)
        log_frame.place(x=10, y=785, width=970, height=190)
        self.log_text = scrolledtext.ScrolledText(log_frame, width=110, height=15, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.root, text='快捷键：Ctrl+P暂停 | Ctrl+R继续 | Ctrl+Q结束', font=('Arial', 8)).place(x=10, y=978)
    def _on_auto_assemble_toggle(self):
        if self.auto_assemble_var.get():
            self.leader_param_entry.config(state='readonly')
            self.lure_param_entry.config(state='readonly')
        else:
            self.leader_param_entry.config(state=tk.DISABLED)
            self.lure_param_entry.config(state=tk.DISABLED)
    def _on_auto_sell_toggle(self):
        if self.auto_sell_var.get():
            self.select_point_btn.config(state=tk.NORMAL)
            self.timeout_relog_check.config(state=tk.NORMAL)
            self.server_radio_standalone.config(state=tk.NORMAL)
            self.server_radio_steam.config(state=tk.NORMAL)
        else:
            self.select_point_btn.config(state=tk.DISABLED)
            self.timeout_relog_check.config(state=tk.DISABLED)
            self.auto_relog_on_timeout_var.set(False)
            self.max_timeout_count_entry.config(state=tk.DISABLED)
            self.server_radio_standalone.config(state=tk.DISABLED)
            self.server_radio_steam.config(state=tk.DISABLED)
            self.selected_point_var.set('未选择')
            state.selected_map_id = 0
            state.selected_point_id = 0
            state.selected_coordinate = ''
    def _on_timeout_relog_toggle(self):
        widget_state = tk.NORMAL if self.auto_relog_on_timeout_var.get() else tk.DISABLED
        self.max_timeout_count_entry.config(state=widget_state)
    def _on_reel_mode_toggle(self):
        is_jig = self.reel_mode_var.get() == 'jig'
        is_sea = self.reel_mode_var.get() == 'sea'
        self.bait_fly_entry.config(state=tk.DISABLED if is_sea else tk.NORMAL)
        self.reel_duration_entry.config(state=tk.NORMAL if is_jig else tk.DISABLED)
        self.pause_duration_entry.config(state=tk.NORMAL if is_jig else tk.DISABLED)
        self.sea_cast_entry.config(state=tk.NORMAL if is_sea else tk.DISABLED)
        self.sea_sink_entry.config(state=tk.NORMAL if is_sea else tk.DISABLED)
        self.sea_twitch_interval_entry.config(state=tk.NORMAL if is_sea else tk.DISABLED)
        self.sea_twitch_duration_entry.config(state=tk.NORMAL if is_sea else tk.DISABLED)
    def _on_server_type_toggle(self):
        if self.server_type_var.get() == 'steam':
            state.login_button_template = 'image/login_button_steam.png'
        else:
            state.login_button_template = 'image/login_button.png'
    def _select_map_and_point(self):
        try:
            with open(SELL_POINT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if not isinstance(config, list):
                messagebox.showerror('错误', f'配置文件{SELL_POINT_CONFIG_FILE}根节点必须是列表！')
                return
        except FileNotFoundError:
            messagebox.showerror('错误', f'未找到卖鱼点位配置文件：{SELL_POINT_CONFIG_FILE}')
            return None
        except json.JSONDecodeError:
            messagebox.showerror('错误', f'配置文件格式错误：{SELL_POINT_CONFIG_FILE}')
            return
        point_window = tk.Toplevel(self.root)
        point_window.title('选择卖鱼地图/点位')
        point_window.geometry('600x400')
        point_window.transient(self.root)
        ttk.Label(point_window, text='选择地图：').grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        map_list = [f"{item['map_id']} - {MAP_NAME_MAP.get(item['map_id'], item['map_name'])}" for item in config]
        if not map_list:
            messagebox.showwarning('提示', '配置文件中未找到任何地图数据！')
            point_window.destroy()
            return None
        else:
            self.map_var = tk.StringVar()
            map_combobox = ttk.Combobox(point_window, textvariable=self.map_var, values=map_list, width=30, state='readonly')
            map_combobox.grid(row=0, column=1, padx=10, pady=10)
            map_combobox.current(0)
            map_combobox.bind('<<ComboboxSelected>>', lambda e: self._load_points(config, point_window))
            self.point_listbox = tk.Listbox(point_window, width=70, height=15)
            self.point_listbox.grid(row=1, columnspan=2, padx=10, pady=10)
            self._load_points(config, point_window)
            ttk.Button(point_window, text='确认选择', command=lambda: self._confirm_point(point_window, config)).grid(row=2, columnspan=2, pady=10)
    def _load_points(self, config, window):
        self.point_listbox.delete(0, tk.END)
        try:
            map_id = int(self.map_var.get().split(' - ')[0])
            map_item = next((item for item in config if item['map_id'] == map_id))
            valid_points = [p for p in map_item['points'] if p.get('is_completed', False)]
            if not valid_points:
                self.point_listbox.insert(0, '该地图暂无已完成的点位')
                return
            else:
                for p in valid_points:
                    self.point_listbox.insert(tk.END, f"点位{p['point_id']} | 坐标{p['coordinate']} | {p['notes']}")
        except Exception as e:
            self.point_listbox.insert(0, f'加载点位失败：{str(e)}')
    def _confirm_point(self, window, config):
        selected_idx = self.point_listbox.curselection()
        if not selected_idx:
            messagebox.showwarning('提示', '请选择一个点位！')
            return None
        else:
            selected_text = self.point_listbox.get(selected_idx)
            point_id = int(selected_text.split('点位')[1].split(' | ')[0])
            map_id = int(self.map_var.get().split(' - ')[0])
            map_item = next((item for item in config if item['map_id'] == map_id))
            point_item = next((p for p in map_item['points'] if p['point_id'] == point_id))
            state.selected_map_id = map_id
            state.selected_point_id = point_id
            state.selected_coordinate = point_item['coordinate']
            map_name = MAP_NAME_MAP.get(map_id, f'地图{map_id}')
            self.selected_point_var.set(f'{map_name} - 点位{point_id}（{state.selected_coordinate}）')
            messagebox.showinfo('选择成功', f'已选择：{map_name} | 点位{point_id} | 坐标{state.selected_coordinate}')
            window.destroy()
    def update_status_label(self, status):
        self.status_var.set(status)
        if status == '运行中':
            self.status_label.config(foreground='green')
        else:
            if status == '暂停中':
                self.status_label.config(foreground='orange')
            else:
                if '小休息' in status:
                    self.status_label.config(foreground='purple')
                else:
                    if '大休息' in status:
                        self.status_label.config(foreground='darkblue')
                    else:
                        self.status_label.config(foreground='red')
    def update_statistics(self):
        self.total_fish_var.set(str(state.total_fish_caught))
        self.star_fish_var.set(str(state.star_fish_count))
        self.blue_fish_var.set(str(state.blue_fish_count))
        self.released_fish_var.set(str(state.released_fish_count))
        self.qualified_fish_var.set(str(state.qualified_fish_count))
        if state.start_time:
            elapsed_seconds = time.time() - state.start_time
            h = int(elapsed_seconds // 3600)
            m = int(elapsed_seconds % 3600 // 60)
            s = int(elapsed_seconds % 60)
            self.run_time_var.set(f'{h:02d}:{m:02d}:{s:02d}')
        d_h = int(state.daily_running_seconds // 3600)
        d_m = int(state.daily_running_seconds % 3600 // 60)
        d_s = int(state.daily_running_seconds % 60)
        self.daily_run_time_var.set(f'{d_h:02d}:{d_m:02d}:{d_s:02d}')
        c_h = int(state.continuous_running_seconds // 3600)
        c_m = int(state.continuous_running_seconds % 3600 // 60)
        c_s = int(state.continuous_running_seconds % 60)
        self.continuous_run_time_var.set(f'{c_h:02d}:{c_m:02d}:{c_s:02d}')
        if state.is_running:
            self.root.after(1000, self.update_statistics)
    def _validate_time_config(self):
        try:
            daily = float(self.daily_max_hours_var.get())
            if daily <= 0 or daily > 24:
                raise ValueError('0-24之间')
            else:
                state.daily_max_hours = daily
                continuous = float(self.continuous_max_hours_var.get())
                if continuous <= 0 or continuous > daily:
                    raise ValueError(f'0-{daily}之间')
                else:
                    state.continuous_max_hours = continuous
                    min_rest = int(self.min_rest_var.get())
                    max_rest = int(self.max_rest_var.get())
                    if min_rest <= 0 or max_rest <= min_rest or max_rest > 60:
                        raise ValueError('最小值>0，最大值≥最小值且≤60')
                    else:
                        state.rest_min_minutes = min_rest
                        state.rest_max_minutes = max_rest
                        print('\n⏰ 加载时间策略配置：')
                        print(f'   每日总运行：{state.daily_max_hours:.1f}h（±0.5h随机）| 单次连续：{state.continuous_max_hours:.1f}h')
                        print(f'   小休息范围：{state.rest_min_minutes}-{state.rest_max_minutes}分钟 | 大休息：{BIG_REST_BASE_HOURS:.1f}h（±0.5h随机）')
                        return True
        except ValueError as e:
            messagebox.showwarning('配置错误', f'时间配置异常：{e}，请输入有效数字')
            return False
    def start_fishing(self):
        # ***<module>.RF4FishingGUI.start_fishing: Failure: Compilation Error
        if not self._validate_time_config():
            return None
        else:
            try:
                custom_max_fish = int(self.max_fish_count_var.get())
                if custom_max_fish < MIN_CUSTOM_MAX_FISH or custom_max_fish > MAX_CUSTOM_MAX_FISH:
                    messagebox.showwarning('提示', f'满户数量需为{MIN_CUSTOM_MAX_FISH}-{MAX_CUSTOM_MAX_FISH}的整数')
                    return
                else:
                    state.max_fish_count = custom_max_fish
                    print(f'✅ 满户数量已设置为：{state.max_fish_count}（范围{MIN_CUSTOM_MAX_FISH}-{MAX_CUSTOM_MAX_FISH}）')
            except ValueError:
                messagebox.showwarning('提示', '满户数量必须是数字')
                return
            try:
                state.current_fish_count = int(self.fish_count_var.get())
                if state.current_fish_count < 0 or state.current_fish_count >= state.max_fish_count:
                    messagebox.showwarning('提示', f'初始渔户需为0-{state.max_fish_count - 1}的整数')
                    return
            except ValueError:
                messagebox.showwarning('提示', '初始渔户必须是数字')
                return
            try:
                multiplier = float(self.multiplier_var.get())
                if multiplier < 0:
                    multiplier = 0.0
            except ValueError:
                multiplier = 0.0
            set_standard_weight_multiplier(multiplier)
            print(f'✅ 达标重量倍数已设置为：{multiplier}倍（标准值×{multiplier}）')
            try:
                state.bait_fly_time = float(self.bait_fly_var.get())
                state.reel_duration = float(self.reel_duration_var.get())
                state.pause_duration = float(self.pause_duration_var.get())
                if any((x <= 0 for x in [state.bait_fly_time, state.reel_duration, state.pause_duration])):
                    raise ValueError('必须大于0')
                else:
                    state.sea_cast_duration = float(self.sea_cast_duration_var.get())
                    state.sea_sink_time = float(self.sea_sink_time_var.get())
                    state.sea_twitch_interval = float(self.sea_twitch_interval_var.get())
                    state.sea_twitch_duration = float(self.sea_twitch_duration_var.get())
                    if any((x <= 0 for x in [state.sea_cast_duration, state.sea_sink_time, state.sea_twitch_interval, state.sea_twitch_duration])):
                        raise ValueError('海钓参数必须大于0')
                    else:
                        if state.reel_mode == 'sea':
                            print(f'\n🌊 海钓模式：抛竿{state.sea_cast_duration:.2f}s | 沉底{state.sea_sink_time:.1f}s | 挑动间隔{state.sea_twitch_interval:.1f}s | 挑动时长{state.sea_twitch_duration:.2f}s')
                        print(f'\n📝 加载钓鱼配置：等待鱼饵落水{state.bait_fly_time:.2f}s | 卷线{state.reel_duration:.3f}s | 停歇{state.pause_duration:.3f}s')
            except ValueError as e:
                messagebox.showwarning('配置错误', f'钓鱼时间配置异常：{e}，请输入大于0的数字')
                return
            state.is_auto_assemble = self.auto_assemble_var.get()
            if state.is_auto_assemble:
                try:
                    state.leader_param = self.leader_param_var.get().strip()
                    float(state.leader_param)
                    state.lure_param = self.lure_param_var.get().strip()
                    if not state.lure_param:
                        raise ValueError('拟饵型号不能为空')
                    else:
                        print(f'\n🔧 自动装配：引线{state.leader_param}kg | 拟饵{state.lure_param}')
                except ValueError as e:
                    messagebox.showwarning('配置错误', f'装配参数异常：{e}')
                    return
            state.is_auto_sell = self.auto_sell_var.get()
            if state.is_auto_sell and (state.selected_map_id == 0 or state.selected_point_id == 0):
                messagebox.showwarning('提示', '开启卖鱼后请先选择地图/点位')
                return None
            else:
                if self.auto_relog_on_timeout_var.get():
                    try:
                        state.max_fast_reel_timeouts = int(self.max_timeout_count_var.get())
                        if state.max_fast_reel_timeouts < 1:
                            raise ValueError
                        else:
                            print(f'✅ 连续超时重登卖鱼已开启：连续{state.max_fast_reel_timeouts}次超时触发')
                    except ValueError:
                        messagebox.showwarning('提示', '连续超时次数需为≥1的整数')
                        # return.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res.__res._res._res.__res.__res.__res.__res.__res.__res.__res.__r
                else:
                    state.max_fast_reel_timeouts = 0
                if self.server_type_var.get() == 'steam':
                    state.login_button_template = 'image/login_button_steam.png'
                else:
                    state.login_button_template = 'image/login_button.png'
                print(f"✅ 服务器类型：{('Steam' if self.server_type_var.get() == 'steam' else '独立端')} | 登录按钮：{os.path.basename(state.login_button_template)}")
                try:
                    state.login_load_wait = float(self.login_load_wait_var.get())
                    if state.login_load_wait <= 0:
                        raise ValueError
                    else:
                        print(f'⏳ 重登等待时间：{state.login_load_wait}s')
                except ValueError:
                    messagebox.showwarning('提示', '重登等待时间需为大于0的数字')
                    return
                state.is_auto_eat = self.auto_eat_var.get()
                state.reel_mode = self.reel_mode_var.get()
                state.last_assembly_check_time = time.time()
                state.total_fish_caught = 0
                state.released_fish_count = 0
                state.qualified_fish_count = 0
                state.star_fish_count = 0
                state.blue_fish_count = 0
                state.daily_running_seconds = 0
                state.last_daily_check_time = time.time()
                state.continuous_running_seconds = 0
                state.last_continuous_check_time = time.time()
                state.is_running = True
                state.is_paused = False
                state.is_resting = False
                state.is_big_resting = False
                state.is_sell_pending = False
                state.pending_sell_info = {}
                state.is_fish_detected = False
                self.keyboard_thread = threading.Thread(target=self._start_keyboard_listener, daemon=True)
                self.keyboard_thread.start()
                self.eat_thread = threading.Thread(target=self._auto_eat_action, daemon=True)
                self.eat_thread.start()
                self.fishing_thread = threading.Thread(target=self._real_time_main_loop, daemon=True)
                self.fishing_thread.start()
                self.simulation_thread = threading.Thread(target=run_simulation_actions, daemon=True)
                self.simulation_thread.start()
                self.start_btn.config(state=tk.DISABLED)
                self.pause_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.NORMAL)
                self.update_status_label('运行中')
                state.start_time = time.time()
                self.update_statistics()
                print('\n✅ RF4钓鱼脚本启动成功！')
                print('🤖 模拟人类操作、日志持久化已开启 | 快捷键：Ctrl+P/R暂停/继续，Ctrl+Q结束')
    def toggle_pause(self):
        if state.is_paused:
            state.is_paused = False
            self.pause_btn.config(text='暂停')
            status = '大休息中' if state.is_big_resting else '小休息中' if state.is_resting else '运行中'
            self.update_status_label(status)
            print('▶️  脚本继续运行')
        else:
            state.is_paused = True
            self.pause_btn.config(text='继续')
            self.update_status_label('暂停中')
            print('⏸️  脚本已暂停')
    def stop_fishing(self):
        state.is_running = False
        state.is_resting = False
        state.is_big_resting = False
        state.is_sell_pending = False
        state.is_big_sell_pending = False
        state.is_fish_detected = False
        state.is_selling_fish = False
        iu.release_all_keys()
        iu.mouse_up('left')
        iu.mouse_up('right')
        self._is_holding_normal_reel = False
        self._consecutive_fast_reel_timeouts = 0
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text='暂停')
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status_label('已停止')
        self._print_fish_statistics()
        print('🛑 脚本已停止，所有线程回收完成！')
    def _format_elapsed_time(self, elapsed_seconds):
        h = int(elapsed_seconds // 3600)
        m = int(elapsed_seconds % 3600 // 60)
        s = int(elapsed_seconds % 60)
        return f'{h:02d}:{m:02d}:{s:02d}'
    def _take_screenshot(self):
        """Take a full-screen screenshot and return as grayscale array."""
        with mss.MSS() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            return cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2GRAY)
    def _detect_target(self, template_path, threshold, screen_gray=None):
        # irreducible cflow, using cdg fallback
        # ***<module>.RF4FishingGUI._detect_target: Failure: Compilation Error
        if screen_gray is None:
            with mss.MSS() as sct:
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                screen_gray = cv2.cvtColor(np.array(sct_img), cv2.COLOR_BGRA2GRAY)
        templates = [template_path] if isinstance(template_path, str) else template_path
        for temp_path in templates:
                template = cv2.imread(temp_path, 0)
                if template is None:
                    print(f'⚠️  模板文件不存在：{temp_path}，跳过该模板检测')
                    continue
                res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                if len(np.where(res >= threshold)[0]) > 0:
                    return True
                return False
            # except Exception as e:
            #     print(f'❌ 模板检测失败：{e}')
            #     return False
    def _find_and_click_template(self, template_path, retry=2, threshold=0.8):
        iu.activate_rf4_window()
        iu.random_sleep(0.1, 0.2)
        for _ in range(retry):
            screen_gray = self._take_screenshot()
            template = cv2.imread(template_path, 0)
            if template is None:
                print(f'❌ 模板不存在：{template_path}')
                return False
            else:
                t_h, t_w = template.shape[:2]
                res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if max_val >= threshold:
                    x = max_loc[0] + t_w // 2
                    y = max_loc[1] + t_h // 2
                    iu.mouse_click(x=x + random.randint((-2), 2), y=y + random.randint((-2), 2))
                    print(f'✅ 精准点击：{os.path.basename(template_path)} | 原坐标({max_loc[0] + t_w // 2},{max_loc[1] + t_h // 2}) | 偏移({x - (max_loc[0] + t_w // 2)},{y - (max_loc[1] + t_h // 2)})')
                    return True
                else:
                    iu.random_sleep(0.2, 0.4)
        print(f'❌ 未识别模板：{os.path.basename(template_path)}')
        return False
    def _fast_cast_rod_action(self):
        if not state.is_running or state.is_selling_fish or state.is_resting or state.is_big_resting:
            return None
        else:
            print('\n🎣 侦测到钓具准备好，执行抛竿...')
            iu.activate_rf4_window()
            iu.release_all_keys()
            iu.random_sleep(0.1, 0.2)
            try:
                if state.reel_mode == 'sea':
                    iu.mouse_down('left')
                    iu.random_sleep(iu.randomize_value(state.sea_cast_duration))
                    iu.mouse_up('left')
                    self._sea_state = 'sinking'
                    self._sea_sink_start = time.time()
                    print(f'🌊 海钓抛竿 {state.sea_cast_duration:.2f}s，等待沉底 {state.sea_sink_time:.1f}s...')
                    iu.release_all_keys()
                    iu.random_sleep(state.bait_fly_time)
                else:
                    iu.key_down(SHIFT_KEY)
                    iu.random_sleep(0.05, 0.1)
                    iu.mouse_down('left')
                    iu.random_sleep(iu.randomize_value(CAST_HOLD_TIME))
                    iu.mouse_up('left')
                    iu.random_sleep(0.02, 0.05)
                    iu.key_up(SHIFT_KEY)
                    bait_fly_time = state.bait_fly_time
                    print(f'✅ 抛竿成功，等待{bait_fly_time:.2f}秒...')
                    iu.release_all_keys()
                    iu.random_sleep(bait_fly_time)
                state.is_fish_detected = False
                self._consecutive_fast_reel_timeouts = 0
            except Exception as e:
                print(f'❌ 抛竿失败：{e}\n{traceback.format_exc()}')
                iu.release_all_keys()
    def _normal_reel_action(self):
        if state.is_selling_fish or state.is_resting or state.is_big_resting:
            return None
        else:
            if self._is_holding_normal_reel:
                return None
            else:
                iu.activate_rf4_window()
                iu.mouse_down('left')
                self._is_holding_normal_reel = True
    def _jig_reel_action(self):
        if state.is_selling_fish or state.is_resting or state.is_big_resting:
            return None
        else:
            iu.activate_rf4_window()
            random_hold = iu.randomize_value(random.uniform(state.reel_duration * 0.9, state.reel_duration * 1.1))
            random_pause = iu.randomize_value(random.uniform(state.pause_duration * 0.9, state.pause_duration * 1.1))
            if time.time() - self._last_jig_print_time > 5:
                print(f'🔄 JIG模式：按住{random_hold:.4f}s → 暂停{random_pause:.4f}s')
                self._last_jig_print_time = time.time()
            iu.key_down(SHIFT_KEY)
            iu.mouse_down('left')
            iu.random_sleep(random_hold)
            iu.mouse_up('left')
            iu.key_up(SHIFT_KEY)
            iu.random_sleep(random_pause)
    def _sea_reel_action(self):
        if state.is_selling_fish or state.is_resting or state.is_big_resting or (not state.is_running):
            return None
        else:
            iu.activate_rf4_window()
            if self._sea_state == 'sinking':
                if time.time() - self._sea_sink_start >= iu.randomize_value(state.sea_sink_time):
                    iu.mouse_down('left')
                    iu.random_sleep(0.05, 0.08)
                    iu.mouse_up('left')
                    self._sea_state = 'locked'
                    self._sea_last_twitch = time.time()
                    print('🌊 假饵沉底，左键锁线，开始挑逗...')
            else:
                if self._sea_state == 'locked':
                    if time.time() - self._sea_last_twitch >= iu.randomize_value(state.sea_twitch_interval):
                        iu.mouse_down('right')
                        iu.random_sleep(iu.randomize_value(state.sea_twitch_duration))
                        iu.mouse_up('right')
                        self._sea_last_twitch = time.time()
    
    def _fast_reel_and_lift_action(self):
        # 状态拦截：卖鱼/休息/停止 直接退出
        if state.is_selling_fish or state.is_resting or state.is_big_resting or (not state.is_running):
            return None
        
        iu.activate_rf4_window()
        
        try:
            if self.fast_reel_first_run:
                iu.release_all_keys()
                iu.key_down(SHIFT_KEY)
                iu.mouse_down('left')
                iu.mouse_down('right')
                self.fast_reel_first_run = False
                self.fast_reel_start_time = time.time()
                self._is_holding_normal_reel = False
            
            # 检测快速收线60秒超时
            if time.time() - self.fast_reel_start_time > 60:
                print('\n⏰ 快速收线超时（>60秒）...')
                self.fast_reel_start_time = time.time()
                
                if state.reel_mode == 'sea':
                    if state.max_fast_reel_timeouts > 0:
                        self._consecutive_fast_reel_timeouts += 1
                        print(f'⏱️ 海钓连续超时：{self._consecutive_fast_reel_timeouts}/{state.max_fast_reel_timeouts}')
                        if self._consecutive_fast_reel_timeouts >= state.max_fast_reel_timeouts:
                            print(f'\n⚠️ 海钓连续{self._consecutive_fast_reel_timeouts}次收线超时，执行重登卖鱼更换位置...')
                            self._consecutive_fast_reel_timeouts = 0
                            iu.release_all_keys()
                            if state.is_auto_sell and state.selected_map_id != 0 and (state.selected_point_id != 0):
                                self._execute_sell_flow(state.selected_map_id, state.selected_point_id, skip_login=False)
                            else:
                                print('⚠️ 自动卖鱼未开启或未选择点位，跳过重登卖鱼')
                else:
                    print('重置状态...')
                    iu.release_all_keys()
                    self.fast_reel_first_run = True
                    state.current_reel_state = 'normal'
                    state.is_fish_detected = False
                    
                    if state.max_fast_reel_timeouts > 0:
                        self._consecutive_fast_reel_timeouts += 1
                        print(f'⏱️ 连续超时：{self._consecutive_fast_reel_timeouts}/{state.max_fast_reel_timeouts}')
                        if self._consecutive_fast_reel_timeouts >= state.max_fast_reel_timeouts:
                            print(f'\n⚠️ 连续{self._consecutive_fast_reel_timeouts}次收线超时，执行重登卖鱼更换位置...')
                            self._consecutive_fast_reel_timeouts = 0
                            if state.is_auto_sell and state.selected_map_id != 0 and (state.selected_point_id != 0):
                                self._execute_sell_flow(state.selected_map_id, state.selected_point_id, skip_login=False)
                            else:
                                print('⚠️ 自动卖鱼未开启或未选择点位，跳过重登卖鱼')
                return None
            
            # 未超时，设置为快速起鱼状态
            state.current_reel_state = 'fast_lift'
        
        except Exception as e:
            print(f'❌ 快速收线异常：{e}')
            iu.release_all_keys()
            self.fast_reel_first_run = True
            state.current_reel_state = 'normal'
            if state.reel_mode == 'sea':
                self._sea_state = 'sinking'
                self._sea_sink_start = time.time()
                
    def _fish_enter_house_action(self, reason, fish_name, weight):
        state.current_fish_count += 1
        weight_display = f'{weight:.3f}' if isinstance(weight, (int, float)) and weight > 0 else '未知'
        print(f"✅ 【入户】{reason} | {fish_name or '未知'} | {weight_display}kg | 渔户{state.current_fish_count}/{state.max_fish_count}")
        if reason in ['达标鱼', '上星鱼（稀有）', '上蓝鱼（超级稀有）', '达标鱼（倍数过滤后）', '倍率为0强制保留']:
            state.qualified_fish_count += 1
            if reason == '上星鱼（稀有）':
                state.star_fish_count += 1
            else:
                if reason == '上蓝鱼（超级稀有）':
                    state.blue_fish_count += 1
        iu.activate_rf4_window()
        iu.key_press('shift')
        iu.key_press(SPACE_KEY)
        delay = iu.randomize_value(random.uniform(1.5, 2.5))
        print(f'⏳ 入户后等待{delay:.2f}秒...')
        iu.random_sleep(delay)
        iu.random_sleep(0.5, 1.0)
        ready_delay = iu.randomize_value(random.uniform(0.5, 1))
        print(f'⏳ 入户完成，额外等待{ready_delay:.2f}秒后再侦测ready模板...')
        iu.random_sleep(ready_delay)
        iu.release_all_keys()
        iu.mouse_up('left')
        iu.mouse_up('right')
        self._is_holding_normal_reel = False
        self._sea_state = 'idle'
        state.current_reel_state = 'normal'
        self.fast_reel_first_run = True
        state.view_offset_records = []
        state.is_view_aligning = False
    def _fish_release_action(self, fish_name, weight):
        state.released_fish_count += 1
        weight_display = f'{weight:.3f}' if isinstance(weight, (int, float)) and weight > 0 else '未知'
        print(f"❌ 【放生】{fish_name or '未知'} | {weight_display}kg | 功德+1")
        iu.activate_rf4_window()
        iu.key_press(RELEASE_KEY)
        iu.random_sleep(iu.randomize_value(2))
        iu.release_all_keys()
        iu.mouse_up('left')
        iu.mouse_up('right')
        self._is_holding_normal_reel = False
        state.current_reel_state = 'normal'
        self.fast_reel_first_run = True
        state.view_offset_records = []
        state.is_view_aligning = False
    def _print_fish_statistics(self):
        elapsed = self._format_elapsed_time(time.time() - state.start_time) if state.start_time else '00:00:00'
        daily = self._format_elapsed_time(state.daily_running_seconds)
        print('\n========================================')
        print('📊 鱼获统计汇总')
        print('========================================')
        print(f'🕒 总运行：{elapsed} | 今日累计：{daily} | AI过滤倍数：{state.used_standard_multiplier:.1f}倍')
        print(f'🐟 总上鱼：{state.total_fish_caught}条 | 达标入户：{state.qualified_fish_count}条 | 放生：{state.released_fish_count}条')
        print(f'⭐ 上星鱼：{state.star_fish_count}条 | 💙 上蓝鱼：{state.blue_fish_count}条')
        if state.total_fish_caught > 0:
            print(f'📈 达标率：{state.qualified_fish_count / state.total_fish_caught * 100:.2f}% | 放生率：{state.released_fish_count / state.total_fish_caught * 100:.2f}%')
        print('========================================')
    def _auto_eat_action(self):
        print(f'\n🍚 自动进食启动（{MIN_EAT_INTERVAL}-{MAX_EAT_INTERVAL}秒/次，按{EAT_KEY}键）')
        while state.is_running:
            while state.is_paused or not state.is_auto_eat or state.is_selling_fish or state.is_eat_paused or state.is_resting or state.is_big_resting:
                time.sleep(0.01)
                if not state.is_running:
                    return
            interval = iu.randomize_value(random.randint(MIN_EAT_INTERVAL, MAX_EAT_INTERVAL))
            for _ in range(int(interval)):
                if not state.is_running or state.is_paused or state.is_selling_fish or state.is_eat_paused or state.is_resting or state.is_big_resting:
                    break
                else:
                    time.sleep(1)
            if state.is_running and (not state.is_paused) and state.is_auto_eat and (not state.is_selling_fish) and (not state.is_eat_paused) and (not state.is_resting) and (not state.is_big_resting):
                                        iu.activate_rf4_window()
                                        iu.key_press(EAT_KEY)
                                        print(f'\n🍚 执行自动进食（按{EAT_KEY}键）')
    def _start_keyboard_listener(self):
        def on_key_press(key):
            global ctrl_pressed
            if state.is_listen_paused:
                return None
            else:
                try:
                    if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                        ctrl_pressed = True
                        return
                    else:
                        if ctrl_pressed:
                            if key == keyboard.KeyCode(char='q'):
                                print('\n🛑 接收到结束指令...')
                                state.is_running = False
                                state.is_selling_fish = False
                                state.is_resting = False
                                state.is_big_resting = False
                                iu.release_all_keys()
                                self.root.after(0, self.stop_fishing)
                            else:
                                if key == keyboard.KeyCode(char='p') and (not state.is_paused):
                                    self.root.after(0, self.toggle_pause)
                                else:
                                    if key == keyboard.KeyCode(char='r') and state.is_paused:
                                            self.root.after(0, self.toggle_pause)
                except:
                    pass
        def on_key_release(key):
            global ctrl_pressed
            try:
                if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                    ctrl_pressed = False
            except:
                pass
        with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
            listener.join()
    def _execute_sell_flow(self, map_id, point_id, skip_login=False):
        """提取的通用卖鱼流程：清空视角 → 设置flags → 执行 → 重置flags"""
        state.view_offset_records = []
        state.is_view_aligning = False
        state.last_rotate_view_time = time.time()
        print('\n🧹 执行卖鱼流程，清空视角偏移记录')
        state.is_selling_fish = True
        state.is_eat_paused = True
        state.is_listen_paused = True
        iu.release_all_keys()
        iu.random_sleep(0.5, 1.0)
        iu.activate_rf4_window()
        iu.random_sleep(1.0, 1.5)
        sell_fish.relog_sell_process(target_map_id=map_id, target_point_id=point_id, skip_login=skip_login)
        state.is_selling_fish = False
        state.is_eat_paused = False
        state.is_listen_paused = False
    def _execute_pending_sell(self):
        if not state.pending_sell_info or not state.is_running:
            return None
        else:
            self._execute_sell_flow(state.pending_sell_info['map_id'], state.pending_sell_info['point_id'], skip_login=False)
            state.is_sell_pending = False
            state.pending_sell_info = {}
    def _real_time_main_loop(self):
        print('========================================')
        print('⌨️  快捷键：Ctrl+P暂停 | Ctrl+R继续 | Ctrl+Q结束')
        print('⏳ 3秒后开始模板侦测...')
        time.sleep(3)
        print('✅ 开始模板侦测，脚本正常运行！')
        print('========================================')
        state.current_reel_state = 'normal'
        last_cast_time = 0
        try:
            while state.is_running:
                check_daily_running_time()
                check_rest_status()
                check_big_rest_status()
                while state.is_paused or state.is_resting or state.is_big_resting:
                    time.sleep(0.1)
                    check_rest_status()
                    check_big_rest_status()
                    if not state.is_running:
                        break
                if not state.is_running:
                    break
                else:
                    check_continuous_running_time()
                    if state.is_auto_assemble and time.time() - state.last_assembly_check_time >= ASSEMBLY_CHECK_INTERVAL:
                            print('\n🔧 检测设备组装状态...')
                            if rf4_assembly.template_exists(DEVICE_UNASSEMBLED_TEMPLATE, rf4_assembly.TEMPLATE_THRESHOLD['device_unassembled']):
                                print('⚠️  检测到设备未组装，执行自动装配...')
                                iu.release_all_keys()
                                state.is_eat_paused = True
                                state.is_listen_paused = True
                                state.view_offset_records = []
                                state.is_view_aligning = False
                                assembly_success = rf4_assembly.main_repair_flow(state.leader_param, state.lure_param)
                                state.is_eat_paused = False
                                state.is_listen_paused = False
                                state.last_assembly_check_time = time.time()
                                if assembly_success:
                                    print('✅ 自动装配完成')
                                else:
                                    print('❌ 自动装配失败，请手动处理')
                            else:
                                print('✅ 设备已组装，无需处理')
                            state.last_assembly_check_time = time.time()
                    if state.current_fish_count >= state.max_fish_count:
                        if state.is_auto_sell:
                            if state.is_resting or state.is_big_resting:
                                print(f'\n📦 渔户满{state.max_fish_count}，挂起卖鱼，休息结束后执行...')
                                state.is_sell_pending = True
                                state.pending_sell_info = {'map_id': state.selected_map_id, 'point_id': state.selected_point_id}
                                state.current_fish_count = state.max_fish_count - 1
                            else:
                                print(f'\n🛒 渔户满{state.max_fish_count}，启动重登卖鱼流程...')
                                state.is_big_sell_pending = False
                                state.is_big_resting = False
                                state.continuous_running_seconds = 0
                                state.daily_running_seconds = 0
                                self._execute_sell_flow(state.selected_map_id, state.selected_point_id, skip_login=False)
                                state.continuous_running_seconds = 0
                                state.last_continuous_check_time = time.time()
                        else:
                            print(f'\n🎉 渔户满{state.max_fish_count}，脚本自动停止！')
                            state.is_running = False
                            iu.release_all_keys()
                            self._print_fish_statistics()
                            self.root.after(0, self.stop_fishing)
                        if not state.is_running:
                            break
                    screen_gray = self._take_screenshot()
                    is_ready_1 = False
                    is_ready_2 = False
                    if time.time() - last_cast_time > READY_TEXT_1_DETECT_INTERVAL:
                        is_ready_1 = self._detect_target('image/ready_text_1.png', READY_MATCH_THRESHOLD, screen_gray)
                    if time.time() - last_cast_time > READY_TEXT_2_DETECT_INTERVAL:
                        is_ready_2 = self._detect_target('image/ready_text_2.png', READY_MATCH_THRESHOLD, screen_gray)
                    is_ready = is_ready_1 or is_ready_2
                    is_fish = False
                    if not state.is_fish_detected and time.time() - self._last_catch_time > 3:
                            is_fish = self._detect_target(FISH_ICON_TEMPLATE, FISH_MATCH_THRESHOLD, screen_gray)
                    is_catched = self._detect_target(FISH_CATCHED_TEMPLATE, CATCHED_MATCH_THRESHOLD, screen_gray)
                    if is_ready:
                        state.current_reel_state = 'normal'
                        iu.release_all_keys()
                        iu.mouse_up('left')
                        iu.mouse_up('right')
                        self._is_holding_normal_reel = False
                    if is_ready and state.pending_rest and (not state.is_resting) and (not state.is_big_resting):
                        rest_min = random.randint(state.rest_min_minutes, state.rest_max_minutes)
                        rest_sec = iu.randomize_value(rest_min * 60)
                        state.rest_end_time = time.time() + rest_sec
                        state.is_resting = True
                        state.pending_rest = False
                        print(f'\n🛌 检测到钓具准备好，执行小休息{rest_sec / 60:.1f}分钟...')
                        app.root.after(0, lambda: app.update_status_label(f'小休息中（剩余{int(rest_sec)}秒）'))
                        app.root.after(0, lambda: app.status_label.config(foreground='purple'))
                        iu.release_all_keys()
                    else:
                        if is_ready and state.is_big_sell_pending and (not state.is_big_resting) and (not state.is_resting):
                            print('\n📦 检测到钓具准备好，执行大休息前置：退出卖鱼（不登录）...')
                            state.view_offset_records = []
                            state.is_view_aligning = False
                            state.last_rotate_view_time = time.time()
                            print('\n🧹 执行大休息流程，清空视角偏移记录')
                            state.is_big_sell_pending = False
                            if state.is_auto_sell and state.selected_map_id!= 0 and (state.selected_point_id!= 0):
                                        state.is_selling_fish = True
                                        state.is_eat_paused = True
                                        state.is_listen_paused = True
                                        iu.release_all_keys()
                                        time.sleep(1)
                                        sell_fish.relog_sell_process(target_map_id=state.selected_map_id, target_point_id=state.selected_point_id, skip_login=True)
                                        state.is_selling_fish = False
                                        state.is_eat_paused = False
                                        state.is_listen_paused = False
                            big_rest_h = random.uniform(BIG_REST_BASE_HOURS - BIG_REST_RANDOM_HOURS, BIG_REST_BASE_HOURS + BIG_REST_RANDOM_HOURS)
                            big_rest_sec = big_rest_h * 3600
                            state.big_rest_end_time = time.time() + big_rest_sec
                            state.is_big_resting = True
                            end_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state.big_rest_end_time))
                            print(f'\n🛌 大休息开始！时长{big_rest_h:.1f}小时，结束时间{end_str}')
                            app.root.after(0, lambda: app.update_status_label(f'大休息中（剩余{int(big_rest_h)}h{int(big_rest_h % 1 * 60)}m）'))
                            app.root.after(0, lambda: app.status_label.config(foreground='darkblue'))
                        else:
                            if is_ready and time.time() - last_cast_time > 5:
                                iu.release_all_keys()
                                self.fast_reel_first_run = True
                                iu.random_sleep(0.1, 0.2)
                                self._fast_cast_rod_action()
                                last_cast_time = time.time()
                                state.current_reel_state = 'normal'
                            else:
                                if is_catched:
                                    iu.release_all_keys()
                                    self._is_holding_normal_reel = False
                                    self.fast_reel_first_run = True
                                    self._consecutive_fast_reel_timeouts = 0
                                    state.total_fish_caught += 1
                                    self._last_catch_time = time.time()
                                    if state.used_standard_multiplier == 0:
                                        print('\n🎣 侦测到鱼上钩，倍率0跳过AI判断，强制入户（节省Token）...')
                                        self._fish_enter_house_action('中鱼强制入户', '未知鱼', 0.0)
                                    else:
                                        print('\n🎣 侦测到鱼上钩，调用AI判断...')
                                        result = get_fish_judgment_result()
                                        fish_name = result.get('fish_name', '未知')
                                        weight = result.get('converted_weight', 0.0)
                                        if result['judgment'] == '留下':
                                            self._fish_enter_house_action(result['reason'], fish_name, weight)
                                        else:
                                            self._fish_release_action(fish_name, weight)
                                    state.current_reel_state = 'normal'
                                    state.is_fish_detected = False
                                else:
                                    if is_fish and state.current_reel_state!= 'fast_lift':
                                        print('🐟 侦测到中鱼，快速收线+抬竿...')
                                        self._fast_reel_and_lift_action()
                                        state.current_reel_state = 'fast_lift'
                                        state.is_fish_detected = True
                                    else:
                                        if state.current_reel_state == 'fast_lift':
                                            self._fast_reel_and_lift_action()
                                        else:
                                            if state.reel_mode == 'jig':
                                                self._jig_reel_action()
                                            else:
                                                if state.reel_mode == 'sea':
                                                    self._sea_reel_action()
                                                else:
                                                    self._normal_reel_action()
                            time.sleep(DETECT_INTERVAL)
        except Exception as e:
            print(f'\n❌ 脚本运行异常：{e}\n{traceback.format_exc()}')
            iu.release_all_keys()
            self._print_fish_statistics()
            self.root.after(0, self.stop_fishing)
            
if __name__ == '__main__':
    if not os.path.exists('image'):
        os.makedirs('image')
        print('📁 已创建image文件夹，请放入模板图片')
    print('========================================')
    print('📌 RF4钓鱼工具 - 仅供学习自动化技术研究，请于24小时内删除')
    print('📢 本程序完全免费，付费购买的请立即退款！')
    # print('💬 QQ群：1035308342（问题反馈/交流）')
    print('✅ 日志持久化 | 大小休息智能挂起 | 防检测拟人化')
    print('✅ 快捷键：Ctrl+P暂停 | Ctrl+R继续 | Ctrl+Q结束')
    print('========================================')
    root = tk.Tk()
    app = RF4FishingGUI(root)
    root.mainloop()
    app.stdout_redirector.close()
    sys.stdout = sys.__stdout__