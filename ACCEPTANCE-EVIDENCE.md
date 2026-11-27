# 验收证据（S5-OPS-009，#2408）

实测环境：Python 3.12.3，pytest 9.2.0，jsonschema 4.26.0。
原始日志见 `evidence/`。

## pytest：25 passed

- `PYTHONPATH=src python -m pytest -q`：25 passed in 0.23s
- 构成：元模式 1 项、顶层字段口径 1 项、合法样例 5 项、非法样例 5 项、
  AC2（price）2 项、AC3（risks）2 项、边界单元 8 项、种子条目一致性 1 项

## AC1：5 合法过、5 非法各因预期原因失败

- 演示 `python3 scripts/validate.py --all`：DEMO: PASS
- valid-01..05 全部 PASS
- invalid-01 additionalProperties：materials.0 出现 price，
  `Additional properties are not allowed ('price' was unexpected)`
- invalid-02 minItems：risks 只有 2 项，`is too short`
- invalid-03 maxLength：title 41 字，`is too long`
- invalid-04 minItems：agenda 只有 2 项，`is too short`
- invalid-05 enum：kpis.0.name 为“报名率”，不在枚举内

## AC2：materials 项加入 price 字段校验失败

- `test_price_in_materials_fails`：materials[0] 加 price 后报错，
  validator 为 additionalProperties，错误信息含 price
- `test_price_in_any_material_item_fails`：最后一项加 price 同样失败

## AC3：risks 少于 3 项校验失败

- `test_risks_fewer_than_three_fails`：risks 截到 2 项后报错，validator 为 minItems
- `test_risks_exactly_three_passes`：risks 恰好 3 项时校验通过

## AC4：Schema 本身通过 draft 2020-12 元模式校验

- `test_schema_passes_draft202012_meta_validation`：
  `Draft202012Validator.check_schema` 通过
- 演示同样打印 `META PASS schemas/ops/event_plan.v1.json`

## 变异自证：MUTATION CHECK: PASS

- A 相：原样 pytest 全部通过
- B1 相：删掉 materials 项的 additionalProperties:false 后，
  price 测试变红（AC2 有真实覆盖）
- B2 相：删掉 risks 的 minItems:3 后，risks 测试变红（AC3 有真实覆盖）
- C 相：11 个 JSON 文件（Schema + 10 份样例）SHA256 与变异前一致

## 一键复跑：SELFTEST: PASS

- `bash setup.sh`：演示 DEMO: PASS、pytest 25 passed、变异自证 PASS、MANIFEST 全 OK
- 完整输出见 `evidence/selftest-setup-sh-20261127.log`

## MANIFEST

- `sha256sum -c MANIFEST` 全 OK
- 清单不含 MANIFEST 自身与自测输出日志
  `evidence/selftest-setup-sh-20261127.log`（后者写入即改变自身哈希，
  无法列入清单自证；该日志仍在仓内，README 已写明）

## Schema 与种子条目

- Schema SHA256：4c29c9f3cdfc19e3030d5410dd2a39d2c05f455fedcf0e673dc2c3cec6150d45
- 种子条目 `seed/gw_output_schemas-ops.event_plan.v1.json`：
  schema_id ops.event_plan、version 1、status draft，
  内嵌 json_schema 与 Schema 文件内容一致（测试 `test_registry_seed_matches_schema_file` 覆盖）
