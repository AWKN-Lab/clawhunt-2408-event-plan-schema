#!/usr/bin/env bash
# #2408 最小样品一键自测（setup.sh）
#
# 解释器选择分两条线，互不干扰：
#   PY      —— 按版本选：第一个 Python >= 3.11 的候选解释器（跑脚本用）。
#   TEST_PY —— 按 pytest 选：遍历候选解释器，逐个试 `python -c "import pytest"`，
#              第一个能过的就是测试解释器；找不到时先建本地 venv 装依赖再重找，
#              仍找不到就报错退出，绝不跳过自测。
# 任何一步失败都退出非零；自测结果（演示、pytest、变异自证、MANIFEST 核验）全部打印出来。
set -u
cd "$(dirname "$0")"

# /tmp 只有 512MB tmpfs，满了会导致 venv 创建（ensurepip 写临时文件）失败；
# 剩余不足 100MB 时改用家目录下的临时目录（pytest 与变异脚本同样走 TMPDIR）。
TMP_AVAIL_KB="$(df -k /tmp 2>/dev/null | awk 'NR==2 {print $4}')"
if [ -n "$TMP_AVAIL_KB" ] && [ "$TMP_AVAIL_KB" -lt 102400 ]; then
  export TMPDIR="$HOME/.cache/clawhunt-tmp"
  mkdir -p "$TMPDIR"
  echo "注意：/tmp 剩余不足 100MB，临时目录改用 $TMPDIR"
fi

CANDIDATES=".venv/bin/python python3.12 python3.11 python3 python"

exists() { [ -x "$1" ] || command -v "$1" >/dev/null 2>&1; }

pick_py() {
  for c in $CANDIDATES; do
    if exists "$c"; then
      if "$c" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        echo "$c"
        return 0
      fi
    fi
  done
  return 1
}

pick_test_py() {
  for c in $CANDIDATES; do
    if exists "$c"; then
      if "$c" -c "import pytest" 2>/dev/null; then
        echo "$c"
        return 0
      fi
    fi
  done
  return 1
}

PY="$(pick_py)" || { echo "ERROR: 未找到 Python >= 3.11 的解释器" >&2; exit 1; }
echo "PY=$PY ($("$PY" --version 2>&1))"

TEST_PY="$(pick_test_py)" || {
  echo "未找到能 import pytest 的解释器，尝试建本地 venv 并安装依赖..."
  "$PY" -m venv .venv || { echo "ERROR: 创建 venv 失败；不要跳过自测。" >&2; exit 1; }
  ./.venv/bin/pip install -r requirements.txt || { echo "ERROR: 安装依赖失败；不要跳过自测。" >&2; exit 1; }
  TEST_PY="$(pick_test_py)" || {
    echo "ERROR: 安装后仍未找到能 import pytest 的解释器；不要跳过自测。" >&2
    exit 1
  }
}
echo "TEST_PY=$TEST_PY ($("$TEST_PY" -c "import pytest; print('pytest', pytest.__version__)" 2>&1))"

echo "=== 1/4 演示：元模式 + 5 合法过 + 5 非法败（应 DEMO: PASS）==="
"$PY" scripts/validate.py --all || { echo "ERROR: 演示未通过" >&2; exit 1; }

echo "=== 2/4 自测 pytest ==="
PYTHONPATH=src "$TEST_PY" -m pytest -q || { echo "ERROR: pytest 未通过" >&2; exit 1; }

echo "=== 3/4 变异自证（应 MUTATION CHECK: PASS）==="
"$TEST_PY" scripts/mutation_check.py || { echo "ERROR: 变异自证未通过" >&2; exit 1; }

echo "=== 4/4 核对 MANIFEST ==="
sha256sum -c MANIFEST || { echo "ERROR: MANIFEST 核对失败" >&2; exit 1; }

echo "SELFTEST: PASS"
exit 0
