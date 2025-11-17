import discord
import requests
import datetime

from src.utils import dates
from src.utils import text
from src.utils import images
from src import constants

from src.classes import *

SELECTION_TIMEOUT = 600


class ExperienceAttribute:
    def __init__(self, id: int, name: str, description: str, precedence: int):
        self.id = id
        self.name = name
        self.description = description
        self.precedence = precedence
        self.experience = None

    def getEmojiForAttribute(self) -> str | None:
        return constants.MOVIE_EXPERIENCE_ATTRIBUTE_EMOJIS.get(self.id)


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
        duration: float,
        description: str,
        cast: str,
        director: str,
        isComingSoon: bool,
        isNowShowing: bool,
        chain: str,
        province: str,
        location: dict,
        sessions: list[Session] | None = None,
    ):
        self.id = id
        self.name = name
        self.friendlyName = friendlyName
        self.ageRating = ageRating
        self.image = image
        self.filmURL = filmURL
        self.releaseDate = releaseDate
        self.duration = duration
        self.description = description
        self.cast = cast
        self.director = director
        self.isComingSoon = isComingSoon
        self.isNowShowing = isNowShowing
        self.chain = chain
        self.province = province
        self.location = location
        self.sessions = sessions if sessions is not None else []

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


async def parseShowtimes(
    rawData: dict, chain, province, location, startDate: datetime.date
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
            rawFilmID = rawFilmData["FilmId"]
            rawName = rawFilmData["Title"]
            friendlyName = rawFilmData["FriendlyName"]

            rawRating = rawFilmData["Cert"]
            formattedRating = rawRating if rawRating != "TBC" else None

            rawImage = rawFilmData["Img"]

            imageFileObject = await images.fetchToFile(
                rawImage,
                "movie-poster.jpg",
            )

            filmURL = f"https://www.landmarkcinemas.com/film-info/{friendlyName}"

            rawReleaseDate = rawFilmData["ReleaseDate"]
            convertedReleaseDate = dates.simpleDateObj(rawReleaseDate)

            rawDuration = float(rawFilmData["RunTime"])
            rawDescription = rawFilmData["Teaser"]
            rawCast = rawFilmData["Cast"]
            rawDirector = rawFilmData["Director"]
            rawComingSoon = rawFilmData["IsComingSoon"]
            rawNowShowing = rawFilmData["IsNowShowing"]

            filmObject = Film(
                id=rawFilmID,
                name=rawName,
                friendlyName=friendlyName,
                ageRating=formattedRating,
                image=imageFileObject,
                filmURL=filmURL,
                releaseDate=convertedReleaseDate,
                duration=rawDuration,
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

                if convertedDate < startDate:
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
        self.add_field(name="Runtime", value=f"{round(film.duration)} mins")

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
                        f"Release: {dates.formatSimpleDate(film.releaseDate, includeTime=False)} · Runtime: {round(film.duration)} mins",
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

        reply.add_field(
            name="Available Experiences",
            value=" ".join(selectedFilm.allAvailableExperienceDisplays()),
            inline=False,
        )

        # Edit the original message with the new embed and new view
        await interaction.response.edit_message(
            embed=reply, view=dateView, file=selectedFilm.image
        )


class MovieSelectInDetails(discord.ui.Select):
    def __init__(self, films, currentFilm):
        options = []
        for film in films:
            options.append(
                discord.SelectOption(
                    label=text.truncateString(film.name, 100)[0],
                    description=text.truncateString(
                        f"Runtime: {round(film.duration)} mins", 100
                    )[0],
                    value=str(film.id),
                    default=(film.id == currentFilm.id),
                )
            )

        self.films = films
        super().__init__(placeholder="Select a movie...", options=options)

    async def callback(
        self, interaction: discord.Interaction
    ):  # MODIFIED: Added type hint
        # FIX 1: Stop the old view to prevent "stacking timeouts"
        self.view.stop()

        filmID = int(self.values[0])
        newFilm = next(f for f in self.films if f.id == filmID)

        newView = DateSelectView(
            film=newFilm, films=self.films, message=self.view.message
        )

        embed = MovieDetailsEmbedReply(newFilm)

        embed.add_field(
            name="Available Experiences",
            value=" ".join(newFilm.allAvailableExperienceDisplays()),
            inline=False,
        )

        await interaction.response.edit_message(embed=embed, view=newView)


class DateSelectView(discord.ui.View):
    def __init__(self, film: Film, films: list[Film], message, preSelectedDate):
        super().__init__(timeout=SELECTION_TIMEOUT)
        self.film = film
        self.films = films
        self.message = message

        self.preSelectedDate = None

        # movie picker - CURRNETLY HIDDEN BECAUSE DISCORD FILE UPLOAD LIMITATIONS
        # self.add_item(MovieSelectInDetails(films, film))

        # date picker
        dateOptions = []
        for session in film.sessions:
            dateOptions.append(
                discord.SelectOption(
                    label=dates.formatSimpleDate(
                        session.date, includeTime=False, relativity=True
                    ),
                    value=session.date.isoformat(),
                    default=session.date == self.preSelectedDate,
                )
            )

        self.add_item(DateSelect(dateOptions, film))

    async def on_timeout(self):
        try:
            if self.message:
                self.disable_all_items()

                await self.message.edit(view=self)
        except discord.NotFound:
            pass  # message already deleted/edited elsewhere


class DateSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], film: Film):
        self.film = film
        super().__init__(placeholder="Select a date...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selectedDate = self.values[0]

        # Update default flags in-place
        for opt in self.options:
            opt.default = opt.value == selectedDate

        reply = MovieDetailsEmbedReply(self.film)

        selectedSession = next(
            filter(
                lambda s: s.date == dates.simpleDateObj(selectedDate).date(),
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
