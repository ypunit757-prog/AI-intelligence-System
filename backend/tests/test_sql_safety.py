from app.tools.registry import _is_safe_readonly_sql


def test_select_allowed():
    assert _is_safe_readonly_sql("SELECT * FROM documents")


def test_drop_blocked():
    assert not _is_safe_readonly_sql("DROP TABLE documents")


def test_delete_blocked():
    assert not _is_safe_readonly_sql("DELETE FROM documents")


def test_non_select_blocked():
    assert not _is_safe_readonly_sql("UPDATE documents SET status='x'")
