"""
tests/test_validator.py
Unit tests for the SQL validation layer.
Run: pytest tests/test_validator.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.validation.sql_validator import SQLValidator

KNOWN_TABLES = {"customers", "orders", "order_items", "products", "sales_reps"}


@pytest.fixture
def validator():
    return SQLValidator(known_tables=KNOWN_TABLES)


class TestBlocklist:
    def test_blocks_drop(self, validator):
        result = validator.validate("DROP TABLE customers")
        assert not result.valid
        assert any("DROP" in e for e in result.errors)

    def test_blocks_delete(self, validator):
        result = validator.validate("DELETE FROM orders WHERE 1=1")
        assert not result.valid

    def test_blocks_truncate(self, validator):
        result = validator.validate("TRUNCATE TABLE order_items")
        assert not result.valid

    def test_blocks_update(self, validator):
        result = validator.validate("UPDATE customers SET email='x@x.com'")
        assert not result.valid

    def test_blocks_insert(self, validator):
        result = validator.validate("INSERT INTO customers VALUES (1,'a')")
        assert not result.valid


class TestSelectAllowed:
    def test_simple_select(self, validator):
        sql = "SELECT customer_id, first_name FROM customers"
        result = validator.validate(sql, schema_tables=KNOWN_TABLES)
        assert result.valid

    def test_select_with_join(self, validator):
        sql = (
            "SELECT c.first_name, SUM(oi.unit_price) AS revenue "
            "FROM customers c "
            "JOIN orders o ON c.customer_id = o.customer_id "
            "JOIN order_items oi ON o.order_id = oi.order_id "
            "GROUP BY c.customer_id "
            "ORDER BY revenue DESC LIMIT 10"
        )
        result = validator.validate(sql, schema_tables=KNOWN_TABLES)
        assert result.valid

    def test_cte_allowed(self, validator):
        sql = (
            "WITH rev AS (SELECT customer_id, SUM(unit_price) AS r "
            "FROM order_items GROUP BY customer_id) "
            "SELECT * FROM rev ORDER BY r DESC LIMIT 5"
        )
        result = validator.validate(sql, schema_tables=KNOWN_TABLES)
        assert result.valid


class TestSchemaCheck:
    def test_warns_unknown_table(self, validator):
        sql = "SELECT * FROM nonexistent_table"
        result = validator.validate(sql, schema_tables=KNOWN_TABLES)
        # Should be invalid (not a SELECT allowed table, but also warn)
        assert len(result.warnings) > 0 or not result.valid

    def test_no_warning_for_known_tables(self, validator):
        sql = "SELECT * FROM customers"
        result = validator.validate(sql, schema_tables=KNOWN_TABLES)
        assert result.valid
        assert not result.warnings


class TestCleaning:
    def test_trailing_semicolon_removed(self, validator):
        sql = "SELECT 1;"
        result = validator.validate(sql)
        assert not result.cleaned_sql.endswith(";")

    def test_whitespace_normalised(self, validator):
        sql = "SELECT   *   FROM   customers"
        result = validator.validate(sql)
        assert "  " not in result.cleaned_sql
