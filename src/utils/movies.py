import discord
import requests
import datetime
import xmltodict

from src.utils import dates
from src.utils import text
from src.utils import images
from src import constants

from src.classes import *

SELECTION_TIMEOUT = 600
TRAILER_SEARCH_CUTOFF = 40.0
TRAILER_SEARCH_INIT_AMOUNT = 250
TRAILER_SEARCH_KEYWORDS = ""

LANDMARK_LOGO = "https://i.breia.net/hIdg4zuf.jpg"

EXCLUDED_LANDMARK_BULLSHIT = ["Mystery Movie", "Behind the Scenes"]


class ExperienceAttribute:
    def __init__(self, id: int, name: str, description: str, precedence: int):
        self.id = id
        self.name = name
        self.description = description
        self.precedence = precedence
        self.experience = None

    def getEmojiForAttribute(self) -> str | None:
        return constants.MOVIE_EXPERIENCE_ATTRIBUTE_EMOJIS.get(self.id, self.name)


class ExperienceTime:
    def __init__(
        self,
        soldOut: bool,
        expired: bool,
        screen: str,
        id: str,
        time: datetime.datetime,
    ):
        self.soldOut = soldOut
        self.expired = expired
        self.screen = screen
        self.id = id
        self.time = time
        self.experience = None


class Experience:
    def __init__(
        self,
        times: list[ExperienceTime] | None = None,
        attributes: list[ExperienceAttribute] | None = None,
    ):
        self.times = times if times is not None else []
        self.attributes = attributes if attributes is not None else []
        self.session = None

    def addExperienceAttribute(self, experienceAttribute: ExperienceAttribute):
        experienceAttribute.experience = self

        self.attributes.append(experienceAttribute)

    def addExperienceTime(self, experienceTime: ExperienceTime):
        experienceTime.experience = self

        self.times.append(experienceTime)

    def listExperienceDisplays(
        self, emojis: bool = True, ignoreUnnessecary: bool = False
    ) -> set[str]:
        results = []

        for attribute in self.attributes:
            if (
                ignoreUnnessecary
                and attribute.id in constants.MOVIE_EXPERIENCE_ATTRIBUTE_IGNORES
            ):
                continue

            emoji = attribute.getEmojiForAttribute()

            results.append(emoji if emojis and emoji else attribute.name)

        return results

    def getMostProminentAttributeName(self, emoji: bool = False) -> str:
        if self.attributes:
            selected = self.attributes[0]

            return f"({selected.name.title() if not emoji else selected.getEmojiForAttribute()})"
        else:
            return ""


class Session:
    def __init__(
        self, date: datetime.date, experiences: list[Experience] | None = None
    ):
        self.date = date
        self.experiences = experiences if experiences is not None else []
        self.film = None

    def addExperience(self, experience: Experience):
        experience.session = self

        self.experiences.append(experience)


class Film:
    def __init__(
        self,
        id: int,
        name: str,
        friendlyName: str,
        ageRating: str | None,
        image: discord.File,
        filmURL: str,
        releaseDate: datetime.datetime,
        runtime: int,
        description: str,
        cast: str,
        director: str,
        isComingSoon: bool,
        isNowShowing: bool,
        chain: str,
        province: str,
        location: dict,
        sessions: list[Session] | None = None,
        trailerLink: str | None = None,
    ):
        self.id = id
        self.name = name
        self.friendlyName = friendlyName
        self.ageRating = ageRating
        self.image = image
        self.filmURL = filmURL
        self.releaseDate = releaseDate
        self.runtime = runtime
        self.description = description
        self.cast = cast
        self.director = director
        self.isComingSoon = isComingSoon
        self.isNowShowing = isNowShowing
        self.chain = chain
        self.province = province
        self.location = location
        self.sessions = sessions if sessions is not None else []
        self.trailerLink = trailerLink

    def addSession(self, session: Session) -> None:
        session.film = self

        self.sessions.append(session)

    def allAvailableExperienceDisplays(
        self, emojis: bool = True, ignoreUnnessecary: bool = False
    ) -> list[str]:
        results = []

        for session in self.sessions:
            for experience in session.experiences:
                for attribute in experience.attributes:
                    if (
                        ignoreUnnessecary
                        and attribute.id in constants.MOVIE_EXPERIENCE_ATTRIBUTE_IGNORES
                    ):
                        continue

                    display = (
                        attribute.getEmojiForAttribute() if emojis else attribute.name
                    )

                    if display not in [result[0] for result in results]:
                        results.append((display, attribute.precedence))

        results.sort(key=lambda d: d[1])

        return [result[0] for result in results]

    def formatRuntime(self) -> str:
        try:
            runtime = round(self.runtime * 60)

            return dates.formatSeconds(runtime)
        except ValueError:
            return f"{self.runtime} mins"


def fetchShowtimes(chain: str, location: str) -> dict:
    if chain == "Landmark":
        url = "https://www.landmarkcinemas.com/Umbraco/Api/MovieApi/MoviesByCinema"

        params = {
            "cinemaId": location,
            "splitByAttributes": "true",
            "expandSessions": "true",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-CA,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.landmarkcinemas.com/showtimes/windsor",
            "Cookie": "LMC_TheatreId=7802; LMC_TheatreURL=%2Fshowtimes%2Fwindsor; LMC_TheatreName=%2Fnow-playing%2Fwindsor",
        }

        response = requests.get(url=url, params=params, headers=headers)

        response.raise_for_status()

        parsedResponse = response.json()

        return parsedResponse
    else:
        raise Exception("Invalid chain passed to fetchShowtimes")


def fetchTrailersForAll(films: list[Film]) -> None:
    # Only need to fetch once
    url = "https://www.landmarkcinemas.com/umbraco/api/ListingApi/GetVideosOverview"

    params = {
        "itemsPerPage": TRAILER_SEARCH_INIT_AMOUNT,
        "currentPage": "1",
        "filterBy": "recent",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://www.landmarkcinemas.com/showtimes/windsor",
        "Cookie": "LMC_TheatreId=7802; LMC_TheatreURL=%2Fshowtimes%2Fwindsor; LMC_TheatreName=%2Fnow-playing%2Fwindsor",
    }

    response = requests.get(url=url, params=params, headers=headers)
    response.raise_for_status()

    parsed = xmltodict.parse(response.text)

    items = parsed["TrailersListing"]["Items"]["TrailersListingItem"]
    if not items:
        return

    # Build a list of titles + URLs for fuzzy search
    trailer_titles = [item["Title"] for item in items]
    trailer_urls = [f"https://www.landmarkcinemas.com{item['Url']}" for item in items]

    # One fuzzy search per film, no API hits
    for film in films:
        if film.chain == "Landmark":
            candidates = text.fuzzySearch(
                film.friendlyName + TRAILER_SEARCH_KEYWORDS,
                trailer_titles,
                scoreCutoff=TRAILER_SEARCH_CUTOFF,
            )

            if not candidates:
                film.trailerLinks = None
                continue

            best_index = candidates[0][2]
            film.trailerLink = trailer_urls[best_index]


async def parseShowtimes(
    rawData: dict, chain, province, location, startDate: datetime.date | None
) -> list[Film]:
    parsed = []

    if chain == "Landmark":
        for rawFilmData in sorted(
            rawData,
            key=lambda f: sum(
                len(exp["Times"])
                for session in f["Sessions"]
                for exp in session["ExperienceTypes"]
            ),
            reverse=True,
        ):
            rawFilmID = rawFilmData.get("FilmId", None)
            rawName = rawFilmData.get("Title", None)

            if rawName in EXCLUDED_LANDMARK_BULLSHIT:
                continue

            friendlyName = rawFilmData.get("FriendlyName", "N/A")

            rawRating = rawFilmData.get("Cert", "TBC")

            formattedRating = rawRating if rawRating != "TBC" else None

            rawImage = rawFilmData.get("Img", LANDMARK_LOGO)

            imageFileObject = await images.fetchToFile(
                rawImage,
                "movie-poster.jpg",
            )

            filmURL = f"https://www.landmarkcinemas.com/film-info/{friendlyName}"

            rawReleaseDate = rawFilmData["ReleaseDate"]
            convertedReleaseDate = dates.simpleDateObj(rawReleaseDate)

            rawRuntime = int(rawFilmData.get("RunTime", 0))
            rawDescription = rawFilmData.get("Teaser", "N/A")
            rawCast = rawFilmData.get("Cast", "N/A")
            rawDirector = rawFilmData.get("Director", "N/A")
            rawComingSoon = rawFilmData.get("IsComingSoon", False)
            rawNowShowing = rawFilmData.get("IsNowShowing", False)

            filmObject = Film(
                id=rawFilmID,
                name=rawName,
                friendlyName=friendlyName,
                ageRating=formattedRating,
                image=imageFileObject,
                filmURL=filmURL,
                releaseDate=convertedReleaseDate,
                runtime=rawRuntime,
                description=rawDescription,
                cast=rawCast,
                director=rawDirector,
                isComingSoon=rawComingSoon,
                isNowShowing=rawNowShowing,
                chain=chain,
                location=location,
                province=province,
            )

            # PARSE SESSIONS
            for rawSessionData in rawFilmData["Sessions"]:
                rawDate = rawSessionData["Date"]

                convertedDate = dates.simpleDateObj(rawDate).date()

                if startDate and convertedDate != startDate:
                    continue

                sessionObject = Session(date=convertedDate)

                # PARSE EXPERIENCES
                for rawExperience in rawSessionData["ExperienceTypes"]:
                    experienceObject = Experience()

                    # PARSE EXPERIENCE ATTRIBUTES
                    for rawExperienceAttribute in sorted(
                        rawExperience["ExperienceAttributes"],
                        key=lambda a: (
                            a["Order"]
                            if a["Id"]
                            not in constants.MOVIE_EXPERIENCE_ATTRIBUTE_ORDER_OVERRIDES
                            else 1.5
                        ),
                    ):
                        rawAttributeID = rawExperienceAttribute["Id"]
                        rawName = rawExperienceAttribute["Name"]
                        rawDescription = rawExperienceAttribute["Description"]
                        rawPrecedence = (
                            rawExperienceAttribute["Order"]
                            if rawExperienceAttribute["Id"]
                            not in constants.MOVIE_EXPERIENCE_ATTRIBUTE_ORDER_OVERRIDES
                            else 1.5
                        )

                        attributeObject = ExperienceAttribute(
                            id=rawAttributeID,
                            name=rawName,
                            description=rawDescription,
                            precedence=rawPrecedence,
                        )

                        experienceObject.addExperienceAttribute(attributeObject)

                    # PARSE EXPERIENCE TIMES
                    for rawExperienceTime in rawExperience["Times"]:
                        rawTime = rawExperienceTime["StartTime"]
                        convertedTime = dates.simpleDateObj(rawTime)
                        convertedDateTime = datetime.datetime.combine(
                            convertedDate, convertedTime.time()
                        )

                        rawSoldOut = rawExperienceTime["SoldOut"]
                        rawSessionExpired = rawExperienceTime["SessionExpired"]
                        rawScreen = rawExperienceTime["Screen"]
                        rawID = rawExperienceTime["Scheduleid"]

                        timeObject = ExperienceTime(
                            soldOut=rawSoldOut,
                            expired=rawSessionExpired,
                            screen=rawScreen,
                            time=convertedDateTime,
                            id=rawID,
                        )

                        experienceObject.addExperienceTime(timeObject)

                    sessionObject.addExperience(experienceObject)

                filmObject.addSession(sessionObject)

            if len(filmObject.sessions) < 1:
                continue

            parsed.append(filmObject)
    else:
        raise Exception("Invalid chain passed to parseShowtimes")

    if len(parsed) < 1:
        raise Exception(
            f"No films were found on or after {dates.formatSimpleDate(startDate if startDate else "Today", discordDateFormat="D")}."
        )

    fetchTrailersForAll(parsed)

    return parsed


class MovieDetailsEmbedReply(EmbedReply):
    def __init__(self, film: Film):
        title = f"Movie Showtimes - {text.truncateString(film.name, 200)[0]} - {film.chain} {film.location["location"]} 🔗↗️"
        commandName = "movies"
        description = text.truncateString(film.description, 2500)[0]
        url = film.filmURL

        super().__init__(title, commandName, url=url, description=description)

        self.set_thumbnail(url="attachment://movie-poster.jpg")
        self.add_field(name="Age Rating", value=film.ageRating)
        self.add_field(name="Runtime", value=film.formatRuntime())

        self.add_field(
            name="Release Date",
            value=dates.formatSimpleDate(film.releaseDate, discordDateFormat="D"),
        )

        self.add_field(name="Directed By", value=film.director)

        self.add_field(name="Cast", value=film.cast)


class MovieSelectionView(discord.ui.View):
    def __init__(self, films: list[Film], preSelectedDate: datetime.date):
        super().__init__(timeout=SELECTION_TIMEOUT)

        self.message: discord.WebhookMessage = None

        # Create the select menu options
        options = []

        for film in films:
            options.append(
                discord.SelectOption(
                    label=text.truncateString(film.name, 100)[0],
                    description=text.truncateString(
                        f"Next Show: {dates.formatSimpleDate(film.sessions[0].date, includeTime=False)} · Release: {dates.formatSimpleDate(film.releaseDate, includeTime=False)} · Runtime: {film.formatRuntime()}",
                        100,
                    )[0],
                    value=str(film.id),
                )
            )

        # Add the Select menu to the view
        self.add_item(
            MovieSelect(options=options, films=films, preSelectedDate=preSelectedDate)
        )

    async def on_timeout(self):
        reply = EmbedReply(
            "Movie Showtimes - Select A Movie - Timed Out",
            "movies",
            True,
            description="Movie selection timed out. Please retry this command.",
        )

        reply.set_thumbnail(url="attachment://cinema-logo.jpg")

        try:
            if self.message:
                await self.message.edit(embed=reply, view=None)
        except discord.NotFound:
            pass  # message already deleted/edited elsewhere


class MovieSelect(discord.ui.Select):
    def __init__(
        self,
        options: list[discord.SelectOption],
        films: list[Film],
        preSelectedDate: datetime.date,
    ):
        # Save all films for later use
        self.preSelectedDate = preSelectedDate
        self.allFilms = films
        super().__init__(placeholder="Select a movie...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selectedFilmID = int(self.values[0])

        selectedFilm = next(f for f in self.allFilms if f.id == selectedFilmID)

        self.view.stop()

        dateView = DateSelectView(
            film=selectedFilm,
            films=self.allFilms,
            message=self.view.message,
            preSelectedDate=self.preSelectedDate,
        )

        reply = MovieDetailsEmbedReply(selectedFilm)

        allAvailableExperienceDisplays = selectedFilm.allAvailableExperienceDisplays()

        reply.add_field(
            name="Available Experiences",
            value=" ".join(allAvailableExperienceDisplays),
            inline=False,
        )

        if self.preSelectedDate:
            try:
                selectedSession = next(
                    filter(
                        lambda s: s.date == self.preSelectedDate,
                        selectedFilm.sessions,
                    )
                )

                # Add showtime fields for the pre-selected date
                for idx, experience in enumerate(selectedSession.experiences, start=1):
                    name = (
                        f"Experience {idx} {experience.getMostProminentAttributeName()}"
                    )

                    times = [
                        f"— {dates.formatSimpleDate(time.time, discordDateFormat='t')} · {time.screen.title()}"
                        for time in experience.times
                    ]

                    reply.add_field(
                        name=name,
                        value=f"{' '.join(experience.listExperienceDisplays())}\n{text.truncateString('\n'.join(times), 1000)[0]}",
                        inline=False,
                    )
            except StopIteration:
                # Should not happen if data is valid, but if it does,
                # just proceed without adding showtimes.
                pass
        # --- END NEW LOGIC ---

        # Edit the original message with the new embed (now with showtimes)
        # and the new view.
        await interaction.response.edit_message(
            embed=reply, view=dateView, file=selectedFilm.image
        )


class DateSelectView(discord.ui.View):
    def __init__(
        self,
        film: Film,
        films: list[Film],
        message: discord.WebhookMessage,
        preSelectedDate: datetime.date | None,
    ):
        super().__init__(timeout=SELECTION_TIMEOUT)
        self.film = film
        self.films = films
        self.message = message
        self.preSelectedDate = preSelectedDate

        # date picker
        dateOptions = []
        for session in film.sessions:
            dateOptions.append(
                discord.SelectOption(
                    label=dates.formatSimpleDate(
                        session.date, includeTime=False, relativity=True, weekday=True
                    ),
                    value=session.date.isoformat(),
                    # This default flag is set based on the passed date
                    default=(
                        session.date == self.preSelectedDate
                        if self.preSelectedDate
                        else False
                    ),
                )
            )

        selectItem = DateSelect(dateOptions, film, message)
        self.add_item(selectItem)

        if film.chain == "Landmark":
            self.add_item(OpenLink("Get Tickets", link=film.filmURL))

            if film.trailerLink:
                self.add_item(OpenLink("View Movie Trailer", link=film.trailerLink))
            else:
                self.add_item(
                    OpenLink(
                        "View All Trailers",
                        link="https://www.landmarkcinemas.com/movie-trailers",
                    )
                )

        # The initDate() call is no longer needed here, as the logic
        # is now handled in MovieSelect.callback before this view is sent.

    async def on_timeout(self):
        try:
            if self.message:
                self.disable_all_items()
                await self.message.edit(view=self)
        except discord.NotFound:
            pass  # message already deleted/edited elsewhere


class DateSelect(discord.ui.Select):
    def __init__(
        self,
        options: list[discord.SelectOption],
        film: Film,
        message: discord.WebhookMessage,
    ):
        self.film = film
        self.message = message
        super().__init__(placeholder="Select a date...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selectedDateStr = self.values[0]
        selectedDate = dates.simpleDateObj(selectedDateStr).date()

        for opt in self.options:
            opt.default = opt.value == selectedDateStr

        self.view.preSelectedDate = selectedDate

        reply = MovieDetailsEmbedReply(self.film)

        reply.add_field(
            name="Available Experiences",
            value=" ".join(self.film.allAvailableExperienceDisplays()),
            inline=False,
        )

        selectedSession = next(
            filter(
                lambda s: s.date == selectedDate,
                self.film.sessions,
            )
        )

        for idx, experience in enumerate(selectedSession.experiences, start=1):
            name = f"Experience {idx} {experience.getMostProminentAttributeName()}"

            times = [
                f"— {dates.formatSimpleDate(time.time, discordDateFormat='t')} · {time.screen.title()}"
                for time in experience.times
            ]

            reply.add_field(
                name=name,
                value=f"{' '.join(experience.listExperienceDisplays())}\n{text.truncateString('\n'.join(times), 1000)[0]}",
                inline=False,
            )

        # Edit message but DO NOT replace the view instance
        await interaction.response.edit_message(embed=reply, view=self.view)


class SeatMap:
    def __init__(self):
        pass


class SeatArea:
    def __init__(self):
        pass


class SeatRow:
    def __init__(self):
        pass


class SeatGroup:
    def __init__(self):
        pass


class Seat:
    def __init__(self):
        pass


def fetchSeatMap(cinemaID: int, sessionID: int):
    pass
