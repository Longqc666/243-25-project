# 花束与库存域 表结构与数据字典

> 主责：庞延新（victory0703）｜v0.2｜2026-11-17｜待何奕佳交叉检查及组内接口定稿
> 依据：[实体清单](../er/domain-bouquet.md)、[建模约定](../README.md)、FR-01～04及B-03～B-08。

## 1 表清单与共同约定

| 表名 | 用途 | 当前版本 |
|---|---|---|
| `category` | 预置分类及名称 | 本域v0.2 |
| `bouquet` | 花束资料、当前价、状态及唯一当前剩余量 | 本域v0.2 |
| `bouquet_image` | 图片存储引用和展示顺序 | 本域v0.2 |

当前库存唯一位置为`bouquet.stock_qty`，不重复建立`bouquet_stock`。数量为束，金额为元/束；字符集按小组约定utf8mb4。主外键按README第9.2节D-01采用BIGINT UNSIGNED，与用户字典及订单v0.2一致；现有流水v0.1尚写BIGINT，需林伟翔同步为UNSIGNED才能真正满足外键同类型、同符号。身份和角色校验由应用承担。

本轮对照main提交`e7e1d78c608bbfb092f3ed26277a3d6c0551594b`（2026-11-17），本域v0.2仍为待评审提案。D-03订单三值含已完成占位但本期不流转，D-04系统库存流水user_id可NULL，D-05保留成交快照/合计及当前量与流水并存，均按统稿决定执行，不再当作未决选项。

以下文本长度、单分类、颜色/档期单值、封面排序及版本策略是本版具体设计提案，并非课程指定值。主键“自增”表示生成方式；“无”表示没有数据库DEFAULT，调用方必须提供；NULL表示字段允许无值。数据库实际版本与约束能力在选做SQL时核对，本稿未执行建表。

## 2 category

表用途：保存预置分类。候选键为`id`与`name`。沿用总体ER中name(UK)、sort_no字段；名称唯一性作为本域提案随本稿评审。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 键及其他约束 | 来源 |
|---|---|---|---|---|---|---|
| id | 分类标识 | BIGINT UNSIGNED AUTO_INCREMENT | 否 | 自增 | PRIMARY KEY | 分类实体的设计标识 |
| name | 分类名称 | VARCHAR(50) | 否 | 无 | UNIQUE；`CHAR_LENGTH(TRIM(name)) > 0` | FR-01、UC-01/07；总体ER候选UK |
| sort_no | 分类展示次序 | INT | 否 | 0 | `CHECK(sort_no >= 0)`，允许同值 | 总体ER候选字段 |

有花束引用的分类禁止物理删除，外键删除策略为RESTRICT；改名不改变id。分类管理功能不因本表而扩展进本期业务。分类名称写入前规范首尾空白，唯一性比较规则随全库排序规则统一；不能假定大小写或全半角必然相同。sort_no同值按id升序。名称长度、排序规则仍需本人/组长核对。

## 3 bouquet

表用途：一条发布对应一种花束，保存当前信息与剩余量。候选键为`id`，花名或“商家+花名”不设唯一限制。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 键及其他约束 | 来源 |
|---|---|---|---|---|---|---|
| id | 花束标识 | BIGINT UNSIGNED AUTO_INCREMENT | 否 | 自增 | PRIMARY KEY | FR-01～04、B-04 |
| seller_id | 发布商家 | BIGINT UNSIGNED | 否 | 无 | FOREIGN KEY→user(id)，RESTRICT | B-03、FR-01/02；总体ER R3及用户字典 |
| category_id | 所属分类 | BIGINT UNSIGNED | 否 | 无 | FOREIGN KEY→category(id)，RESTRICT | FR-01/02、UC-01/07 |
| name | 花名 | VARCHAR(100) | 否 | 无 | `CHAR_LENGTH(TRIM(name)) > 0` | FR-01～04 |
| price | 当前单价，元/束 | DECIMAL(10,2) | 否 | 无 | `CHECK(price > 0)` | B-05/08、FR-01/04 |
| stock_qty | 当前剩余可预订量，束 | INT | 否 | 无 | `CHECK(stock_qty >= 0)` | B-05、FR-01/02/05/07 |
| meaning_scene | 花语/适用场景文本 | VARCHAR(500) | 否 | 无 | `CHAR_LENGTH(TRIM(meaning_scene)) > 0` | FR-01/03/04 |
| description | 补充描述 | TEXT | 是 | NULL | 无额外取值约束 | UC-01选填项 |
| color | 单个颜色选项值 | VARCHAR(32) | 是 | NULL | 非NULL时须属已有发布选项，应用校验 | FR-03、UC-01/07 |
| festival_slot | 单个节日档期选项值 | VARCHAR(64) | 是 | NULL | 非NULL时须属已有发布选项，应用校验 | FR-03、UC-01/07 |
| status | 上下架状态 | VARCHAR(16) | 否 | 已下架（待上架） | CHECK取值为已下架（待上架）/已上架/已下架 | FR-01/02、UC-01/07 |
| version | 并发更新版本 | BIGINT | 否 | 0 | `CHECK(version >= 0)`；成功有效更新递增 | UC-07 A7/A11设计落点 |
| created_at | 创建时间 | DATETIME | 否 | CURRENT_TIMESTAMP | 创建后不修改；本版作为默认上新排序时间 | UC-01、FR-03 |
| updated_at | 最后成功修改时间 | DATETIME | 否 | CURRENT_TIMESTAMP | 每次成功有效更新由应用设置 | UC-07 |

字段校验还需拒绝非法原始输入，例如小数数量、超精度金额、超长文本，不能依赖数据库类型转换后再当作合法数据。数量默认不设0，避免漏填与真实输入0混淆。`DECIMAL(10,2)`的存储范围不是小组已确认的业务价格上限；更小的业务上限另定。

### 3.1 本表约束与操作规则

1. 上架前在同一操作中检查余量>0。不能设置全局`status='已上架'`就要求余量永远>0的CHECK，否则最后一束正常预订无法落库。
2. 检索读取`status='已上架' AND stock_qty>0`，详情重新读取当前状态；不另存容易失步的“可预订”布尔值。
3. 版本方案采用每次成功的资料、状态或库存变更递增`version`，并维护`updated_at`。商家提交旧表单必须携带读取时版本和旧余量；未命中就提示刷新，不覆盖新值。
4. 新预订条件扣减同时校验最新状态与余量；取消在核对订单归属、可取消状态和时限后按当前余量加原数量，不要求花束仍上架。取消不得把花束自动上架。
5. 不物理删除被历史订单/流水引用的花束；不级联删除订单或流水。未纳入本期删除功能，不新增删除标志或删除流程。
6. 当前报价字段为`bouquet.price`；下单事务在一致的花束版本上读取报价并写入`order_item.unit_price`，行金额写`order_item.amount`、合计写`orders.total_amount`。商家改价只影响此后的新订单，不回写历史成交快照。最早可送达日期按Q-03与下单共用来源，本表不编造算法或固定日期字段。
7. 管理员强制下架后的重上架权限规则尚未定稿；最终方案若需增加禁售原因等数据，应同步用户域与UC-07，本版不声称单一status字段已实现该扩展限制。

## 4 bouquet_image

表用途：保存图片存储引用与排序。候选键为`id`。一个存储文件是否允许被多条图片元数据复用不作唯一限制。

| 字段名 | 含义 | 类型与长度 | 可空 | 默认值 | 键及其他约束 | 来源 |
|---|---|---|---|---|---|---|
| id | 图片标识 | BIGINT UNSIGNED AUTO_INCREMENT | 否 | 自增 | PRIMARY KEY | 图片实体设计标识 |
| bouquet_id | 所属花束 | BIGINT UNSIGNED | 否 | 无 | FOREIGN KEY→bouquet(id)，RESTRICT | FR-01/04 |
| image_url | 定位图片的存储键 | VARCHAR(512) | 否 | 无 | `CHAR_LENGTH(TRIM(image_url)) > 0` | FR-01/04存储落点 |
| sort_no | 显示次序 | INT | 否 | 0 | `CHECK(sort_no >= 0)`；允许同值 | 图片展示设计选择 |
| created_at | 元数据创建时间 | DATETIME | 否 | CURRENT_TIMESTAMP | 创建后不修改 | 设计元数据 |

本版按`sort_no ASC,id ASC`展示，第一张作为缩略图，不重复维护独立封面标志。成功发布至少一张图片，UC-01/07沿用至少保留一张的暂定规则；上传校验Q-01暂定jpg/png、单张≤2MB，张数上限待定。

图片文件校验与存储可用性属于应用/存储责任；数据库外键只保证引用花束存在。花束及图片元数据须作为一次完整发布保存，成功前完成文件校验，失败不留下已完成发布的半条数据；外部文件存储与数据库不假定天然具有同一事务，失败时由应用清理临时文件。

## 5 跨域外键与库存流水接口

| 接口 | 本版约定 | 状态 |
|---|---|---|
| `stock_change.bouquet_id → bouquet.id` | BIGINT UNSIGNED；当前量在`bouquet.stock_qty` | D-01已定，流水v0.1需同步类型 |
| `order_item.bouquet_id → bouquet.id` | 多条历史明细可引用同一花束；不对bouquet_id单独唯一 | 已对照何奕佳11月17日字典v0.2，待双方复核 |
| `bouquet.seller_id → user.id` | BIGINT UNSIGNED；每条花束一个商家账号，应用检验role与归属 | 已对照用户字典/总体ER R3 |
| `category.id → bouquet.category_id` | 一分类0..N花束，花束分类非空 | 本域提案 |
| `bouquet.id → bouquet_image.bouquet_id` | 图片所属花束非空；至少一张由发布操作维护 | 本域提案 |

沿用流水字段`quantity_delta`、`before_qty`、`after_qty`、`change_type`、`order_id`、`user_id`、`created_at`。对一次成功变化，本域要求：before_qty是该次变更前实际量，after_qty=before_qty+quantity_delta，after_qty等于该事务写入的stock_qty；后续发生新变化不回写历史流水。

建议发布记录一条“初始化”流水（0→初始余量，即使初始为0也记一次）；下单扣减、取消回补、实际改变数量的商家调整各记一次。商家将余量设为原值属于无数量变化，不写额外库存变更；如同操作另有资料修改，维护资料版本。上述初始化、零改量细节待林伟翔确认。

订单域已提交`orders.idempotency_key`唯一键、`order_item.bouquet_id`及单价快照，接口名直接沿用。其参考扣减目前未带`version`；本域提议下单、取消、商家改量都维护`version`与`updated_at`，需两位相邻负责人同步采纳后才能称全组一致。新下单的最终写入还须同时验证花束仍已上架；报价读取与扣减应属于同一个一致版本，不能拿旧价生成“下单时快照”。

`stock_qty`、`version`、订单/明细、状态日志及库存流水在相应业务事务中整体提交；任一步失败整体回滚。每种业务只写适用记录，并非所有编辑都生成订单日志。幂等命中的重试只读取原结果，不再次递增版本或写流水。

## 6 约束能保证什么

| 约束/责任 | 能保证 | 不能独自保证 |
|---|---|---|
| PK/NOT NULL | 标识唯一，必填字段有值 | 文本不全空白、操作者归属 |
| FK | 引用的分类/花束/商家存在 | 该用户有权操作、父花束至少有一张图 |
| CHECK | 本行价格/余量/次序/版本和状态取值 | 跨表库存与订单同步、文件真实存在 |
| 流水业务唯一键 | 确认业务粒度后防止重复成功流水 | 单独保证整个取消事务只回补一次 |
| 应用与事务 | 身份、日期、幂等结果、条件更新、整体回滚 | 不能省略基础键与取值约束 |

当前订单域暂定一单一种花束；`UNIQUE(order_id,bouquet_id)`只能禁止同一花束重复明细，不能单独阻止一单写入不同花束。应用/事务须保证本期每单恰好一行；若改约束或扩展多花束，应共同同步流水粒度。流水`UNIQUE(order_id,change_type)`的适用前提、取消与创建请求标识等问题见[接口核对](../review/bouquet-order-stock-interface-2026-11-17.md)。本稿不修改相邻负责人已提交文件。

## 7 复核事项

需何奕佳复核表结构与订单粒度，庞华杰复核本域与总体ER的字段合并，林伟翔确认流水初始化及版本协作。文本长度、单值筛选、上新时间、Q-12及Q-03未自动转为已确认规则。图表一致性见[独立关系图](relations-bouquet.md)，运行验证未执行。

## 8 与总体ER的整合对照

本域沿用总体ER的seller_id→user.id、category.name唯一、category.sort_no、bouquet.price、bouquet_image.image_url及sort_no。image_url为可访问图片地址或由存储服务解析的定位字符串，字段VARCHAR(512)为本域长度提案。总体图尚未展开的meaning_scene、description、color、festival_slot、version及时间字段以本域字典补齐；不得把总体图“关键属性”误当作完整数据字典。花束上下架三态按UC-01/07明确，订单三态占位按D-03分别处理。

商家账号停用后花束是否继续可检索，用户字典第10节及总体ER仍列未决。本稿不擅自增加隐藏规则；发布/管理请求须核对当前账号可用性，检索是否增加user.status过滤待小组统一并同步需求。


## 9 参考DDL（按Issue #9补充，未执行）

对应[T4 #9](https://github.com/Longqc666/243-25-project/issues/9)。以下仅说明设计如何落到表，未执行建表、插入或约束测试；不是已验证可部署的脚本。依据[MySQL 8.0 CHECK文档](https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html)，采用MySQL 8.0.16及以上实际执行CHECK的版本/InnoDB/utf8mb4作为参考，实际环境先核对。user须先按用户域创建，主键BIGINT UNSIGNED；分类名称的比较规则随全组数据库排序规则统一。

```sql
CREATE TABLE category (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  sort_no INT NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_category_name (name),
  CONSTRAINT ck_category_name CHECK (CHAR_LENGTH(TRIM(name)) > 0),
  CONSTRAINT ck_category_sort CHECK (sort_no >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bouquet (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  seller_id BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock_qty INT NOT NULL,
  meaning_scene VARCHAR(500) NOT NULL,
  description TEXT NULL,
  color VARCHAR(32) NULL DEFAULT NULL,
  festival_slot VARCHAR(64) NULL DEFAULT NULL,
  status VARCHAR(16) NOT NULL DEFAULT '已下架（待上架）',
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_bouquet_seller (seller_id),
  KEY idx_bouquet_category (category_id),
  CONSTRAINT fk_bouquet_seller FOREIGN KEY (seller_id) REFERENCES `user`(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_bouquet_category FOREIGN KEY (category_id) REFERENCES category(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_bouquet_name CHECK (CHAR_LENGTH(TRIM(name)) > 0),
  CONSTRAINT ck_bouquet_price CHECK (price > 0),
  CONSTRAINT ck_bouquet_stock CHECK (stock_qty >= 0),
  CONSTRAINT ck_bouquet_meaning CHECK (CHAR_LENGTH(TRIM(meaning_scene)) > 0),
  CONSTRAINT ck_bouquet_status CHECK (status IN ('已下架（待上架）','已上架','已下架')),
  CONSTRAINT ck_bouquet_version CHECK (version >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bouquet_image (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  bouquet_id BIGINT UNSIGNED NOT NULL,
  image_url VARCHAR(512) NOT NULL,
  sort_no INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_image_bouquet (bouquet_id),
  CONSTRAINT fk_image_bouquet FOREIGN KEY (bouquet_id) REFERENCES bouquet(id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT ck_image_url CHECK (CHAR_LENGTH(TRIM(image_url)) > 0),
  CONSTRAINT ck_image_sort CHECK (sort_no >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

角色/归属、账号可用性、日期算法、颜色/档期选项、成功发布至少一张图、版本递增、updated_at更新及跨表库存事务由应用承担，DDL未伪造这些保证。余量0且状态已上架是正常售罄情形，不加会阻止最后一束成交的全局CHECK。商家改价/改量提交旧版本时拒绝覆盖。
