import discord
import requests
import datetime

from src.utils import dates
from src.utils import text
from src import constants

from src.classes import *

ITEM_SEARCH_QUERY_RETURN_LIMIT = 10

DEFAULT_CURRENCY = "RUB"


class TarkovEmbedReply(EmbedReply):
    def __init__(self, title, error=False, *, url=None, description=None):
        super().__init__(title, "tarkov", error, url=url, description=description)

        self.set_footer(
            text=f"Data provided by tarkov.dev",
            icon_url="https://tarkov.dev/apple-touch-icon.png",
        )

        self.set_author(
            name=f"BenBot - Tarkov",
            url="https://github.com/brendeni1/BenBot/blob/main/src/cogs/tarkov.py",
            icon_url="https://cdn.discordapp.com/emojis/1337974783396286575.webp?size=96",
        )


class ItemPrice:
    def __init__(
        self,
        *,
        currency: dict[str] = next(
            filter(lambda c: c["shortName"] == DEFAULT_CURRENCY, constants.CURRENCIES)
        ),
        price: int,
        priceRUB: int,
    ):
        self.currency = currency
        self.price = price
        self.priceRUB = priceRUB or price

    def getPrice(self, formatted: bool = True):
        if formatted:
            return f"{self.currency["symbol"]} {self.price:,}"
        else:
            return self.price

    def __str__(self):
        return f"{self.currency["symbol"]} {self.price:,}"


class Vendor:
    def __init__(self, *, name: str, slug: str):
        self.name = name
        self.slug = slug


class ItemOffer:
    def __init__(self, *, vendor: Vendor, price: ItemPrice):
        self.vendor = vendor
        self.price = price


class HideoutStation:
    def __init__(
        self,
        *,
        id: str,
        name: str,
        slug: str,
        image: str,
        crafts: list["Craft"] = None,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.image = image
        self.crafts = crafts if crafts is not None else []


class Craft:
    def __init__(
        self,
        *,
        id: str,
        station: HideoutStation,
        level: int,
        duration: int,
        requiredItems: list["SmallItem"],
        rewardItems: list["SmallItem"],
    ):
        self.id = id
        self.station = station
        self.level = level
        self.duration = duration
        self.requiredItems = requiredItems
        self.rewardItems = rewardItems


class Barter:
    def __init__(
        self,
        *,
        id: str,
        trader: "Trader",
        level: int,
        requiredItems: list["SmallItem"],
        rewardItems: list["SmallItem"],
        buyLimit: int,
    ):
        self.id = id
        self.trader = trader
        self.level = level
        self.requiredItems = requiredItems
        self.rewardItems = rewardItems
        self.buyLimit = buyLimit


class Trader:
    def __init__(
        self, *, name: str, description: str, image: str, barters: list[Barter] = None
    ):
        self.name = name
        self.description = description
        self.image = image
        self.barters = barters if barters is not None else []


class ItemCategory:
    def __init__(self, *, id: str, name: str, slug: str):
        self.id = id
        self.name = name
        self.slug = slug


class SmallTask:
    def __init__(
        self,
        *,
        id: str,
        name: str,
        slug: str,
        trader: Trader,
        map: str,
        experience: int,
        wikiLink: str,
        image: str,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.trader = trader
        self.map = map
        self.experience = experience
        self.wikiLink = wikiLink
        self.image = image


class Item:
    def __init__(
        self,
        *,
        id: str,
        name: str,
        shortName: str,
        slug: str,
        description: str,
        weight: float,
        width: float,
        height: float,
        categories: list[ItemCategory],
        basePrice: "ItemPrice",
        avg24hPrice: "ItemPrice",
        low24hPrice: "ItemPrice",
        high24hPrice: "ItemPrice",
        change48hPrice: "ItemPrice",
        change48hPercent: float,
        buys: list["ItemOffer"],
        sells: list["ItemOffer"],
        lastUpdate: datetime.datetime,
        itemImage: str,
        gridImage: str,
        inspectImage: str,
        wikiLink: str,
        apiLink: str,
        tasksUsed: list["SmallTask"],
        tasksRecieved: list["SmallTask"],
        bartersFor: list["Barter"],
        bartersUsing: list["Barter"],
        craftsFor: list["Craft"],
        craftsUsing: list["Craft"],
    ):
        self.id = id
        self.name = name
        self.shortName = shortName
        self.slug = slug
        self.description = description

        self.weight = weight
        self.height = height
        self.width = width
        self.categories = categories

        self.basePrice = basePrice
        self.avg24hPrice = avg24hPrice
        self.low24hPrice = low24hPrice
        self.high24hPrice = high24hPrice
        self.change48hPrice = change48hPrice
        self.change48hPercent = change48hPercent

        self.buys = buys
        self.sells = sells

        self.lastUpdate = lastUpdate

        self.itemImage = itemImage
        self.gridImage = gridImage
        self.inspectImage = inspectImage

        self.wikiLink = wikiLink
        self.apiLink = apiLink

        self.tasksUsed = tasksUsed
        self.tasksRecieved = tasksRecieved

        self.bartersFor = bartersFor
        self.bartersUsing = bartersUsing

        self.craftsFor = craftsFor
        self.craftsUsing = craftsUsing

    def getDescription(self, formatted: bool = True) -> str:
        if formatted:
            return self.description or "*(No Description Available)*"
        else:
            return self.description

    def toEmbed(self) -> TarkovEmbedReply:
        embed = TarkovEmbedReply(
            title=f"{text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
            url=self.wikiLink,
            description=f"{text.truncateString(self.getDescription(), 2048)[0]}\n\n*(Data updated {dates.formatSimpleDate(self.lastUpdate, discordDateFormat="R") if self.lastUpdate else "<Unknown>"})*",
        )

        embed.set_thumbnail(url=self.gridImage)

        embed.add_field(
            name="Item Category",
            value=" > ".join([category.name for category in self.categories[::-1]]),
        )

        embed.add_field(
            name="Item Dimensions (W x H)",
            value=f"{self.width}x{self.height} ({self.weight} kg)",
        )

        embed.add_field(
            name="Item Links",
            value=f"[Wiki Link]({self.wikiLink})\n[API Link]({self.apiLink})",
        )

        embed.add_field(
            name="Item Base Price",
            value=str(self.basePrice),
        )

        embed.add_field(
            name="Item 24h Price",
            value=f"Avg: {str(self.avg24hPrice)}\n(Low: {str(self.low24hPrice)} High: {str(self.high24hPrice)})",
        )

        embed.add_field(
            name="Item 48h Change",
            value=f"{str(self.change48hPrice) if self.change48hPrice else "(No Data)"} ({"-" if  self.change48hPrice and self.change48hPrice < 0 else "+" if self.change48hPrice and self.change48hPrice > 0 else "" + str(self.change48hPercent) if self.change48hPrice and self.change48hPercent else "N/A"})",
        )

        embed.set_footer(
            text=f"Item data provided by tarkov.dev · Item ID: {self.id}",
            icon_url="https://tarkov.dev/apple-touch-icon.png",
        )

        return embed


class SmallItem:
    def __init__(
        self,
        id: str,
        name: str,
        shortName: str,
        slug: str,
        description: str,
        width: float,
        height: float,
        weight: float,
        itemImage: str,
        gridImage: str,
        inspectImage: str,
        wikiLink: str,
        apiLink: str,
    ):
        self.id = id
        self.name = name
        self.shortName = shortName
        self.slug = slug
        self.description = description
        self.width = width
        self.height = height
        self.weight = weight
        self.itemImage = itemImage
        self.gridImage = gridImage
        self.inspectImage = inspectImage
        self.wikiLink = wikiLink
        self.apiLink = apiLink


def fetchItems(
    itemQuery: str, byId: bool, limit: int = ITEM_SEARCH_QUERY_RETURN_LIMIT
) -> list[Item]:
    headers = {"Content-Type": "application/json"}

    searchKey = "ids" if byId else "names"

    query = f"""
    {{
        items({searchKey}: ["{itemQuery}"], limit: {ITEM_SEARCH_QUERY_RETURN_LIMIT}) {{
            id
            name
            shortName
            normalizedName
            description
            height
            width
            weight
            categories {{
                id
                name
                normalizedName
            }}
            basePrice
            avg24hPrice
            low24hPrice
            high24hPrice
            changeLast48h
            changeLast48hPercent
            buyFor {{
                vendor {{
                    name
                    normalizedName
                }}
                price
                priceRUB
                currency
            }}
            sellFor {{
                vendor {{
                    name
                    normalizedName
                }}
                price
                priceRUB
                currency
            }}
            updated
            image512pxLink
            gridImageLink
            inspectImageLink
            wikiLink
            link
            usedInTasks {{
                id
                name
                normalizedName
                trader {{
                    name
                    description
                    image4xLink
                }}
                map {{
                    name
                }}
                experience
                wikiLink
                taskImageLink
            }}
            receivedFromTasks {{
                id
                name
                normalizedName
                trader {{
                    name
                    description
                    image4xLink
                }}
                map {{
                    name
                }}
                experience
                wikiLink
                taskImageLink
            }}
            bartersFor {{
                id
                trader {{
                    name
                    description
                    image4xLink
                }}
                level
                requiredItems {{
                    item {{
                        id
                        name
                        shortName
                        normalizedName
                        description
                        height
                        width
                        weight
                        image512pxLink
                        gridImageLink
                        inspectImageLink
                        wikiLink
                        link
                    }}
                }}
                rewardItems {{
                    item {{
                        id
                        name
                        shortName
                        normalizedName
                        description
                        height
                        width
                        weight
                        image512pxLink
                        gridImageLink
                        inspectImageLink
                        wikiLink
                        link
                    }}
                }}
                buyLimit
            }}
            bartersUsing {{
                id
                trader {{
                    name
                    description
                    image4xLink
                }}
                level
                requiredItems {{
                    item {{
                        id
                        name
                        shortName
                        normalizedName
                        description
                        weight
                        height
                        width
                        image512pxLink
                        gridImageLink
                        inspectImageLink
                        wikiLink
                        link
                    }}
                }}
                rewardItems {{
                    item {{
                        id
                        name
                        shortName
                        normalizedName
                        description
                        weight
                        height
                        width
                        image512pxLink
                        gridImageLink
                        inspectImageLink
                        wikiLink
                        link
                    }}
                }}
                buyLimit
            }}
            craftsFor {{
                id
                station {{
                    id
                    name
                    normalizedName
                    imageLink
                }}
                level
                duration
                requiredItems {{
                    item {{
                        id
                        name
                        shortName
                        normalizedName
                        description
                        weight
                        height
                        width
                        image512pxLink
                        gridImageLink
                        inspectImageLink
                        wikiLink
                        link
                    }}
                }}
                rewardItems {{
                    item {{
                        id
                        name
                        shortName
                        normalizedName
                        description
                        weight
                        height
                        width
                        image512pxLink
                        gridImageLink
                        inspectImageLink
                        wikiLink
                        link
                    }}
                }}
            }}
        }}
    }}
    """

    response = requests.post(
        "https://api.tarkov.dev/graphql", headers=headers, json={"query": query}
    )

    response.raise_for_status()

    rawResponseData = response.json()

    parsedItems = []

    def parseSimplePrice(amount):
        if amount is None:
            return None

        return ItemPrice(price=amount, priceRUB=amount)

    def parseOffer(offerData):
        return ItemOffer(
            vendor=Vendor(
                name=offerData["vendor"]["name"],
                slug=offerData["vendor"]["normalizedName"],
            ),
            price=ItemPrice(
                currency=next(
                    filter(
                        lambda c: c["shortName"] == offerData["currency"],
                        constants.CURRENCIES,
                    )
                ),
                price=offerData["price"],
                priceRUB=offerData["priceRUB"],
            ),
        )

    def parseCategory(category):
        return ItemCategory(
            id=category["id"],
            name=str(category.get("name", "")).title(),
            slug=category.get("normalizedName", ""),
        )

    def parseTrader(traderData):
        return Trader(
            name=traderData["name"],
            description=traderData.get("description", ""),
            image=traderData.get("image4xLink", ""),
        )

    def parseNestedItem(wrapper):
        i = wrapper["item"]
        return SmallItem(
            id=i["id"],
            name=i["name"],
            shortName=i["shortName"],
            slug=i["normalizedName"],
            description=i.get("description", ""),
            weight=i.get("weight", ""),
            width=i.get("width", ""),
            height=i.get("height", ""),
            itemImage=i["image512pxLink"],
            inspectImage=i["inspectImageLink"],
            gridImage=i["gridImageLink"],
            wikiLink=i.get("wikiLink", ""),
            apiLink=i.get("link", ""),
        )

    if "data" in rawResponseData and "items" in rawResponseData["data"]:
        for itemData in rawResponseData["data"]["items"]:

            categories = [parseCategory(c) for c in itemData.get("categories", [])]

            basePrice = parseSimplePrice(itemData.get("basePrice"))
            avg24hPrice = parseSimplePrice(itemData.get("avg24hPrice"))
            low24hPrice = parseSimplePrice(itemData.get("low24hPrice"))
            high24hPrice = parseSimplePrice(itemData.get("high24hPrice"))
            changePrice48h = parseSimplePrice(itemData.get("changeLast48h"))

            buys = [parseOffer(o) for o in itemData.get("buyFor", [])]
            sells = [parseOffer(o) for o in itemData.get("sellFor", [])]

            tasksUsed = []
            for t in itemData.get("usedInTasks", []):
                mapName = t["map"]["name"] if t.get("map") else "Any"
                tasksUsed.append(
                    SmallTask(
                        id=t["id"],
                        name=t["name"],
                        slug=t["normalizedName"],
                        trader=parseTrader(t["trader"]),
                        map=mapName,
                        experience=t["experience"],
                        wikiLink=t.get("wikiLink", ""),
                        image=t.get("taskImageLink", ""),
                    )
                )

            tasksReceived = []
            for t in itemData.get("receivedFromTasks", []):
                mapName = t["map"]["name"] if t.get("map") else "Any"
                tasksReceived.append(
                    SmallTask(
                        id=t["id"],
                        name=t["name"],
                        slug=t["normalizedName"],
                        trader=parseTrader(t["trader"]),
                        map=mapName,
                        experience=t["experience"],
                        wikiLink=t.get("wikiLink", ""),
                        image=t.get("taskImageLink", ""),
                    )
                )

            bartersFor = []
            for b in itemData.get("bartersFor", []):
                bartersFor.append(
                    Barter(
                        id=b["id"],
                        trader=parseTrader(b["trader"]),
                        level=b["level"],
                        requiredItems=[parseNestedItem(x) for x in b["requiredItems"]],
                        rewardItems=[parseNestedItem(x) for x in b["rewardItems"]],
                        buyLimit=b["buyLimit"],
                    )
                )

            bartersUsing = []
            for b in itemData.get("bartersUsing", []):
                bartersUsing.append(
                    Barter(
                        id=b["id"],
                        trader=parseTrader(b["trader"]),
                        level=b["level"],
                        requiredItems=[parseNestedItem(x) for x in b["requiredItems"]],
                        rewardItems=[parseNestedItem(x) for x in b["rewardItems"]],
                        buyLimit=b["buyLimit"],
                    )
                )

            craftsFor = []
            for c in itemData.get("craftsFor", []):
                stationData = c["station"]
                station = HideoutStation(
                    id=stationData["id"],
                    name=stationData["name"],
                    slug=stationData["normalizedName"],
                    image=stationData["imageLink"],
                )
                craftsFor.append(
                    Craft(
                        id=c["id"],
                        station=station,
                        level=c["level"],
                        duration=c["duration"],
                        requiredItems=[parseNestedItem(x) for x in c["requiredItems"]],
                        rewardItems=[parseNestedItem(x) for x in c["rewardItems"]],
                    )
                )

            lastUpdateStr = itemData.get("updated")
            lastUpdate = (
                dates.simpleDateObj(lastUpdateStr)
                if lastUpdateStr
                else dates.simpleDateObj(timeNow=True)
            )

            itemObj = Item(
                id=itemData["id"],
                name=itemData["name"],
                shortName=itemData.get("shortName", itemData["name"]),
                slug=itemData["normalizedName"],
                description=itemData.get("description", ""),
                weight=itemData.get("weight", ""),
                height=itemData.get("height", ""),
                width=itemData.get("width", ""),
                categories=categories,
                basePrice=basePrice,
                avg24hPrice=avg24hPrice,
                low24hPrice=low24hPrice,
                high24hPrice=high24hPrice,
                change48hPrice=changePrice48h,
                change48hPercent=itemData.get("changeLast48hPercent") or 0.0,
                buys=buys,
                sells=sells,
                lastUpdate=lastUpdate,
                gridImage=itemData.get("gridImageLink", ""),
                itemImage=itemData.get("image512pxLink", ""),
                inspectImage=itemData.get("inspectImageLink", ""),
                wikiLink=itemData.get("wikiLink", ""),
                apiLink=itemData.get("link", ""),
                tasksUsed=tasksUsed,
                tasksRecieved=tasksReceived,
                bartersFor=bartersFor,
                bartersUsing=bartersUsing,
                craftsFor=craftsFor,
                craftsUsing=[],
            )

            parsedItems.append(itemObj)

    return parsedItems
