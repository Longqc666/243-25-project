# 用户与角色域 —— 表结构与数据字典

> 实验二 · 数据库设计 ｜ 主责人：庞华杰 ｜ 交叉检查：庞延新、何奕佳 ｜ 版本 v0.2 · 2026-11-18
> 本版按何奕佳《用户与角色域 交叉检查意见》（review/user-domain-by-order-2026-11-17.md）U-01～U-06 修订
> 依据：[database/README.md](../README.md) 分工与建模约定、[概念 ER 图](../er/er-overall.md)
> 基线：FR-08（主）、FR-01、FR-02、FR-05、FR-06；B-02、B-03；NFR-03

## 1 表清单

| 表名 | 用途 | 说明 |
|---|---|---|
| `role` | 角色字典：顾客 / 商家 / 管理员 | 固定 3 行，不随业务增长 |
| `user` | 平台账号：登录、角色、状态与联系方式 | 一账号一行、一行一角色（B-03） |
| `seller_profile` | 商家档案：店铺名、简介、联系电话、自提地址 | 与 `user` 共享主键的 1:0..1 表 |

三表均不物理删除：账号停用改 `status`，档案随商家存在。删除账号会破坏订单与流水的历史引用（`ON DELETE RESTRICT`），不属于本期功能。

## 2 表 role 数据字典

**表用途**：固定角色字典，为 `user.role_id` 提供取值与显示名；同时承载“只有三种角色”的约束。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 约束 | 来源 |
|---|---|---|---|---|---|---|
| id | 角色标识 | TINYINT UNSIGNED | 否 | — | PRIMARY KEY | 建模约定 4 |
| code | 角色编码 | VARCHAR(20) | 否 | — | **UNIQUE**；CHECK ∈（customer/seller/admin） | FR-08、B-03 |
| name | 角色名称 | VARCHAR(20) | 否 | — | — | FR-08 |
| description | 说明 | VARCHAR(100) | 是 | NULL | — | — |

**预置数据**（初始化脚本，非业务写入）：

| id | code | name | description |
|---|---|---|---|
| 1 | customer | 顾客 | 检索、查看、预订与取消本人订单 |
| 2 | seller | 商家 | 发布与管理本人花束、查看本店订单 |
| 3 | admin | 管理员 | 账号停用与违规内容处置，只读业务数据 |

**说明**：角色表用 TINYINT 主键，是“业务表主键统一 BIGINT”约定的唯一例外——它只有 3 行、不被业务表以外引用、不对外暴露；`user.role_id` 与之同类型即可。

## 3 表 user 数据字典

**表用途**：保存登录凭据、角色与账号状态，是 `orders.user_id`、`bouquet.seller_id`、两张流水表 `user_id` 的引用目标，也是 UC-05 登录与角色识别的数据来源。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 约束 | 来源 |
|---|---|---|---|---|---|---|
| id | 主键 | BIGINT UNSIGNED | 否 | AUTO_INCREMENT | PRIMARY KEY | 建模约定 4 |
| username | 登录名 | VARCHAR(50) | 否 | — | **UNIQUE**；CHECK（长度 3—30，字母/数字/下划线） | FR-08、B-02 |
| password_hash | 密码哈希 | VARCHAR(255) | 否 | — | 只存 bcrypt 哈希（60 字符），不存明文 | **NFR-03** |
| display_name | 姓名或昵称 | VARCHAR(50) | 否 | — | — | FR-01、FR-06 |
| phone | 手机号 | VARCHAR(20) | 否 | — | **UNIQUE**；CHECK（11 位数字） | NFR-03（响应中不得出现他人手机号） |
| email | 邮箱 | VARCHAR(100) | 是 | NULL | — | 预留字段，本期不参与登录、不加唯一约束 |
| avatar_url | 头像地址 | VARCHAR(255) | 是 | NULL | — | FR-01 商家信息展示 |
| role_id | 角色 | TINYINT UNSIGNED | 否 | — | FOREIGN KEY → `role(id)`；INDEX | **B-03** |
| status | 账号状态 | VARCHAR(8) | 否 | '正常' | **CHECK ∈（正常/停用）** | 管理员停用（1.5 纳入范围） |
| last_login_at | 最近登录时间 | DATETIME | 是 | NULL | — | 审计辅助 |
| created_at | 创建时间 | DATETIME | 否 | CURRENT_TIMESTAMP | — | 建模约定 1 |
| updated_at | 更新时间 | DATETIME | 否 | CURRENT_TIMESTAMP ON UPDATE | — | 建模约定 1 |

**其他约束与说明**

- `UNIQUE (username)`、`UNIQUE (phone)`：登录与联系的业务标识；密码不参与唯一性。
- `role_id` 单值外键：一个账号同一时刻只有一种角色（B-03）；不建 `user_role` 多值表，因为需求没有“一人多角色”的场景，多值表会让 `orders.user_id` 的归属判断复杂化。
- **不存明文密码**（NFR-03）：`password_hash` 保存 bcrypt 自带的盐与算法标识，`$2b$` 开头；是否升级算法由实现层决定，库里不额外存盐列。
- 账号停用只改 `status`，不删除行：历史订单、流水与花束的引用必须继续有效。
- 本期不提供注册、找回密码、角色变更（B-02）；`user` 行由初始化脚本写入。

**示例数据**（走查用，非真实账号）：

| id | username | display_name | phone | role_id | status |
|---|---|---|---|---|---|
| 1 | admin | 平台管理员 | 13800000001 | 3 | 正常 |
| 3 | seller_lin | 林小满 | 13800000003 | 2 | 正常 |
| 10 | cust_zhou | 周小雨 | 13800000010 | 1 | 正常 |

## 4 表 seller_profile 数据字典

**表用途**：保存商家的店铺资料，供 UC-01 发布页与 UC-06 详情的“商家信息”读取；与 `user` 一对一，只有 `role_id = 2` 的账号才应有一行。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 约束 | 来源 |
|---|---|---|---|---|---|---|
| user_id | 商家账号 | BIGINT UNSIGNED | 否 | — | **PRIMARY KEY**；FOREIGN KEY → `user(id)` | FR-01、FR-04 |
| shop_name | 店铺名 | VARCHAR(100) | 否 | — | **UNIQUE** | FR-04 商家信息 |
| shop_intro | 店铺简介 | VARCHAR(500) | 是 | NULL | — | 扩展位 |
| contact_phone | 联系电话 | VARCHAR(20) | 否 | — | CHECK（11 位数字） | FR-04 |
| pickup_address | 自提地址 | VARCHAR(200) | 是 | NULL | — | FR-05 自提方式 |
| created_at | 创建时间 | DATETIME | 否 | CURRENT_TIMESTAMP | — | 建模约定 1 |
| updated_at | 更新时间 | DATETIME | 否 | CURRENT_TIMESTAMP ON UPDATE | — | 建模约定 1 |

**其他约束与说明**

- 用 `user_id` 同时作主键与外键实现 1:0..1：一个商家最多一行档案，档案不能脱离账号存在。
- **“只有商家才有档案”不是外键能表达的约束**：`seller_profile.user_id` 只保证该用户存在。插入前必须由应用层校验 `user.role_id = 2`（或使用触发器）；放任直接写库会产生“顾客拥有店铺”的不一致，走查 W-06 专门说明这一点。
- `shop_name` 唯一：同一店铺名不允许两个商家重复注册，便于顾客按店铺识别。
- 商家停用后档案保留，不做级联删除。`user.status` 改为“停用”时，同一事务把该商家名下 `status='已上架'` 的花束置为“已下架”，检索与下单自然不可见；历史订单、明细与流水不受影响，仍可查看与取消（D-06）。

## 5 索引与外键清单

| 对象 | 类型 | 字段 | 用途 |
|---|---|---|---|
| `pk_role` | 主键 | role.id | — |
| `uk_role_code` | 唯一 | role.code | 角色编码唯一 |
| `pk_user` | 主键 | user.id | — |
| `uk_user_username` | 唯一 | user.username | 登录、防重 |
| `uk_user_phone` | 唯一 | user.phone | 联系方式唯一 |
| `idx_user_role` | 普通 | user.role_id | 按角色统计与数据范围过滤 |
| `idx_user_status` | 普通 | user.status | 停用账号筛查 |
| `pk_seller_profile` | 主键 | seller_profile.user_id | 1:1 约束 |
| `uk_seller_shop` | 唯一 | seller_profile.shop_name | 店铺名唯一 |
| `fk_user_role` | 外键 | user.role_id → role(id) | 角色必须存在 |
| `fk_profile_user` | 外键 | seller_profile.user_id → user(id) | 档案必须挂在账号上 |

全部外键 `ON DELETE RESTRICT ON UPDATE RESTRICT`：账号与档案都不物理删除，避免订单、花束与流水出现悬空引用。

## 6 规范化说明

**函数依赖**

- `role`：`id → code, name, description`；`code → id, name, description`。`id` 与 `code` 都是候选键，非主属性完全依赖候选键，属 BCNF。
- `user`：`id → username, password_hash, display_name, phone, email, avatar_url, role_id, status, last_login_at, created_at, updated_at`；`username`、`phone` 唯一，也是候选键。
- `seller_profile`：`user_id → shop_name, shop_intro, contact_phone, pickup_address, created_at, updated_at`。

**范式判断**

1. 三张表主键都是单属性（`user_id` 也是单列主键），不存在部分依赖，满足 2NF。
2. `user` 中不保存角色名称。若把 `role.name` 放进 `user`，则 `id → role_id → role_name` 构成传递依赖；拆出 `role` 字典后，角色名只依赖 `role.id`，`user` 满足 3NF。
3. `seller_profile` 是 1:1 拆分，不是把多值属性塞进 `user`：店铺资料对顾客/管理员为 NULL，独立成表避免空值膨胀，也让 `shop_name` 的唯一约束只作用于商家。拆分后无部分依赖与传递依赖，满足 3NF。
4. 1NF 补充：头像只存 URL、不存二进制，一个账号一行头像，不构成多值属性。

**有意保留的冗余（本域之外，供统稿引用）**

- `order_item.unit_price`：下单时的单价快照（B-08），商家改价不影响历史订单。
- `orders.total_amount`：下单时点的合计快照，查询时不由明细回算。
- `bouquet.stock_qty` 与 `stock_change`：当前值与变更流水并存，同事务写入。

这三处保存的是不同时间点的状态，不是同一事实的重复，因此不违反 3NF；理由须在统稿时统一说明（见 [er-overall.md](../er/er-overall.md) 第 5 节）。

## 7 约束落点对照

| 需求约束 | 本域落点 | 说明 |
|---|---|---|
| B-02 预置账号、无注册 | 无注册入口；`user` 行由初始化脚本写入 | 账号管理不在本期 |
| B-03 一账号一角色 | `user.role_id` 单值外键 | 不建多值角色表 |
| NFR-03 密码非明文 | `password_hash` 只存 bcrypt 哈希 | 不存明文或可逆加密 |
| NFR-03 不泄露他人信息 | `phone`、`display_name` 属敏感列 | 查询按登录态过滤，应用层责任 |
| 账号可停用 | `user.status` CHECK ∈（正常/停用） | 停用后拒绝登录由应用层校验 |
| 商家唯一档案 | `seller_profile.user_id` 主键 | 一商家一档案 |
| 只有商家有档案 | 无声明式约束（CHECK 不能跨表） | **应用层或触发器校验 `role_id=2`**；验收情境 W-06：给定 `role_id=1` 的账号，插入 `seller_profile` 应被拒绝且不产生档案行 |
| 商家只能操作本人花束 | 通过 `bouquet.seller_id = 当前 user.id` 判断 | 花束域落点，应用层责任 |

## 8 跨域接口

| 本域字段 | 引用方 | 约定 |
|---|---|---|
| `user.id` | `orders.user_id`、`bouquet.seller_id`、`order_status_log.user_id`、`stock_change.user_id` | 统一 BIGINT UNSIGNED，两侧类型一致；账号不删除 |
| `user.role_id` | 各域的数据范围判断 | 只有 `role_id=1` 可下单与取消；`role_id=2` 可发布；`role_id=3` 只读业务数据 |
| `seller_profile.user_id` | UC-01 发布页、UC-06 详情 | 发布页要求当前商家已有档案；无档案时不展示店铺信息 |
| `user.status` | 登录与会话校验 | 停用账号不得登录；已产生的订单与花束不追溯删除 |

## 9 参考 DDL（未执行；MySQL 8.0 / InnoDB / utf8mb4）

> 未执行建表语句，以下 DDL 只用于说明约束可落地；执行顺序必须先于 `orders`、`bouquet` 等引用表。

```sql
CREATE TABLE `role` (
  id          TINYINT UNSIGNED NOT NULL,
  code        VARCHAR(20)  NOT NULL,
  name        VARCHAR(20)  NOT NULL,
  description VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_code (code),
  CONSTRAINT ck_role_code CHECK (code IN ('customer','seller','admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user` (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username      VARCHAR(50)  NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name  VARCHAR(50)  NOT NULL,
  phone         VARCHAR(20)  NOT NULL,
  email         VARCHAR(100) NULL DEFAULT NULL,
  avatar_url    VARCHAR(255) NULL DEFAULT NULL,
  role_id       TINYINT UNSIGNED NOT NULL,
  status        VARCHAR(8)   NOT NULL DEFAULT '正常',
  last_login_at DATETIME     NULL DEFAULT NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_username (username),
  UNIQUE KEY uk_user_phone (phone),
  KEY idx_user_role (role_id),
  KEY idx_user_status (status),
  CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES `role`(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_user_status CHECK (status IN ('正常','停用')),
  CONSTRAINT ck_user_username CHECK (username REGEXP '^[A-Za-z0-9_]{3,30}$'),
  CONSTRAINT ck_user_phone CHECK (phone REGEXP '^[0-9]{11}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE seller_profile (
  user_id        BIGINT UNSIGNED NOT NULL,
  shop_name      VARCHAR(100) NOT NULL,
  shop_intro     VARCHAR(500) NULL DEFAULT NULL,
  contact_phone  VARCHAR(20)  NOT NULL,
  pickup_address VARCHAR(200) NULL DEFAULT NULL,
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uk_seller_shop (shop_name),
  CONSTRAINT ck_profile_phone CHECK (contact_phone REGEXP '^[0-9]{11}$'),
  CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES `user`(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 10 待确认项

| # | 问题 | 当前建议 | 影响 |
|---|---|---|---|
| 1 | 是否需要记录商家资质与审核状态 | 本期不做（FR 未要求） | 若增加，需扩展 seller_profile |
| 2 | 手机号是否允许非 11 位（如座机） | 统一 11 位手机号，座机放 `pickup_address` 说明 | CHECK 与表单校验 |
| 3 | 顾客是否需要收货地址表 | 本期不建：FR-05 只有自提/配送方式，地址在配送场景未定义 | 若补地址，需新增表并改 UC-03 |
| 4 | 商家停用后其花束是否仍可检索 | **已定（D-06）**：停用时同事务联动下架其在架花束；检索条件仍只看 `bouquet.status`，无需联表 user | 走查 W-05、花束域 `bouquet.status` |
| 5 | 是否允许修改角色 | 本期不允许（B-03 与预置账号） | 角色变更需重走发布/下单归属校验 |

---

## 变更记录

| 版本 | 日期 | 内容 | 修改人 |
|---|---|---|---|
| v0.1 | 2026-11-17 | 建立 role、user、seller_profile 表结构与数据字典：字段六要素、索引外键、约束落点、跨域接口、规范化说明与参考 DDL | 庞华杰 |
| v0.2 | 2026-11-18 | 按交叉检查 U-01～U-06 修订：DDL 补 username/phone/contact_phone 的 REGEXP CHECK，email 定位为预留字段，补 W-06 验收，1NF 说明合并，D-06 明确商家停用联动下架 | 庞华杰 |
