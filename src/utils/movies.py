from attr import attributes
import discord
import datetime

from src.utils import dates


class ExperienceAttribute:
    def __init__(self, id: int, name: str, description: str, precedence: int):
        self.id = id
        self.name = name
        self.description = description
        self.precedence = precedence


class Session:
    def __init__(self, date: datetime.datetime, experiences: list[Experience]):  # type: ignore
        self.date = date
        self.experiences = experiences


class Experience:
    def __init__(
        self,
        session: Session,
        time: datetime.datetime,
        soldOut: bool,
        expired: bool,
        screen: str,
        attributes: list[ExperienceAttribute],
    ):
        self.session = session
        self.time = time
        self.soldOut = soldOut
        self.expired = expired
        self.screen = screen
        self.attributes = attributes


class Film:
    def __init__(
        self,
        id: int,
        name: str,
        ageRating: str | None,
        image: str,
        releaseDate: datetime.datetime,
        duration: float,
        description: str,
        cast: str,
        director: str,
        sessions: list[Session],
        isComingSoon: bool,
        isNowShowing: bool,
    ):
        self.id = id
        self.name = name
        self.ageRating = ageRating
        self.image = image
        self.releaseDate = releaseDate
        self.duration = duration
        self.description = description
        self.cast = cast
        self.sessions = sessions
        self.isComingSoon = isComingSoon
        self.isNowShowing = isNowShowing


def test() -> list[discord.Member]:
    return "hello world"
