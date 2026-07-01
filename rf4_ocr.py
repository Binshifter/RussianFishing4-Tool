"""PP-OCRv4 ONNX 文字识别模块，用于替代部分模板匹配。"""

import os
import re
import cv2
import numpy as np

try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

_ocr_engine = None


def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None and OCR_AVAILABLE:
        _ocr_engine = RapidOCR()
    return _ocr_engine


def ocr_text(image, keywords=None):
    if image is None or not OCR_AVAILABLE:
        return []
    engine = get_ocr_engine()
    if engine is None:
        return []
    result, _ = engine(image)
    if not result:
        return []
    texts = [item[1] for item in result]
    if keywords is None:
        return texts
    matched = []
    for text in texts:
        for kw in keywords:
            if kw in text:
                matched.append(text)
                break
    return matched


def detect_text_in_region(screen_bgr, x1, y1, x2, y2, keywords):
    if screen_bgr is None or not OCR_AVAILABLE:
        return False
    h, w = screen_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return False
    crop = screen_bgr[y1:y2, x1:x2]
    matched = ocr_text(crop, keywords)
    return len(matched) > 0


def get_fish_count_from_screen(screen_bgr):
    """从屏幕 OCR 识别鱼护计数（X/Y 格式）。

    只识别屏幕中心横竖交叉分成四块后的右下区域。

    Returns:
        (current, max_count) 或 None
    """
    if screen_bgr is None or not OCR_AVAILABLE:
        return None
    h, w = screen_bgr.shape[:2]

    engine = get_ocr_engine()
    if engine is None:
        return None

    # 只识别右下区域：屏幕中心横竖交叉分成四块的右下那一块
    x1 = w // 2
    y1 = h // 2
    x2 = w
    y2 = h
    crop = screen_bgr[y1:y2, x1:x2]

    # 保存右下区域截图用于调试
    debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_fish_count.png')
    cv2.imwrite(debug_path, crop)
    print(f'  鱼护识别区域: ({x1},{y1}) -> ({x2},{y2}), 尺寸: {crop.shape[1]}x{crop.shape[0]}')

    # 对右下区域进行 OCR 识别
    result, _ = engine(crop)
    if result:
        print(f'  鱼护 OCR 共识别到 {len(result)} 条文字:')
        for item in result:
            box, text, score = item
            print(f'    "{text}" (置信度:{score})')
    else:
        print('  鱼护 OCR 未识别到任何文字')
    if not result:
        return None

    # 查找包含 "/" 的数字模式
    for item in result:
        text = item[1]
        # 匹配 "数字/数字" 格式，如 92/150
        m = re.search(r'(\d+)\s*/\s*(\d+)', text)
        if m:
            current = int(m.group(1))
            max_count = int(m.group(2))
            if 0 <= current <= max_count <= 999:
                print(f'  ✅ 找到鱼护计数: {current}/{max_count}')
                return (current, max_count)

    # 如果没找到，尝试查找类似的数字模式（可能是 OCR 识别错误）
    for item in result:
        text = item[1]
        # 尝试匹配 "数字 数字" 或 "数字:数字"
        m = re.search(r'(\d+)\s*[/／:]\s*(\d+)', text)
        if m:
            current = int(m.group(1))
            max_count = int(m.group(2))
            if 0 <= current <= max_count <= 999:
                print(f'  ⚠️ 可能找到鱼护计数：{current}/{max_count} (原文:"{text}")')
                return (current, max_count)

    return None


def get_fish_info_from_screen(screen_bgr):
    """从屏幕 OCR 识别鱼名和重量。

    Returns:
        (fish_name, weight_kg) 或 (None, None)
        fish_name: 鱼名（如 "鳟鱼"）
        weight_kg: 重量（千克，如 0.922）
    """
    if screen_bgr is None or not OCR_AVAILABLE:
        return None, None

    engine = get_ocr_engine()
    if engine is None:
        return None, None

    # 全屏识别
    result, _ = engine(screen_bgr)
    if not result:
        return None, None

    fish_name = None
    weight_kg = None

    rarity_tags = ['珍贵的', '常见的', '稀有的', '普通的', '罕见的', '史诗', '传说', '稀有', '珍贵', '常见', '普通', '罕见']
    skip_patterns = ['厘米', 'cm', '公分', '分钟', '秒', '/', 'XP', '经验', '点数', '高级', '总共', '入户', '释放', 'Space', 'Backspace', '登录']

    sorted_items = sorted(result, key=lambda item: item[0][0][1])

    for item in sorted_items:
        box, text, score = item
        text = text.strip()

        if not text:
            continue

        has_skip = any(p in text for p in skip_patterns)
        if has_skip:
            continue

        is_rarity = any(tag in text for tag in rarity_tags)
        if is_rarity:
            continue

        is_pure_number = bool(re.fullmatch(r'[\d.,\s]+', text))
        if is_pure_number:
            continue

        if not fish_name:
            fish_name = text

        if weight_kg is None:
            m = re.search(r'(\d+(?:\.\d+)?)\s*(克|千克|公斤|kg|g)', text, re.IGNORECASE)
            if m:
                value = float(m.group(1))
                unit = m.group(2).lower()
                if unit in ['克', 'g']:
                    weight_kg = value / 1000
                elif unit in ['千克', '公斤', 'kg']:
                    weight_kg = value
                print(f'  匹配到重量：{value}{unit} → {weight_kg}kg')

    if fish_name:
        print(f'  ✅ 识别到鱼名：{fish_name}')
    if weight_kg is not None:
        print(f'  ✅ 识别到重量：{weight_kg:.3f}kg')

    return fish_name, weight_kg
