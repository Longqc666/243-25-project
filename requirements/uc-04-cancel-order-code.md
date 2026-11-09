# UC-04 取消订单 —— 流程示意代码（辅助材料）

> 配套 [uc-04-cancel-order.md](uc-04-cancel-order.md) v0.2 · 2026-11-09 ｜ 非实验一交付物
> 说明：实验一要求需求只写业务结果、不写实现。本代码仅用于把 FR-07、B-05、B-06、NFR-01、NFR-02、NFR-03 的约束表达成可走读的流程，不绑定技术选型；幂等判重位置与 UC-03 v0.2 第 3 步同口径（判重先于归属与状态校验）。实验二、三再演化为正式设计。

```java
/** 示意代码：取消订单（UC-04 v0.2）。表达业务约束，非实现要求。 */
CancelResult cancelOrder(long orderId, User loginUser, String idempotencyKey) {
    // 1) 登录与角色校验（FR-08 / A1）
    if (loginUser == null) {
        return CancelResult.redirectToLogin();                  // 未登录：引导登录（A1），不做任何变更（F1—F4）
    }
    if (loginUser.role != Role.CUSTOMER) {
        return CancelResult.reject("仅顾客本人可取消");          // 商家/管理员：角色不符（A1、Q-05、AC-UC04-06）
    }

    // 2) 幂等判重：命中即返回首次成功结果，不再校验归属与状态（NFR-02 / A3，与 UC-03 v0.2 第 3 步同口径）
    CancelResult seen = idempotencyStore.get(idempotencyKey);
    if (seen != null) {
        return seen;                                            // S-05：旧请求再次到达，不得改判拒绝
    }

    // 3) 归属与存在性校验：统一提示，不泄露他人订单信息（NFR-03 / A2）
    Order order = orderDao.findById(orderId);
    if (order == null || !order.customerId.equals(loginUser.id)) {
        return CancelResult.reject("订单不存在或无权操作");       // 响应不含原属顾客姓名、联系方式
    }

    // 4) 状态与时限校验：仅"有效"且在时限内可取消（B-06 / A3、A4）
    if (OrderStatus.CANCELED.equals(order.status)) {
        return CancelResult.of("订单已取消");                    // 无幂等键命中的新请求遇到已取消订单（A3）
    }
    if (!OrderStatus.VALID.equals(order.status)
            || !withinCancelWindow(order, now())) {             // 暂定：送达日期 0:00 前（本用例第 6 节）
        return CancelResult.reject("该订单当前状态或时间不可取消");
    }

    // 5) 条件更新 + 回补 + 历史写入：同一事务，要么同时变更、要么都不变更（NFR-01 类比 / A5、A6）
    int updated = orderDao.updateStatusIfValid(orderId, OrderStatus.CANCELED, now(), loginUser.id);
    if (updated == 0) {
        return CancelResult.of("订单已取消");                    // 并发下另一请求已完成取消
    }
    bouquetDao.increaseAvailable(order.bouquetId, order.quantity);   // 回补 +N（B-06：仅回补原订单一次，写回 UC-07 维护的可预订数量）
    orderHistoryDao.append(orderId, OrderStatus.VALID, OrderStatus.CANCELED, loginUser.id, now());  // 历史只增不删

    CancelResult ok = CancelResult.success(orderId, order.bouquetId, order.quantity, now());
    idempotencyStore.put(idempotencyKey, ok);
    return ok;
}
```

与用例正文的对应关系：步骤 1—2 → 代码 1)；步骤 3 → 代码 2)；步骤 4 → 代码 3)；步骤 5 → 代码 4)；步骤 6—7 → 代码 5)；失败路径 A1—A6 与各 return 一一对应。
