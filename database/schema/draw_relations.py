# -*- coding: utf-8 -*-
"""绘制“鲜花预订与交易平台”表间关系图（T8 · 逻辑设计 · 全部实际表）。

依赖 Pillow；Windows 下使用微软雅黑。运行后在同目录生成 relations.png。
连线语义：由子表外键(FK)指向被引用表主键(PK)，线上标注基数。
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------- 画布 ----------
W, H = 2560, 2020
S = 2
OUT_SCALE = 1.0

FONT_DIR = r"C:\Windows\Fonts"
F_CN = FONT_DIR + r"\msyh.ttc"
F_CN_B = FONT_DIR + r"\msyhbd.ttc"

INK = (29, 49, 69)
MUTED = (105, 122, 139)
HAIR = (214, 222, 232)
BG = (248, 250, 252)

# 域配色
C_USER = (37, 99, 235)      # 用户域 蓝
C_USER_H = (219, 234, 254)
C_FLW = (5, 150, 105)       # 花束域 绿
C_FLW_H = (209, 250, 229)
C_ORD = (217, 119, 6)       # 订单域 橙
C_ORD_H = (254, 243, 199)
C_LOG = (124, 58, 237)      # 流水域 紫
C_LOG_H = (237, 233, 254)
C_ROLE = (100, 116, 139)    # role 字典表 灰
C_ROLE_H = (241, 245, 249)

PK_C = (180, 83, 9)         # PK 徽标 琥珀
FK_C = (37, 99, 235)        # FK 徽标 蓝
UK_C = (5, 150, 105)        # UK 徽标 绿

font_cache = {}
def F(size, bold=False):
    key = (size, bold)
    if key not in font_cache:
        font_cache[key] = ImageFont.truetype(F_CN_B if bold else F_CN, size * S)
    return font_cache[key]

img = Image.new("RGB", (W * S, H * S), BG)
dr = ImageDraw.Draw(img, "RGBA")

# ---------- 表定义：(键, 域色头, 域色底, x, y, w, [(字段, 徽标), ...]) ----------
T = {}
def table(key, color, head_bg, x, y, w, fields):
    h = 50 + len(fields) * 34 + 14
    T[key] = dict(x=x, y=y, w=w, h=h, color=color, head_bg=head_bg, fields=fields)
    return T[key]

table("role", C_ROLE, C_ROLE_H, 120, 150, 400, [
    ("id", "PK"), ("code", "UK"), ("name", ""), ("description", ""),
])
table("user", C_USER, C_USER_H, 760, 110, 560, [
    ("id", "PK"), ("username", "UK"), ("role_id", "FK"), ("status", ""), ("created_at", ""),
])
table("category", C_FLW, C_FLW_H, 1900, 110, 460, [
    ("id", "PK"), ("name", "UK"), ("sort_no", ""),
])
table("seller_profile", C_USER, C_USER_H, 120, 570, 460, [
    ("user_id", "PK·FK"), ("shop_name", ""), ("pickup_address", ""),
])
table("bouquet", C_FLW, C_FLW_H, 1560, 490, 480, [
    ("id", "PK"), ("seller_id", "FK"), ("category_id", "FK"), ("name", ""),
    ("price", ""), ("stock_qty", ""), ("status", ""), ("version", ""),
])
table("bouquet_image", C_FLW, C_FLW_H, 2320, 490, 240, [
    ("id", "PK"), ("bouquet_id", "FK"), ("image_url", ""), ("sort_no", ""),
])
table("orders", C_ORD, C_ORD_H, 700, 960, 560, [
    ("id", "PK"), ("user_id", "FK"), ("status", ""), ("idempotency_key", "UK"),
    ("delivery_date", ""), ("cancelled_at", ""),
])
table("order_item", C_ORD, C_ORD_H, 2100, 1020, 420, [
    ("id", "PK"), ("order_id", "FK"), ("bouquet_id", "FK"), ("quantity", ""),
    ("unit_price", ""), ("amount", ""),
])
table("order_status_log", C_LOG, C_LOG_H, 110, 1250, 470, [
    ("id", "PK"), ("order_id", "FK"), ("from_status", ""), ("to_status", ""),
    ("user_id", "FK"), ("created_at", ""),
])
table("stock_change", C_LOG, C_LOG_H, 830, 1420, 540, [
    ("id", "PK"), ("bouquet_id", "FK"), ("order_id", "FK·可空"), ("change_type", ""),
    ("quantity_delta", ""), ("before_qty", ""), ("after_qty", ""), ("user_id", "FK"),
    ("created_at", ""),
])

def anchor(tkey, side, ratio=0.5):
    t = T[tkey]
    if side == "top":    return (t["x"] + t["w"] * ratio, t["y"])
    if side == "bottom": return (t["x"] + t["w"] * ratio, t["y"] + t["h"])
    if side == "left":   return (t["x"], t["y"] + t["h"] * ratio)
    if side == "right":  return (t["x"] + t["w"], t["y"] + t["h"] * ratio)

def draw_tables():
    for key, t in T.items():
        x, y, w, h = t["x"], t["y"], t["w"], t["h"]
        # 阴影
        dr.rounded_rectangle([x*S+6*S, y*S+6*S, (x+w)*S+6*S, (y+h)*S+6*S],
                             radius=10*S, fill=(0, 0, 0, 28))
        # 表体
        dr.rounded_rectangle([x*S, y*S, (x+w)*S, (y+h)*S], radius=10*S,
                             fill=(255, 255, 255, 255), outline=t["color"]+ (255,), width=2*S)
        # 表头
        dr.rounded_rectangle([x*S, y*S, (x+w)*S, (y+44)*S], radius=10*S, fill=t["color"]+(235,))
        dr.rectangle([x*S, (y+36)*S, (x+w)*S, (y+44)*S], fill=t["color"]+(235,))
        dr.text((x*S+14*S, (y+8)*S), key, font=F(26, True), fill=(255, 255, 255, 255))
        # 字段
        fy = y + 52
        for fname, badge in t["fields"]:
            badge_txt, badge_col = {
                "PK": ("PK", PK_C), "FK": ("FK", FK_C), "UK": ("UK", UK_C),
                "PK·FK": ("PK FK", PK_C), "FK·可空": ("FK 可空", FK_C), "": ("", None),
            }.get(badge, ("", None))
            dr.text((x*S+14*S, fy*S), fname, font=F(19), fill=INK + (255,))
            if badge_txt:
                bw = dr.textlength(badge_txt, font=F(14, True)) / S + 10
                bx = x + w - bw - 12
                dr.rounded_rectangle([bx*S, (fy+1)*S, (bx+bw)*S, (fy+24)*S],
                                     radius=6*S, fill=badge_col + (36,))
                dr.text(((bx+5)*S, (fy+2)*S), badge_txt, font=F(14, True), fill=badge_col + (255,))
            fy += 34
        # 底部分隔线
        dr.line([x*S, (y+h-2)*S, (x+w)*S, (y+h-2)*S], fill=t["color"]+(120,), width=2*S)

def arrow(p_from, p_to, color, label=None, lab_t=0.5, dash=False):
    """折线连接：p_from 为子表出发点，p_to 为父表落点（箭头端）"""
    pts = [p_from] + [p for p in p_to[1]] + [p_to[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if dash:
            _dash_line(a, b, color + (230,), 2 * S, dash=12 * S, gap=8 * S)
        else:
            dr.line([a[0]*S, a[1]*S, b[0]*S, b[1]*S], fill=color + (230,), width=2*S)
    # 箭头（指向父表）
    a, b = pts[-2], pts[-1]
    ang = math.atan2(b[1]-a[1], b[0]-a[0])
    L = 14 * S
    p1 = (b[0] - L*math.cos(ang - 0.42), b[1] - L*math.sin(ang - 0.42))
    p2 = (b[0] - L*math.cos(ang + 0.42), b[1] - L*math.sin(ang + 0.42))
    dr.polygon([b[0]*S, b[1]*S, p1[0]*S, p1[1]*S, p2[0]*S, p2[1]*S], fill=color + (255,))
    # 基数标签
    if label:
        mx, my = pts[0][0] + (pts[-1][0]-pts[0][0]) * lab_t, pts[0][1] + (pts[-1][1]-pts[0][1]) * lab_t
        tw = dr.textlength(label, font=F(15, True)) / S
        dr.rounded_rectangle([(mx-tw/2-6)*S, (my-12)*S, (mx+tw/2+6)*S, (my+12)*S],
                             radius=5*S, fill=(255, 255, 255, 230), outline=color+(180,), width=1*S)
        dr.text(((mx-tw/2)*S, (my-9)*S), label, font=F(15, True), fill=color + (255,))

def _dash_line(a, b, fill, width, dash=12, gap=8):
    x1, y1, x2, y2 = a[0], a[1], b[0], b[1]
    dist = math.hypot(x2-x1, y2-y1)
    if dist == 0:
        return
    ux, uy = (x2-x1)/dist, (y2-y1)/dist
    d = 0
    while d < dist:
        e = min(d + dash, dist)
        dr.line([(x1+ux*d)*S, (y1+uy*d)*S, (x1+ux*e)*S, (y1+uy*e)*S], fill=fill, width=width)
        d = e + gap

# ---------- 连线 ----------
# （路径点序列，颜色，基数标签，标签位置）
cons = [
    # 用户域
    ([(anchor("user", "left", 0.35)), (anchor("role", "right", 0.5))], C_USER, "N:1", 0.55),          # user.role_id→role
    ([(anchor("seller_profile", "right", 0.5)), ((650, 640)), ((650, 300)), (anchor("user", "left", 0.75))], C_USER, "1:0..1", 0.3),  # seller_profile.user_id→user
    # 花束域
    ([(anchor("bouquet", "top", 0.28)), ((1750, 405)), (anchor("user", "right", 0.75))], C_FLW, "N:1", 0.45),   # bouquet.seller_id→user
    ([(anchor("bouquet", "top", 0.72)), ((1985, 480)), (anchor("category", "bottom", 0.5))], C_FLW, "N:1", 0.5),  # bouquet.category_id→category
    ([(anchor("bouquet_image", "left", 0.5)), (anchor("bouquet", "right", 0.72))], C_FLW, "N:1", 0.5),          # bouquet_image.bouquet_id→bouquet
    # 订单域
    ([(anchor("orders", "top", 0.25)), (anchor("user", "bottom", 0.35))], C_ORD, "N:1", 0.5),                    # orders.user_id→user
    ([(anchor("order_item", "left", 0.45)), (anchor("orders", "right", 0.6))], C_ORD, "本期 1:1", 0.5),          # order_item.order_id→orders
    ([(anchor("order_item", "top", 0.4)), ((2290, 920)), (anchor("bouquet", "bottom", 0.72))], C_ORD, "N:1", 0.5),  # order_item.bouquet_id→bouquet
    # 流水域
    ([(anchor("order_status_log", "top", 0.5)), ((345, 1215)), (anchor("orders", "bottom", 0.15))], C_LOG, "N:1", 0.45),  # log.order_id→orders
    ([(anchor("order_status_log", "left", 0.35)), ((58, 1337)), ((58, 262)), (anchor("user", "left", 0.9))], C_LOG, "N:1", 0.35),  # log.user_id→user
    ([(anchor("stock_change", "top", 0.45)), (anchor("orders", "bottom", 0.55))], C_LOG, "N:1（可空）", 0.45),     # stock_change.order_id→orders
    ([(anchor("stock_change", "right", 0.35)), ((1810, 1540)), (anchor("bouquet", "bottom", 0.42))], C_LOG, "N:1", 0.5),  # stock_change.bouquet_id→bouquet
    ([(anchor("stock_change", "left", 0.6)), ((800, 1600)), ((700, 1500)), ((700, 1330)), (anchor("user", "bottom", 0.6))], C_LOG, "N:1（可空）", 0.3),  # stock_change.user_id→user
]

# ---------- 绘制顺序：先连线，再压表 ----------
# 标题
dr.text((W*S/2 - dr.textlength("鲜花预订与交易平台 —— 表间关系图（逻辑设计 · 全部实际表）", font=F(40, True))/2*S,
         26*S), "鲜花预订与交易平台 —— 表间关系图（逻辑设计 · 全部实际表）",
        font=F(40, True), fill=INK + (255,))
sub = "T8 · 软件工程导论实验二 · 第 25 组 ｜ 绘制：林伟翔 ｜ v0.1 · 2026-11-18 ｜ 主外键 BIGINT UNSIGNED（D-01，role.id 例外 TINYINT）｜ 箭头：外键 → 被引用主键"
dr.text((W*S/2 - dr.textlength(sub, font=F(19))/2*S, 88*S), sub, font=F(19), fill=MUTED + (255,))

for pts, color, label, lab_t in cons:
    arrow(pts[0], (pts[-1], pts[1:-1]), color, label, lab_t)

draw_tables()

# ---------- 图例 ----------
lg_x, lg_y = 120, 1815
dr.rounded_rectangle([lg_x*S, lg_y*S, (lg_x+1300)*S, (lg_y+170)*S], radius=10*S,
                     fill=(255, 255, 255, 240), outline=HAIR + (255,), width=2*S)
dr.text(((lg_x+16)*S, (lg_y+10)*S), "图例", font=F(20, True), fill=INK + (255,))
legend = [
    (C_USER, "用户与角色域（庞华杰）"), (C_FLW, "花束与库存域（庞延新）"),
    (C_ORD, "订单域（何奕佳）"), (C_LOG, "订单状态与库存流水域（林伟翔）"),
]
for i, (c, txt) in enumerate(legend):
    lx = lg_x + 16 + (i % 2) * 620
    ly = lg_y + 46 + (i // 2) * 40
    dr.rounded_rectangle([lx*S, ly*S, (lx+26)*S, (ly+26)*S], radius=5*S, fill=c+(255,))
    dr.text(((lx+36)*S, (ly+2)*S), txt, font=F(17), fill=INK + (255,))
dr.text((lg_x*S, (lg_y+128)*S),
        "PK=主键  FK=外键  UK=唯一键 ｜ seller_profile 为 1:0..1（PK=FK）｜ order_item 本期一单一花束（UNIQUE order_id）",
        font=F(15), fill=MUTED + (255,))
dr.text((lg_x*S, (lg_y+150)*S),
        "stock_change.order_id 可空，且 UNIQUE(order_id, change_type) 保证取消仅回补一次；全部外键 ON DELETE RESTRICT，主外键 BIGINT UNSIGNED（D-01，role.id 例外 TINYINT）",
        font=F(15), fill=MUTED + (255,))

# ---------- 输出 ----------
img = img.resize((int(W * S * OUT_SCALE), int(H * S * OUT_SCALE)), Image.LANCZOS)
out = Path(__file__).with_name("relations.png")
img.save(out)
print("已生成:", out, img.size)
