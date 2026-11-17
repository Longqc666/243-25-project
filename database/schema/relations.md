# 表间关系图说明（T8 · 逻辑设计 · 全部实际表）

> 实验二 · 数据库设计 ｜ 主责人：林伟翔（绘制与统稿）｜ 版本 v0.1 · 2026-11-18
> 依据：[er/domain-order-status.md](../er/domain-order-status.md)、[er/domain-order.md](../er/domain-order.md)、[er/domain-bouquet.md](../er/domain-bouquet.md)、[schema/user.md](schema/user.md)（T2～T7 四域字典）及组长总体 ER 图（[er/er-overall.md](../er/er-overall.md)）
> 图：[relations.png](relations.png)（5120×4040），由 [draw_relations.py](draw_relations.py) 生成，可复现

## 一、表清单（10 张，全部实际表）

| 域 | 表 | 主键 | 主外键类型 |
|---|---|---|---|
| 用户与角色域（庞华杰） | user | id | BIGINT UNSIGNED |
| 〃 | role | id | **TINYINT UNSIGNED**（约定 1 的唯一例外，见第四节） |
| 〃 | seller_profile | user_id | BIGINT UNSIGNED（PK=FK，1:0..1） |
| 花束与库存域（庞延新） | category | id | BIGINT UNSIGNED |
| 〃 | bouquet | id | BIGINT UNSIGNED |
| 〃 | bouquet_image | id | BIGINT UNSIGNED |
| 订单域（何奕佳） | orders | id | BIGINT UNSIGNED |
| 〃 | order_item | id | BIGINT UNSIGNED |
| 订单状态与库存流水域（林伟翔） | order_status_log | id | BIGINT UNSIGNED |
| 〃 | stock_change | id | BIGINT UNSIGNED |

类型统一依据统稿决定 D-01（2026-11-17）：主外键统一 BIGINT UNSIGNED，`role.id` 例外（TINYINT UNSIGNED，仅 3 行字典表、无跨域引用）。

## 二、外键连线清单（13 条，与图逐一对应）

| # | 子表.外键 | → 父表.主键 | 基数 | 说明 | 来源 |
|---|---|---|---|---|---|
| 1 | user.role_id | role.id | N:1 | 角色必须存在；role.id 为 TINYINT 例外 | B-03；用户域字典 |
| 2 | seller_profile.user_id | user.id | **1:0..1** | PK=FK，一商家至多一份档案 | FR-01/04；用户域字典 |
| 3 | bouquet.seller_id | user.id | N:1 | 发布商家；应用层校验 role 与归属 | B-03；花束域字典 |
| 4 | bouquet.category_id | category.id | N:1 | 分类非空 | FR-01/02 |
| 5 | bouquet_image.bouquet_id | bouquet.id | N:1 | 图片归属花束 | FR-01/04 |
| 6 | orders.user_id | user.id | N:1 | 下单顾客；归属校验基础（不代替越权判断） | FR-05/08 |
| 7 | order_item.order_id | orders.id | **本期 1:1** | UNIQUE(order_id)：本期一单一花束 | FR-05/06；订单域字典 |
| 8 | order_item.bouquet_id | bouquet.id | N:1 | 明细指向真实花束 | FR-05 |
| 9 | order_status_log.order_id | orders.id | N:1 | 每次状态变化一行日志 | FR-06/07；B-06 |
| 10 | order_status_log.user_id | user.id | N:1 | 操作人可追溯 | FR-08；G3 |
| 11 | stock_change.bouquet_id | bouquet.id | N:1 | 每次剩余量变化一行流水 | B-05 |
| 12 | stock_change.order_id | orders.id | N:1（可空） | 商家调整场景为 NULL；**UNIQUE(order_id, change_type)** 保证同一订单至多一次扣减、一次回补 | FR-05/07；B-06；NFR-02 |
| 13 | stock_change.user_id | user.id | N:1（可空） | 同上 | FR-08 |

全部外键 `ON DELETE RESTRICT`：订单与花束均不物理删除（B-06 历史保留），流水不得悬空。

## 三、关系说明要点

1. **用户为中心的两组 1:N**：user 下发 bouquet（商家发布）、orders（顾客下单）、order_status_log 与 stock_change（操作人），共 4 条线指向 user，体现 FR-08"身份与操作可追溯"。
2. **订单域与流水域的衔接**：orders.id 被三张表引用（order_item、order_status_log、stock_change），其中流水域两条线上带业务约束——`order_status_log` 记录状态每次变化；`stock_change` 以 UNIQUE(order_id, change_type) 保证取消仅回补一次（B-06）、重复请求只产生一次效果（NFR-02）。
3. **花束域两条 1:N**：bouquet → bouquet_image（图片）、category → bouquet（分类），加上 bouquet.seller_id → user，构成商品供给侧。
4. **seller_profile 1:0..1**：user_id 同时作主键与外键，档案不脱离账号存在。
5. **不含**：泛化"用户"抽象与登录用例在总体 ER 图（[er/er-overall.md](../er/er-overall.md)）表达，本图为逻辑层实际表；`bouquet_stock` 独立表不设——剩余量在 bouquet.stock_qty 上、变化走 stock_change 流水（B-05 口径）。

## 四、与需求约束的落点对照

| 约束 | 关系图落点 |
|---|---|
| B-05 剩余量非负、与有效订单一致 | bouquet.stock_qty CHECK ≥0 + stock_change.after_qty CHECK ≥0 + 扣减/回补与流水同事务 |
| B-06 取消仅回补一次、历史保留 | orders/order_item/流水均 RESTRICT 不删除；UNIQUE(order_id, change_type) |
| B-08 单价快照 | order_item.unit_price 与 bouquet.price 分离（连线即"明细引用花束但不继承价格"） |
| NFR-02 重复请求一次效果 | orders.idempotency_key UK + UNIQUE(order_id, change_type) |
| NFR-03 越权防护 | orders.user_id / 流水 user_id 归属 + 应用层按登录态过滤 |

## 五、图与字典的一致性核对

- 10 张表与 T4～T7 字典一一对应，无遗漏、无多余。
- 13 条连线与各域字典"索引与外键清单"逐条一致；类型 BIGINT UNSIGNED 已按 D-01 对齐（T7 v0.2、订单域 v0.3）。
- 每条连线可在走查（[walkthrough.md](../walkthrough.md)）中找到对应场景步骤。

## 变更记录

| 版本 | 日期 | 内容 | 修改人 |
|---|---|---|---|
| v0.1 | 2026-11-18 | 建立全部 10 张表的表间关系图（PNG）与本说明：13 条外键连线、基数与约束落点对照；AI 辅助绘制与整理，本人逐条对照四域字典核验（登记于 records/ai-use.md） | 林伟翔 |
