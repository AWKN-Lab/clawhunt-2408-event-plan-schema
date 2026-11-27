"""活动方案输出 Schema 校验（S5-OPS-009）。

只做一件事：用 draft 2020-12 校验活动方案 JSON。
校验后的内容只进入复核队列，不得直接对外发送（本模块不发任何请求）。
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "schemas" / "ops" / "event_plan.v1.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def check_schema_meta() -> None:
    """AC4：Schema 本身通过 draft 2020-12 元模式校验。"""
    Draft202012Validator.check_schema(load_schema())


def validate_data(data: dict) -> list:
    """返回全部校验错误（空列表表示通过）。"""
    return list(Draft202012Validator(load_schema()).iter_errors(data))


def validate_file(path: str | Path) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_data(data)


def error_summary(errors: list) -> str:
    """第一条错误的人可读摘要：字段路径 + 校验器 + 原因。"""
    if not errors:
        return "valid"
    first = errors[0]
    path = ".".join(str(p) for p in first.absolute_path) or "(root)"
    return f"{path}: [{first.validator}] {first.message}"
