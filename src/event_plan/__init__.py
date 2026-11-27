"""活动方案输出 Schema 校验包（S5-OPS-009）。"""

from .validate import check_schema_meta, error_summary, load_schema, validate_data, validate_file

__all__ = ["check_schema_meta", "error_summary", "load_schema", "validate_data", "validate_file"]
