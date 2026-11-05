from orderflow.storage import connect_database, find_orders_by_email, save_order


def test_storage_roundtrip():
    with connect_database() as conn:
        save_order(conn, "student@example.test", 500)
        assert len(find_orders_by_email(conn, "student@example.test")) == 1


def test_storage_rejects_sql_injection_payload():
    with connect_database() as conn:
        save_order(conn, "alice@example.test", 100)
        save_order(conn, "bob@example.test", 200)
        assert find_orders_by_email(conn, "x' OR '1'='1") == []
