import llm
import json
from llm_tools_sqlite import sqlite_query, sqlite_list_databases, sqlite_schema
import sqlite_utils


def test_tool(monkeypatch, tmpdir):
    working_dir = str(tmpdir)
    monkeypatch.chdir(working_dir)
    demo = sqlite_utils.Database("demo.db")
    demo["pelicans"].insert_all(
        [
            {"name": "Stella"},
            {"name": "Martha"},
            {"name": "Lola"},
        ]
    )

    model = llm.get_model("echo")
    chain_response = model.chain(
        json.dumps(
            {
                "tool_calls": [
                    {"name": "sqlite_list_databases", "arguments": {}},
                    {
                        "name": "sqlite_query",
                        "arguments": {
                            "database_name": "demo",
                            "sql": "SELECT count(*) n FROM pelicans",
                        },
                    },
                    {"name": "sqlite_schema", "arguments": {"database_name": "demo"}},
                    {
                        "name": "sqlite_query",
                        "arguments": {
                            "database_name": "demo",
                            "sql": "drop table pelicans",
                        },
                    },
                ]
            }
        ),
        tools=[sqlite_query, sqlite_list_databases, sqlite_schema],
    )
    responses = list(chain_response.responses())
    assert len(responses) == 2
    text = responses[-1].text()
    info = json.loads(text)
    assert info["tool_results"] == [
        {"name": "sqlite_list_databases", "output": '["demo"]', "tool_call_id": None},
        {"name": "sqlite_query", "output": '[{"n": 3}]', "tool_call_id": None},
        {
            "name": "sqlite_schema",
            "output": "CREATE TABLE [pelicans] (\n   [name] TEXT\n);",
            "tool_call_id": None,
        },
        {
            "name": "sqlite_query",
            "output": "Error: attempt to write a readonly database",
            "tool_call_id": None,
        },
    ]
