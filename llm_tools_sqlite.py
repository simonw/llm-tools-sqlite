import json
import llm
import pathlib
import sqlite_utils
import sqlite3


def sqlite_query(database_name: str, sql: str) -> str:
    """
    Run SQLite SQL against the specified database. Use sqlite_list_databases to see available database names.
    """
    db = sqlite_utils.Database(
        sqlite3.connect("file:{}.db?mode=ro".format(database_name), uri=True)
    )
    try:
        results = db.query(sql)
        return json.dumps(list(results))
    except Exception as ex:
        return f"Error: {ex}"


def sqlite_list_databases() -> str:
    """
    List all available SQLite databases names - call this once at the start of the conversation.
    """
    return json.dumps([filepath.stem for filepath in pathlib.Path(".").glob("*.db")])


def sqlite_schema(database_name: str) -> str:
    """
    Get the schema of the specified SQLite database.
    """
    db = sqlite_utils.Database(database_name + ".db")
    return db.schema


@llm.hookimpl
def register_tools(register):
    register(sqlite_query)
    register(sqlite_list_databases)
    register(sqlite_schema)
