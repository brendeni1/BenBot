import json
import os

from src.classes import AppReply

def jsonDB(path: str) -> dict:
    if ".json" not in path:
        path = f"src/data/{path}.json"

    try:
        with open(path, "r") as database:
            loadedJSON = json.load(database)

            return loadedJSON
    except FileNotFoundError:
        return{
            "success": False,
            "reply": AppReply(
                False,
                f"<:bensad:801246370106179624> That command couldn't be executed. (utils/db.py: FileNotFoundError using {path})",
                "FileNotFoundError",
                True
            )
        }