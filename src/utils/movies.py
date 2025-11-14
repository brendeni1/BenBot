import discord
import requests
import datetime

from src.utils import dates
from src.utils import text
from src.utils import images
from src import constants

from src.classes import *

SELECTION_TIMEOUT = 5


class ExperienceAttribute:
    def __init__(self, id: int, name: str, description: str, precedence: int):
        self.id = id
        self.name = name
        self.description = description
        self.precedence = precedence
        self.experience = None


class ExperienceTime:
    def __init__(
        self,
        soldOut: bool,
        expired: bool,
        screen: str,
        time: datetime.datetime,
    ):
        self.soldOut = soldOut
        self.expired = expired
        self.screen = screen
        self.time = time
        self.experience = None


class Experience:
    def __init__(
        self,
        times: list[ExperienceTime] | None = None,
        attributes: list[ExperienceAttribute] | None = None,
    ):
        self.times = attributes if attributes is not None else []
        self.attributes = attributes if attributes is not None else []
        self.session = None

    def addExperienceAttribute(self, experienceAttribute: ExperienceAttribute):
        experienceAttribute.experience = self

        self.attributes.append(experienceAttribute)

    def addExperienceTime(self, experienceTime: ExperienceTime):
        experienceTime.experience = self

        self.times.append(experienceTime)


class Session:
    def __init__(
        self, date: datetime.datetime, experiences: list[Experience] | None = None
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


async def parseShowtimes(rawData: dict, chain, province, location) -> list[Film]:
    parsed = []

    if chain == "Landmark":
        for rawFilmData in rawData:
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

                convertedDate = dates.simpleDateObj(rawDate)

                sessionObject = Session(date=convertedDate)

                # PARSE EXPERIENCES
                for rawExperience in rawSessionData["ExperienceTypes"]:
                    experienceObject = Experience()

                    # PARSE EXPERIENCE ATTRIBUTES
                    for rawExperienceAttribute in rawExperience["ExperienceAttributes"]:
                        rawAttributeID = rawExperienceAttribute["Id"]
                        rawName = rawExperienceAttribute["Name"]
                        rawDescription = rawExperienceAttribute["Description"]
                        rawPrecedence = rawExperienceAttribute["Order"]

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
                            convertedDate.date(), convertedTime.time()
                        )

                        rawSoldOut = rawExperienceTime["SoldOut"]
                        rawSessionExpired = rawExperienceTime["SessionExpired"]
                        rawScreen = rawExperienceTime["Screen"]

                        timeObject = ExperienceTime(
                            soldOut=rawSoldOut,
                            expired=rawSessionExpired,
                            screen=rawScreen,
                            time=convertedDateTime,
                        )

                        experienceObject.addExperienceTime(timeObject)

                    sessionObject.addExperience(experienceObject)

                filmObject.addSession(sessionObject)

            parsed.append(filmObject)
    else:
        raise Exception("Invalid chain passed to parseShowtimes")

    return parsed


class MovieSelectionView(discord.ui.View):
    def __init__(self, films: list[Film]):
        super().__init__(timeout=SELECTION_TIMEOUT)

        self.message = None

        # Create the select menu options
        options = []

        for film in films:
            options.append(
                discord.SelectOption(
                    label=text.truncateString(film.name, 100)[0],
                    description=text.truncateString(
                        f"Runtime: {round(film.duration)} mins", 100
                    )[0],
                    value=str(film.id),
                )
            )

        # Add the Select menu to the view
        self.add_item(MovieSelect(options=options, films=films))

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
    def __init__(self, options: list[discord.SelectOption], films: list[Film]):
        # Save all films for later use
        self.allFilms = films
        super().__init__(placeholder="Select a movie...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selectedFilmID = int(self.values[0])

        selectedFilm = next(f for f in self.allFilms if f.id == selectedFilmID)

        dateView = DateSelectView(film=selectedFilm)

        reply = EmbedReply(
            f"Movie Showtimes - {text.truncateString(selectedFilm.name, 200)[0]} - {selectedFilm.chain} {selectedFilm.location["location"]} 🔗↗️",
            "movies",
            description=text.truncateString(selectedFilm.description, 2500)[0],
            url=selectedFilm.filmURL,
        )

        reply.set_thumbnail(url="attachment://movie-poster.jpg")

        reply.add_field(name="Age Rating", value=selectedFilm.ageRating)

        reply.add_field(name="Runtime", value=f"{round(selectedFilm.duration)} mins")

        reply.add_field(
            name="Released On",
            value=dates.formatSimpleDate(
                selectedFilm.releaseDate, discordDateFormat="D"
            ),
        )

        reply.add_field(name="Directed By", value=selectedFilm.director)

        reply.add_field(name="Cast", value=selectedFilm.cast)

        # Edit the original message with the new embed and new view
        await interaction.response.edit_message(
            embed=reply, view=None, file=selectedFilm.image
        )


class DateSelectView(discord.ui.View):
    def __init__(self, film: Film):
        super().__init__(timeout=SELECTION_TIMEOUT)
        self.film = film  # Store the film for the callback
        self.message = None

        # Create options from the film's sessions
        options = []
        for session in film.sessions:
            # Format the date nicely
            date_str = session.date.strftime("%A, %B %d")  # e.g., "Friday, November 14"
            options.append(
                discord.SelectOption(
                    label=date_str,
                    value=session.date.strftime(
                        "%Y-%m-%d"
                    ),  # Use a standard format for the value
                )
            )

        self.add_item(DateSelect(options=options, film=film))


class DateSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], film: Film):
        self.film = film
        super().__init__(
            placeholder="Select a date...", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Find the selected Session object
        selected_date_str = self.values[0]
        selected_session = None
        for s in self.film.sessions:
            if s.date.strftime("%Y-%m-%d") == selected_date_str:
                selected_session = s
                break

        if not selected_session:
            await interaction.response.send_message(
                "Error: Could not find that session.", ephemeral=True
            )
            return

        # --- Now, build the FINAL showtimes embed ---

        # Create the base embed (re-using film info)
        embed = discord.Embed(
            title=f"{self.film.name} - Showtimes",
            description=f"Showing times for **{selected_session.date.strftime('%A, %B %d')}**",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=self.film.image)

        for experience in selected_session.experiences:
            experience_name = " | ".join([attr.name for attr in experience.attributes])
            if not experience_name:
                experience_name = "Showtimes"  # Fallback

            time_strings = []
            for time_obj in experience.times:
                if time_obj.expired:
                    continue  # Don't show times that have already passed

                time_str = time_obj.time.strftime("%I:%M %p")  # e.g., "07:00 PM"

                if time_obj.soldOut:
                    time_strings.append(f"~~{time_str}~~ (Sold Out)")
                else:
                    # Use inline code blocks for a clean look
                    time_strings.append(f"`{time_str}`")

            if time_strings:
                embed.add_field(
                    name=f"🎬 {experience_name}",
                    value=" ".join(time_strings),
                    inline=False,
                )

        if not embed.fields:
            embed.description = f"Sorry, there are no more showtimes available for {self.film.name} on this day."

        # Edit the message one last time, removing all UI components
        await interaction.response.edit_message(embed=embed, view=None)
