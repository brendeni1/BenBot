import discord
import requests
import datetime

from src.utils import dates
from src.utils import text
from src import constants

from src.classes import *


class ItemPrice:
    def __init__(
        self,
        name: str,
        price: int,
        priceRUB: int,
    ):
        pass


class Vendor:
    def __init__(self, name: str, slug: str):
        pass


class ItemOffer:
    def __init__(self, vendor: Vendor, price: ItemPrice):  # type: ignore
        pass


class Item:
    def __init__(
        self,
        *,
        id: str,
        name: str,
        shortName: str,
        slug: str,
        description: str,
        basePrice: ItemPrice,
        avg24hPrice: ItemPrice,
        buys: list[ItemOffer],
        sells: list[ItemOffer],
        lastUpdate: datetime.datetime,
        image: str,
        wikiLink: str,
        apiLink: str,
    ):
        pass


def fetch(query):
    headers = {"Content-Type": "application/json"}

    response = requests.post(
        "https://api.tarkov.dev/graphql", headers=headers, json={"query": query}
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"Tarkov query failed to run by returning code of {response.status_code}. Query: {query}"
        )


def parseItem():
    pass
