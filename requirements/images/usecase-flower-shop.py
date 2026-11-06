# -*- coding: utf-8 -*-
"""绘制“鲜花预订与交易平台”UML 用例图。

依赖 Pillow；在 Windows 下使用微软雅黑与 Segoe UI 字体。
运行后会在本文件同目录生成 usecase-flower-shop.png。
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ----------------------------------------------------------------------------
# 基础画布：先按 2 倍尺寸绘制，最后缩小以获得平滑边缘。
# ----------------------------------------------------------------------------
W, H = 1700, 1400
S = 2
OUT_SCALE = 1.5

FONT_DIR = r"C:\Windows\Fonts"
FONT_CN = FONT_DIR + r"\msyh.ttc"
FONT_CN_BOLD = FONT_DIR + r"\msyhbd.ttc"
FONT_EN = FONT_DIR + r"\segoeui.ttf"
FONT_EN_SEMI = FONT_DIR + r"\seguisb.ttf"

INK = (29, 49, 69)
MUTED = (105, 122, 139)
SOFT = (138, 153, 168)
HAIRLINE = (219, 227, 235)
ACTOR = (45, 68, 91)
ASSOC = (122, 141, 158)

CORE_FILL = (233, 243, 252)
CORE_LINE = (55, 113, 160)
SUPPORT_FILL = (250, 246, 237)
SUPPORT_LINE = (182, 153, 105)
INCLUDE_FILL = (239, 247, 241)
INCLUDE_LINE = (111, 151, 121)
CORAL = (198, 108, 89)


def sc(v):
    return int(round(v * S))


def font(path, size, index=0):
    return ImageFont.truetype(path, int(size * S), index=index)


F_TITLE = font(FONT_CN_BOLD, 46)
F_SUB = font(FONT_CN, 17)
F_META = font(FONT_EN, 10)
F_META2 = font(FONT_CN, 12)
F_BADGE = font(FONT_CN_BOLD, 11)
F_BOUND = font(FONT_CN_BOLD, 21)
F_BOUND_META = font(FONT_EN, 8)
F_UC_ID = font(FONT_EN_SEMI, 10)
F_UC_NAME = font(FONT_CN_BOLD, 17.5)
F_UC_NAME_S = font(FONT_CN_BOLD, 16.5)
F_INC = font(FONT_CN_BOLD, 14)
F_ACTOR = font(FONT_CN_BOLD, 19)
F_ABSTRACT = font(FONT_CN, 11)
F_INCLUDE_LABEL = font(FONT_EN_SEMI, 10.5)
F_TINY = font(FONT_CN, 10.5)
F_LEGEND = font(FONT_CN, 12)
F_LEGEND_B = font(FONT_CN_BOLD, 12)
F_NOTE = font(FONT_CN, 12)

img = Image.new("RGB", (W * S, H * S), (248, 250, 253))
draw = ImageDraw.Draw(img)

# 背景：由冷白到暖白的极浅渐变
grad = Image.new("RGB", (1, H * S))
top = (247, 250, 253)
bot = (253, 251, 247)
for yy in range(H * S):
    t = yy / max(1, H * S - 1)
    grad.putpixel(
        (0, yy),
        (
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t),
        ),
    )
img = grad.resize((W * S, H * S))
draw = ImageDraw.Draw(img)


def P(x, y):
    return (sc(x), sc(y))


def line(p1, p2, fill, width=2.0, joint="curve"):
    draw.line([P(*p1), P(*p2)], fill=fill, width=max(1, sc(width)), joint=joint)


def rounded(box, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(
        [sc(x1), sc(y1), sc(x2), sc(y2)],
        radius=sc(radius),
        fill=fill,
        outline=outline,
        width=max(1, sc(width)),
    )


def txt(x, y, s, fnt, fill, anchor="la"):
    draw.text(P(x, y), s, font=fnt, fill=fill, anchor=anchor)


def ellipse(cx, cy, rx, ry, fill=None, outline=None, width=1):
    draw.ellipse(
        [sc(cx - rx), sc(cy - ry), sc(cx + rx), sc(cy + ry)],
        fill=fill,
        outline=outline,
        width=max(1, sc(width)),
    )


# ----------------------------------------------------------------------------
# 页眉
# ----------------------------------------------------------------------------
# 左侧珊瑚色竖条
draw.rounded_rectangle(
    [sc(55), sc(62), sc(62), sc(139)],
    radius=sc(3),
    fill=CORAL,
)

txt(82, 55, "REQUIREMENTS  /  USE-CASE MODEL", F_BADGE, (135, 112, 98))
txt(80, 76, "用例图", F_TITLE, INK)
txt(84, 136, "鲜花预订与交易平台  ·  需求分析 v0.2", F_SUB, MUTED)

txt(1645, 80, "UML USE CASE DIAGRAM", F_META, (150, 163, 176), anchor="ra")
txt(1645, 102, "2026.11  /  SYSTEM ANALYSIS", F_META, (150, 163, 176), anchor="ra")

line((55, 172), (1645, 172), HAIRLINE, 1.0)

# ----------------------------------------------------------------------------
# 系统边界与阴影
# ----------------------------------------------------------------------------
bx1, by1, bx2, by2 = 300, 320, 1400, 1090

shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle(
    [sc(bx1), sc(by1 + 9), sc(bx2), sc(by2 + 14)],
    radius=sc(24),
    fill=(29, 48, 68, 28),
)
shadow = shadow.filter(ImageFilter.GaussianBlur(sc(15)))
img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
draw = ImageDraw.Draw(img)

rounded((bx1, by1, bx2, by2), 24, fill=(255, 255, 255), outline=(198, 211, 224), width=2.2)

# 边界标题
txt(330, 348, "鲜花预订与交易平台系统", F_BOUND, (37, 65, 89))
txt(1370, 355, "SYSTEM BOUNDARY", F_BOUND_META, (160, 174, 187), anchor="ra")
line((330, 388), (1370, 388), (234, 240, 246), 1.0)

# ----------------------------------------------------------------------------
# 用例定义
# ----------------------------------------------------------------------------
USE_CASES = [
    # id, name, cx, cy, w, h, kind
    ("UC-05", "登录与角色识别", 620, 455, 250, 74, "support"),
    (None, "查看/修改个人信息", 965, 455, 260, 74, "support"),

    ("UC-02", "检索花束", 500, 550, 230, 74, "core"),
    ("UC-06", "查看花束详情", 500, 642, 230, 74, "support"),
    ("UC-03", "预订下单", 500, 734, 230, 74, "core"),
    ("UC-04", "取消订单", 500, 826, 230, 74, "core"),
    ("UC-08", "我的订单", 500, 918, 230, 74, "support"),

    ("UC-01", "发布花束", 620, 1010, 230, 74, "core"),
    ("UC-07", "管理我的花束", 880, 1010, 230, 74, "support"),
    (None, "查看本店订单", 1130, 1010, 230, 74, "support"),

    (None, "账号管理", 1200, 560, 250, 74, "support"),
    (None, "查看全部花束与订单", 1200, 660, 270, 74, "support"),
    (None, "强制下架违规花束", 1200, 760, 260, 74, "support"),

    (None, "校验并扣减可预订数量", 830, 735, 250, 58, "include"),
    (None, "回补可预订数量", 830, 845, 220, 56, "include"),
]

UC = {}
for item in USE_CASES:
    uid, name, cx, cy, w, h, kind = item
    UC[uid or name] = {
        "id": uid,
        "name": name,
        "cx": cx,
        "cy": cy,
        "w": w,
        "h": h,
        "kind": kind,
    }


def edge_point(uc, tx, ty):
    """从椭圆中心指向目标点，返回椭圆边界上的交点。"""
    dx = tx - uc["cx"]
    dy = ty - uc["cy"]
    rx = uc["w"] / 2.0
    ry = uc["h"] / 2.0
    denom = math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
    if denom == 0:
        return (uc["cx"], uc["cy"])
    return (uc["cx"] + dx / denom, uc["cy"] + dy / denom)


# ----------------------------------------------------------------------------
# 泛化路径（画在角色后面）
# ----------------------------------------------------------------------------
def polyline(points, fill, width=2.1, radius=0):
    for a, b in zip(points[:-1], points[1:]):
        line(a, b, fill, width)
    if radius > 0:
        for p in points[1:-1]:
            ellipse(p[0], p[1], radius / 2.0, radius / 2.0, fill=fill)


def hollow_triangle(tip, back, fill=(255, 255, 255), outline=SOFT, width=1.8, size=15):
    tx, ty = tip
    bx, by = back
    ang = math.atan2(ty - by, tx - bx)
    half = size * 0.62
    # 底边中点
    mx = tx - math.cos(ang) * size
    my = ty - math.sin(ang) * size
    # 底边两端
    px = math.cos(ang + math.pi / 2) * half
    py = math.sin(ang + math.pi / 2) * half
    tri = [
        P(tx, ty),
        P(mx + px, my + py),
        P(mx - px, my - py),
    ]
    draw.polygon(tri, fill=fill)
    draw.line(tri + [tri[0]], fill=outline, width=max(1, sc(width)), joint="curve")


GEN = (176, 187, 198)

# 顾客 -> 用户（从左侧接入）
cust_gen = [(105, 734), (220, 734), (220, 242), (790, 242), (818, 242)]
polyline(cust_gen, GEN, 1.6, 0)
hollow_triangle((818, 242), (790, 242), size=15, outline=(150, 164, 177), width=1.5)

# 商家 -> 用户（从下方接入）
merch_gen = [(840, 1170), (260, 1170), (260, 262), (850, 262), (850, 253)]
polyline(merch_gen, GEN, 1.6, 0)
hollow_triangle((850, 253), (850, 262), size=15, outline=(150, 164, 177), width=1.5)

# 管理员 -> 用户（从右侧接入，绕开管理员的关联线）
admin_gen = [(1552, 560), (1585, 560), (1585, 242), (910, 242), (882, 242)]
polyline(admin_gen, GEN, 1.6, 0)
hollow_triangle((882, 242), (910, 242), size=15, outline=(150, 164, 177), width=1.5)

# 泛化关系说明（外围细线容易被误读为边框）
txt(500, 226, "角色泛化", F_TINY, (145, 159, 172))

# ----------------------------------------------------------------------------
# 角色关联线
# ----------------------------------------------------------------------------
def associate(ax, ay, uc):
    ex, ey = edge_point(uc, ax, ay)
    line((ax, ay), (ex, ey), ASSOC, 2.2)


# 用户（抽象）共享登录与个人信息
for key in ["UC-05", "查看/修改个人信息"]:
    associate(850, 228, UC[key])

# 顾客
for key in ["UC-02", "UC-06", "UC-03", "UC-04", "UC-08"]:
    associate(140, 734, UC[key])

# 商家
for key in ["UC-01", "UC-07", "查看本店订单"]:
    associate(880, 1170, UC[key])

# 管理员
for key in ["账号管理", "查看全部花束与订单", "强制下架违规花束"]:
    associate(1530, 560, UC[key])

# ----------------------------------------------------------------------------
# include 关系
# ----------------------------------------------------------------------------
INCLUDE = (109, 148, 119)


def dashed(p1, p2, fill=INCLUDE, width=1.8, dash=8, gap=6):
    x1, y1 = p1
    x2, y2 = p2
    total = math.hypot(x2 - x1, y2 - y1)
    if total == 0:
        return
    ux, uy = (x2 - x1) / total, (y2 - y1) / total
    d = 0.0
    while d < total:
        e = min(d + dash, total)
        line((x1 + ux * d, y1 + uy * d), (x1 + ux * e, y1 + uy * e), fill, width)
        d = e + gap


def open_arrow(tip, prev, fill=INCLUDE, width=1.8, size=11):
    tx, ty = tip
    px, py = prev
    ang = math.atan2(ty - py, tx - px)
    for delta in (math.radians(27), -math.radians(27)):
        qx = tx - math.cos(ang + delta) * size
        qy = ty - math.sin(ang + delta) * size
        line((tx, ty), (qx, qy), fill, width)


# 预订下单 include 校验并扣减
uc_book = UC["UC-03"]
uc_inc1 = UC["校验并扣减可预订数量"]
start = edge_point(uc_book, uc_inc1["cx"], uc_inc1["cy"])
end = edge_point(uc_inc1, uc_book["cx"], uc_book["cy"])
dashed(start, end)
open_arrow(end, start)
# 标签
mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
label = "«include»"
bb = draw.textbbox((0, 0), label, font=F_INCLUDE_LABEL)
tw, th = (bb[2] - bb[0]) / S, (bb[3] - bb[1]) / S
draw.rounded_rectangle(
    [sc(mx - tw / 2 - 5), sc(my - th - 9), sc(mx + tw / 2 + 5), sc(my - 4)],
    radius=sc(4),
    fill=(255, 255, 255),
)
txt(mx, my - 8, label, F_INCLUDE_LABEL, INCLUDE, anchor="mm")

# 取消订单 include 回补
uc_cancel = UC["UC-04"]
uc_inc2 = UC["回补可预订数量"]
start2 = edge_point(uc_cancel, uc_inc2["cx"], uc_inc2["cy"])
end2 = edge_point(uc_inc2, uc_cancel["cx"], uc_cancel["cy"])
dashed(start2, end2)
open_arrow(end2, start2)
mx2, my2 = (start2[0] + end2[0]) / 2, (start2[1] + end2[1]) / 2
bb2 = draw.textbbox((0, 0), label, font=F_INCLUDE_LABEL)
tw2, th2 = (bb2[2] - bb2[0]) / S, (bb2[3] - bb2[1]) / S
draw.rounded_rectangle(
    [sc(mx2 - tw2 / 2 - 5), sc(my2 - th2 - 10), sc(mx2 + tw2 / 2 + 5), sc(my2 - 5)],
    radius=sc(4),
    fill=(255, 255, 255),
)
txt(mx2, my2 - 9, label, F_INCLUDE_LABEL, INCLUDE, anchor="mm")

# ----------------------------------------------------------------------------
# 用例阴影
# ----------------------------------------------------------------------------
uc_shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
usd = ImageDraw.Draw(uc_shadow)
for uc in UC.values():
    usd.ellipse(
        [
            sc(uc["cx"] - uc["w"] / 2 + 3),
            sc(uc["cy"] - uc["h"] / 2 + 5),
            sc(uc["cx"] + uc["w"] / 2 + 3),
            sc(uc["cy"] + uc["h"] / 2 + 5),
        ],
        fill=(31, 50, 69, 20),
    )
uc_shadow = uc_shadow.filter(ImageFilter.GaussianBlur(sc(5)))
img = Image.alpha_composite(img.convert("RGBA"), uc_shadow).convert("RGB")
draw = ImageDraw.Draw(img)

# ----------------------------------------------------------------------------
# 绘制用例
# ----------------------------------------------------------------------------
for uc in UC.values():
    kind = uc["kind"]
    if kind == "core":
        fill, outline, lw = CORE_FILL, CORE_LINE, 2.8
        # 外侧浅色描边，强调核心业务
        ellipse(uc["cx"], uc["cy"], uc["w"] / 2 + 3.5, uc["h"] / 2 + 3.5,
                fill=None, outline=(224, 236, 247), width=2.0)
    elif kind == "support":
        fill, outline, lw = SUPPORT_FILL, SUPPORT_LINE, 2.0
    else:
        fill, outline, lw = INCLUDE_FILL, INCLUDE_LINE, 1.8

    ellipse(uc["cx"], uc["cy"], uc["w"] / 2, uc["h"] / 2, fill=fill, outline=outline, width=lw)

    if uc["id"]:
        txt(uc["cx"], uc["cy"] - 15, uc["id"], F_UC_ID, (112, 133, 151), anchor="mm")
        txt(uc["cx"], uc["cy"] + 12, uc["name"], F_UC_NAME, (35, 60, 82), anchor="mm")
    elif kind == "include":
        txt(uc["cx"], uc["cy"], uc["name"], F_INC, (49, 92, 64), anchor="mm")
    else:
        txt(uc["cx"], uc["cy"], uc["name"], F_UC_NAME_S, (58, 67, 77), anchor="mm")

# ----------------------------------------------------------------------------
# 角色
# ----------------------------------------------------------------------------
def actor(x, y, color=ACTOR, lw=3.2):
    r = 11
    cy = y - 38
    # 头
    draw.ellipse(
        [sc(x - r), sc(cy - r), sc(x + r), sc(cy + r)],
        fill=(255, 255, 255),
        outline=color,
        width=max(1, sc(lw)),
    )
    # 躯干
    line((x, cy + r), (x, y + 2), color, lw)
    # 手臂
    line((x - 20, y - 15), (x + 20, y - 15), color, lw)
    # 腿
    line((x, y + 2), (x - 14, y + 28), color, lw)
    line((x, y + 2), (x + 14, y + 28), color, lw)


# 用户（抽象）
actor(850, 225)
txt(895, 190, "用户", F_ACTOR, INK)
txt(896, 220, "«抽象»", F_ABSTRACT, (129, 145, 160))

# 顾客
actor(140, 734)
txt(140, 786, "顾客", F_ACTOR, INK, anchor="mm")

# 商家
actor(880, 1170)
txt(880, 1222, "商家", F_ACTOR, INK, anchor="mm")

# 管理员
actor(1530, 560)
txt(1530, 612, "管理员", F_ACTOR, INK, anchor="mm")

# ----------------------------------------------------------------------------
# 图例
# ----------------------------------------------------------------------------
legend_y = 1292
line((330, 1248), (1370, 1248), (229, 236, 243), 1.0)
txt(330, 1270, "图例", F_LEGEND_B, (93, 112, 130))

# 核心
draw.ellipse([sc(390), sc(legend_y - 10), sc(424), sc(legend_y + 10)], fill=CORE_FILL, outline=CORE_LINE, width=max(1, sc(1.8)))
txt(434, legend_y, "核心业务用例", F_LEGEND, (82, 99, 116), anchor="lm")

# 支撑
draw.ellipse([sc(575), sc(legend_y - 10), sc(609), sc(legend_y + 10)], fill=SUPPORT_FILL, outline=SUPPORT_LINE, width=max(1, sc(1.8)))
txt(619, legend_y, "支撑用例", F_LEGEND, (82, 99, 116), anchor="lm")

# include
dashed((700, legend_y), (752, legend_y), INCLUDE, 1.6, 7, 5)
open_arrow((752, legend_y), (700, legend_y), size=9)
txt(764, legend_y, "«include» 包含关系", F_LEGEND, (82, 99, 116), anchor="lm")

# 泛化
line((985, legend_y), (1020, legend_y), GEN, 1.8)
hollow_triangle((1035, legend_y), (1018, legend_y), size=13)
txt(1046, legend_y, "角色泛化", F_LEGEND, (82, 99, 116), anchor="lm")

# 抽象角色
txt(1168, legend_y, "«抽象» 抽象角色", F_LEGEND, (82, 99, 116), anchor="lm")

# 说明
txt(
    330,
    1335,
    "注：顾客、商家与管理员均泛化为「用户」，共享「登录与角色识别」及「查看/修改个人信息」；管理员不参与交易，仅承担账号与内容管理。",
    F_NOTE,
    (116, 132, 147),
)

# ----------------------------------------------------------------------------
# 输出
# ----------------------------------------------------------------------------
out_size = (int(W * OUT_SCALE), int(H * OUT_SCALE))
img = img.resize(out_size, Image.Resampling.LANCZOS)
out = Path(__file__).with_name("usecase-flower-shop.png")
img.save(out, "PNG", optimize=True)
print(out, img.size)
