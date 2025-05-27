import json
import llm
import pathlib
import sqlite_utils
import sqlite3


class SQLite(llm.Toolbox):
    def __init__(self, path: str):
        self.path = path
        self.db = sqlite_utils.Database(
            sqlite3.connect("file:{}?mode=ro".format(path), uri=True)
        )

    def query(self, sql: str) -> str:
        """
        Run SQLite SQL against the specified database. Use list_databases to see available database names.
        """
        try:
            results = self.db.query(sql)
            return json.dumps(list(results))
        except Exception as ex:
            return f"Error: {ex}"

    def schema(self) -> str:
        """
        Get the schema of the specified SQLite database.
        """
        return self.db.schema


@llm.hookimpl
def register_tools(register):
    register(SQLite)
