#!/usr/bin/env python3
"""变异自证：证明测试真的在校验 Schema，而不是走过场。

三相，全部在临时复制的目录里跑，原始样例与 Schema 的 SHA256 前后不变：
  A 相：原样跑 pytest，全部通过。
  B 相：把 Schema 改坏两处，各跑对应的测试，测试必须变红——
    B1：删掉 materials 项的 additionalProperties:false，
        则“materials 加入 price 字段应失败”的测试必须失败；
    B2：删掉 risks 的 minItems:3，
        则“risks 少于 3 项应失败”的测试必须失败。
  C 相：样例与 Schema 的 SHA256 与变异前一致（变异只发生在临时副本里）。

任一相不符即退出非零；三相全过打印 MUTATION CHECK: PASS。
临时目录走 TMPDIR 或家目录缓存，不往 /tmp 堆大目录（/tmp 只有约 400MB 空闲）。
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_REL = Path("schemas/ops/event_plan.v1.json")


def sha256_tree(base: Path) -> dict[str, str]:
    out = {}
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix == ".json":
            rel = str(path.relative_to(base))
            if rel.startswith(("schemas/", "examples/")):
                out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def run_pytest(cwd: Path, select: str | None = None) -> int:
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if select:
        cmd += ["-k", select]
    env = dict(os.environ, PYTHONPATH=str(cwd / "src"))
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=300)
    return proc.returncode


def main() -> int:
    before = sha256_tree(ROOT)
    tmp_parent = Path(os.environ.get("TMPDIR") or Path.home() / ".cache" / "clawhunt-tmp")
    tmp_parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="clawhunt-2408-mutation-", dir=tmp_parent))
    try:
        shutil.copytree(
            ROOT, work / "copy",
            ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "evidence"),
        )
        copy = work / "copy"

        print("A 相：原样 pytest 应全过")
        if run_pytest(copy) != 0:
            print("MUTATION CHECK: FAIL（A 相：原样测试未通过）")
            return 1
        print("A 相通过")

        print("B1 相：删 materials additionalProperties:false，price 测试必须变红")
        schema_path = copy / SCHEMA_REL
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        del schema["properties"]["materials"]["items"]["additionalProperties"]
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if run_pytest(copy, "price_in_materials") == 0:
            print("MUTATION CHECK: FAIL（B1 相：删掉拦截后 price 测试仍通过，测试未覆盖 AC2）")
            return 1
        print("B1 相通过（price 测试变红）")

        print("B2 相：删 risks minItems:3，risks 测试必须变红")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        del schema["properties"]["risks"]["minItems"]
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if run_pytest(copy, "risks_fewer_than_three") == 0:
            print("MUTATION CHECK: FAIL（B2 相：删掉下限后 risks 测试仍通过，测试未覆盖 AC3）")
            return 1
        print("B2 相通过（risks 测试变红）")

        print("C 相：原始样例与 Schema 的 SHA256 应与变异前一致")
        after = sha256_tree(ROOT)
        if before != after:
            print("MUTATION CHECK: FAIL（C 相：原始文件被改动）")
            for key in sorted(set(before) | set(after)):
                if before.get(key) != after.get(key):
                    print(f"  changed: {key}")
            return 1
        print(f"C 相通过（{len(before)} 个 JSON 文件 SHA256 一致）")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("MUTATION CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
