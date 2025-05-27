import llm
import json
from llm_tools_sqlite import SQLite
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
                    {
                        "name": "SQLite_query",
                        "arguments": {
                            "sql": "SELECT count(*) n FROM pelicans",
                        },
                    },
                    {"name": "SQLite_schema", "arguments": {}},
                    {
                        "name": "SQLite_query",
                        "arguments": {
                            "sql": "drop table pelicans",
                        },
                    },
                ]
            }
        ),
        tools=[SQLite("demo.db")],
    )
    responses = list(chain_response.responses())
    assert len(responses) == 2
    text = responses[-1].text()
    info = json.loads(text)
    assert info["tool_results"] == [
        {"name": "SQLite_query", "output": '[{"n": 3}]', "tool_call_id": None},
        {
            "name": "SQLite_schema",
            "output": "CREATE TABLE [pelicans] (\n   [name] TEXT\n);",
            "tool_call_id": None,
        },
        {
            "name": "SQLite_query",
            "output": "Error: attempt to write a readonly database",
            "tool_call_id": None,
        },
    ]
