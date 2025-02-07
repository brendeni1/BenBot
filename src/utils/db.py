import json
import os
import re

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

def listDBs(path: str = "src/data", withFileExtensions: bool = False) -> list[str]:
    databases = os.listdir(path)

    if withFileExtensions:
        return databases

    cleanDatabases = []

    for database in databases:
        extension = (re.search(r"\S[^.]+$", database, re.I|re.M)).group()
        
        replaced = database.replace(extension, "")
        
        cleanDatabases.append(replaced)
    
    return cleanDatabases