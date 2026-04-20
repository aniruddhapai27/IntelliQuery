from ai.agents.sql_agent import SQLAgent


def test_sql_normal_form_single_table_is_2nf():
    agent = SQLAgent()
    assert agent.classify_normal_form("SELECT id, name FROM customers LIMIT 10") == "2NF"


def test_sql_normal_form_join_query_is_3nf():
    agent = SQLAgent()
    assert (
        agent.classify_normal_form(
            "SELECT c.name, o.total FROM customers c JOIN orders o ON c.id = o.customer_id"
        )
        == "3NF"
    )


def test_sql_normal_form_non_select_returns_none():
    agent = SQLAgent()
    assert agent.classify_normal_form("DELETE FROM customers") is None
