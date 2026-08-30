"""
tests/test_executor.py
Unit tests for Pandas code execution (no live DB required).
Run: pytest tests/test_executor.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from src.db.executor import execute_pandas_code


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "customer_id": [1, 2, 3, 1, 2],
        "revenue": [1000.0, 2500.0, 800.0, 1500.0, 3000.0],
        "region": ["North", "South", "North", "South", "North"],
    })


class TestPandasExecution:
    def test_simple_aggregation(self, sample_df):
        code = "result = df.groupby('customer_id')['revenue'].sum().reset_index()"
        ok, result, err = execute_pandas_code(code, sample_df)
        assert ok
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_filter_and_sort(self, sample_df):
        code = "result = df[df['revenue'] > 1000].sort_values('revenue', ascending=False)"
        ok, result, err = execute_pandas_code(code, sample_df)
        assert ok
        assert all(result["revenue"] > 1000)

    def test_no_df_injected(self):
        code = "result = 42"
        ok, result, err = execute_pandas_code(code)
        assert ok
        assert result == 42

    def test_syntax_error_caught(self, sample_df):
        code = "result = df.groupby('x'"   # unclosed paren
        ok, result, err = execute_pandas_code(code, sample_df)
        assert not ok
        assert err

    def test_runtime_error_caught(self, sample_df):
        code = "result = df['nonexistent_column'].sum()"
        ok, result, err = execute_pandas_code(code, sample_df)
        assert not ok
        assert err
