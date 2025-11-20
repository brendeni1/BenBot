import discord
import requests
import datetime

from src.utils import dates
from src.utils import text
from src import constants

from src.classes import *


class Item:
    def __init__(
        self,
        id: str,
    ):
        pass


class ContainedItem:
    pass


class AttributeItem:
    pass


class Task:
    pass


class TaskRewards:
    pass


class Task:
    pass


class TaskItem:
    pass


class Trader:
    pass


class TraderLevel:
    pass


class TraderStanding:
    pass


class SkillLevel:
    pass


class Skill:
    pass


class OfferUnlock:
    pass


class Achievement:
    pass


class CustomizationItem:
    pass


class TraderCashOffer:
    pass


class TraderReputationLevel:
    pass


class Vendor:
    pass


class ItemPrice:
    pass


class Barter:
    pass


class Craft:
    pass


class HideoutStation:
    pass


class HideoutStationBonus:
    pass


class HideoutStationLevel:
    pass


class RequirementHideoutStationLevel:
    pass


class RequirementItem:
    pass


class RequirementSkill:
    pass


class RequirementTrader:
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
