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
    tool_results = info["tool_results"]
    # tool_call_id is assigned by the model/echo plugin, not by this tool, and its
    # value differs across llm versions (older ones pass None). Assert the shape
    # rather than a fixed value so the test does not break on a dependency bump.
    assert [r["name"] for r in tool_results] == [
        "SQLite_query",
        "SQLite_schema",
        "SQLite_query",
    ]
    assert tool_results[0]["output"] == '[{"n": 3}]'
    # The schema rendering quotes identifiers differently across sqlite-utils
    # versions (brackets vs double quotes), so assert the content, not the exact
    # string.
    schema = tool_results[1]["output"]
    assert schema.startswith("CREATE TABLE")
    assert "pelicans" in schema
    assert "name" in schema
    assert "TEXT" in schema
    assert tool_results[2]["output"] == "Error: attempt to write a readonly database"
    for result in tool_results:
        assert "tool_call_id" in result
        assert result["tool_call_id"] is None or isinstance(
            result["tool_call_id"], str
        )
