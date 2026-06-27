# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'ai_judgment.py'
# Bytecode version: 3.9.0beta5 (3425)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

global GLOBAL_FISH_DATABASE
global STANDARD_WEIGHT_MULTIPLIER
import requests
import json
import os
import base64
from PIL import ImageGrab, Image
from io import BytesIO
import pygetwindow as gw
import time
API_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
API_KEY = '899b454f-1a00-45c0-96b5-f755b4c1f32a'
JSON_FILE_PATH = 'fish_database.json'
GLOBAL_FISH_DATABASE = None
FISH_JUDGMENT_CACHE = {}
STANDARD_WEIGHT_MULTIPLIER = 1.0
def set_standard_weight_multiplier(multiplier):
    """\n    供主脚本调用，设置达标重量的倍数\n    :param multiplier: 浮点数，如1.0、1.1、1.2等\n    """
    global STANDARD_WEIGHT_MULTIPLIER
    if isinstance(multiplier, (int, float)) and multiplier >= 0:
        STANDARD_WEIGHT_MULTIPLIER = multiplier
        print(f'✅ 达标重量倍数已设置为：{STANDARD_WEIGHT_MULTIPLIER}倍（标准值×{STANDARD_WEIGHT_MULTIPLIER}）')
    else:
        STANDARD_WEIGHT_MULTIPLIER = 1.0
        print('⚠️  倍数输入不合法，默认使用1.0倍标准值')
def capture_and_process_image_in_memory():
    """\n    自动获取《Russian Fishing 4》游戏窗口\n    截取：宽度完整（避免鱼名横向截断）、高度前1/4（匹配鱼名/重量所在区域）\n    适度降低压缩级别，保留文字细节，兼顾体积和识别率\n    内存中处理，无磁盘I/O，兼顾速度和兼容性\n    """
    try:
        game_window_title_key = 'Russian Fishing 4'
        game_windows = gw.getWindowsWithTitle(game_window_title_key)
        if not game_windows:
            print(f'⚠️  未找到标题包含「{game_window_title_key}」的游戏窗口，切换为全屏截图（高度前1/4）')
            screen_img = ImageGrab.grab()
            screen_width, screen_height = screen_img.size
            screenshot = ImageGrab.grab((0, 0, screen_width, int(screen_height / 4)))
        else:
            game_window = game_windows[0]
            try:
                game_window.activate()
                time.sleep(0.2)
            except:
                print('⚠️  无法激活游戏窗口，直接截取宽度完整+高度前1/4区域')
            game_left = game_window.left
            game_top = game_window.top
            game_right = game_window.right
            game_bottom = game_window.bottom
            game_left = max(0, game_left)
            game_top = max(0, game_top)
            game_right = max(game_left + 100, game_right)
            game_bottom = max(game_top + 100, game_bottom)
            game_width = game_right - game_left
            game_height = game_bottom - game_top
            valid_top = game_top
            valid_bottom = game_top + int(game_height / 4)
            valid_bottom = max(valid_top + 100, valid_bottom)
            valid_bottom = min(valid_bottom, game_bottom)
            print(f'✅ 找到游戏窗口，完整坐标：({game_left}, {game_top}, {game_right}, {game_bottom})')
            print(f'✅ 截取区域：宽度完整（{game_width}px）、高度前1/4（{int(game_height / 4)}px）')
            print(f'✅ 最终截取坐标：({game_left}, {valid_top}, {game_right}, {valid_bottom})')
            game_window_bbox = (game_left, valid_top, game_right, valid_bottom)
            screenshot = ImageGrab.grab(game_window_bbox)
        print('✅ 游戏窗口/全屏「宽度完整+高度前1/4」区域截图成功（保留鱼名/重量，恢复识别率）')
        img_buffer = BytesIO()
        screenshot.save(img_buffer, format='PNG', optimize=True, quality=95, compress_level=4)
        img_buffer.seek(0)
        print('✅ 截图保存成功（内存中，低压缩级别，保留文字细节）')
        base64_bytes = base64.b64encode(img_buffer.read())
        base64_str = base64_bytes.decode('utf-8')
        base64_data = f'data:image/png;base64,{base64_str}'
        encode_size_kb = len(base64_str) / 1024
        print(f'✅ 图片转Base64成功，编码长度：{encode_size_kb:.2f} KB（兼顾体积和识别率）')
        return base64_data
    except Exception as e:
        print(f'❌ 内存中处理图片失败：{e}')
        return None
def load_fish_database():
    """\n    JSON数据库缓存到全局变量，仅启动时加载一次，避免重复读取/解析\n    """
    global GLOBAL_FISH_DATABASE
    if GLOBAL_FISH_DATABASE is not None:
        return GLOBAL_FISH_DATABASE
    else:
        if not os.path.exists(JSON_FILE_PATH):
            print(f'❌ 未找到JSON鱼数据库：{JSON_FILE_PATH}')
            return None
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            GLOBAL_FISH_DATABASE = json.load(f)
        fish_count = len(GLOBAL_FISH_DATABASE.get('fish_list', []))
        print(f'✅ 成功加载JSON鱼数据库（共{fish_count}种鱼，已缓存到内存）')
        return GLOBAL_FISH_DATABASE
    except json.JSONDecodeError as e:
        print(f'❌ 加载JSON数据库失败：格式错误 {e}')
        return
    except Exception as e:
        print(f'❌ 加载JSON数据库失败：{e}')
        return None
def local_fish_judgment(fish_name, weight_gram):
    # irreducible cflow, using cdg fallback
    """\n    本地完成所有逻辑判断（毫秒级响应），精准匹配鱼名配置\n    新增：达标阈值 = standard_weight × 全局倍数（STANDARD_WEIGHT_MULTIPLIER）\n    稀有/超级稀有鱼不受倍数影响，仅过滤低重量达标鱼\n    """
    # ***<module>.local_fish_judgment: Failure: Different control flow
    cache_key = f'{fish_name}_{weight_gram}_{STANDARD_WEIGHT_MULTIPLIER}'
    if cache_key in FISH_JUDGMENT_CACHE:
        print('✅ 命中本地判断缓存，直接返回结果')
        return FISH_JUDGMENT_CACHE[cache_key]
    weight_kg = round(weight_gram / 1000, 3)
    fish_database = load_fish_database()
    if not fish_database:
        raise Exception('JSON鱼数据库未成功加载（无缓存）')
    fish_config = None
    target_fish_list = fish_database.get('fish_list', [])
    for fish in target_fish_list:
        fish_config_name = fish['name']
        if fish_name == fish_config_name:
            fish_config = fish
            break
    if not fish_config:
        result = {'judgment': '留下', 'grade': '识别失败默认入户', 'reason': f'本地未匹配到「{fish_name}」的配置，默认留下', 'fish_name': fish_name, 'converted_weight': weight_kg}
        FISH_JUDGMENT_CACHE[cache_key] = result
        return result
    standard_weight = float(fish_config.get('standard_weight', 0.0))
    rare_weight = float(fish_config.get('rare_weight', 0.0))
    super_rare_weight = float(fish_config.get('super_rare_weight', 0.0))
    fish_name_cn = fish_config['name']
    effective_standard_weight = round(standard_weight * STANDARD_WEIGHT_MULTIPLIER, 3)
    print(f'✅ {fish_name_cn} 阈值计算：标准值{standard_weight}kg × {STANDARD_WEIGHT_MULTIPLIER}倍 = 实际生效阈值{effective_standard_weight}kg')
    if weight_kg >= super_rare_weight:
        result = {'judgment': '留下', 'grade': '上蓝鱼（超级稀有）', 'reason': f'{fish_name_cn}重量{weight_gram}克（{weight_kg}公斤）≥超级稀有阈值{super_rare_weight}公斤，判断留下（不受倍数影响）', 'fish_name': fish_name_cn, 'converted_weight': weight_kg}
        if rare_weight <= weight_kg < super_rare_weight:
                result = {'judgment': '留下', 'grade': '上星鱼（稀有）', 'reason': f'{fish_name_cn}重量{weight_gram}克（{weight_kg}公斤）≥稀有阈值{rare_weight}公斤且＜超级稀有阈值{super_rare_weight}公斤，判断留下（不受倍数影响）', 'fish_name': fish_name_cn, 'converted_weight': weight_kg}
                if effective_standard_weight <= weight_kg < rare_weight:
                        result = {'judgment': '留下', 'grade': '达标鱼（倍数过滤后）', 'reason': f'{fish_name_cn}重量{weight_gram}克（{weight_kg}公斤）≥实际生效达标阈值{effective_standard_weight}公斤（标准值{standard_weight}kg×{STANDARD_WEIGHT_MULTIPLIER}倍）且＜稀有阈值{rare_weight}公斤，判断留下', 'fish_name': fish_name_cn, 'converted_weight': weight_kg}
                        result = {'judgment': '放生', 'grade': '无', 'reason': f'{fish_name_cn}重量{weight_gram}克（{weight_kg}公斤）＜实际生效达标阈值{effective_standard_weight}公斤（标准值{standard_weight}kg×{STANDARD_WEIGHT_MULTIPLIER}倍），判断放生', 'fish_name': fish_name_cn, 'converted_weight': weight_kg}
    FISH_JUDGMENT_CACHE[cache_key] = result
    return result
def call_ai_fish_judgment():
    """\n    完全对齐原始curl请求格式，解决400 Bad Request错误\n    截取「宽度完整+高度前1/4」区域，恢复识别率，兼顾体积优化\n    """
    fish_database = load_fish_database()
    if not fish_database:
        return {'judgment': '留下', 'grade': '识别失败默认入户', 'reason': '本地JSON数据库加载失败，默认留下', 'fish_name': '未知鱼', 'converted_weight': 0.0}
    else:
        base64_image = capture_and_process_image_in_memory()
        if not base64_image:
            return {'judgment': '留下', 'grade': '识别失败默认入户', 'reason': '图片在内存中处理失败，无法调用AI识别', 'fish_name': '未知鱼', 'converted_weight': 0.0}
        else:
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
            prompt_text = '请严格完成以下任务，仅返回要求的JSON格式，无需额外内容：1.  识别对象：图片是游戏《Russian Fishing 4》「宽度完整+高度前1/4」区域（包含完整鱼名和重量），提取2个核心信息：- 鱼名（中文，必须**严格按照游戏界面显示的名称原样提取**，不增删、不简化、不修改任何字符！）- 重量（仅提取数字，单位为克，位于鱼名附近，转换为整数，确保数字准确）2.  关键要求（核心：禁止主动简化，而非禁止大类名称）：- 若游戏界面显示的是带修饰词的鱼名（如湖鳟鱼、白刺盖太阳鱼），必须完整提取所有修饰词，禁止省略为鳟鱼、太阳鱼。- 若游戏界面显示的是无修饰词的鱼名（如鳟鱼、太阳鱼、鲤鱼、鲑鱼），直接原样返回，禁止额外添加修饰词。- 一字不差：鱼名必须和游戏界面显示的完全一致，多一个字少一个字都不行。3.  清晰示例（区分“独立鱼种”和“带修饰词鱼种”）：- 游戏显示「鳟鱼」→ 正确返回：鳟鱼 | 错误返回：湖鳟鱼、虹鳟鱼- 游戏显示「湖鳟鱼」→ 正确返回：湖鳟鱼 | 错误返回：鳟鱼- 游戏显示「太阳鱼」→ 正确返回：太阳鱼 | 错误返回：白刺盖太阳鱼- 游戏显示「白刺盖太阳鱼」→ 正确返回：白刺盖太阳鱼 | 错误返回：太阳鱼4.  返回要求：必须返回JSON格式，字段不可缺少、不可额外添加，格式如下：{\"fish_name\": \"识别到的鱼名（严格按游戏界面原样）\",\"weight_gram\": 320}5.  强制要求：即使有轻微遮挡，也必须尽力还原游戏界面显示的鱼名，实在无法识别时填“未知鱼”，重量填0。'
            payload = {'model': 'doubao-seed-1-6-lite-251015', 'max_completion_tokens': 65535, 'messages': [{'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': base64_image}}, {'type': 'text', 'text': prompt_text}]}], 'reasoning_effort': 'medium'}
            try:
                print('✅ 开始调用指定豆包AI进行鱼名/重量识别（保留完整信息，恢复识别率）')
                response = requests.post(API_URL, headers=headers, json=payload, timeout=40)
                response.raise_for_status()
                api_response = response.json()
                ai_result_str = api_response['choices'][0]['message']['content']
                ai_result = json.loads(ai_result_str)
                fish_name_ai = ai_result.get('fish_name', '未知鱼')
                weight_gram_ai = int(ai_result.get('weight_gram', 0))
                print(f'✅ AI识别完成：鱼名={fish_name_ai}，重量={weight_gram_ai}克')
                try:
                    final_result = local_fish_judgment(fish_name_ai, weight_gram_ai)
                except Exception as e:
                    print(f'⚠️  本地判断异常，使用兜底结果：{e}')
                    final_result = {'judgment': '留下', 'grade': '识别失败默认入户', 'reason': f'本地判断异常：{str(e)}，默认留下', 'fish_name': fish_name_ai, 'converted_weight': round(weight_gram_ai / 1000, 3) if weight_gram_ai else 0.0}
                return final_result
            except requests.exceptions.RequestException as e:
                try:
                    error_response = response.text
                    print(f'❌ API返回详细错误信息：{error_response}')
                except:
                    print('❌ 无法获取API详细错误信息（请求未到达服务端或无响应）')
                print(f'❌ 指定AI API调用失败：{e}')
                return {'judgment': '留下', 'grade': '识别失败默认入户', 'reason': f'AI API调用失败：{str(e)}，默认留下', 'fish_name': '未知鱼', 'converted_weight': 0.0}
            except json.JSONDecodeError as e:
                print(f'❌ AI返回结果解析失败：{e}')
                return {'judgment': '留下', 'grade': '识别失败默认入户', 'reason': 'AI返回结果格式错误，无法解析', 'fish_name': '未知鱼', 'converted_weight': 0.0}
            except Exception as e:
                print(f'❌ AI判断流程异常：{e}')
                return {'judgment': '留下', 'grade': '识别失败默认入户', 'reason': f'未知异常：{str(e)}，默认留下', 'fish_name': '未知鱼', 'converted_weight': 0.0}
def get_fish_judgment_result():
    """\n    统一入口函数，rf4_fishing_core.py 无需任何修改，直接调用\n    所有优化和修复逻辑封装在内，对调用方透明\n    """
    return call_ai_fish_judgment()