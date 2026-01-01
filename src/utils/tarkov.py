import discord
import aiohttp
import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor

from src.utils import dates
from src.utils import text
from src import constants

from src.classes import *

ITEM_SEARCH_QUERY_RETURN_LIMIT = 25

DEFAULT_CURRENCY = "RUB"

ITEM_DETAIL_REPLY_TIMEOUT_MINS = 14 * 60


class ItemSelect(discord.ui.Select):
    """
    A Select menu that allows the user to choose one of the fetched items.
    """

    def __init__(self, items: list["Item"], initial_index: int):
        options = []
        for i, item in enumerate(items):
            # The 'value' will store the index of the item in the list
            options.append(
                discord.SelectOption(
                    label=text.truncateString(item.name.title(), 100)[0],
                    description=text.truncateString(item.getDescription(), 100)[0],
                    value=str(i),
                    default=(i == initial_index),
                )
            )

        super().__init__(
            placeholder="Choose an item...",
            options=options,
        )
        self.items = items

    async def callback(self, interaction: discord.Interaction):
        # The selected value is the string index of the chosen item
        selected_index = int(self.values[0])
        selected_item = self.items[selected_index]

        # Re-generate the embeds for the selected item
        # We include crafts and barters for a complete display
        new_embeds = selected_item.toEmbeds(
            includeCrafts=self.view.includeCrafts,
            includeBarters=self.view.includeBarters,
        )

        # Recreate the view to update the selected default option
        new_view = ItemView(
            self.items,
            selected_index,
            includeCrafts=self.view.includeCrafts,
            includeBarters=self.view.includeBarters,
        )

        self.view.stop()

        # Edit the original message to display the new item's details
        await interaction.response.edit_message(embeds=new_embeds, view=new_view)


class ItemView(discord.ui.View):
    """
    A View to hold the ItemSelect menu.
    """

    def __init__(
        self,
        items: list["Item"],
        initial_index: int,
        includeCrafts: bool,
        includeBarters: bool,
    ):
        super().__init__(
            timeout=ITEM_DETAIL_REPLY_TIMEOUT_MINS, disable_on_timeout=True
        )

        self.includeCrafts = includeCrafts
        self.includeBarters = includeBarters

        self.add_item(ItemSelect(items, initial_index))


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

    def __str__(self):
        return self.name.title()


class ItemOffer:
    def __init__(self, *, vendor: Vendor, price: ItemPrice):
        self.vendor = vendor
        self.price = price

    def __str__(self):
        return f"• {self.vendor} for {self.price}"


class HideoutStation:
    def __init__(
        self,
        *,
        id: str,
        name: str,
        slug: str,
        image: str,
        crafts: list["Craft"] = None,
        levels: list["HideoutStationLevel"] = None,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.image = image
        self.crafts = crafts if crafts is not None else []
        self.levels = levels if levels is not None else []

    def __str__(self):
        return self.name.title()


class HideoutStationLevel:
    def __init__(
        self,
        *,
        id: str,
        station: HideoutStation,
        description: str,
        level: int,
        constructionTime: int,
        itemRequirements: list["ContainedItem"],
    ):
        self.id = id
        self.station = station
        self.description = description
        self.level = level
        self.constructionTime = constructionTime
        self.itemRequirements = itemRequirements

    def getDescription(self, formatted: bool = True) -> str:
        if formatted:
            return self.description or "*(No Description Available)*"
        else:
            return self.description

    def formatLevelWithTarget(self, targetItem) -> str:
        quantity = None

        try:
            matchingItem: ContainedItem = next(
                filter(lambda i: i.item.id == targetItem.id, self.itemRequirements)
            )

            quantity = matchingItem.quantity
        except StopIteration:
            pass

        return f"•{f" *(x{quantity:,})*" if quantity else ""} Level {self.level} *({dates.formatSeconds(self.constructionTime) if self.constructionTime else "Instant"})*"

    def __str__(self):
        return f"• Level {self.level} *({dates.formatSeconds(self.constructionTime) if self.constructionTime else "Instant"})*"


class Craft:
    def __init__(
        self,
        *,
        id: str,
        station: HideoutStation,
        level: int,
        duration: int,
        requiredItems: list["ContainedItem"],
        rewardItems: list["ContainedItem"],
    ):
        self.id = id
        self.station = station
        self.level = level
        self.duration = duration
        self.requiredItems = requiredItems
        self.rewardItems = rewardItems

    def formatCraft(
        self,
        targetItem,
        includeRewards: bool = True,
        isReward: bool = False,
        showLevel: bool = True,
    ) -> str:
        prefix = ""
        duration = dates.formatSeconds(self.duration)

        # Determine if there is a quantity multiplier to show (e.g. x60 ammo)
        if isReward:
            try:
                quantity = next(
                    filter(lambda i: i.item.id == targetItem.id, self.rewardItems)
                ).quantity
                prefix = f"(Makes *x{quantity:,}*)"
            except StopIteration:
                pass

        elif not includeRewards and len(self.rewardItems) > 0:
            prefix = f"(x{self.rewardItems[0].quantity:,})"

        # If we are hiding the level (grouping), move the prefix to the body
        # Otherwise, keep it in the header
        header_prefix = f" {prefix}" if showLevel and prefix else ""
        body_prefix = f"{prefix} " if not showLevel and prefix else ""

        if showLevel:
            base = f"• **Level {self.level}{header_prefix}**\n> {body_prefix}Required Items: {", ".join(str(i) for i in self.requiredItems)}"
        else:
            base = f"> {body_prefix}Required Items: {", ".join(str(i) for i in self.requiredItems)}"

        if includeRewards:
            rewardStr = (
                f"\n> Reward Items: {", ".join(str(i) for i in self.rewardItems)}"
            )
            return (
                base
                + rewardStr
                + f"\n{constants.UNICODE_WHITESPACE["4"]}*(Takes {duration})*"
            )
        else:
            return base + f"\n{constants.UNICODE_WHITESPACE["4"]}*(Takes {duration})*"


class Barter:
    def __init__(
        self,
        *,
        id: str,
        trader: "Trader",
        level: int,
        requiredItems: list["ContainedItem"],
        rewardItems: list["ContainedItem"],
        buyLimit: int,
    ):
        self.id = id
        self.trader = trader
        self.level = level
        self.requiredItems = requiredItems
        self.rewardItems = rewardItems
        self.buyLimit = buyLimit

    def formatBarter(
        self,
        targetItem,
        includeRewards: bool = True,
        isReward: bool = False,
        showLevel: bool = True,
    ) -> str:
        prefix = ""

        # Determine if there is a quantity multiplier to show (e.g. x60 ammo)
        if isReward:
            try:
                quantity = next(
                    filter(lambda i: i.item.id == targetItem.id, self.rewardItems)
                ).quantity
                prefix = f"(Gives *x{quantity:,}*)"
            except StopIteration:
                pass

        elif not includeRewards and len(self.rewardItems) > 0:
            prefix = f"(x{self.rewardItems[0].quantity:,})"

        # If we are hiding the level (grouping), move the prefix to the body
        # Otherwise, keep it in the header
        header_prefix = f" {prefix}" if showLevel and prefix else ""
        body_prefix = f"{prefix} " if not showLevel and prefix else ""

        if showLevel:
            base = f"• **Level {self.level}{header_prefix}**\n> {body_prefix}Required Items: {", ".join(str(i) for i in self.requiredItems)}"
        else:
            base = f"> {body_prefix}Required Items: {", ".join(str(i) for i in self.requiredItems)}"

        if includeRewards:
            rewardStr = (
                f"\n> Reward Items: {", ".join(str(i) for i in self.rewardItems)}"
            )
            return (
                base
                + rewardStr
                + f"\n{constants.UNICODE_WHITESPACE["4"]}*(Limit {self.buyLimit})*"
            )
        else:
            return (
                base + f"\n{constants.UNICODE_WHITESPACE["4"]}*(Limit {self.buyLimit})*"
            )


class Trader:
    def __init__(
        self, *, name: str, description: str, image: str, barters: list[Barter] = None
    ):
        self.name = name
        self.description = description
        self.image = image
        self.barters = barters if barters is not None else []

    def __str__(self):
        return self.name.title()


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
        minPlayerLevel: int,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.trader = trader
        self.map = map
        self.experience = experience
        self.wikiLink = wikiLink
        self.image = image
        self.minPlayerLevel = minPlayerLevel

    def __str__(self):
        return (
            f"• {self.trader.name.title()} > {self.name.title()} ({self.map.title()})"
        )


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
        hideoutUpgradesUsing: list["HideoutStationLevel"],
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

        self.hideoutUpgradesUsing = hideoutUpgradesUsing

    def getDescription(self, formatted: bool = True) -> str:
        if formatted:
            return self.description or "*(No Description Available)*"
        else:
            return self.description

    def toEmbeds(
        self, includeCrafts: bool, includeBarters: bool
    ) -> list[TarkovEmbedReply]:
        embeds = []

        # ITEM DETAIL EMBED

        baseUrl = self.wikiLink if self.wikiLink else "https://tarkov.dev/"

        itemDetailEmbed = TarkovEmbedReply(
            title=f"Details - {text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
            url=baseUrl,
            description=f"{text.truncateString(self.getDescription(), 2048)[0]}\n\n*(Data updated {dates.formatSimpleDate(self.lastUpdate, discordDateFormat="R") if self.lastUpdate else "<Unknown>"})*",
        )

        itemDetailEmbed.set_thumbnail(url=self.gridImage)

        itemDetailEmbed.add_field(
            name="Item Category",
            value=" > ".join([category.name for category in self.categories[::-1]]),
        )

        itemDetailEmbed.add_field(
            name="Item Size (W x H)",
            value=f"{self.width}x{self.height} ({self.weight} kg)",
        )

        itemDetailEmbed.add_field(
            name="Item Links",
            value=f"[Wiki Link]({baseUrl})\n[API Link]({self.apiLink})",
        )

        itemDetailEmbed.add_field(
            name="Item Base Price",
            value=str(self.basePrice),
        )

        itemDetailEmbed.add_field(
            name="Item 24h Price",
            value=f"Avg: {str(self.avg24hPrice)}\n(Low: {str(self.low24hPrice)} High: {str(self.high24hPrice)})",
        )

        itemDetailEmbed.add_field(
            name="Item 48h Change",
            value=f"{str(self.change48hPrice) if self.change48hPrice else "(No Data)"} ({"- " if self.change48hPrice and self.change48hPrice < 0 else "+ " if self.change48hPrice and self.change48hPrice > 0 else "" + str(self.change48hPercent) + "%" if self.change48hPrice and self.change48hPercent else "N/A"})",
        )

        itemDetailEmbed.add_field(
            name="Buy Item From",
            value="\n".join(text.truncateList([str(o) for o in self.buys], 1024))
            or "*(Not Buyable)*",
        )

        itemDetailEmbed.add_field(
            name="Sell Item To",
            value="\n".join(text.truncateList([str(o) for o in self.sells], 1024))
            or "*(Not Sellable)*",
        )

        itemDetailEmbed.set_footer(
            text=f"Item data provided by tarkov.dev · Item ID: {self.id}",
            icon_url="https://tarkov.dev/apple-touch-icon.png",
        )

        embeds.append(itemDetailEmbed)

        # QUEST EMBED

        questDetailEmbed = TarkovEmbedReply(
            title=f"Quests - {text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
            url=baseUrl + "#Quests",
        )

        questDetailEmbed.set_thumbnail(url=self.gridImage)

        questDetailEmbed.add_field(
            name="Quests Needing Item",
            value=(
                "\n".join(
                    text.truncateList(
                        [f"[{t}]({t.wikiLink}) 🔗↗️" for t in self.tasksUsed], 1024
                    )
                )
                if self.tasksUsed
                else "*(No Quests Needing Item)*"
            ),
        )

        questDetailEmbed.add_field(
            name="Quests Rewarding Item",
            value=(
                "\n".join(
                    text.truncateList(
                        [f"[{t}]({t.wikiLink}) 🔗↗️" for t in self.tasksRecieved], 1024
                    )
                )
                if self.tasksRecieved
                else "*(No Quests Rewarding Item)*"
            ),
        )

        questDetailEmbed.set_footer(
            text=f"Quest data provided by tarkov.dev · Item ID: {self.id}",
            icon_url="https://tarkov.dev/apple-touch-icon.png",
        )

        embeds.append(questDetailEmbed)

        # HIDEOUT LEVEL EMBED

        hideoutDetailEmbed = TarkovEmbedReply(
            title=f"Hideout - {text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
            url=baseUrl + "#Hideout",
        )

        hideoutDetailEmbed.set_thumbnail(url=self.gridImage)

        levelsByStation: dict[str, list[HideoutStationLevel]] = {}

        for level in self.hideoutUpgradesUsing:

            stationName = level.station.name.title()

            if stationName not in levelsByStation:
                levelsByStation[stationName] = []

            levelsByStation[stationName].append(level)

        for station in levelsByStation:
            hideoutDetailEmbed.add_field(
                name=station,
                value="\n".join(
                    text.truncateList(
                        [
                            l.formatLevelWithTarget(self)
                            for l in levelsByStation[station]
                        ],
                        limit=1024,
                    )
                ),
            )

        if not levelsByStation:
            hideoutDetailEmbed.description = "*(Not Used In Any Hideout Upgrades)*"

        hideoutDetailEmbed.set_footer(
            text=f"Hideout data provided by tarkov.dev · Item ID: {self.id}",
            icon_url="https://tarkov.dev/apple-touch-icon.png",
        )

        embeds.append(hideoutDetailEmbed)

        # CRAFTS EMBEDS

        if includeCrafts:
            # Structure: { "StationName": { level_int: [Craft, Craft] } }
            craftsForByStation = {}

            for craft in self.craftsFor:
                name = craft.station.name.title()
                if name not in craftsForByStation:
                    craftsForByStation[name] = {}

                if craft.level not in craftsForByStation[name]:
                    craftsForByStation[name][craft.level] = []

                craftsForByStation[name][craft.level].append(craft)

            craftsForDetailEmbed = TarkovEmbedReply(
                title=f"Crafts Rewarding - {text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
                url=baseUrl + "#Crafting",
            )

            craftsForDetailEmbed.set_thumbnail(url=self.gridImage)

            if craftsForByStation:
                for stationName, levelsData in craftsForByStation.items():
                    lines = []
                    sortedLevels = sorted(levelsData.keys())

                    for level in sortedLevels:
                        lines.append(f"• Level {level}")
                        for craft in levelsData[level]:
                            lines.append(
                                craft.formatCraft(
                                    targetItem=self,
                                    includeRewards=False,
                                    isReward=True,
                                    showLevel=False,
                                )
                            )

                    craftsForDetailEmbed.add_field(
                        name=stationName,
                        value="\n".join(text.truncateList(lines, limit=1024)),
                        inline=False,
                    )

                craftsForDetailEmbed.set_footer(
                    text=f"Crafting data provided by tarkov.dev · Item ID: {self.id}",
                    icon_url="https://tarkov.dev/apple-touch-icon.png",
                )

                embeds.append(craftsForDetailEmbed)

            # Structure: { "StationName": { level_int: [Craft, Craft] } }
            craftsUsingByStation = {}

            for craft in self.craftsUsing:
                name = craft.station.name.title()
                if name not in craftsUsingByStation:
                    craftsUsingByStation[name] = {}

                if craft.level not in craftsUsingByStation[name]:
                    craftsUsingByStation[name][craft.level] = []

                craftsUsingByStation[name][craft.level].append(craft)

            craftsUsingDetailEmbed = TarkovEmbedReply(
                title=f"Crafts Using - {text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
                url=baseUrl + "#Crafting?discord=broken",
            )

            craftsUsingDetailEmbed.set_thumbnail(url=self.gridImage)

            if craftsUsingByStation:
                for stationName, levelsData in craftsUsingByStation.items():
                    # Build list of strings for this station
                    lines = []
                    # Sort levels (1, 2, 3...)
                    sortedLevels = sorted(levelsData.keys())

                    for level in sortedLevels:
                        lines.append(f"• Level {level}")
                        for craft in levelsData[level]:
                            lines.append(
                                craft.formatCraft(
                                    targetItem=self,
                                    includeRewards=True,
                                    isReward=False,
                                    showLevel=False,
                                )
                            )

                    craftsUsingDetailEmbed.add_field(
                        name=stationName,
                        value="\n".join(text.truncateList(lines, limit=1024)),
                        inline=False,
                    )

                craftsUsingDetailEmbed.set_footer(
                    text=f"Crafting data provided by tarkov.dev · Item ID: {self.id}",
                    icon_url="https://tarkov.dev/apple-touch-icon.png",
                )

                embeds.append(craftsUsingDetailEmbed)

        # BARTER EMBEDS

        if includeBarters:
            bartersForByTrader = {}

            for barter in self.bartersFor:
                name = barter.trader.name.title()
                if name not in bartersForByTrader:
                    bartersForByTrader[name] = {}

                if barter.level not in bartersForByTrader[name]:
                    bartersForByTrader[name][barter.level] = []

                bartersForByTrader[name][barter.level].append(barter)

            bartersForDetailEmbed = TarkovEmbedReply(
                title=f"Barters Rewarding - {text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
                url=baseUrl + "#Trading",
            )

            bartersForDetailEmbed.set_thumbnail(url=self.gridImage)

            if bartersForByTrader:
                for traderName, levelsData in bartersForByTrader.items():
                    lines = []
                    sortedLevels = sorted(levelsData.keys())

                    for level in sortedLevels:
                        lines.append(f"• Level {level}")
                        for barter in levelsData[level]:
                            lines.append(
                                barter.formatBarter(
                                    targetItem=self,
                                    includeRewards=False,
                                    isReward=True,
                                    showLevel=False,
                                )
                            )

                    bartersForDetailEmbed.add_field(
                        name=traderName,
                        value="\n".join(text.truncateList(lines, limit=1024)),
                        inline=False,
                    )

                bartersForDetailEmbed.set_footer(
                    text=f"Barter data provided by tarkov.dev · Item ID: {self.id}",
                    icon_url="https://tarkov.dev/apple-touch-icon.png",
                )

                embeds.append(bartersForDetailEmbed)

            bartersUsingByTrader = {}

            for barter in self.bartersUsing:
                name = barter.trader.name.title()
                if name not in bartersUsingByTrader:
                    bartersUsingByTrader[name] = {}

                if barter.level not in bartersUsingByTrader[name]:
                    bartersUsingByTrader[name][barter.level] = []

                bartersUsingByTrader[name][barter.level].append(barter)

            bartersUsingDetailEmbed = TarkovEmbedReply(
                title=f"Barters Using - {text.truncateString(self.name.title(), 180)[0]} 🔗↗️",
                url=baseUrl + "#Trading?discord=broken",
            )

            bartersUsingDetailEmbed.set_thumbnail(url=self.gridImage)

            if bartersUsingByTrader:
                for traderName, levelsData in bartersUsingByTrader.items():
                    lines = []
                    # Sort levels (1, 2, 3...)
                    sortedLevels = sorted(levelsData.keys())

                    for level in sortedLevels:
                        lines.append(f"• Level {level}")
                        for barter in levelsData[level]:
                            lines.append(
                                barter.formatBarter(
                                    targetItem=self,
                                    includeRewards=True,
                                    isReward=False,
                                    showLevel=False,
                                )
                            )

                    bartersUsingDetailEmbed.add_field(
                        name=traderName,
                        value="\n".join(text.truncateList(lines, limit=1024)),
                        inline=False,
                    )

                bartersUsingDetailEmbed.set_footer(
                    text=f"Barter data provided by tarkov.dev · Item ID: {self.id}",
                    icon_url="https://tarkov.dev/apple-touch-icon.png",
                )

                embeds.append(bartersUsingDetailEmbed)

        if not embeds:
            raise Exception("No details available from API.")

        return embeds

    def __str__(self):
        return self.name.title()


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

    def __str__(self):
        return self.name.title()


class ContainedItem:
    def __init__(self, item: SmallItem | Item, count: float, quantity: float):
        self.item = item
        self.count = count
        self.quantity = quantity

    def __str__(self):
        return f"{self.item.shortName} (*x{self.quantity:,}*)"


async def apiFetch(query: str) -> dict:
    """
    Performs an asynchronous POST request using aiohttp.
    """
    headers = {"Content-Type": "application/json"}
    url = "https://api.tarkov.dev/graphql"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers=headers, json={"query": query}
        ) as response:
            response.raise_for_status()
            return await response.json()


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


def parseHideoutStationLevel(levelData, station: HideoutStation):
    return HideoutStationLevel(
        id=levelData["id"],
        station=station,
        description=levelData.get("description", ""),
        level=levelData.get("level", 1),
        constructionTime=levelData.get("constructionTime", ""),
        itemRequirements=[
            parseNestedItem(i) for i in levelData.get("itemRequirements", [])
        ],
    )


def parseNestedItem(wrapper):
    i = wrapper["item"]

    item = SmallItem(
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

    return ContainedItem(
        item=item,
        count=wrapper.get("count", 0),
        quantity=wrapper.get("quantity", 0),
    )


async def fetchHideoutStations() -> list[HideoutStation]:
    hideoutQuery = """
    {
        hideoutStations(lang: en) {
            id
            name
            normalizedName
            imageLink
            levels {
                id
                description
                level
                constructionTime
                itemRequirements {
                    item {
                        id
                        name
                        shortName
                        normalizedName
                        description
                        width
                        height
                        weight
                        image512pxLink
                        gridImageLink
                        inspectImageLink
                        wikiLink
                        link
                    }
                    count
                    quantity
                }
            }
        }
    }
    """
    rawHideoutResponseData = await apiFetch(query=hideoutQuery)
    parsedHideoutStations: list[HideoutStation] = []

    if (
        "data" in rawHideoutResponseData
        and "hideoutStations" in rawHideoutResponseData["data"]
    ):
        for stationData in rawHideoutResponseData["data"]["hideoutStations"]:
            station = HideoutStation(
                id=stationData.get("id"),
                name=stationData.get("name"),
                slug=stationData.get("normalizedName"),
                image=stationData.get("imageLink", ""),
            )

            station.levels = [
                parseHideoutStationLevel(l, station=station)
                for l in stationData.get("levels", [])
            ]
            parsedHideoutStations.append(station)

    return parsedHideoutStations


async def fetchItems(
    itemQuery: str, byId: bool, limit: int = ITEM_SEARCH_QUERY_RETURN_LIMIT
) -> list[Item]:
    searchKey = "ids" if byId else "names"

    graphql_query = f"""
    {{
        items({searchKey}: ["{itemQuery}"], limit: {limit}) {{
            id
            name
            shortName
            normalizedName
            description
            height
            width
            weight
            categories {{ id name normalizedName }}
            basePrice
            avg24hPrice
            low24hPrice
            high24hPrice
            changeLast48h
            changeLast48hPercent
            buyFor {{ vendor {{ name normalizedName }} price priceRUB currency }}
            sellFor {{ vendor {{ name normalizedName }} price priceRUB currency }}
            updated
            image512pxLink
            gridImageLink
            inspectImageLink
            wikiLink
            link
            usedInTasks {{
                id name normalizedName 
                trader {{ name description image4xLink }}
                map {{ name }}
                experience wikiLink taskImageLink minPlayerLevel
            }}
            receivedFromTasks {{
                id name normalizedName 
                trader {{ name description image4xLink }}
                map {{ name }}
                experience wikiLink taskImageLink minPlayerLevel
            }}
            bartersFor {{
                id trader {{ name description image4xLink }} level
                requiredItems {{ item {{ id name shortName normalizedName description height width weight image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
                rewardItems {{ item {{ id name shortName normalizedName description height width weight image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
                buyLimit
            }}
            bartersUsing {{
                id trader {{ name description image4xLink }} level
                requiredItems {{ item {{ id name shortName normalizedName description weight height width image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
                rewardItems {{ item {{ id name shortName normalizedName description weight height width image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
                buyLimit
            }}
            craftsFor {{
                id station {{ id name normalizedName imageLink }} level duration
                requiredItems {{ item {{ id name shortName normalizedName description weight height width image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
                rewardItems {{ item {{ id name shortName normalizedName description weight height width image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
            }}
            craftsUsing {{
                id station {{ id name normalizedName imageLink }} level duration
                requiredItems {{ item {{ id name shortName normalizedName description weight height width image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
                rewardItems {{ item {{ id name shortName normalizedName description weight height width image512pxLink gridImageLink inspectImageLink wikiLink link }} count quantity }}
            }}
        }}
    }}
    """

    rawItemResponseData, parsedHideoutStations = await asyncio.gather(
        apiFetch(graphql_query), fetchHideoutStations()
    )

    requiredHideoutItemIDS = {
        req.item.id
        for station in parsedHideoutStations
        for level in station.levels
        for req in level.itemRequirements
    }

    parsedItems = []

    if "data" in rawItemResponseData and "items" in rawItemResponseData["data"]:
        for itemData in rawItemResponseData["data"]["items"]:

            categories = [parseCategory(c) for c in itemData.get("categories", [])]

            basePrice = parseSimplePrice(itemData.get("basePrice"))
            avg24hPrice = parseSimplePrice(itemData.get("avg24hPrice"))
            low24hPrice = parseSimplePrice(itemData.get("low24hPrice"))
            high24hPrice = parseSimplePrice(itemData.get("high24hPrice"))
            changePrice48h = parseSimplePrice(itemData.get("changeLast48h"))

            buys = [parseOffer(o) for o in itemData.get("buyFor", [])]

            buys.sort(key=lambda o: o.price.priceRUB, reverse=True)

            sells = [parseOffer(o) for o in itemData.get("sellFor", [])]

            sells.sort(key=lambda o: o.price.priceRUB, reverse=True)

            tasksUsed: list[SmallTask] = []
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
                        minPlayerLevel=t.get("minPlayerLevel", 0),
                    )
                )

            tasksUsed.sort(key=lambda t: t.minPlayerLevel)

            tasksReceived: list[SmallTask] = []
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
                        minPlayerLevel=t.get("minPlayerLevel", 0),
                    )
                )

            tasksReceived.sort(key=lambda t: t.minPlayerLevel)

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

            craftsUsing = []
            for c in itemData.get("craftsUsing", []):
                stationData = c["station"]
                station = HideoutStation(
                    id=stationData["id"],
                    name=stationData["name"],
                    slug=stationData["normalizedName"],
                    image=stationData["imageLink"],
                )
                craftsUsing.append(
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
                craftsUsing=craftsUsing,
                hideoutUpgradesUsing=None,
            )

            itemObj.hideoutUpgradesUsing = [
                level
                for station in parsedHideoutStations
                for level in station.levels
                if any(req.item.id == itemObj.id for req in level.itemRequirements)
            ]

            parsedItems.append(itemObj)

    return parsedItems
