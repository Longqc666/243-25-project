# 订单域 —— 实体、属性与业务规则清单

> 实验二 · 数据库设计 ｜ 主责人：何奕佳（订单域）｜ 版本 v0.1 · 2026-11-16
> 需求基线：FR-05（主）、FR-06、FR-08；B-05、B-06、B-08；NFR-01、NFR-02、NFR-03 ｜ 依据：`database/README.md` 分工与建模约定
> 交叉确认：`orders.status` / `orders.idempotency_key`（林伟翔，流水域）、`order_item.bouquet_id`（庞延新，花束域）、`orders.user_id`（庞华杰，用户域）

## 1 本域范围

订单域保存**顾客预订产生的结果数据**，为以下需求提供落点：

- FR-05：预订下单生成"有效"订单，记录数量、送达日期、履约方式与**下单时单价快照**；
- FR-06：顾客查看本人订单列表与详情，按状态筛选，不返回他人订单；
- FR-07：订单状态由"有效"改为"已取消"，**只改状态不删除**（历史保留）；
- NFR-02：同一提交请求重复到达只产生 1 条订单（幂等键唯一）；
- B-08：改价不影响已产生订单的金额（快照落在 `order_item.unit_price`）。

本域**不定义**花束主档与剩余量（庞延新：花束与库存域）、**不定义**状态流水与库存流水（林伟翔：状态与库存流水域）、**不定义**用户与角色（庞华杰：用户与角色域）。本域只保证"订单这一层"的数据完整，跨表的状态变更与库存扣减由同一事务协调，责任在走查中写明。

## 2 实体一：orders（订单主表）

### 2.1 标识

- 主键：`id`（BIGINT，代理主键，AUTO_INCREMENT）。
- 业务标识：`order_no`（VARCHAR(32)，UNIQUE）——对外展示的订单号，避免把自增主键暴露给顾客；UC-03 的成功后置条件 P1 要求"订单号"。
- 幂等标识：`idempotency_key`（VARCHAR(64)，UNIQUE）——由提交端生成的请求标识，重复请求命中后直接返回首次结果（UC-03 A5）。

### 2.2 属性清单

| 属性 | 类型 | 可空 | 含义 | 来源依据 |
|---|---|---|---|---|
| id | BIGINT, AUTO_INCREMENT | 否 | 主键 | 建模约定 4 |
| order_no | VARCHAR(32) | 否 | 对外订单号，如 SO202611150001 | UC-03 P1；FR-06 |
| user_id | BIGINT | 否 | 下单顾客，外键 → user.id，取自登录态，不接受前端传入 | FR-05、FR-08；B-03 |
| status | VARCHAR(16) | 否 | 订单状态，默认"有效"；CHECK ∈（有效 / 已取消 / 已完成） | FR-06、FR-07；Q-10（本期仅两态流转） |
| total_amount | DECIMAL(10,2) | 否 | 订单金额合计（元），下单时确定，等于明细金额之和 | FR-05；B-08 |
| delivery_date | DATE | 否 | 送达或自提日期 | FR-05；Q-03（窗口暂定） |
| fulfillment_type | VARCHAR(8) | 否 | 履约方式，CHECK ∈（自提 / 配送） | FR-05 |
| idempotency_key | VARCHAR(64) | 否 | 提交请求的幂等键，UNIQUE | NFR-02；UC-03 A5/AC-UC03-09 |
| created_at | DATETIME | 否 | 下单时间，默认 CURRENT_TIMESTAMP | FR-05、FR-06 |
| cancelled_at | DATETIME | 是 | 取消时间；NULL 表示未取消，取消时写入一次 | FR-07；B-06 |
| updated_at | DATETIME | 否 | 最后更新时间，状态变更时刷新 | 建模约定 1 |

### 2.3 本实体约束

1. **`UNIQUE (idempotency_key)`**：NFR-02 的落点。重复提交在插入阶段即被拒绝，返回首次结果，不进入扣减流程（对应 UC-03 第 3 步判重先于库存校验）。
2. **`UNIQUE (order_no)`**：业务标识唯一，供顾客与客服按号查询。
3. **`CHECK (status IN ('有效','已取消','已完成'))`**：取值必须与用例状态名一致；按 Q-10 本期只产生"有效 → 已取消"一次流转，"已完成"仅占位、不产生流转。
4. **`CHECK (total_amount >= 0)`**：金额不为负；金额构成由明细数量与单价快照确定，不取花束当前价。
5. **只改状态不删除**：B-06 要求历史订单保留，本表不提供 DELETE 路径；取消只写 `status='已取消'` 与 `cancelled_at`。
6. **取消的条件更新**：应用层以 `UPDATE ... WHERE id=? AND status='有效'` 提交，影响行数为 0 即表示已被取消或不存在，不重复回补（与 UC-04 第 6 步、NFR-02 一致）。

## 3 实体二：order_item（订单明细）

### 3.1 标识

- 主键：`id`（BIGINT，代理主键，AUTO_INCREMENT）。
- 业务唯一性：`UNIQUE (order_id, bouquet_id)`——同一订单内同一花束只出现一行；当前业务为"一单一花束"，该约束同时防止同一订单重复写入明细。

### 3.2 属性清单

| 属性 | 类型 | 可空 | 含义 | 来源依据 |
|---|---|---|---|---|
| id | BIGINT, AUTO_INCREMENT | 否 | 主键 | 建模约定 4 |
| order_id | BIGINT | 否 | 所属订单，外键 → orders.id | FR-05、FR-06 |
| bouquet_id | BIGINT | 否 | 花束，外键 → bouquet.id | FR-05（庞延新域） |
| quantity | INT | 否 | 预订数量（束），CHECK 1—99 | Q-02；FR-05 |
| unit_price | DECIMAL(10,2) | 否 | **下单时单价快照**（元/束），CHECK > 0 | **B-08**；FR-05 |
| amount | DECIMAL(10,2) | 否 | 行金额 = quantity × unit_price | FR-05 |
| created_at | DATETIME | 否 | 创建时间 | 建模约定 1 |

### 3.3 本实体约束

1. **`unit_price` 是快照不是引用**：取值来自下单瞬间的花束单价，之后商家改价（UC-07 5A）不更新历史明细；这是 B-08 的唯一落点。
2. **`CHECK (quantity BETWEEN 1 AND 99)`**：Q-02 的落点；是否超过剩余量不由此约束保证，而由下单时对 `bouquet.stock_qty` 的条件更新保证（跨表，见第 5 节）。
3. **`amount = quantity × unit_price`**：两者写入后金额不再变化；不建生成列以免与快照语义混淆（如采用生成列，需在字典中注明计算口径）。
4. **外键 `ON DELETE RESTRICT`**：订单与花束均不物理删除，历史明细不得悬空。

## 4 联系与基数

| 联系 | 基数 | 可选性 | 说明 |
|---|---|---|---|
| user — orders | 1 : N | 订单侧必选 | 一名顾客可有多笔历史订单；单笔订单必属于一名顾客（B-03：同一账号同一时刻一种角色） |
| orders — order_item | 1 : N | 明细侧必选 | 当前业务一单一花束（N=1），结构预留多花束；一单至少一条明细 |
| bouquet — order_item | 1 : N | 明细侧必选 | 一种花束可出现在多条历史订单中；花束下架不影响历史订单（B-07 的延伸） |

**基数要点（指导书检查重点）**：同一花束可以有多条历史订单，但**同一订单只对应一条有效占用**——"当前最多一个有效订单"由 `stock_change` 的唯一约束与库存数量共同保证，不由 `orders` 的自反约束表达。

## 5 本域业务规则汇总（供 ER 图与走查引用）

| 规则 | 内容 | 数据落点 |
|---|---|---|
| B-08 | 下单时记录单价快照，改价不影响历史订单 | `order_item.unit_price` 写入后不再更新 |
| NFR-02 | 重复提交只产生一次业务效果 | `orders.idempotency_key` UNIQUE；重复请求返回首单 |
| Q-02 | 单笔数量 1—99 束 | `order_item.quantity` CHECK |
| Q-10 | 本期仅"有效/已取消"两态 | `orders.status` CHECK 含占位值但不产生流转 |
| B-06 | 取消只改状态、历史保留 | `orders.status` + `cancelled_at`；无 DELETE |
| NFR-01 | 并发只成功一单、剩余量不为负 | 不在本域，由 `bouquet.stock_qty` 条件更新 + `stock_change` 唯一约束（庞延新、林伟翔域）保证 |
| NFR-03 | 越权不可见 | `orders.user_id` 归属 + 应用层校验；外键不承担越权判断 |

## 6 跨域接口（须与相邻域共同定稿）

| 接口 | 对方域 | 约定内容 |
|---|---|---|
| `orders.user_id` → `user.id` | 庞华杰（用户与角色域） | 主键统一 BIGINT；顾客身份取自登录态，不由前端传入 |
| `order_item.bouquet_id` → `bouquet.id` | 庞延新（花束与库存域） | 下单同一事务内：条件更新 `bouquet.stock_qty` 并写 `stock_change`（`change_type='下单扣减'`，`delta=-N`） |
| `orders.status` / `cancelled_at` | 林伟翔（状态与库存流水域） | **每次状态变化写一行 `order_status_log`**；取消时同时写 `stock_change`（`change_type='取消回补'`，`delta=+N`），三处同事务 |
| `orders.id` | 林伟翔（状态与库存流水域） | `order_status_log.order_id` 与 `stock_change.order_id` 的外键目标，类型 BIGINT 对齐 |

**跨表一致性说明**：`stock_change.bouquet_id` 必须等于对应订单明细的 `order_item.bouquet_id`，MySQL 无法用跨表 CHECK 表达，由下单/取消事务在写入时带出，属应用层责任（走查中写明）。

## 7 本域待确认项

| # | 问题 | 当前建议 |
|---|---|---|
| 1 | `order_no` 的生成规则 | 建议 `SO + yyyyMMdd + 4 位当日序列`，由应用生成；不依赖自增主键对外 |
| 2 | 是否保存花束名称/图片快照 | 建议至少保存 `bouquet_name_snapshot`：花束改名或下架后，历史订单仍能显示下单时的名称（当前未建列，待组内确认后追加） |
| 3 | 一张订单是否允许包含多个花束 | 暂定一单一花束（FR-05 未定义多花束）；`order_item` 结构预留，接口不变 |
| 4 | `total_amount` 是否冗余 | 建议保留：它是"下单时点"的金额快照，由明细求和可验证，但不应在查询时回算 |
| 5 | 状态枚举是否预留"已完成" | 与林伟翔待确认项 4 同一问题，建议按 Q-10 预留但不流转；需与 README 建模约定 3 统一 |
| 6 | 幂等键作用域 | 建议全局唯一（UUID），由提交端生成；若改为"用户+业务"复合唯一，需同步 UC-03 A5 |

## 8 与实验一成果的对应

- UC-03 第 3 步（幂等判重）→ `orders.idempotency_key` UNIQUE：命中即返回首单，不再校验库存。
- UC-03 第 7 步（条件扣减）→ `bouquet.stock_qty` 条件更新 + `order_item` 写入 + `stock_change('下单扣减')`，同一事务。
- UC-03 P1（成功后置）→ `orders`（订单号、金额、送达日期、履约方式、下单时间）+ `order_item`（数量、单价快照）。
- UC-08 第 1—3 步（列表与筛选）→ `orders` 按 `user_id` + `created_at` 倒序，按 `status` 过滤；越权由 `user_id` 校验拒绝（NFR-03）。
- UC-04 第 6 步（取消）→ `orders` 条件更新 + `order_status_log` + `stock_change('取消回补')`，同一事务。

---

## 变更记录

| 版本 | 日期 | 内容 | 修改人 |
|---|---|---|---|
| v0.1 | 2026-11-16 | 建立订单域实体清单：orders / order_item 的标识、属性、约束、联系基数、跨域接口与待确认项 | 何奕佳 |
