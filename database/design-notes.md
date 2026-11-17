# 数据库设计说明 函数依赖与规范化

> 起草：庞延新（victory0703）｜v0.2｜2026-11-17
> 覆盖T9本轮三张本域关键表，另说明订单快照和流水的保留理由；其他域的最终依赖由对应负责人补充复核。

## 1 基线与设计选择

依据[花束域字典](schema/bouquet.md)、[现有流水字典](schema/order-status.md)、[订单字典](schema/order.md)、[用户字典](schema/user.md)、README的D-01～D-05、B-05/06/08与FR-01～08。字段级结论以本轮v0.2方案及当前已知业务依赖为前提，不替代其他域定稿。

当前库存采用`bouquet.stock_qty`一个权威位置；`stock_change`为事件历史。价格采用花束当前价与订单成交快照分别保存。商家资料、分类名称与花束信息分表，避免更新异常。

## 2 三张关键表的函数依赖

### 2.1 category

- 候选键：`id`、`name`。本域沿用总体ER候选name唯一，最终按统一空白及排序规则检查。
- 主要依赖：`id → name, sort_no`；`name → id, sort_no`。
- 字段为单值；单属性候选键下不存在对键的真子集的部分依赖；本表当前没有非主属性决定其他非主属性的已知依赖。
- 在上述全部已知依赖下符合第三范式。改分类名只改一行，不重写所有花束。

### 2.2 bouquet

- 候选键：`id`。名称可重名可变更；不假定`(seller_id,name)`唯一。
- 主要依赖：`id → seller_id, category_id, name, price, stock_qty, meaning_scene, description, color, festival_slot, status, version, created_at, updated_at`。
- 所有属性均为单值；`meaning_scene`是一个自然语言描述值，不是逗号拼接的多值集合。颜色和档期本版各单值；若多选需关联表。
- 当前候选键为单属性，不存在非主属性的部分依赖。商家名、分类名均不复制到本表，没有已识别的非主属性间传递依赖。
- 在本版依赖集合下符合第三范式；不能仅以存在代理主键推断范式，后续字段变化仍需重查。

若把`category_name`存进本表，会出现`id → category_id → category_name`，分类改名须同时更新多条花束；故分类名留在category，通过引用读取。商家资料同理。

### 2.3 bouquet_image

- 候选键：`id`。`image_url`不假设全局唯一；`(bouquet_id,sort_no)`允许同值，也不是候选键。
- 主要依赖：`id → bouquet_id, image_url, sort_no, created_at`。
- 字段单值，未见部分依赖或非主属性间传递依赖，在当前依赖下符合第三范式。
- 不重复保存所属花束的当前名称、单价等。排序由`sort_no,id`稳定确定，不引入第二个“封面”状态需要同步。

## 3 历史快照与日志为何保留

| 数据 | 业务含义 | 保留理由和维护责任 |
|---|---|---|
| bouquet.price | 当前报价 | 可被商家修改，仅影响之后的新订单 |
| order_item.unit_price | 下单时成交单价 | B-08历史事实；与当前价不是相同时间语义；订单字典v0.2已定义字段，写入后不随花束改价更新 |
| stock_change.before_qty/after_qty | 某次事件发生时的前后量 | 历史审计，不随当前stock_qty回写；应有after=before+delta、前后非负等行内约束 |
| order_status_log.from_status/to_status | 某次状态流转 | 保留订单创建/取消历史，不通过重写当前订单状态替代历史 |

如果流水同时保存before、delta、after，三者存在计算冗余，不能直接宣称整张流水表严格第三范式；本稿只对第2节三张表作范式结论。历史快照和delta冗余的取舍须由流水负责人说明，并用一致性约束维护。

11月17日订单v0.2字典已保存`order_item.quantity`、`unit_price`、`amount`及`orders.total_amount`。其中存在`(quantity,unit_price) → amount`的计算依赖；本稿不据代理主键替明细表宣布严格第三范式。保留行金额、合计时应说明舍入、金额上限和一致性：行金额等于数量乘成交价，订单合计等于本期唯一明细金额；合计由事务维护。使用生成列从不可变的明细快照计算金额，本身也不会破坏成交价快照；这是待订单负责人选择的实现方式。

## 4 库存事务与权限责任

1. 发布：完整保存花束及至少一张图片；本版提议以0为before_qty写初始化流水，after_qty等于初始stock_qty。
2. 新下单：先身份验证及既有成功请求识别；新请求再检查花束状态、数量、日期，并按当前状态与余量条件扣减。订单、明细、库存、适用日志和成功流水整体提交。重试命中不重复扣减。
3. 取消：先身份与请求归属校验，再识别成功重试；新取消核对订单属于本人、状态有效和时限，以订单有效状态作为变化条件，只回补一次。按取消当时实际余量加原数量，不能把余量重置为历史before_qty。
4. 商家改量：提交读取时的版本/旧量；任何已完成的相关变更使条件过期时拒绝覆盖。成功变更记录旧量、新量和差额；零变化不写库存事件为本版提案。
5. 下架和改价不改变已有订单，不删除历史；取消下架花束订单仍可合法回补，且不自动上架。

FK只保证引用存在，不保证“仅本人可操作”；CHECK只检验本行，不替代跨表状态、库存和流水同事务的一致性。只追加日志还需应用写入路径与数据库权限约束，不是去掉updated_at就自然只追加。

## 5 当前需要复核的接口

- 订单域v0.2已暂定一单一种花束；复合唯一键尚不能强制该业务上限，须明确应用保证或共同调整键。扩展多花束前必须同步`UNIQUE(order_id,change_type)`，否则会误拦合法流水。
- 下单幂等与取消幂等属于不同操作；`orders.idempotency_key`不能未经说明同时作为两种独立请求的唯一结果依据。
- 流水前后量等式、操作人取值及实体中的changed_at与字典created_at需统一，详见[接口核对](review/bouquet-order-stock-interface-2026-11-17.md)。

本轮已修正原本地稿把花束当前价误写为unit_price的问题：统一为`bouquet.price`，订单成交价仍为`order_item.unit_price`，ER接口、关系图及函数依赖均同步。

D-01已定主外键UNSIGNED，D-03已定订单枚举，D-04已定系统库存操作人NULL，D-05已定快照/合计及当前值与流水并存；这些决定直接采用。保留冗余的决定不等于每张含计算属性的表都严格第三范式，用户字典/总体ER中相关笼统范式表述建议同步本节的限定。

以上不阻止本域v0.2提交评审，但全组最终版合并前需形成决定并同步ER、字典、关系图、走查及报告。本稿为设计分析，未执行SQL或运行应用。

## 6 技术参考

约束能力参考[MySQL CHECK约束](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html)及[MySQL唯一索引](https://dev.mysql.com/doc/refman/8.4/en/create-index.html)。这些用于解释约束范围，不意味着已确定小组部署的数据库版本。


## 7 跨域关键表函数依赖汇总（对应T9 #10）

依据[任务#10](https://github.com/Longqc666/243-25-project/issues/10)补充订单和库存流水，不复制各域完整字典。字段以订单v0.2、流水v0.1及统稿决定为准。FD描述同一时点有效数据，不假设记录在生命周期内不能改任何值。

| 表 | 已知候选键/主要函数依赖 | 2NF检查 | 3NF检查与取舍 |
|---|---|---|---|
| bouquet | id；id决定第2.2节列出的全部非键属性 | 单属性候选键，无部分依赖 | 不复制角色名/分类名，已知依赖下3NF；商家/分类信息外置 |
| orders | id、order_no、idempotency_key各为非空唯一候选键；每个键决定user_id、status、total_amount、delivery_date、fulfillment_type、created_at、cancelled_at、updated_at及其他候选键 | 各候选键单列，无部分依赖 | 当前没有已知非键决定其他非键的行内FD。明细总和与total_amount是跨表计算冗余，单独说明事务维护；不能只因行内3NF忽略跨表一致性 |
| order_item | id及非空唯一(order_id,bouquet_id)；各键决定quantity、unit_price、amount、created_at | 按已声明键，没有已知非键只依赖order_id或bouquet_id；成交价不是由bouquet_id单独决定的当前价 | (quantity,unit_price)→amount的计算依赖使本期存储金额的关系不严格满足3NF；按D-05保留金额设计，写入校验金额乘积，历史不随当前价更新 |
| stock_change | id为全表候选键，id决定bouquet_id、order_id、change_type、quantity_delta、before_qty、after_qty、user_id、created_at；(order_id,change_type)只在order_id非NULL的订单事件子集唯一，不能作全表候选键 | 全表单列键，无已知部分依赖；商家NULL订单事件不靠该唯一键防重 | (before_qty,quantity_delta)→after_qty，决定因素不是超键，存在计算冗余，不严格3NF。为G3留痕保留前后量，补等式/非负校验，并与当前库存同事务 |

一单一花束是当前业务上限，但物理复合唯一键不能单独实现；应用保证或键修订共同定稿后再检查新的候选键和依赖，不假装扩多花束无需修改流水。

| 保留数据 | 需求与理由 | 维护责任 |
|---|---|---|
| order_item.unit_price | B-08：下单时价格事实，时间语义不同于bouquet.price | 一致版本读取后写入，不随改价重写 |
| orders.total_amount及order_item.amount | FR-05、D-05：保留下单金额；属于有意计算冗余 | 行金额=数量×成交价，合计=明细和；决定精度/舍入/上限，事务一次写入；本期恰好一条明细 |
| bouquet.stock_qty与stock_change | B-05、G3、D-05：当前可用量与历史事件都需读取 | 每次变更事务写当前量和流水，历史不回写；after=before+delta，当前量等于该次写入after |

与用户字典第6节在“保留哪些业务事实”上采用相同决定；对“这些冗余都不违反3NF”的笼统结论作上述限定，并在接口核对中交组长统一。合法快照和计算冗余不是同一种理由，不能用“有历史意义”替代函数依赖检查。最终评审若改金额或日志保存方案，再同步FD及范式结论。
