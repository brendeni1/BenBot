import json
import os
import re
import pickle

def jsonDB(path: str) -> dict:
    if ".json" not in path:
        path = f"src/data/{path}.json"

    with open(path, "r") as database:
        loadedJSON = json.load(database)

        return loadedJSON

def listDBs(path: str = "src/data", withFileExtensions: bool = False, filterByExtension: str = None) -> list[str]:
    databases = os.listdir(path)

    if not databases:
        return None

    if filterByExtension:
        databases = filter(lambda database: database.endswith(filterByExtension), databases)

    if withFileExtensions:
        return databases

    cleanDatabases = []

    for database in databases:
        extension = (re.search(r"\S[^.]+$", database, re.I|re.M)).group()
        
        replaced = database.replace(extension, "")
        
        cleanDatabases.append(replaced)
    
    return cleanDatabases

def serializeObj(obj) -> bytes:
    return pickle.dumps(obj)

def deserializeObj(byteObj: bytes):
    return pickle.loads(byteObj)