import discord
import aiohttp
import datetime
import xmltodict
import io
import os

from src.utils import dates
from src.utils import text
from src.utils import images
from src import constants

# Keep existing data classes
from src.classes import *

LANDMARK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.5",
    "Cache-Control": "max-age=0",
    "Dnt": "1",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Brave";v="146"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-Gpc": "1",
    "Upgrade-Insecure-Requests": "1",
}

CINEPLEX_API_KEY = os.getenv("CINEPLEX_API_KEY")

SELECTION_TIMEOUT = 890
TRAILER_SEARCH_CUTOFF = 40.0
TRAILER_SEARCH_INIT_AMOUNT = 250
TRAILER_SEARCH_KEYWORDS = ""

LANDMARK_LOGO = "https://i.breia.net/hIdg4zuf.jpg"
CINEPLEX_LOGO = "https://i.breia.net/XcLCj1ub.png"

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

    def getMostProminentAttributeName(
        self, emoji: bool = False, titleCase: bool = True
    ) -> str:
        if self.attributes:
            selected = self.attributes[0]

            return f"({selected.name.title() if titleCase else selected.name if not emoji else selected.getEmojiForAttribute()})"
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
        image_bytes: bytes | None = None,  # Changed from discord.File to bytes
        imageLink: str | None = None,
        sessions: list[Session] | None = None,
        trailerLink: str | None = None,
    ):
        self.id = id
        self.name = name
        self.friendlyName = friendlyName
        self.ageRating = ageRating
        self._image_bytes = image_bytes  # Store raw bytes
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
        self.imageLink = imageLink
        self.sessions = sessions if sessions is not None else []
        self.trailerLink = trailerLink

    @property
    def image(self) -> discord.File:
        """Generates a fresh discord.File object from the stored bytes."""
        # Create new BytesIO stream every time this is accessed
        return (
            discord.File(io.BytesIO(self._image_bytes), filename="movie-poster.jpg")
            if self._image_bytes
            else self.imageLink
        )

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


async def fetchShowtimes(
    chain: str, location: str, startDate: datetime.datetime = datetime.datetime.now()
) -> dict:
    if not startDate:
        startDate = datetime.datetime.now()

    async with aiohttp.ClientSession() as session:
        if chain == "Landmark":
            url = "https://www.landmarkcinemas.com/Umbraco/Api/MovieApi/MoviesByCinema"

            params = {
                "cinemaId": location,
                "splitByAttributes": "true",
                "expandSessions": "true",
            }

            async with session.get(
                url=url, params=params, headers=LANDMARK_HEADERS
            ) as response:
                response.raise_for_status()
                parsedResponse = await response.json()
                return parsedResponse

        elif chain == "Cineplex":
            url = f"https://apis.cineplex.com/prod/cpx/theatrical/api/v1/showtimes"

            parsedStartDate = dates.formatSimpleDate(
                timestamp=startDate, formatString="%-m/%-d/%Y"
            )

            params = {"language": "en", "locationId": location, "date": parsedStartDate}

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "ocp-apim-subscription-key": CINEPLEX_API_KEY,
            }

            async with session.get(url=url, params=params, headers=headers) as response:
                response.raise_for_status()
                parsedResponse = await response.json()
                return parsedResponse
        else:
            raise Exception("Invalid chain passed to fetchShowtimes")


async def fetchTrailersForAll(films: list[Film]) -> None:
    url = "https://www.landmarkcinemas.com/umbraco/api/ListingApi/GetVideosOverview"

    params = {
        "itemsPerPage": TRAILER_SEARCH_INIT_AMOUNT,
        "currentPage": "1",
        "filterBy": "recent",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=url, params=params, headers=LANDMARK_HEADERS
        ) as response:
            response.raise_for_status()
            text_data = await response.text()

    parsed = xmltodict.parse(text_data)

    items = parsed["TrailersListing"]["Items"]["TrailersListingItem"]
    if not items:
        return

    trailer_titles = [item["Title"] for item in items]
    trailer_urls = [f"https://www.landmarkcinemas.com{item['Url']}" for item in items]

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
            # Read bytes immediately and use them to init Film
            imageBytes = imageFileObject.fp.read()

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
                image_bytes=imageBytes,  # Pass bytes here
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

            for rawSessionData in rawFilmData["Sessions"]:
                rawDate = rawSessionData["Date"]

                convertedDate = dates.simpleDateObj(rawDate).date()

                if startDate and convertedDate != startDate:
                    continue

                sessionObject = Session(date=convertedDate)

                for rawExperience in rawSessionData["ExperienceTypes"]:
                    experienceObject = Experience()

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
    elif chain == "Cineplex":
        if not rawData:
            raise Exception("No showtimes found for that date/movie.")

        rawDataMovies = rawData[0].setdefault("dates", {})[0].get("movies", [])

        for rawFilmData in sorted(
            rawDataMovies,
            key=lambda f: sum(
                len(experience["sessions"]) for experience in f["experiences"]
            ),
            reverse=True,
        ):

            rawFilmID = rawFilmData.get("id", None)
            rawName = rawFilmData.get("name", None)

            friendlyName = rawFilmData.get("FriendlyName", "N/A")

            rawRating = rawFilmData.get("localRating", "TBC")

            formattedRating = rawRating if rawRating != "TBC" else None

            rawImage = rawFilmData.get("largePosterImageUrl", CINEPLEX_LOGO)

            filmURL = rawFilmData.get(
                "deeplinkUrl", "https://www.cineplex.com/?openTM=true"
            )

            rawReleaseDate = None
            convertedReleaseDate = (
                dates.simpleDateObj(rawReleaseDate) if rawReleaseDate else None
            )

            rawRuntime = int(rawFilmData.get("runtimeInMinutes", 0))
            genres = rawFilmData.get("genres", [])

            rawDescription = (
                "No Description/Genres" if not genres else ", ".join(genres)
            )

            rawCast = None
            rawDirector = None
            rawComingSoon = False
            rawNowShowing = False

            filmObject = Film(
                id=rawFilmID,
                name=rawName,
                friendlyName=friendlyName,
                ageRating=formattedRating,
                imageLink=rawImage,
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

            sessionDate = (
                rawData[0]
                .setdefault("dates", {})[0]
                .get(
                    "startDate",
                )
            )

            sessionObject = Session(date=dates.simpleDateObj(sessionDate).date())

            for rawExperiencesData in rawFilmData["experiences"]:
                experienceObj = Experience()

                for rawExperienceAttribute in rawExperiencesData["experienceTypes"]:
                    customID = rawExperienceAttribute.lower().replace(" ", "-")

                    experienceAttributeObj = ExperienceAttribute(
                        id=rawExperienceAttribute,
                        name=rawExperienceAttribute,
                        description="No Description",
                        precedence=1,
                    )

                    experienceObj.addExperienceAttribute(experienceAttributeObj)

                for session in rawExperiencesData["sessions"]:
                    soldOut = session.get("isSoldOut", False)
                    expired = session.get("isInThePast", False)
                    screen = session.get("auditorium", "Unknown Screen")
                    id = session.get("vistaSessionId", False)
                    time = session.get("showStartDateTime", None)

                    experienceTimeObj = ExperienceTime(
                        soldOut=soldOut,
                        expired=expired,
                        screen=screen,
                        id=id,
                        time=time,
                    )

                    experienceObj.addExperienceTime(experienceTimeObj)

                sessionObject.addExperience(experienceObj)

            filmObject.addSession(sessionObject)

            if len(filmObject.sessions) < 1:
                continue

            parsed.append(filmObject)
    else:
        raise Exception("Invalid chain passed to parseShowtimes")

    if len(parsed) < 1:
        raise Exception(
            f"No films were found on or after {dates.formatSimpleDate(startDate if startDate else 'Today', discordDateFormat='D')}."
        )

    await fetchTrailersForAll(parsed)

    return parsed


class MovieDetailsEmbedReply(EmbedReply):
    def __init__(self, film: Film):
        title = f"Movie Showtimes - {text.truncateString(film.name, 200)[0]} - {film.chain} {film.location['location']} 🔗↗️"
        commandName = "movies"
        description = text.truncateString(film.description, 2500)[0]
        url = film.filmURL

        super().__init__(title, commandName, url=url, description=description)

        self.set_thumbnail(
            url="attachment://movie-poster.jpg" if film._image_bytes else film.imageLink
        )
        self.add_field(name="Age Rating", value=film.ageRating)
        self.add_field(name="Runtime", value=film.formatRuntime())

        if film.releaseDate:
            self.add_field(
                name="Release Date",
                value=dates.formatSimpleDate(film.releaseDate, discordDateFormat="D"),
            )

        if film.director:
            self.add_field(name="Directed By", value=film.director)
        if film.cast:
            self.add_field(name="Cast", value=film.cast)


# ==========================================
# NEW DASHBOARD ARCHITECTURE
# ==========================================


def build_dashboard_embed(film: Film, selectedDate: datetime.date) -> EmbedReply:
    """Helper to generate the embed for any film/date combo."""
    reply = MovieDetailsEmbedReply(film)

    # Experience List
    reply.add_field(
        name="Available Experiences",
        value=" ".join(film.allAvailableExperienceDisplays()),
        inline=False,
    )

    # Find the session for the selected date
    try:
        selectedSession = next(filter(lambda s: s.date == selectedDate, film.sessions))

        for idx, experience in enumerate(selectedSession.experiences, start=1):
            name = f"Experience {idx} {experience.getMostProminentAttributeName(titleCase=film.chain == 'Landmark')}"
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
        reply.add_field(
            name="No Showtimes",
            value=f"No showtimes found for {dates.formatSimpleDate(selectedDate, includeTime=False)}.",
            inline=False,
        )

    return reply


class DashboardView(discord.ui.View):
    """
    The master view that holds both the Movie dropdown and the Date dropdown.
    Allows changing either 'on the fly'.
    """

    def __init__(
        self,
        current_film: Film,
        all_films: list[Film],
        current_date: datetime.date,
        message: discord.WebhookMessage = None,
    ):
        super().__init__(timeout=SELECTION_TIMEOUT)
        self.current_film = current_film
        self.all_films = all_films
        self.current_date = current_date
        self.message = message

        self.populate_components()

    def populate_components(self):
        """Clears and rebuilds the dropdowns and buttons based on current state."""
        self.clear_items()

        # 1. Movie Selector (Row 0)
        movie_options = []
        for film in self.all_films:
            movie_options.append(
                discord.SelectOption(
                    label=text.truncateString(film.name, 100)[0],
                    description=text.truncateString(
                        f"Release: {dates.formatSimpleDate(film.releaseDate, includeTime=False) if film.releaseDate else 'Unknown'} · Runtime: {film.formatRuntime()}",
                        100,
                    )[0],
                    value=str(film.id),
                    default=(film.id == self.current_film.id),
                )
            )
        self.add_item(DashboardMovieSelect(movie_options))

        # 2. Date Selector (Row 1)
        # Only show dates that actually have sessions for the *current* film
        date_options = []
        sessions_sorted = sorted(self.current_film.sessions, key=lambda s: s.date)

        for session in sessions_sorted:
            date_options.append(
                discord.SelectOption(
                    label=dates.formatSimpleDate(
                        session.date, includeTime=False, relativity=True, weekday=True
                    ),
                    value=session.date.isoformat(),
                    default=(session.date == self.current_date),
                )
            )

        # Fallback if somehow current date isn't in sessions (shouldn't happen via logic, but safe)
        if not date_options:
            date_options.append(
                discord.SelectOption(label="No Dates Available", value="none")
            )

        self.add_item(DashboardDateSelect(date_options))

        self.add_item(OpenLink("Get Tickets", link=self.current_film.filmURL))

        # 3. External Links (Row 2)
        if self.current_film.chain == "Landmark":
            if self.current_film.trailerLink:
                self.add_item(
                    OpenLink("View Movie Trailer", link=self.current_film.trailerLink)
                )
            else:
                self.add_item(
                    OpenLink(
                        "View All Trailers",
                        link="https://www.landmarkcinemas.com/movie-trailers",
                    )
                )

    async def update_view(self, interaction: discord.Interaction):
        """Updates the message with the new Embed and View state."""
        # Re-generate items to ensure 'default' ticks are correct
        self.populate_components()

        embed = build_dashboard_embed(self.current_film, self.current_date)

        # We must re-attach the file because editing a message usually invalidates
        # previous `attachment://` references. accessing .image property creates a FRESH file.
        await interaction.response.edit_message(
            embed=embed,
            view=self,
            file=(
                self.current_film.image
                if self.current_film._image_bytes
                else discord.MISSING
            ),
        )

    async def on_timeout(self):
        try:
            if self.message:
                self.disable_all_items()
                await self.message.edit(view=self)
        except discord.NotFound:
            pass


class DashboardMovieSelect(discord.ui.Select):
    def __init__(self, options):
        # We assume the parent View has .all_films
        super().__init__(
            placeholder="Select a different movie...", options=options, row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: DashboardView = self.view
        selected_id = int(self.values[0])

        # 1. Update the Current Film
        new_film = next((f for f in view.all_films if f.id == selected_id), None)
        if new_film:
            view.current_film = new_film

            # 2. Intellectually update the Date
            # If the new movie has a session on the currently selected date, keep it.
            # Otherwise, default to the new movie's first available date.
            available_dates = [s.date for s in new_film.sessions]
            if view.current_date not in available_dates:
                if available_dates:
                    view.current_date = min(available_dates)  # Closest/First date
                # else: keep current_date, it'll just show "No showtimes" in embed

        await view.update_view(interaction)


class DashboardDateSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Select a date...", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        view: DashboardView = self.view
        val = self.values[0]

        if val != "none":
            # Update Current Date
            view.current_date = dates.simpleDateObj(val).date()

        await view.update_view(interaction)


# ==========================================
# INITIAL SELECTION VIEW
# ==========================================


class MovieSelectionView(discord.ui.View):
    """
    The initial view shown when /movies showtimes is called.
    Allows the user to pick the FIRST movie.
    """

    def __init__(self, films: list[Film], preSelectedDate: datetime.date):
        super().__init__(timeout=SELECTION_TIMEOUT)
        self.films = films
        self.preSelectedDate = preSelectedDate
        self.message: discord.WebhookMessage = None

        options = []
        for film in films:
            options.append(
                discord.SelectOption(
                    label=text.truncateString(film.name, 100)[0],
                    description=text.truncateString(
                        f"Next: {dates.formatSimpleDate(film.sessions[0].date, includeTime=False)} · Runtime: {film.formatRuntime()}",
                        100,
                    )[0],
                    value=str(film.id),
                )
            )

        self.add_item(InitialMovieSelect(options=options))

    async def on_timeout(self):
        # Standard timeout logic for the initial menu
        reply = EmbedReply(
            "Movie Showtimes - Timed Out",
            "movies",
            True,
            description="Movie selection timed out. Please retry this command.",
        )
        try:
            if self.message:
                await self.message.edit(embed=reply, view=None)
        except discord.NotFound:
            pass


class InitialMovieSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption]):
        super().__init__(placeholder="Select a movie...", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: MovieSelectionView = self.view
        selectedFilmID = int(self.values[0])
        selectedFilm = next(f for f in view.films if f.id == selectedFilmID)

        # Stop the initial view
        view.stop()

        # Determine initial date
        # If user pre-selected a date in the slash command AND the movie has it: use it.
        # Otherwise: use the movie's first available date.
        initial_date = None
        available_dates = [s.date for s in selectedFilm.sessions]

        if view.preSelectedDate and view.preSelectedDate in available_dates:
            initial_date = view.preSelectedDate
        elif available_dates:
            initial_date = min(available_dates)
        else:
            initial_date = datetime.date.today()  # Fallback

        # Create the Master Dashboard View
        dashboard_view = DashboardView(
            current_film=selectedFilm,
            all_films=view.films,
            current_date=initial_date,
            message=view.message,
        )

        embed = build_dashboard_embed(selectedFilm, initial_date)

        await interaction.response.edit_message(
            embed=embed,
            view=dashboard_view,
            file=(selectedFilm.image if selectedFilm._image_bytes else discord.MISSING),
        )
