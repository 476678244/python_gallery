"""
Scandinavian Flat Illustration Atoms
统一扁平插画原子组件
"""
import math
from design_system import PALETTE, I, rgb, add_rect, add_oval, push_back

C = PALETTE

# ============================================================================
# 几何基础
# ============================================================================
def sun_flat(slide, cx, cy, r, color=None):
    """扁平太阳 - 大圆加小圆点装饰"""
    c = color or C["warm_yellow"]
    # 主圆
    add_oval(slide, cx-r, cy-r, r*2, r*2, c)
    # 装饰小圆点 (Scandinavian style dots)
    dot_r = int(r * 0.15)
    for a in range(0, 360, 60):
        rad = math.radians(a)
        dot_cx = cx + int(r * 1.4 * math.cos(rad))
        dot_cy = cy + int(r * 1.4 * math.sin(rad))
        add_oval(slide, dot_cx-dot_r, dot_cy-dot_r, dot_r*2, dot_r*2, c)

def cloud_flat(slide, cx, cy, w, h, color=None):
    """扁平云朵 - 两个重叠椭圆"""
    c = color or C["frost_white"]
    # 左大椭圆
    add_oval(slide, cx-int(w*0.45), cy-int(h*0.2), int(w*0.7), int(h*0.8), c)
    # 右小椭圆
    add_oval(slide, cx, cy-int(h*0.35), int(w*0.55), int(h*0.7), c)

def hill_flat(slide, x, y, w, h, color):
    """扁平山丘 - 单一椭圆"""
    add_oval(slide, x, y, w, h, color)

def ground_flat(slide, x, y, w, h, color):
    """扁平地面"""
    add_rect(slide, x, y, w, h, color)

# ============================================================================
# 植物
# ============================================================================
def tree_round(slide, cx, cy, scale=1.0, leaf_color=None, trunk_color=None):
    """圆形树冠树 - Scandinavian风格"""
    lc = leaf_color or C["spring_green"]
    tc = trunk_color or C["ink_brown"]
    s = scale
    
    # 树干 - 简单矩形
    tw = int(I(0.08 * s))
    th = int(I(0.35 * s))
    add_rect(slide, cx-tw//2, cy, tw, th, tc)
    
    # 树冠 - 两个重叠大圆，低细节
    cr = int(I(0.28 * s))
    add_oval(slide, cx-cr, cy-int(I(0.25*s)), cr*2, int(I(0.55*s)), lc)
    add_oval(slide, cx-int(I(0.12*s)), cy-int(I(0.40*s)), int(I(0.45*s)), int(I(0.42*s)), lc)

def flower_simple(slide, cx, cy, scale=1.0, petal_color=None):
    """简单花朵 - 五瓣扁平"""
    pc = petal_color or C["flower_pink"]
    s = scale
    
    # 茎
    add_rect(slide, cx-int(I(0.02*s)), cy-int(I(0.20*s)), int(I(0.04*s)), int(I(0.25*s)), C["spring_green"])
    
    # 花瓣 - 中心加一个，四角各一个
    pr = int(I(0.10 * s))
    add_oval(slide, cx-pr, cy-int(I(0.25*s))-pr, pr*2, pr*2, pc)  # 中心
    for dx, dy in [(-0.08,-0.25), (0.08,-0.25), (0,-0.33), (0,-0.17)]:
        add_oval(slide, cx+int(I(dx*s))-int(pr*0.6), cy+int(I(dy*s))-int(pr*0.6), 
                 int(pr*1.2), int(pr*1.2), pc)
    # 花蕊
    add_oval(slide, cx-int(I(0.04*s)), cy-int(I(0.25*s))-int(I(0.04*s)), 
             int(I(0.08*s)), int(I(0.08*s)), C["warm_yellow"])

def grass_simple(slide, x, y, w, h, color=None):
    """简单草地 - 纯色块加极简草叶"""
    c = color or C["spring_gnd"]
    add_rect(slide, x, y, w, h, c)
    # 极简草叶指示 - 几个小竖条
    step = int(I(0.20))
    for i in range(0, int(w), step):
        if i % (step*2) == 0:
            add_rect(slide, x+i, y-int(I(0.06)), int(I(0.03)), int(I(0.08)), C["spring_green"])

# ============================================================================
# 动物 - 极简几何
# ============================================================================
def deer_simple(slide, x, y, scale=1.0):
    """极简鹿 - 大色块几何"""
    s = scale
    body_c = C["soft_coral"]
    
    # 身体 - 椭圆
    add_oval(slide, x, y, int(I(0.55*s)), int(I(0.30*s)), body_c)
    # 脖子
    add_rect(slide, x+int(I(0.38*s)), y-int(I(0.25*s)), int(I(0.12*s)), int(I(0.30*s)), body_c)
    # 头 - 小椭圆
    add_oval(slide, x+int(I(0.35*s)), y-int(I(0.38*s)), int(I(0.22*s)), int(I(0.18*s)), body_c)
    # 耳朵
    add_oval(slide, x+int(I(0.40*s)), y-int(I(0.44*s)), int(I(0.08*s)), int(I(0.12*s)), body_c)
    # 腿 - 简单矩形
    for lx in [0.08, 0.15, 0.38, 0.45]:
        add_rect(slide, x+int(I(lx*s)), y+int(I(0.22*s)), int(I(0.06*s)), int(I(0.22*s)), body_c)

def ox_simple(slide, x, y, scale=1.0):
    """极简牛 - 圆润大色块"""
    s = scale
    body_c = C["wheat_gold"]
    spot_c = C["frost_white"]
    
    # 身体 - 大椭圆
    add_oval(slide, x, y, int(I(0.60*s)), int(I(0.32*s)), body_c)
    # 白色斑点 (Scandinavian装饰性)
    add_oval(slide, x+int(I(0.12*s)), y+int(I(0.04*s)), int(I(0.18*s)), int(I(0.14*s)), spot_c)
    # 头
    add_oval(slide, x+int(I(0.48*s)), y-int(I(0.08*s)), int(I(0.20*s)), int(I(0.18*s)), body_c)
    # 角 - 小三角形状用椭圆近似
    add_oval(slide, x+int(I(0.52*s)), y-int(I(0.16*s)), int(I(0.06*s)), int(I(0.12*s)), C["ink_brown"])
    add_oval(slide, x+int(I(0.60*s)), y-int(I(0.16*s)), int(I(0.06*s)), int(I(0.12*s)), C["ink_brown"])
    # 腿
    for lx in [0.08, 0.18, 0.38, 0.48]:
        add_rect(slide, x+int(I(lx*s)), y+int(I(0.24*s)), int(I(0.08*s)), int(I(0.20*s)), C["ink_brown"])

def frog_simple(slide, x, y, scale=1.0):
    """极简青蛙 - 扁平几何"""
    s = scale
    body_c = C["spring_green"]
    
    # 身体 - 大椭圆
    add_oval(slide, x, y, int(I(0.32*s)), int(I(0.22*s)), body_c)
    # 头
    add_oval(slide, x+int(I(0.06*s)), y-int(I(0.12*s)), int(I(0.20*s)), int(I(0.16*s)), body_c)
    # 眼睛 - 白底黑点
    add_oval(slide, x+int(I(0.08*s)), y-int(I(0.16*s)), int(I(0.08*s)), int(I(0.08*s)), C["frost_white"])
    add_oval(slide, x+int(I(0.16*s)), y-int(I(0.16*s)), int(I(0.08*s)), int(I(0.08*s)), C["frost_white"])
    add_oval(slide, x+int(I(0.10*s)), y-int(I(0.14*s)), int(I(0.04*s)), int(I(0.04*s)), C["ink_dark"])
    add_oval(slide, x+int(I(0.18*s)), y-int(I(0.14*s)), int(I(0.04*s)), int(I(0.04*s)), C["ink_dark"])

def ladybug_simple(slide, x, y, scale=1.0):
    """极简瓢虫 - 半圆身体"""
    s = scale
    # 身体
    add_oval(slide, x, y, int(I(0.22*s)), int(I(0.18*s)), C["soft_coral"])
    # 头
    add_oval(slide, x+int(I(0.07*s)), y-int(I(0.08*s)), int(I(0.08*s)), int(I(0.08*s)), C["ink_dark"])
    # 点
    for dx, dy in [(0.05,0.04), (0.12,0.04), (0.08,0.10)]:
        add_oval(slide, x+int(I(dx*s)), y+int(I(dy*s)), int(I(0.04*s)), int(I(0.04*s)), C["frost_white"])

def butterfly_simple(slide, x, y, scale=1.0):
    """极简蝴蝶 - 对称扁平"""
    s = scale
    wing_c = C["flower_pink"]
    # 身体
    add_rect(slide, x+int(I(0.08*s)), y, int(I(0.04*s)), int(I(0.20*s)), C["ink_brown"])
    # 左翅膀
    add_oval(slide, x, y+int(I(0.02*s)), int(I(0.10*s)), int(I(0.12*s)), wing_c)
    add_oval(slide, x, y+int(I(0.10*s)), int(I(0.08*s)), int(I(0.10*s)), wing_c)
    # 右翅膀
    add_oval(slide, x+int(I(0.10*s)), y+int(I(0.02*s)), int(I(0.10*s)), int(I(0.12*s)), wing_c)
    add_oval(slide, x+int(I(0.12*s)), y+int(I(0.10*s)), int(I(0.08*s)), int(I(0.10*s)), wing_c)

# ============================================================================
# 人物 - 扁平化 (关键改进)
# ============================================================================
def person_flat(slide, x, y, body_color, scale=1.0, pose="stand", season="spring"):
    """Scandinavian扁平人物 - 清晰比例，梯形身体，明确人形"""
    s = scale
    skin_c = rgb(0xF5, 0xD0, 0xC0)  # 更自然的肤色
    
    # 基础尺寸
    head_d = int(I(0.22 * s))  # 头部直径
    body_w = int(I(0.26 * s))
    body_h = int(I(0.32 * s))
    
    # 头部位置 (身体上偏)
    head_x = x
    head_y = y - body_h - int(I(0.08 * s))
    
    # === 头部 ===
    # 脸 - 正圆
    add_oval(slide, head_x, head_y, head_d, head_d, skin_c)
    # 头发 - 半圆覆盖顶部
    add_oval(slide, head_x-int(I(0.02*s)), head_y-int(I(0.06*s)), 
             head_d+int(I(0.04*s)), int(I(0.14*s)), C["ink_brown"])
    
    # === 身体 - 用矩形+圆角效果 (梯形感) ===
    body_x = head_x + (head_d - body_w)//2
    body_y = y - body_h
    # 主体矩形
    add_rect(slide, body_x, body_y, body_w, body_h, body_color)
    # 底部圆角 (用椭圆模拟)
    add_oval(slide, body_x-int(I(0.02*s)), body_y+body_h-int(I(0.06*s)), 
             body_w+int(I(0.04*s)), int(I(0.12*s)), body_color)
    
    # === 手臂 - 明确的位置 ===
    arm_w = int(I(0.05 * s))
    arm_h = int(I(0.20 * s))
    arm_y = body_y + int(I(0.04 * s))
    
    if pose == "wave":
        # 右臂上举
        add_rect(slide, body_x-arm_w, arm_y, arm_w, arm_h, skin_c)  # 左臂下垂
        add_rect(slide, body_x-arm_w, arm_y-int(I(0.12*s)), arm_w, arm_h, skin_c)  # 左上举
        # 手
        add_oval(slide, body_x-int(I(0.02*s)), arm_y-int(I(0.16*s)), int(I(0.08*s)), int(I(0.08*s)), skin_c)
    elif pose == "hold":
        # 双臂前伸
        add_rect(slide, body_x+int(I(0.03*s)), arm_y+int(I(0.08*s)), arm_w, int(I(0.14*s)), skin_c)
        add_rect(slide, body_x+body_w-int(I(0.08*s)), arm_y+int(I(0.08*s)), arm_w, int(I(0.14*s)), skin_c)
    else:  # stand - 自然下垂，稍微外张
        add_rect(slide, body_x-arm_w-int(I(0.02*s)), arm_y, arm_w, arm_h, skin_c)
        add_rect(slide, body_x+body_w+int(I(0.02*s)), arm_y, arm_w, arm_h, skin_c)
    
    # === 腿部 ===
    if season == "summer":
        leg_h = int(I(0.18 * s))
        leg_c = skin_c  # 短裤露出腿
        # 短裤
        add_rect(slide, body_x+int(I(0.02*s)), y-int(I(0.02*s)), 
                 int(body_w*0.40), int(I(0.08*s)), body_color)
        add_rect(slide, body_x+int(body_w*0.58), y-int(I(0.02*s)), 
                 int(body_w*0.40), int(I(0.08*s)), body_color)
    else:
        leg_h = int(I(0.22 * s))
        leg_c = C["ink_brown"]  # 长裤
    
    leg_w = int(I(0.07 * s))
    leg_y = y
    
    # 左腿
    add_rect(slide, body_x+int(I(0.03*s)), leg_y, leg_w, leg_h, leg_c)
    # 右腿
    add_rect(slide, body_x+body_w-leg_w-int(I(0.03*s)), leg_y, leg_w, leg_h, leg_c)
    
    # === 简单面部特征 (可选，增加识别度) ===
    eye_y = head_y + int(I(0.10*s))
    # 两个小黑点眼睛
    add_oval(slide, head_x+int(I(0.06*s)), eye_y, int(I(0.03*s)), int(I(0.03*s)), C["ink_dark"])
    add_oval(slide, head_x+head_d-int(I(0.09*s)), eye_y, int(I(0.03*s)), int(I(0.03*s)), C["ink_dark"])
    # 微笑
    add_oval(slide, head_x+int(I(0.08*s)), head_y+int(I(0.14*s)), int(I(0.06*s)), int(I(0.03*s)), C["soft_coral"])

# ============================================================================
# 人造物
# ============================================================================
def house_simple(slide, x, y, scale=1.0):
    """极简房屋 - 几何色块"""
    s = scale
    wall_c = C["frost_white"]
    roof_c = C["soft_coral"]
    
    # 房体 - 矩形
    add_rect(slide, x, y, int(I(0.32*s)), int(I(0.28*s)), wall_c)
    # 屋顶 - 大三角用椭圆近似
    add_oval(slide, x-int(I(0.04*s)), y-int(I(0.12*s)), int(I(0.40*s)), int(I(0.20*s)), roof_c)
    # 门
    add_rect(slide, x+int(I(0.12*s)), y+int(I(0.12*s)), int(I(0.08*s)), int(I(0.16*s)), C["ink_brown"])
    # 窗
    add_oval(slide, x+int(I(0.04*s)), y+int(I(0.06*s)), int(I(0.08*s)), int(I(0.08*s)), C["rain_blue"])

def kite_simple(slide, x, y, scale=1.0):
    """极简风筝 - 菱形"""
    s = scale
    kite_c = C["warm_yellow"]
    # 菱形主体用椭圆近似
    add_oval(slide, x, y, int(I(0.20*s)), int(I(0.28*s)), kite_c)
    # 装饰条纹
    add_rect(slide, x+int(I(0.08*s)), y, int(I(0.04*s)), int(I(0.28*s)), C["soft_coral"])
    add_rect(slide, x, y+int(I(0.12*s)), int(I(0.20*s)), int(I(0.04*s)), C["soft_coral"])
    # 尾巴
    for i in range(3):
        add_oval(slide, x+int(I(0.06*s)), y+int(I(0.30+i*0.08)*s), int(I(0.08*s)), int(I(0.06*s)), 
                 C["flower_pink"] if i%2==0 else C["warm_yellow"])

def umbrella_simple(slide, x, y, scale=1.0):
    """极简雨伞"""
    s = scale
    # 伞面 - 半圆
    add_oval(slide, x-int(I(0.24*s)), y-int(I(0.12*s)), int(I(0.48*s)), int(I(0.28*s)), C["rain_blue"])
    # 伞柄
    add_rect(slide, x-int(I(0.02*s)), y, int(I(0.04*s)), int(I(0.35*s)), C["ink_brown"])

def water_wheel_simple(slide, x, y, scale=1.0):
    """极简水车"""
    s = scale
    r = int(I(0.28 * s))
    # 外圈
    add_oval(slide, x-r, y-r, r*2, r*2, C["wheat_gold"])
    # 中心
    add_oval(slide, x-int(I(0.08*s)), y-int(I(0.08*s)), int(I(0.16*s)), int(I(0.16*s)), C["ink_brown"])
    # 辐条 - 十字
    add_rect(slide, x-int(I(0.02*s)), y-r, int(I(0.04*s)), r*2, C["ink_brown"])
    add_rect(slide, x-r, y-int(I(0.02*s)), r*2, int(I(0.04*s)), C["ink_brown"])

def scarecrow_simple(slide, x, y, scale=1.0):
    """极简稻草人"""
    s = scale
    # 十字架
    add_rect(slide, x+int(I(0.10*s)), y, int(I(0.05*s)), int(I(0.55*s)), C["ink_brown"])
    add_rect(slide, x, y+int(I(0.12*s)), int(I(0.25*s)), int(I(0.05*s)), C["ink_brown"])
    # 头 - 大圆
    add_oval(slide, x+int(I(0.06*s)), y-int(I(0.08*s)), int(I(0.18*s)), int(I(0.18*s)), C["wheat_gold"])
    # 帽子
    add_oval(slide, x, y-int(I(0.16*s)), int(I(0.30*s)), int(I(0.10*s)), C["soft_coral"])

# ============================================================================
# 天气/自然现象
# ============================================================================
def rain_simple(slide, x, y, w, h, n=8):
    """极简雨滴 - 短竖线"""
    step_x = w // max(1, n//2)
    step_y = h // 2
    for i in range(n):
        rx = x + (i % 4) * step_x + int(I(0.08))
        ry = y + (i // 4) * step_y
        add_rect(slide, rx, ry, int(I(0.03)), int(I(0.12)), C["rain_blue"])

def snow_simple(slide, x, y, w, h, n=6):
    """极简雪花 - 小白点"""
    import random
    random.seed(42)
    for _ in range(n):
        sx = x + int(random.random() * w)
        sy = y + int(random.random() * h)
        r = int(I(0.05))
        add_oval(slide, sx-r, sy-r, r*2, r*2, C["frost_white"])

def lightning_simple(slide, x, y, scale=1.0):
    """极简闪电 - 折线用矩形近似"""
    s = scale
    c = C["warm_yellow"]
    # 闪电形状 - 两个矩形组成Z形
    add_rect(slide, x, y, int(I(0.10*s)), int(I(0.25*s)), c)
    add_rect(slide, x-int(I(0.06*s)), y+int(I(0.20*s)), int(I(0.20*s)), int(I(0.08*s)), c)
    add_rect(slide, x+int(I(0.08*s)), y+int(I(0.22*s)), int(I(0.08*s)), int(I(0.18*s)), c)

def lotus_simple(slide, x, y, scale=1.0):
    """极简莲花"""
    s = scale
    # 荷叶 - 大椭圆
    add_oval(slide, x, y+int(I(0.12*s)), int(I(0.42*s)), int(I(0.16*s)), C["spring_green"])
    # 茎
    add_rect(slide, x+int(I(0.18*s)), y, int(I(0.04*s)), int(I(0.18*s)), C["spring_green"])
    # 花 - 粉色椭圆
    add_oval(slide, x+int(I(0.10*s)), y-int(I(0.08*s)), int(I(0.22*s)), int(I(0.20*s)), C["flower_pink"])
    # 花蕊
    add_oval(slide, x+int(I(0.16*s)), y-int(I(0.04*s)), int(I(0.10*s)), int(I(0.08*s)), C["warm_yellow"])

def watermelon_simple(slide, x, y, scale=1.0):
    """极简西瓜"""
    s = scale
    # 瓜体 - 半圆
    add_oval(slide, x, y, int(I(0.35*s)), int(I(0.22*s)), C["spring_green"])
    # 瓜肉
    add_oval(slide, x+int(I(0.06*s)), y+int(I(0.04*s)), int(I(0.23*s)), int(I(0.14*s)), C["soft_coral"])
    # 瓜籽 - 小黑点
    for sx, sy in [(0.12,0.08), (0.18,0.10), (0.15,0.06)]:
        add_oval(slide, x+int(I(sx*s)), y+int(I(sy*s)), int(I(0.02*s)), int(I(0.03*s)), C["ink_dark"])

# ============================================================================
# 作物/植物
# ============================================================================
def wheat_simple(slide, x, y, w, h, rows=3, cols=5):
    """极简麦田 - 简化麦穗"""
    sw = w // cols
    sh = h // rows
    for r in range(rows):
        for c in range(cols):
            wx = x + c * sw + sw//3
            wy = y + r * sh
            # 麦秆
            add_rect(slide, wx+int(I(0.02)), wy+sh//3, int(I(0.03)), sh*2//3, C["spring_green"])
            # 麦穗 - 简单椭圆
            add_oval(slide, wx-int(I(0.04)), wy, int(I(0.12)), sh//3, C["wheat_gold"])

def cotton_simple(slide, x, y, scale=1.0):
    """极简棉花"""
    s = scale
    # 枝干
    add_rect(slide, x+int(I(0.08*s)), y, int(I(0.04*s)), int(I(0.40*s)), C["ink_brown"])
    # 棉桃 - 三个白椭圆
    for cy in [0.08, 0.22, 0.36]:
        add_oval(slide, x+int(I(0.04*s)), y+int(I(cy*s)), int(I(0.16*s)), int(I(0.14*s)), C["frost_white"])

def seedling_simple(slide, x, y, scale=1.0):
    """极简幼苗"""
    s = scale
    # 茎
    add_rect(slide, x+int(I(0.03*s)), y, int(I(0.04*s)), int(I(0.20*s)), C["spring_green"])
    # 两片叶子
    add_oval(slide, x, y-int(I(0.08*s)), int(I(0.12*s)), int(I(0.08*s)), C["spring_green"])
    add_oval(slide, x+int(I(0.02*s)), y-int(I(0.12*s)), int(I(0.10*s)), int(I(0.08*s)), C["spring_green"])

def persimmon_simple(slide, x, y, scale=1.0):
    """极简柿子树"""
    s = scale
    # 树干
    add_rect(slide, x+int(I(0.08*s)), y+int(I(0.16*s)), int(I(0.08*s)), int(I(0.32*s)), C["ink_brown"])
    # 树冠 - 紫灰色圆
    add_oval(slide, x, y, int(I(0.28*s)), int(I(0.22*s)), C["light_gray"])
    # 柿子 - 橙色小圆
    for px, py in [(0.04,0.06), (0.16,0.02), (0.20,0.10)]:
        add_oval(slide, x+int(I(px*s)), y+int(I(py*s)), int(I(0.10*s)), int(I(0.12*s)), C["autumn_amber"])

# ============================================================================
# 鸟类
# ============================================================================
def bird_simple(slide, x, y, scale=1.0):
    """极简鸟 - M形用简单形状"""
    s = scale
    body_c = C["ink_brown"]
    # 身体 - 小椭圆
    add_oval(slide, x, y, int(I(0.14*s)), int(I(0.08*s)), body_c)
    # 翅膀 - 两个小椭圆
    add_oval(slide, x-int(I(0.04*s)), y-int(I(0.04*s)), int(I(0.10*s)), int(I(0.06*s)), body_c)
    add_oval(slide, x+int(I(0.08*s)), y-int(I(0.04*s)), int(I(0.10*s)), int(I(0.06*s)), body_c)

def egret_simple(slide, x, y, scale=1.0):
    """极简白鹭 - 白色长条"""
    s = scale
    # 身体
    add_oval(slide, x, y, int(I(0.12*s)), int(I(0.35*s)), C["frost_white"])
    # 脖子/头
    add_oval(slide, x+int(I(0.02*s)), y-int(I(0.12*s)), int(I(0.10*s)), int(I(0.12*s)), C["frost_white"])
    # 嘴
    add_rect(slide, x+int(I(0.10*s)), y-int(I(0.06*s)), int(I(0.12*s)), int(I(0.03*s)), C["warm_yellow"])

# ============================================================================
# 其他
# ============================================================================
def snowman_simple(slide, x, y, scale=1.0):
    """极简雪人"""
    s = scale
    # 身体 - 两个叠圆
    add_oval(slide, x-int(I(0.04*s)), y+int(I(0.12*s)), int(I(0.28*s)), int(I(0.24*s)), C["frost_white"])
    add_oval(slide, x, y-int(I(0.08*s)), int(I(0.20*s)), int(I(0.20*s)), C["frost_white"])
    # 帽子
    add_rect(slide, x-int(I(0.02*s)), y-int(I(0.20*s)), int(I(0.24*s)), int(I(0.08*s)), C["ink_brown"])
    # 围巾
    add_rect(slide, x, y, int(I(0.20*s)), int(I(0.06*s)), C["soft_coral"])

def moon_simple(slide, x, y, scale=1.0):
    """极简月亮"""
    s = scale
    add_oval(slide, x, y, int(I(0.28*s)), int(I(0.28*s)), C["warm_yellow"])
    # 陨石坑 - 浅色斑点
    add_oval(slide, x+int(I(0.08*s)), y+int(I(0.06*s)), int(I(0.06*s)), int(I(0.06*s)), C["wheat_gold"])
    add_oval(slide, x+int(I(0.16*s)), y+int(I(0.12*s)), int(I(0.04*s)), int(I(0.04*s)), C["wheat_gold"])

def firefly_simple(slide, x, y, scale=1.0):
    """极简萤火虫"""
    s = scale
    # 发光身体
    add_oval(slide, x, y, int(I(0.10*s)), int(I(0.06*s)), C["warm_yellow"])
    # 翅膀
    add_oval(slide, x-int(I(0.06*s)), y-int(I(0.02*s)), int(I(0.10*s)), int(I(0.06*s)), C["sky_mint"])
    add_oval(slide, x+int(I(0.06*s)), y-int(I(0.02*s)), int(I(0.10*s)), int(I(0.06*s)), C["sky_mint"])

def leaf_simple(slide, x, y, scale=1.0, color=None):
    """极简叶子"""
    s = scale
    c = color or C["spring_green"]
    # 叶片 - 椭圆
    add_oval(slide, x, y, int(I(0.15*s)), int(I(0.10*s)), c)
    # 叶柄
    add_rect(slide, x+int(I(0.06*s)), y+int(I(0.08*s)), int(I(0.03*s)), int(I(0.08*s)), C["ink_brown"])

def dragonfly_simple(slide, x, y, scale=1.0):
    """极简蜻蜓"""
    s = scale
    # 身体
    add_rect(slide, x+int(I(0.10*s)), y, int(I(0.04*s)), int(I(0.22*s)), C["ink_brown"])
    # 翅膀 - 四片
    add_oval(slide, x, y+int(I(0.04*s)), int(I(0.12*s)), int(I(0.04*s)), C["rain_blue"])
    add_oval(slide, x+int(I(0.16*s)), y+int(I(0.04*s)), int(I(0.12*s)), int(I(0.04*s)), C["rain_blue"])
    add_oval(slide, x, y+int(I(0.12*s)), int(I(0.10*s)), int(I(0.04*s)), C["rain_blue"])
    add_oval(slide, x+int(I(0.18*s)), y+int(I(0.12*s)), int(I(0.10*s)), int(I(0.04*s)), C["rain_blue"])

def fan_simple(slide, x, y, scale=1.0):
    """极简扇子"""
    s = scale
    # 扇面 - 半圆
    add_oval(slide, x, y, int(I(0.20*s)), int(I(0.15*s)), C["soft_coral"])
    # 扇柄
    add_rect(slide, x+int(I(0.08*s)), y+int(I(0.12*s)), int(I(0.04*s)), int(I(0.15*s)), C["ink_brown"])

def pumpkin_simple(slide, x, y, scale=1.0):
    """极简南瓜"""
    s = scale
    # 瓜体 - 扁椭圆
    add_oval(slide, x, y+int(I(0.06*s)), int(I(0.30*s)), int(I(0.22*s)), C["autumn_amber"])
    # 瓜柄
    add_rect(slide, x+int(I(0.12*s)), y, int(I(0.06*s)), int(I(0.08*s)), C["spring_green"])

def wind_simple(slide, x, y, scale=1.0):
    """极简风/凉风"""
    s = scale
    # 风曲线 - 用三条横线表示
    for i, wy in enumerate([0, 0.08, 0.16]):
        w = int(I((0.20 - i*0.03)*s))
        add_rect(slide, x, y+int(I(wy*s)), w, int(I(0.03*s)), C["light_gray"])

def chrysanthemum_simple(slide, x, y, scale=1.0):
    """极简菊花"""
    s = scale
    # 花瓣 - 多个小椭圆围绕中心
    center_x = x + int(I(0.12*s))
    center_y = y + int(I(0.10*s))
    for a in range(0, 360, 45):
        rad = math.radians(a)
        px = center_x + int(I(0.08*s) * math.cos(rad))
        py = center_y + int(I(0.08*s) * math.sin(rad))
        add_oval(slide, px-int(I(0.04*s)), py-int(I(0.04*s)), int(I(0.10*s)), int(I(0.06*s)), C["flower_pink"])
    # 花蕊
    add_oval(slide, center_x-int(I(0.04*s)), center_y-int(I(0.04*s)), int(I(0.08*s)), int(I(0.08*s)), C["warm_yellow"])
    # 茎
    add_rect(slide, center_x-int(I(0.02*s)), y+int(I(0.16*s)), int(I(0.04*s)), int(I(0.18*s)), C["spring_green"])

def birds_flying_simple(slide, x, y, scale=1.0):
    """极简大雁南飞 - V字形"""
    s = scale
    # 三只鸟 V 字队形
    positions = [(0, 0), (-0.15, 0.12), (0.15, 0.12)]
    for bx, by in positions:
        # 鸟身
        add_oval(slide, x+int(I(bx*s)), y+int(I(by*s)), int(I(0.10*s)), int(I(0.05*s)), C["warm_gray"])
        # 翅膀
        add_oval(slide, x+int(I((bx-0.04)*s)), y+int(I((by-0.02)*s)), int(I(0.06*s)), int(I(0.04*s)), C["warm_gray"])
        add_oval(slide, x+int(I((bx+0.08)*s)), y+int(I((by-0.02)*s)), int(I(0.06*s)), int(I(0.04*s)), C["warm_gray"])

def food_storage_simple(slide, x, y, scale=1.0):
    """极简食物储存/过冬储备"""
    s = scale
    # 仓库/箱子
    add_rect(slide, x, y+int(I(0.08*s)), int(I(0.28*s)), int(I(0.20*s)), C["wheat_gold"])
    # 盖子
    add_oval(slide, x-int(I(0.02*s)), y+int(I(0.04*s)), int(I(0.32*s)), int(I(0.12*s)), C["autumn_amber"])
    # 装饰条纹
    add_rect(slide, x+int(I(0.06*s)), y+int(I(0.12*s)), int(I(0.04*s)), int(I(0.12*s)), C["soft_coral"])
    add_rect(slide, x+int(I(0.18*s)), y+int(I(0.12*s)), int(I(0.04*s)), int(I(0.12*s)), C["soft_coral"])

def pine_tree_simple(slide, x, y, scale=1.0):
    """极简松树/雪松"""
    s = scale
    # 树干
    add_rect(slide, x+int(I(0.10*s)), y+int(I(0.25*s)), int(I(0.08*s)), int(I(0.18*s)), C["ink_brown"])
    # 三层树冠 - 三角形用椭圆近似
    add_oval(slide, x, y+int(I(0.18*s)), int(I(0.28*s)), int(I(0.18*s)), C["spring_green"])
    add_oval(slide, x+int(I(0.02*s)), y+int(I(0.08*s)), int(I(0.24*s)), int(I(0.16*s)), C["spring_green"])
    add_oval(slide, x+int(I(0.04*s)), y-int(I(0.02*s)), int(I(0.20*s)), int(I(0.14*s)), C["spring_green"])

def dumpling_simple(slide, x, y, scale=1.0):
    """极简饺子/汤圆"""
    s = scale
    # 饺子体 - 半月形
    add_oval(slide, x, y, int(I(0.16*s)), int(I(0.12*s)), C["frost_white"])
    # 褶皱 - 小线条
    add_rect(slide, x+int(I(0.06*s)), y+int(I(0.02*s)), int(I(0.02*s)), int(I(0.08*s)), C["light_gray"])
    add_rect(slide, x+int(I(0.10*s)), y+int(I(0.02*s)), int(I(0.02*s)), int(I(0.08*s)), C["light_gray"])

def plum_blossom_simple(slide, x, y, scale=1.0):
    """极简梅花"""
    s = scale
    # 五瓣花
    c = rgb(0xD8, 0x70, 0x80)  # 梅红色
    center_x = x + int(I(0.10*s))
    center_y = y + int(I(0.08*s))
    for a in range(0, 360, 72):
        rad = math.radians(a)
        px = center_x + int(I(0.06*s) * math.cos(rad))
        py = center_y + int(I(0.06*s) * math.sin(rad))
        add_oval(slide, px-int(I(0.04*s)), py-int(I(0.04*s)), int(I(0.08*s)), int(I(0.08*s)), c)
    # 花蕊
    add_oval(slide, center_x-int(I(0.02*s)), center_y-int(I(0.02*s)), int(I(0.04*s)), int(I(0.04*s)), C["warm_yellow"])
    # 枝干
    add_rect(slide, center_x-int(I(0.02*s)), y+int(I(0.12*s)), int(I(0.04*s)), int(I(0.15*s)), C["ink_brown"])

def ice_simple(slide, x, y, scale=1.0):
    """极简冰块/结冰"""
    s = scale
    # 冰块 - 浅蓝色矩形
    add_rect(slide, x, y+int(I(0.06*s)), int(I(0.20*s)), int(I(0.14*s)), rgb(0xC8, 0xE0, 0xF0))
    # 冰面反光
    add_oval(slide, x+int(I(0.04*s)), y+int(I(0.08*s)), int(I(0.08*s)), int(I(0.04*s)), rgb(0xE8, 0xF4, 0xF8))
