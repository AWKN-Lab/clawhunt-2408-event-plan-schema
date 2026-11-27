#!/usr/bin/env python3
"""校验命令行：校验一个或多个活动方案 JSON。

用法：
  python3 scripts/validate.py examples/valid/valid-01.json
  python3 scripts/validate.py --meta            # 只校验 Schema 自身的元模式
  python3 scripts/validate.py --all             # 演示：元模式 + 5 合法过 + 5 非法败

每个文件打印一行 PASS / FAIL（含第一条错误摘要）；
--all 末尾打印 DEMO: PASS（全部符合预期）或 DEMO: FAIL。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from event_plan import check_schema_meta, error_summary, validate_file  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_INVALID = {
    "invalid-01-price-in-materials.json": "additionalProperties",
    "invalid-02-risks-too-few.json": "minItems",
    "invalid-03-title-too-long.json": "maxLength",
    "invalid-04-agenda-too-few.json": "minItems",
    "invalid-05-kpi-name-not-in-enum.json": "enum",
}


def check_one(path: Path) -> bool:
    errors = validate_file(path)
    if not errors:
        print(f"PASS {path}")
        return True
    print(f"FAIL {path}: {error_summary(errors)}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="校验活动方案 JSON")
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--meta", action="store_true", help="只校验 Schema 自身的元模式")
    ap.add_argument("--all", action="store_true", help="演示：元模式 + 全部样例")
    args = ap.parse_args()

    ok = True
    if args.meta or args.all:
        try:
            check_schema_meta()
            print("META PASS schemas/ops/event_plan.v1.json")
        except Exception as exc:  # noqa: BLE001
            print(f"META FAIL schemas/ops/event_plan.v1.json: {exc}")
            ok = False

    if args.all:
        for path in sorted((ROOT / "examples" / "valid").glob("*.json")):
            ok = check_one(path) and ok
        for path in sorted((ROOT / "examples" / "invalid").glob("*.json")):
            errors = validate_file(path)
            expected = EXPECTED_INVALID[path.name]
            if errors and errors[0].validator == expected:
                print(f"FAIL(as expected, {expected}) {path}: {error_summary(errors)}")
            else:
                got = errors[0].validator if errors else "passed"
                print(f"UNEXPECTED {path}: expected {expected}, got {got}")
                ok = False
        print("DEMO: PASS" if ok else "DEMO: FAIL")
        return 0 if ok else 1

    if not args.files:
        ap.error("请给出要校验的 JSON 文件，或用 --meta / --all")
    for path in args.files:
        ok = check_one(path) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
