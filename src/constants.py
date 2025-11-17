RATINGS_OUT_OF = 10
RATINGS_STEP = 0.5

EMOJI_MAP = {
    "0": "0️⃣",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
}

RANKING_MEDALS = {
    "1": "🥇",
    "2": "🥈",
    "3": "🥉",
}

MOVIE_CINEMAS = {
    "Landmark": {
        "AB": [
            {
                "id": "184",
                "location": "Calgary Country Hills",
                "slug": "calgary-country-hills",
            },
            {
                "id": "7800",
                "location": "Calgary Market Mall",
                "slug": "calgary-market-mall",
            },
            {"id": "196", "location": "Calgary Shawnessy", "slug": "calgary-shawnessy"},
            {"id": "206", "location": "Drayton Valley", "slug": "drayton-valley"},
            {
                "id": "182",
                "location": "Edmonton City Centre",
                "slug": "edmonton-city-centre",
            },
            {"id": "7782", "location": "Edson", "slug": "edson"},
            {
                "id": "7799",
                "location": "Fort McMurray Eagle Ridge",
                "slug": "fort-mcmurray-eagle-ridge",
            },
            {"id": "197", "location": "Spruce Grove", "slug": "spruce-grove"},
            {"id": "7795", "location": "St. Albert", "slug": "st-albert"},
            {"id": "217", "location": "Sylvan Lake", "slug": "sylvan-lake"},
            {
                "id": "7801",
                "location": "Edmonton Tamarack",
                "slug": "tamarack-edmonton",
            },
        ],
        "BC": [
            {"id": "203", "location": "Courtenay", "slug": "courtenay"},
            {"id": "204", "location": "Cranbrook", "slug": "cranbrook"},
            {"id": "209", "location": "Fort St. John", "slug": "fort-st-john"},
            {"id": "211", "location": "Kelowna, Grand 10", "slug": "kelowna-grand-10"},
            {"id": "213", "location": "Nanaimo", "slug": "nanaimo"},
            {"id": "214", "location": "New Westminster", "slug": "new-westminster"},
            {"id": "195", "location": "Penticton", "slug": "penticton"},
            {"id": "187", "location": "Surrey, Guildford", "slug": "surrey-guildford"},
            {
                "id": "207",
                "location": "West Kelowna, Xtreme",
                "slug": "west-kelowna-xtreme",
            },
        ],
        "MB": [
            {"id": "181", "location": "Brandon", "slug": "brandon"},
            {"id": "202", "location": "Winkler", "slug": "winkler"},
            {
                "id": "186",
                "location": "Winnipeg, Grant Park",
                "slug": "winnipeg-grant-park",
            },
        ],
        "ON": [
            {"id": "180", "location": "Caledon, Bolton", "slug": "caledon-bolton"},
            {
                "id": "188",
                "location": "Hamilton, Jackson Square",
                "slug": "hamilton-jackson-square",
            },
            {"id": "189", "location": "Kanata", "slug": "kanata"},
            {"id": "190", "location": "Kingston", "slug": "kingston"},
            {"id": "192", "location": "London", "slug": "london"},
            {"id": "193", "location": "Orleans", "slug": "orleans"},
            {
                "id": "194",
                "location": "St. Catharines, Pen Centre",
                "slug": "st-catharines-pen-centre",
            },
            {"id": "200", "location": "Waterloo", "slug": "waterloo"},
            {"id": "201", "location": "Whitby", "slug": "whitby"},
            {"id": "7802", "location": "Windsor", "slug": "windsor"},
        ],
        "SK": [
            {"id": "7796", "location": "Regina", "slug": "regina"},
            {"id": "7798", "location": "Saskatoon", "slug": "saskatoon"},
        ],
    },
    "Cineplex": {
        "TEST": [
            {"id": "1", "location": "TEST"},
        ]
    },
}

MOVIE_EXPERIENCE_ATTRIBUTE_EMOJIS = {
    "ULTRA 2D": "<:landmarklaserultra:1438620427382689905>",
    "CC": "<:landmarkcc:1438620425231007938>",
    "DVS": "<:landmarkdvs:1438620426074067056>",
    "Recliner": "<:landmarkrecliner:1438620431312617543>",
    "Premiere": "<:landmarkpremiere:1438620429358075933>",
    "Loungers": "<:landmarklounger:1438620428229804052>",
    "Shout Out": "<:landmarkshoutout:1438620432293953667>",
    "2D": "<:landmark2d:1438620424177975316>",
    "3D": "<:landmark3d:1438626057782693888>",
    "LUXE 2D": "<:landmarkluxe:1438624990562881716>",
    "18+": "<:landmark18:1438624988318924902>",
    "EnglishSub": "<:landmarkenglishsub:1438624989262647356>",
}

MOVIE_EXPERIENCE_ATTRIBUTE_IGNORES = [
    "CC",
    "DVS",
]
