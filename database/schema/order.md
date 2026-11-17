# 订单域 —— 表结构与数据字典

> 实验二 · 数据库设计 ｜ 主责人：何奕佳 ｜ 交叉检查：林伟翔 ｜ 版本 v0.2 · 2026-11-17
> 依据：[订单域实体清单](../er/domain-order.md) v0.1、[database/README.md](../README.md) 建模约定
> 基线：FR-05（主）、FR-06、FR-08；B-05、B-06、B-08；NFR-01、NFR-02、NFR-03

## 1 表清单

| 表名 | 用途 | 只追加 |
|---|---|---|
| `orders` | 订单主表：一笔预订一行，记录顾客、状态、金额合计、送达日期、履约方式与幂等键 | 否（只改状态，不删除） |
| `order_item` | 订单明细：一张订单内的花束、数量与**下单时单价快照** | 否（写入后不再更新） |

两表均无物理删除路径：取消只改 `orders.status` 与 `cancelled_at`（B-06 历史保留）。

## 2 表 orders 数据字典

**表用途**：保存每一笔预订的结果。UC-03 下单成功时写入一行（状态"有效"），UC-04 取消时把状态条件更新为"已取消"并写入 `cancelled_at`；UC-08 按 `user_id` 读取本人订单。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 约束 | 来源 |
|---|---|---|---|---|---|---|
| id | 主键 | BIGINT UNSIGNED AUTO_INCREMENT | 否 | 自增 | PRIMARY KEY | 建模约定 4 |
| order_no | 对外订单号 | VARCHAR(32) | 否 | — | **UNIQUE** | UC-03 P1；FR-06 |
| user_id | 下单顾客 | BIGINT UNSIGNED | 否 | — | FOREIGN KEY → user(id)；INDEX (user_id, created_at) | FR-05、FR-08 |
| status | 订单状态 | VARCHAR(16) | 否 | '有效' | **CHECK ∈（有效/已取消/已完成）**；INDEX | FR-06、FR-07；Q-10 |
| total_amount | 金额合计（元） | DECIMAL(10,2) | 否 | — | CHECK (total_amount >= 0) | FR-05；B-08 |
| delivery_date | 送达/自提日期 | DATE | 否 | — | — | FR-05；Q-03 |
| fulfillment_type | 履约方式 | VARCHAR(8) | 否 | — | CHECK ∈（自提/配送） | FR-05 |
| idempotency_key | 幂等键 | VARCHAR(64) | 否 | — | **UNIQUE** | NFR-02；UC-03 A5 |
| created_at | 下单时间 | DATETIME | 否 | CURRENT_TIMESTAMP | — | FR-05、FR-06 |
| cancelled_at | 取消时间 | DATETIME | 是 | NULL | 取消时写入一次；未取消为 NULL | FR-07；B-06 |
| updated_at | 最后更新时间 | DATETIME | 否 | CURRENT_TIMESTAMP ON UPDATE | — | 建模约定 1 |

**其他约束与说明**

- `UNIQUE (idempotency_key)`：NFR-02 的落点。同一请求重复到达时，第二次插入直接冲突，应用返回首次订单（AC-UC03-09 要求"不得改判为售罄"）。
- `UNIQUE (order_no)`：业务标识唯一；订单号由应用生成（`SO + yyyyMMdd + 4 位序列`，见待确认项 1）。
- `status` 三值 CHECK：按 Q-10，本期只产生"有效 → 已取消"一次流转，"已完成"仅为占位值，不产生流转；该占位与 `database/README.md` 建模约定 3 一致，但与 Q-10 的"两态"表述存在口径差异，见待确认项 5。
- 取消采用**条件更新**：`UPDATE orders SET status='已取消', cancelled_at=NOW() WHERE id=? AND status='有效'`；影响行数为 0 表示已取消或不存在，不再回补（UC-04 A3/A5）。
- 本表不保存花束信息与单价：它们落在 `order_item`，便于后续扩展一单多花束。

**示例数据**（走查用，非真实记录）：

| id | order_no | user_id | status | total_amount | delivery_date | fulfillment_type | idempotency_key | created_at | cancelled_at |
|---|---|---|---|---|---|---|---|---|---|
| 100 | SO202611150001 | 10 | 有效 | 398.00 | 2026-11-18 | 自提 | K1-8f3a… | 2026-11-15 09:00:00 | NULL |
| 101 | SO202611150002 | 10 | 已取消 | 199.00 | 2026-11-19 | 配送 | K2-1c7d… | 2026-11-15 10:00:00 | 2026-11-15 11:30:00 |

## 3 表 order_item 数据字典

**表用途**：保存订单内每种花束的数量与成交单价。`unit_price` 是 B-08 的唯一落点——商家改价不影响历史明细，UC-08 展示金额时以明细为准。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 约束 | 来源 |
|---|---|---|---|---|---|---|
| id | 主键 | BIGINT UNSIGNED AUTO_INCREMENT | 否 | 自增 | PRIMARY KEY | 建模约定 4 |
| order_id | 所属订单 | BIGINT UNSIGNED | 否 | — | FOREIGN KEY → orders(id)；**UNIQUE (order_id, bouquet_id)** | FR-05、FR-06 |
| bouquet_id | 花束 | BIGINT UNSIGNED | 否 | — | FOREIGN KEY → bouquet(id)；INDEX | FR-05（庞延新域） |
| quantity | 预订数量（束） | INT | 否 | — | **CHECK (quantity BETWEEN 1 AND 99)** | Q-02；FR-05 |
| unit_price | 单价快照（元/束） | DECIMAL(10,2) | 否 | — | **CHECK (unit_price > 0)** | **B-08**；FR-05 |
| amount | 行金额（元） | DECIMAL(10,2) | 否 | — | CHECK (amount >= 0)；= quantity × unit_price | FR-05 |
| created_at | 创建时间 | DATETIME | 否 | CURRENT_TIMESTAMP | — | 建模约定 1 |

**其他约束与说明**

- `UNIQUE (order_id, bouquet_id)`：同一订单内同一花束只一行；当前业务一单一花束，该约束同时防止重复写入明细。
- `quantity` 的上界 1—99 是 Q-02 的落点；**"不超过剩余量"不由本表约束**——那需要读取 `bouquet.stock_qty`，由下单事务的条件更新保证（见第 5 节）。
- `unit_price` 写入后不再更新；`amount` 由应用写入且与 `quantity × unit_price` 一致（不建生成列，避免与"快照"语义混淆；若改生成列需在字典注明）。
- 外键均 `ON DELETE RESTRICT`：订单与花束都不物理删除，历史明细不得悬空。

## 4 索引与外键清单

| 对象 | 类型 | 字段 | 用途 |
|---|---|---|---|
| `pk_orders` | 主键 | id | — |
| `uk_orders_no` | 唯一 | order_no | 按单号查询、防重 |
| `uk_orders_idem` | 唯一 | idempotency_key | **NFR-02 幂等** |
| `idx_orders_user_created` | 普通 | (user_id, created_at) | UC-08 本人订单按下单时间倒序 |
| `idx_orders_status` | 普通 | status | UC-08 状态筛选 |
| `uk_item_order_bouquet` | 唯一 | (order_id, bouquet_id) | 防重复明细 |
| `idx_item_bouquet` | 普通 | bouquet_id | 按花束查历史订单 |
| `fk_orders_user` | 外键 | orders.user_id → user(id) | 归属校验的基础（不代替越权判断） |
| `fk_item_order` | 外键 | order_item.order_id → orders(id) | 明细必须挂在订单下 |
| `fk_item_bouquet` | 外键 | order_item.bouquet_id → bouquet(id) | 明细必须指向真实花束 |

## 5 约束落点对照（供走查与 ER 图核对）

| 需求约束 | 本域落点 | 相邻域配合 |
|---|---|---|
| B-08 下单时单价快照 | `order_item.unit_price` 写入后不更新 | UC-07 改价只影响之后的新订单 |
| NFR-02 重复提交只产生一次 | `orders.idempotency_key` UNIQUE | `stock_change` 唯一约束再兜一层 |
| Q-02 数量 1—99 束 | `order_item.quantity` CHECK | — |
| B-05 剩余量非负、与有效订单一致 | 不在本域：数量是否超过剩余量由下单条件更新判断 | `bouquet.stock_qty >= 0` + `stock_change.after_qty >= 0` |
| B-06 取消只改状态、历史保留 | `orders.status` + `cancelled_at`；无 DELETE | `order_status_log` 只追加；`stock_change` 唯一约束保证只回补一次 |
| NFR-03 越权不可见 | `orders.user_id` 归属 + 应用层按登录态过滤 | 外键只保证引用存在，越权判断属应用层（写明） |
| Q-10 状态两态 | `status` CHECK 预留"已完成"但不流转 | `order_status_log.status` 同口径 |

## 6 DDL（参考，未执行；MySQL 8.0 / InnoDB / utf8mb4）

> 未执行 SQL 不影响评分；以下 DDL 用于说明约束可落地，实际执行时需先创建 `user`、`bouquet` 两张被引用表。

```sql
CREATE TABLE orders (
  id              BIGINT UNSIGNED        NOT NULL AUTO_INCREMENT,
  order_no        VARCHAR(32)   NOT NULL,
  user_id         BIGINT UNSIGNED        NOT NULL,
  status          VARCHAR(16)   NOT NULL DEFAULT '有效',
  total_amount    DECIMAL(10,2) NOT NULL,
  delivery_date   DATE          NOT NULL,
  fulfillment_type VARCHAR(8)   NOT NULL,
  idempotency_key VARCHAR(64)   NOT NULL,
  created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cancelled_at    DATETIME      NULL DEFAULT NULL,
  updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_orders_no   (order_no),
  UNIQUE KEY uk_orders_idem (idempotency_key),
  KEY idx_orders_user_created (user_id, created_at),
  KEY idx_orders_status (status),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_orders_status CHECK (status IN ('有效','已取消','已完成')),
  CONSTRAINT ck_orders_amount CHECK (total_amount >= 0),
  CONSTRAINT ck_orders_fulfillment CHECK (fulfillment_type IN ('自提','配送'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE order_item (
  id          BIGINT UNSIGNED        NOT NULL AUTO_INCREMENT,
  order_id    BIGINT UNSIGNED        NOT NULL,
  bouquet_id  BIGINT UNSIGNED        NOT NULL,
  quantity    INT           NOT NULL,
  unit_price  DECIMAL(10,2) NOT NULL,
  amount      DECIMAL(10,2) NOT NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_item_order_bouquet (order_id, bouquet_id),
  KEY idx_item_bouquet (bouquet_id),
  CONSTRAINT fk_item_order FOREIGN KEY (order_id) REFERENCES orders(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_item_bouquet FOREIGN KEY (bouquet_id) REFERENCES bouquet(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_item_qty   CHECK (quantity BETWEEN 1 AND 99),
  CONSTRAINT ck_item_price CHECK (unit_price > 0),
  CONSTRAINT ck_item_amount CHECK (amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 7 跨域接口（与流水域已对齐）

| 本域字段 | 引用/使用方 | 约定 |
|---|---|---|
| `orders.id` | `order_status_log.order_id`、`stock_change.order_id` | BIGINT UNSIGNED 对齐；订单不删除，故流水外键不会被置空 |
| `orders.status` | `order_status_log.from_status/to_status` | **每次状态变化写一行日志**；取消写 `('有效' → '已取消')` |
| `orders.cancelled_at` | — | 与状态日志中的取消时间保持同一事务内一致 |
| `order_item.bouquet_id` | `stock_change.bouquet_id` | 同一事务内两者的 `bouquet_id` 必须相同（跨表，应用层保证） |
| `order_item`.quantity | `stock_change.quantity_delta` | 下单扣减 `delta = -quantity`；取消回补 `delta = +quantity` |

## 8 待确认项

| # | 问题 | 当前建议 | 影响 |
|---|---|---|---|
| 1 | `order_no` 生成规则 | `SO + yyyyMMdd + 4 位当日序列`，应用生成 | 唯一键与展示 |
| 2 | 是否保存 `bouquet_name_snapshot` | 建议追加一列，保证改名/下架后历史订单仍显示下单时名称 | 字段增减 |
| 3 | 一单多花束 | 暂定一单一花束，结构预留 | 唯一键 (order_id, bouquet_id) 已支持扩展 |
| 4 | `total_amount` 是否保留冗余 | 保留：下单时点快照，查询不回算 | 与明细求和的一致性由应用保证 |
| 5 | 状态枚举是否含"已完成" | 按 Q-10 预留不流转；与 README 约定 3 同时统一 | 两处 CHECK |
| 6 | 幂等键作用域 | 全局唯一（UUID） | UC-03 A5 的判重语义 |

## 9 与实验一成果的对应

- UC-03 第 3 步判重 → `uk_orders_idem`；命中后返回首单，不再扣减（AC-UC03-09）。
- UC-03 第 7 步条件扣减 → `bouquet.stock_qty` 条件更新 + 本域两表插入 + `stock_change('下单扣减')`，同事务；任一失败整体回滚（A6）。
- UC-08 列表/筛选/详情 → `idx_orders_user_created` + `status` 过滤，越权按 `user_id` 拒绝。
- UC-04 取消 → 条件更新 `status` + 写 `cancelled_at` + `order_status_log` + `stock_change('取消回补')`，同事务；重复取消影响 0 行，不回补。

---

## 变更记录

| 版本 | 日期 | 内容 | 修改人 |
|---|---|---|---|
| v0.1 | 2026-11-16 | 建立 orders、order_item 表结构与数据字典：字段六要素、索引外键清单、约束落点对照、参考 DDL、跨域接口与待确认项 | 何奕佳 |
| v0.2 | 2026-11-17 | 按统稿决定 D-01 把 `orders.id`、`user_id` 及 `order_item` 的主外键类型全部改为 `BIGINT UNSIGNED`，参考 DDL 同步；与 `schema/user.md` 和流水域外键目标对齐 | 何奕佳 |
