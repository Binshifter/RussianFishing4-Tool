# Visit https://www.lddgo.net/string/pyc-compile-decompile for more information
# Version : Python 3.9


class RF4State:
    '''Centralized runtime state for all RF4 automation modules.'''
    
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.is_resting = False
        self.is_big_resting = False
        self.is_selling_fish = False
        self.is_sell_pending = False
        self.is_big_sell_pending = False
        self.is_fish_detected = False
        self.current_reel_state = 'normal'
        self.pending_rest = False
        self.pending_sell_info = {}
        self.reel_mode = 'normal'
        self.is_auto_eat = True
        self.is_auto_sell = False
        self.is_auto_assemble = False
        self.max_fish_count = 100
        self.bait_fly_time = 4
        self.reel_duration = 0.1
        self.pause_duration = 1
        self.selected_map_id = 0
        self.selected_point_id = 0
        self.selected_coordinate = ''
        self.leader_param = ''
        self.lure_param = ''
        self.used_standard_multiplier = 0
        self.sea_cast_duration = 0.1
        self.sea_sink_time = 82
        self.sea_twitch_interval = 2
        self.sea_twitch_duration = 0.6
        self.continuous_max_hours = 6
        self.daily_max_hours = 14
        self.rest_min_minutes = 5
        self.rest_max_minutes = 30
        self.max_fast_reel_timeouts = 0
        self.login_button_template = 'image/login_button.png'
        self.login_load_wait = 37
        self.total_fish_caught = 0
        self.released_fish_count = 0
        self.qualified_fish_count = 0
        self.star_fish_count = 0
        self.blue_fish_count = 0
        self.start_time = 0
        self.current_fish_count = 0
        self.daily_running_seconds = 0
        self.last_daily_check_time = 0
        self.continuous_running_seconds = 0
        self.last_continuous_check_time = 0
        self.rest_end_time = 0
        self.big_rest_end_time = 0
        self.last_assembly_check_time = 0
        self.last_rotate_view_time = 0
        self.view_offset_records = []
        self.is_view_aligning = False
        self.last_human_act_time = 0
        self.is_eat_paused = False
        self.is_listen_paused = False
        self.is_waiting_login = False
        self.last_login_check_print_time = 0
        self.last_big_rest_print_time = 0
        self.last_small_rest_print_time = 0


state = RF4State()