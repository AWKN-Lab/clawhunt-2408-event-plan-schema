"""#2408 活动方案输出 Schema 测试。

覆盖四条验收标准：
  AC1：5 份合法样例校验通过、5 份非法样例各自因预期原因失败
  AC2：materials 项加入 price 字段的样例校验失败
  AC3：risks 少于 3 项的样例校验失败
  AC4：Schema 本身通过 draft 2020-12 元模式校验
另加边界单元测试：时间格式、T±N 格式、枚举、整数、非负数、40 字上限。
只用虚构数据，不出现真实个人信息与企业信息。
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from event_plan import check_schema_meta, load_schema, validate_data

ROOT = Path(__file__).resolve().parent.parent
VALID_DIR = ROOT / "examples" / "valid"
INVALID_DIR = ROOT / "examples" / "invalid"

EXPECTED_INVALID = {
    "invalid-01-price-in-materials.json": ("additionalProperties", ["materials", 0]),
    "invalid-02-risks-too-few.json": ("minItems", ["risks"]),
    "invalid-03-title-too-long.json": ("maxLength", ["title"]),
    "invalid-04-agenda-too-few.json": ("minItems", ["agenda"]),
    "invalid-05-kpi-name-not-in-enum.json": ("enum", ["kpis", 0, "name"]),
}


def load_example(name: str, invalid: bool = False) -> dict:
    folder = INVALID_DIR if invalid else VALID_DIR
    return json.loads((folder / name).read_text(encoding="utf-8"))


def first_error_for(data: dict, path: list) -> object | None:
    for err in validate_data(data):
        if list(err.absolute_path) == path:
            return err
    return None


# ---- AC4：Schema 本身通过 draft 2020-12 元模式校验 ----

def test_schema_passes_draft202012_meta_validation():
    check_schema_meta()


def test_schema_top_level_fields_match_spec():
    schema = load_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(schema["required"]) == {
        "title", "one_liner", "goal", "kpis", "agenda", "roles",
        "materials", "promotion_plan", "risks", "signup_suggestion", "pending_items",
    }
    assert "lint_issues" in schema["properties"]
    assert "lint_issues" not in schema["required"]
    assert schema["properties"]["agenda"]["minItems"] == 3
    assert schema["properties"]["agenda"]["maxItems"] == 20
    assert schema["properties"]["risks"]["minItems"] == 3
    assert schema["properties"]["materials"]["items"]["additionalProperties"] is False


# ---- AC1：5 份合法样例校验通过 ----

@pytest.mark.parametrize("name", sorted(p.name for p in VALID_DIR.glob("*.json")))
def test_valid_examples_pass(name):
    assert len(list(VALID_DIR.glob("*.json"))) == 5
    assert validate_data(load_example(name)) == []


# ---- AC1：5 份非法样例各自因预期原因失败 ----

@pytest.mark.parametrize("name", sorted(EXPECTED_INVALID))
def test_invalid_examples_fail_with_expected_reason(name):
    expected_validator, expected_path = EXPECTED_INVALID[name]
    errors = validate_data(load_example(name, invalid=True))
    assert errors, f"{name} 应校验失败却通过了"
    err = first_error_for(load_example(name, invalid=True), expected_path)
    assert err is not None, f"{name} 未在 {expected_path} 处报错"
    assert err.validator == expected_validator


# ---- AC2：materials 项加入 price 字段校验失败 ----

def test_price_in_materials_fails():
    data = load_example("valid-01.json")
    data["materials"][0]["price"] = 1200
    err = first_error_for(data, ["materials", 0])
    assert err is not None and err.validator == "additionalProperties"
    assert "price" in err.message


def test_price_in_any_material_item_fails():
    data = load_example("valid-01.json")
    data["materials"][-1]["price"] = 1
    assert validate_data(data), "任一 materials 项加 price 都应失败"


# ---- AC3：risks 少于 3 项校验失败 ----

def test_risks_fewer_than_three_fails():
    data = load_example("valid-01.json")
    data["risks"] = data["risks"][:2]
    err = first_error_for(data, ["risks"])
    assert err is not None and err.validator == "minItems"


def test_risks_exactly_three_passes():
    data = load_example("valid-01.json")
    data["risks"] = data["risks"][:3]
    assert validate_data(data) == []


# ---- 边界单元测试 ----

def test_agenda_time_must_be_hh_mm():
    data = load_example("valid-01.json")
    data["agenda"][0]["start"] = "9:00"  # 缺前导零
    assert first_error_for(data, ["agenda", 0, "start"]) is not None
    data = load_example("valid-01.json")
    data["agenda"][0]["end"] = "25:00"  # 小时越界
    assert first_error_for(data, ["agenda", 0, "end"]) is not None


def test_due_and_promotion_day_must_match_T_plus_minus_N():
    data = load_example("valid-01.json")
    data["roles"][0]["due"] = "D-3"
    assert first_error_for(data, ["roles", 0, "due"]) is not None
    data = load_example("valid-01.json")
    data["promotion_plan"][0]["day"] = "3天前"
    assert first_error_for(data, ["promotion_plan", 0, "day"]) is not None


def test_agenda_format_and_channel_must_be_in_enum():
    data = load_example("valid-01.json")
    data["agenda"][0]["format"] = "演讲"
    assert first_error_for(data, ["agenda", 0, "format"]) is not None
    data = load_example("valid-01.json")
    data["promotion_plan"][0]["channel"] = "短信"
    assert first_error_for(data, ["promotion_plan", 0, "channel"]) is not None


def test_kpi_target_value_must_be_integer():
    data = load_example("valid-01.json")
    data["kpis"][0]["target_value"] = 85.5
    assert first_error_for(data, ["kpis", 0, "target_value"]) is not None


def test_material_quantity_must_be_non_negative_integer():
    data = load_example("valid-01.json")
    data["materials"][0]["quantity"] = -1
    assert first_error_for(data, ["materials", 0, "quantity"]) is not None


def test_title_max_40_chars_boundary():
    data = load_example("valid-01.json")
    data["title"] = "春" * 40
    assert validate_data(data) == []
    data["title"] = "春" * 41
    assert first_error_for(data, ["title"]) is not None


def test_lint_issues_is_optional_and_allowed():
    data = load_example("valid-01.json")
    assert "lint_issues" not in data
    assert validate_data(data) == []
    data["lint_issues"] = [{"code": "TITLE_TOO_LONG", "message": "标题超过建议长度"}]
    assert validate_data(data) == []


def test_agenda_more_than_20_items_fails():
    data = load_example("valid-01.json")
    extra = copy.deepcopy(data["agenda"][0])
    while len(data["agenda"]) < 21:
        data["agenda"].append(copy.deepcopy(extra))
    assert first_error_for(data, ["agenda"]) is not None


def test_registry_seed_matches_schema_file():
    """种子条目内嵌的 json_schema 与 Schema 文件逐字节一致（内容相等）。"""
    seed = json.loads((ROOT / "seed" / "gw_output_schemas-ops.event_plan.v1.json").read_text(encoding="utf-8"))
    assert seed["schema_id"] == "ops.event_plan"
    assert seed["version"] == 1
    assert seed["status"] == "draft"
    assert seed["json_schema"] == load_schema()
