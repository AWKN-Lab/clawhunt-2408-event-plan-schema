# 字段说明表：活动方案输出 Schema v1（S5-OPS-009）

Schema 文件：`schemas/ops/event_plan.v1.json`（draft 2020-12）。
除 lint_issues 外全部为必填顶层字段；lint_issues 为顶层保留可选字段。

## 顶层字段

| 字段 | 类型 | 必填 | 约束 | 说明 |
|---|---|---|---|---|
| title | string | 是 | 1–40 字 | 活动标题 |
| one_liner | string | 是 | 1–60 字 | 一句话介绍 |
| goal | string | 是 | 非空 | 活动目标 |
| kpis | array | 是 | 至少 1 项 | 目标指标，见下 |
| agenda | array | 是 | 3–20 项 | 议程，见下 |
| roles | array | 是 | 至少 1 项 | 分工，见下 |
| materials | array | 是 | 项内 additionalProperties=false | 物料，见下；无法出现价格字段，AI 不计算金额 |
| promotion_plan | array | 是 | 至少 1 项 | 宣传节奏，见下 |
| risks | array | 是 | 至少 3 项 | 风险预案，见下 |
| signup_suggestion | object | 是 | mode / capacity / waitlist 必填 | 报名建议，见下 |
| pending_items | array | 是 | 每项为非空字符串 | 待确认事项 |
| lint_issues | array | 否 | 每项含 code、message | 顶层保留字段，由系统入队前写入，提示词要求模型不输出该字段 |

## kpis（数组每项）

| 字段 | 类型 | 约束 |
|---|---|---|
| name | string | 枚举：报名人数 / 到场率 / 新增对接意向数 / 满意度 |
| target_value | integer | 目标值，整数 |

## agenda（数组每项）

| 字段 | 类型 | 约束 |
|---|---|---|
| start | string | HH:MM，如 14:00 |
| end | string | HH:MM，如 14:10 |
| segment | string | 环节名称，非空 |
| purpose | string | 环节目的，非空 |
| format | string | 枚举：开场 / 分享 / 圆桌 / 互动 / 对接 / 茶歇 / 合影 |
| owner_role | string | 负责角色，非空 |

## roles（数组每项）

| 字段 | 类型 | 约束 |
|---|---|---|
| role | string | 角色名，非空 |
| tasks | array | 至少 1 项，每项为非空字符串 |
| due | string | 截止日，匹配 `^T[+-][0-9]+$`，如 T-7、T+1 |

## materials（数组每项）

| 字段 | 类型 | 约束 |
|---|---|---|
| name | string | 物料名，非空 |
| quantity | integer | 数量，非负整数 |
| owner_role | string | 负责角色，非空 |

本对象 additionalProperties 为 false：除上述三字段外任何字段（含 price）都会导致校验失败。

## promotion_plan（数组每项）

| 字段 | 类型 | 约束 |
|---|---|---|
| day | string | 宣传日，匹配 `^T[+-][0-9]+$`，如 T-14、T+1 |
| channel | string | 枚举：公众号 / 小红书 / 社群 / 朋友圈 / 小程序通知 / 站内通知 |
| action | string | 宣传动作，非空 |

## risks（数组每项）

| 字段 | 类型 | 约束 |
|---|---|---|
| risk | string | 风险描述，非空 |
| likelihood | string | 枚举：低 / 中 / 高 |
| mitigation | string | 应对措施，非空 |

## signup_suggestion（对象）

| 字段 | 类型 | 约束 |
|---|---|---|
| mode | string | 报名方式，如先到先得、审核制，非空 |
| capacity | integer | 名额上限，非负整数 |
| waitlist | boolean | 是否开启候补名单 |

## 样例对照

- 5 份合法样例：`examples/valid/valid-01..05.json`（春季会员对接会、新会员欢迎日、出海经验分享会、季度资源对接专场、会员年终答谢会）。
- 5 份非法样例：`examples/invalid/`，每份只改一处，预期失败原因见 README。
