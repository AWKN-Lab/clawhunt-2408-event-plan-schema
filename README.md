# 活动方案输出 Schema（S5-OPS-009）

ClawHunt #2408 最小可验证样品：会员空间平台活动方案输出 JSON Schema（draft 2020-12），
覆盖议程、分工、物料、宣传节奏与风险预案。

## 一句话

`schemas/ops/event_plan.v1.json` 定义活动方案的输出结构；
`examples/` 给出 5 份合法与 5 份非法虚构样例；
`src/event_plan/` 提供校验模块；`tests/` 用 pytest 覆盖四条验收标准；
`seed/` 给出登记到网关 Schema 注册表的种子条目。

## 快速开始

```bash
bash setup.sh   # 建 venv、装依赖、演示、pytest、变异自证、MANIFEST 核验，全过打印 SELFTEST: PASS
```

只校验单个文件：

```bash
python3 scripts/validate.py examples/valid/valid-01.json
python3 scripts/validate.py --all    # 元模式 + 5 合法过 + 5 非法败，末尾 DEMO: PASS
python3 scripts/validate.py --meta   # 只校验 Schema 自身的元模式
```

只跑测试（需先装依赖）：

```bash
PYTHONPATH=src python3 -m pytest -q
```

## 文件说明

| 文件 | 说明 |
|---|---|
| `schemas/ops/event_plan.v1.json` | 本单交付的 Schema（draft 2020-12） |
| `examples/valid/valid-01..05.json` | 5 份合法虚构样例，校验全部通过 |
| `examples/invalid/invalid-01..05.json` | 5 份非法虚构样例，各自因预期原因失败 |
| `src/event_plan/validate.py` | 校验模块：元模式校验、文件校验、错误摘要 |
| `scripts/validate.py` | 校验命令行（演示入口） |
| `scripts/mutation_check.py` | 变异自证：改坏 Schema 后对应测试必须变红 |
| `tests/test_event_plan.py` | pytest 测试，覆盖四条验收标准与边界 |
| `seed/gw_output_schemas-ops.event_plan.v1.json` | 注册表种子条目（schema_id ops.event_plan，version 1，status draft） |
| `docs/FIELDS.md` | 字段说明表 |
| `ACCEPTANCE-EVIDENCE.md` | 验收证据：测试数、变异、SELFTEST 的实测记录 |
| `MANIFEST` | 逐文件 SHA256 清单（不含 MANIFEST 自身与自测输出日志） |
| `setup.sh` / `requirements.txt` | 一键复跑 / 依赖（jsonschema、pytest） |

## 验收标准对照

1. 5 份合法样例校验通过、5 份非法样例各自因预期原因失败（测试输出）——`tests/test_event_plan.py` 的 5+5 参数化测试，非法样例的预期失败原因见下表。
2. 在 materials 项中加入 price 字段的样例校验失败（单元测试）——`test_price_in_materials_fails`：materials 项 `additionalProperties` 为 false，price 触发 additionalProperties 错误。
3. risks 少于 3 项的样例校验失败（单元测试）——`test_risks_fewer_than_three_fails`：risks 的 `minItems` 为 3。
4. Schema 本身通过 draft 2020-12 元模式校验——`test_schema_passes_draft202012_meta_validation`，即 `Draft202012Validator.check_schema` 通过。

非法样例的预期失败原因：

| 样例 | 预期失败 |
|---|---|
| invalid-01-price-in-materials.json | additionalProperties（materials 项出现 price） |
| invalid-02-risks-too-few.json | minItems（risks 只有 2 项） |
| invalid-03-title-too-long.json | maxLength（title 41 字） |
| invalid-04-agenda-too-few.json | minItems（agenda 只有 2 项） |
| invalid-05-kpi-name-not-in-enum.json | enum（kpi name 为“报名率”） |

## 关键口径（与任务描述一致）

- title 不超过 40 字、one_liner 不超过 60 字；agenda 3–20 项，start/end 为 HH:MM；
  roles 的 due 与 promotion_plan 的 day 匹配 `^T[+-][0-9]+$`（如 T-14、T+1）。
- kpis 的 name 只取 报名人数 / 到场率 / 新增对接意向数 / 满意度，target_value 为整数。
- agenda 的 format 只取 开场 / 分享 / 圆桌 / 互动 / 对接 / 茶歇 / 合影。
- promotion_plan 的 channel 只取 公众号 / 小红书 / 社群 / 朋友圈 / 小程序通知 / 站内通知。
- materials 项 `additionalProperties` 为 false，因此无法出现价格字段，AI 不计算金额；
  quantity 为非负整数。
- risks 至少 3 项，每项含 risk、likelihood（低 / 中 / 高）、mitigation。
- 顶层保留可选字段 lint_issues，由系统入队前写入，提示词要求模型不输出该字段。
- 校验后的内容只进入复核队列，不得直接对外发送；本样品不发任何网络请求。

## 对接点（生产集成时）

- 注册表登记：`seed/` 的种子条目对应 S5-GW-021 注册表的 gw_output_schemas 表
  （schema_id ops.event_plan、version 1、status draft）；生产登记时把种子条目写入注册表即可，
  json_schema 字段内容与 `schemas/ops/event_plan.v1.json` 逐字节一致。
- 网关复核队列（S5-GW）：调用方按本 Schema 校验 AI 输出，通过后进入复核队列；
  lint_issues 由系统入队前写入，不由模型输出。
- 只用虚构测试数据，不出现客户名称与任何真实个人信息。

## 测试结果

见 `ACCEPTANCE-EVIDENCE.md` 与 `evidence/` 下的原始日志。
