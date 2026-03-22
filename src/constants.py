from src.classes import EmbedReply

DEFAULT_IMAGE = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQxsTcVDHm4n830jTn_4vnXiRJY-EzSJ2KprQ&s"

STORAGE_CHANNEL_ID = 1451968436006813728

RATINGS_OUT_OF = 10
RATINGS_STEP = 0.5

CURRENCIES = [
    {
        "name": "United States Dollar",
        "shortName": "USD",
        "symbol": "$",
    },
    {
        "name": "Russian Rouble",
        "shortName": "RUB",
        "symbol": "₽",
    },
    {
        "name": "Euro",
        "shortName": "EUR",
        "symbol": "€",
    },
]

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
    "Cineplex": {
        "ON": [
            {
                "id": "7257",
                "location": "Devonshire Mall",
                "slug": "cineplex-odeon-devonshire-mall-cinemas",
            },
            {"id": "7297", "location": "Chatham", "slug": "galaxy-cinemas-chatham"},
            {"id": "7138", "location": "Sarnia", "slug": "galaxy-cinemas-sarnia"},
            {
                "id": "7112",
                "location": "Westmount and VIP",
                "slug": "cineplex-odeon-westmount-cinemas-and-vip",
            },
            {
                "id": "7267",
                "location": "St. Thomas",
                "slug": "galaxy-cinemas-st-thomas",
            },
            {"id": "7422", "location": "London", "slug": "silvercity-london-cinemas"},
            {"id": "7268", "location": "Waterloo", "slug": "galaxy-cinemas-waterloo"},
            {"id": "7291", "location": "Brantford", "slug": "galaxy-cinemas-brantford"},
            {
                "id": "7296",
                "location": "Kitchener and VIP",
                "slug": "cineplex-cinemas-kitchener-and-vip",
            },
            {
                "id": "7269",
                "location": "Cambridge",
                "slug": "cineplex-cinemas-cambridge",
            },
            {"id": "7272", "location": "Guelph", "slug": "galaxy-cinemas-guelph"},
            {
                "id": "7117",
                "location": "Pergola Commons",
                "slug": "galaxy-cinemas-pergola-commons",
            },
            {"id": "7415", "location": "Ancaster", "slug": "cineplex-cinemas-ancaster"},
            {
                "id": "7290",
                "location": "Hamilton Mountain",
                "slug": "cineplex-cinemas-hamilton-mountain",
            },
            {
                "id": "7413",
                "location": "Burlington",
                "slug": "silvercity-burlington-cinemas",
            },
            {"id": "7285", "location": "Milton", "slug": "cineplex-cinemas-milton"},
            {
                "id": "7273",
                "location": "Oakville and VIP",
                "slug": "cineplex-cinemas-oakville-and-vip",
            },
            {
                "id": "7270",
                "location": "Orangeville",
                "slug": "galaxy-cinemas-orangeville",
            },
            {
                "id": "7264",
                "location": "Owen Sound",
                "slug": "galaxy-cinemas-owen-sound",
            },
            {
                "id": "7313",
                "location": "Junxion Erin Mills",
                "slug": "cineplex-junxion-erin-mills",
            },
            {
                "id": "7123",
                "location": "Winston Churchill & VIP",
                "slug": "cineplex-cinemas-winston-churchill-vip",
            },
            {
                "id": "7122",
                "location": "Courtney Park",
                "slug": "cineplex-cinemas-courtney-park",
            },
            {
                "id": "7411",
                "location": "Brampton",
                "slug": "silvercity-brampton-cinemas",
            },
            {
                "id": "7420",
                "location": "Mississauga Square One",
                "slug": "cineplex-cinemas-mississauga-square-one",
            },
            {
                "id": "7206",
                "location": "Seaway Mall",
                "slug": "cineplex-odeon-seaway-mall-cinemas",
            },
            {
                "id": "7260",
                "location": "Queensway and VIP",
                "slug": "cineplex-cinemas-queensway-and-vip",
            },
            {"id": "7408", "location": "Vaughan", "slug": "cineplex-cinemas-vaughan"},
            {
                "id": "7256",
                "location": "Niagara Square",
                "slug": "cineplex-odeon-niagara-square-cinemas",
            },
            {"id": "7406", "location": "Yorkdale", "slug": "cineplex-cinemas-yorkdale"},
            {
                "id": "7402",
                "location": "Scotiabank Toronto",
                "slug": "scotiabank-theatre-toronto",
            },
            {
                "id": "7130",
                "location": "Yonge-Dundas and VIP",
                "slug": "cineplex-cinemas-yongedundas-and-vip",
            },
            {
                "id": "7199",
                "location": "Varsity and VIP",
                "slug": "cineplex-cinemas-varsity-and-vip",
            },
            {
                "id": "7288",
                "location": "Collingwood",
                "slug": "galaxy-cinemas-collingwood",
            },
            {
                "id": "7400",
                "location": "Yonge-Eglinton and VIP",
                "slug": "cineplex-cinemas-yongeeglinton-and-vip",
            },
            {
                "id": "7298",
                "location": "Empress Walk",
                "slug": "cineplex-cinemas-empress-walk",
            },
            {
                "id": "7405",
                "location": "Richmond Hill",
                "slug": "silvercity-richmond-hill-cinemas",
            },
            {
                "id": "7139",
                "location": "Don Mills VIP",
                "slug": "cineplex-vip-cinemas-don-mills-age-restricted-19",
            },
            {
                "id": "7115",
                "location": "Fairview Mall",
                "slug": "cineplex-cinemas-fairview-mall",
            },
            {
                "id": "7253",
                "location": "Eglinton Town Centre",
                "slug": "cineplex-odeon-eglinton-town-centre-cinemas",
            },
            {
                "id": "7213",
                "location": "Markham and VIP",
                "slug": "cineplex-cinemas-markham-and-vip",
            },
            {
                "id": "7284",
                "location": "Aurora",
                "slug": "cineplex-odeon-aurora-cinemas",
            },
            {
                "id": "7404",
                "location": "Scarborough",
                "slug": "cineplex-cinemas-scarborough",
            },
            {
                "id": "7407",
                "location": "Newmarket",
                "slug": "silvercity-newmarket-cinemas-and-xscape-entertainment-centre",
            },
            {"id": "7249", "location": "Barrie", "slug": "galaxy-cinemas-barrie"},
            {
                "id": "7240",
                "location": "Morningside",
                "slug": "cineplex-odeon-morningside-cinemas",
            },
            {
                "id": "7135",
                "location": "North Barrie",
                "slug": "cineplex-cinemas-north-barrie",
            },
            {
                "id": "7312",
                "location": "Pickering and VIP",
                "slug": "cineplex-cinemas-pickering-and-vip",
            },
            {"id": "7248", "location": "Ajax", "slug": "cineplex-odeon-ajax-cinemas"},
            {"id": "7271", "location": "Midland", "slug": "galaxy-cinemas-midland"},
            {
                "id": "7289",
                "location": "Oshawa",
                "slug": "cineplex-odeon-oshawa-cinemas",
            },
            {"id": "7274", "location": "Orillia", "slug": "galaxy-cinemas-orillia"},
            {
                "id": "7241",
                "location": "Clarington Place",
                "slug": "cineplex-odeon-clarington-place-cinemas",
            },
            {
                "id": "7263",
                "location": "Peterborough",
                "slug": "galaxy-cinemas-peterborough",
            },
            {
                "id": "7266",
                "location": "Sault Ste Marie",
                "slug": "galaxy-cinemas-sault-ste-marie",
            },
            {"id": "7429", "location": "Sudbury", "slug": "silvercity-sudbury-cinemas"},
            {
                "id": "7409",
                "location": "Belleville",
                "slug": "galaxy-cinemas-belleville",
            },
            {"id": "7265", "location": "North Bay", "slug": "galaxy-cinemas-north-bay"},
            {
                "id": "7259",
                "location": "Gardiners Road",
                "slug": "cineplex-odeon-gardiners-road-cinemas",
            },
            {"id": "7424", "location": "Ottawa", "slug": "cineplex-cinemas-ottawa"},
            {
                "id": "7286",
                "location": "Barrhaven",
                "slug": "cineplex-odeon-barrhaven-cinemas",
            },
            {
                "id": "7247",
                "location": "South Keys",
                "slug": "cineplex-odeon-south-keys-cinemas",
            },
            {
                "id": "7311",
                "location": "Lansdowne and VIP",
                "slug": "cineplex-cinemas-lansdowne-and-vip",
            },
            {
                "id": "7428",
                "location": "Scotiabank Ottawa",
                "slug": "scotiabank-theatre-ottawa",
            },
            {"id": "7262", "location": "Cornwall", "slug": "galaxy-cinemas-cornwall"},
            {
                "id": "7430",
                "location": "Thunder Bay",
                "slug": "silvercity-thunder-bay-cinemas",
            },
        ],
        "QC": [
            {"id": "9268", "location": "Gatineau", "slug": "cinema-starcite-gatineau"},
            {
                "id": "9153",
                "location": "Carrefour Dorion",
                "slug": "cinema-cineplex-odeon-carrefour-dorion",
            },
            {"id": "9407", "location": "Kirkland", "slug": "cinema-cineplex-kirkland"},
            {"id": "9408", "location": "Laval", "slug": "cinema-cineplex-laval"},
            {
                "id": "9121",
                "location": "Royalmount",
                "slug": "cinema-cineplex-royalmount",
            },
            {
                "id": "9195",
                "location": "Carrefour Angrignon",
                "slug": "cinema-famous-players-carrefour-angrignon",
            },
            {
                "id": "9109",
                "location": "Forum et VIP",
                "slug": "cinema-cineplex-forum-et-vip",
            },
            {
                "id": "9406",
                "location": "Banque Scotia Montr\u00c3\u00a9al",
                "slug": "cinema-banque-scotia-montreal",
            },
            {
                "id": "9172",
                "location": "Quartier Latin",
                "slug": "cinema-cineplex-odeon-quartier-latin",
            },
            {
                "id": "9401",
                "location": "Montr\u00c3\u00a9al",
                "slug": "cinema-starcite-montreal",
            },
            {
                "id": "9185",
                "location": "Brossard et VIP",
                "slug": "cinema-cineplex-odeon-brossard-et-vip",
            },
            {
                "id": "9143",
                "location": "Saint-Bruno",
                "slug": "cinema-cineplex-odeon-saintbruno",
            },
            {
                "id": "9190",
                "location": "Capitol Saint-Jean",
                "slug": "capitol-saintjean",
            },
            {
                "id": "9188",
                "location": "Sherbrooke",
                "slug": "cinema-galaxy-sherbrooke",
            },
            {
                "id": "9186",
                "location": "Victoriaville",
                "slug": "cinema-galaxy-victoriaville",
            },
            {
                "id": "9177",
                "location": "Sainte-Foy",
                "slug": "cinema-cineplex-odeon-saintefoy",
            },
            {
                "id": "9196",
                "location": "IMAX aux Galeries de la Capitale",
                "slug": "cinema-cineplex-imax-aux-galeries-de-la-capitale",
            },
            {
                "id": "9181",
                "location": "Beauport",
                "slug": "cinema-cineplex-odeon-beauport",
            },
        ],
        "NB": [
            {
                "id": "6111",
                "location": "Fredericton",
                "slug": "cineplex-cinemas-fredericton",
            },
            {
                "id": "6107",
                "location": "Saint John",
                "slug": "cineplex-cinemas-saint-john",
            },
            {
                "id": "6112",
                "location": "Miramichi",
                "slug": "cineplex-cinemas-miramichi",
            },
            {
                "id": "6109",
                "location": "Trinity Drive",
                "slug": "cineplex-cinemas-trinity-drive",
            },
            {"id": "6110", "location": "Dieppe", "slug": "cineplex-cinemas-dieppe"},
        ],
        "MB": [
            {
                "id": "2402",
                "location": "St. Vital",
                "slug": "silvercity-st-vital-cinemas",
            },
            {
                "id": "2114",
                "location": "Junxion Kildonan Place",
                "slug": "cineplex-junxion-kildonan-place",
            },
            {
                "id": "2111",
                "location": "McGillivray and VIP",
                "slug": "cineplex-odeon-mcgillivray-cinemas-and-vip",
            },
            {
                "id": "2401",
                "location": "Scotiabank Winnipeg",
                "slug": "scotiabank-theatre-winnipeg",
            },
            {
                "id": "2112",
                "location": "City Northgate",
                "slug": "cinema-city-northgate",
            },
        ],
        "NS": [
            {"id": "5134", "location": "Yarmouth", "slug": "cineplex-cinemas-yarmouth"},
            {
                "id": "5132",
                "location": "New Minas",
                "slug": "cineplex-cinemas-new-minas",
            },
            {
                "id": "5119",
                "location": "Lower Sackville",
                "slug": "cineplex-cinemas-lower-sackville",
            },
            {
                "id": "5130",
                "location": "Scotiabank Halifax",
                "slug": "scotiabank-theatre-halifax",
            },
            {
                "id": "5143",
                "location": "Park Lane",
                "slug": "cineplex-cinemas-park-lane",
            },
            {
                "id": "5145",
                "location": "Dartmouth Crossing",
                "slug": "cineplex-cinemas-dartmouth-crossing",
            },
            {"id": "5140", "location": "Truro", "slug": "cineplex-cinemas-truro"},
            {
                "id": "5114",
                "location": "New Glasgow",
                "slug": "cineplex-cinemas-new-glasgow",
            },
            {"id": "5103", "location": "Sydney", "slug": "cineplex-cinemas-sydney"},
        ],
        "PE": [
            {
                "id": "6160",
                "location": "Summerside",
                "slug": "cineplex-cinemas-summerside",
            },
            {
                "id": "6161",
                "location": "Charlottetown",
                "slug": "cineplex-cinemas-charlottetown",
            },
        ],
        "SK": [
            {
                "id": "4108",
                "location": "Southland",
                "slug": "cineplex-cinemas-southland",
            },
            {
                "id": "4114",
                "location": "Normanview",
                "slug": "cineplex-cinemas-normanview",
            },
            {"id": "4113", "location": "Moose Jaw", "slug": "galaxy-cinemas-moose-jaw"},
            {
                "id": "4112",
                "location": "Prince Albert",
                "slug": "galaxy-cinemas-prince-albert",
            },
            {
                "id": "4115",
                "location": "at The Centre",
                "slug": "cineplex-cinemas-at-the-centre",
            },
            {
                "id": "4403",
                "location": "Scotiabank Saskatoon and VIP",
                "slug": "scotiabank-theatre-saskatoon-and-vip",
            },
        ],
        "NL": [
            {
                "id": "8124",
                "location": "Millbrook",
                "slug": "cineplex-cinemas-millbrook",
            },
            {
                "id": "8126",
                "location": "Scotiabank St. John's",
                "slug": "scotiabank-theatre-st-johns",
            },
        ],
        "AB": [
            {
                "id": "3140",
                "location": "Medicine Hat",
                "slug": "galaxy-cinemas-medicine-hat",
            },
            {
                "id": "3101",
                "location": "Lethbridge",
                "slug": "galaxy-cinemas-lethbridge",
            },
            {
                "id": "3152",
                "location": "East Hills",
                "slug": "cineplex-cinemas-east-hills",
            },
            {
                "id": "3103",
                "location": "Seton and VIP",
                "slug": "cineplex-cinemas-seton-and-vip",
            },
            {
                "id": "3142",
                "location": "Sunridge Spectrum",
                "slug": "cineplex-odeon-sunridge-spectrum-cinemas",
            },
            {
                "id": "3150",
                "location": "CrossIron Mills and XSCAPE Entertainment Centre",
                "slug": "silvercity-crossiron-mills-cinemas-and-xscape-entertainment-centre",
            },
            {
                "id": "3401",
                "location": "Scotiabank Chinook",
                "slug": "scotiabank-theatre-chinook",
            },
            {
                "id": "3157",
                "location": "VIP University District (age restricted 18+)",
                "slug": "cineplex-vip-cinemas-university-district-age-restricted-18",
            },
            {
                "id": "3409",
                "location": "Westhills",
                "slug": "cineplex-odeon-westhills-cinemas",
            },
            {"id": "3132", "location": "Red Deer", "slug": "galaxy-cinemas-red-deer"},
            {
                "id": "3138",
                "location": "Crowfoot Crossing",
                "slug": "cineplex-odeon-crowfoot-crossing-cinemas",
            },
            {
                "id": "3146",
                "location": "Sherwood Park",
                "slug": "cineplex-cinemas-sherwood-park",
            },
            {
                "id": "3151",
                "location": "Manning Town Centre",
                "slug": "cineplex-cinemas-manning-town-centre",
            },
            {
                "id": "3144",
                "location": "South Edmonton",
                "slug": "cineplex-odeon-south-edmonton-cinemas",
            },
            {
                "id": "3149",
                "location": "Windermere and VIP",
                "slug": "cineplex-odeon-windermere-cinemas-and-vip",
            },
            {
                "id": "3143",
                "location": "North Edmonton and VIP",
                "slug": "cineplex-cinemas-north-edmonton-and-vip",
            },
            {
                "id": "3403",
                "location": "Scotiabank Edmonton",
                "slug": "scotiabank-theatre-edmonton",
            },
            {
                "id": "3141",
                "location": "Grande Prairie",
                "slug": "cineplex-odeon-grande-prairie-cinemas",
            },
        ],
        "BC": [
            {"id": "1413", "location": "Vernon", "slug": "galaxy-cinemas-vernon"},
            {
                "id": "1410",
                "location": "Orchard Plaza",
                "slug": "cineplex-cinemas-orchard-plaza",
            },
            {
                "id": "1137",
                "location": "Aberdeen Mall",
                "slug": "cineplex-cinemas-aberdeen-mall",
            },
            {
                "id": "1144",
                "location": "Chilliwack",
                "slug": "galaxy-cinemas-chilliwack",
            },
            {"id": "1407", "location": "Mission", "slug": "silvercity-mission-cinemas"},
            {
                "id": "1148",
                "location": "Abbotsford and VIP",
                "slug": "cineplex-cinemas-abbotsford-and-vip",
            },
            {"id": "1405", "location": "Langley", "slug": "cineplex-cinemas-langley"},
            {
                "id": "1142",
                "location": "Meadowtown",
                "slug": "cineplex-odeon-meadowtown-cinemas",
            },
            {
                "id": "1412",
                "location": "Coquitlam and VIP",
                "slug": "cineplex-cinemas-coquitlam-and-vip",
            },
            {
                "id": "1136",
                "location": "Strawberry Hill",
                "slug": "cineplex-cinemas-strawberry-hill",
            },
            {
                "id": "1408",
                "location": "Metropolis",
                "slug": "cineplex-cinemas-metropolis",
            },
            {
                "id": "1158",
                "location": "VIP Brentwood (age restricted 19+)",
                "slug": "cineplex-vip-cinemas-brentwood-age-restricted-19",
            },
            {
                "id": "1409",
                "location": "Riverport",
                "slug": "silvercity-riverport-cinemas",
            },
            {
                "id": "1147",
                "location": "International Village",
                "slug": "cineplex-odeon-international-village-cinemas",
            },
            {
                "id": "1145",
                "location": "Marine Gateway and VIP",
                "slug": "cineplex-cinemas-marine-gateway-and-vip",
            },
            {
                "id": "1422",
                "location": "Scotiabank Vancouver",
                "slug": "scotiabank-theatre-vancouver",
            },
            {
                "id": "1151",
                "location": "Park Royal and VIP",
                "slug": "cineplex-cinemas-park-royal-and-vip",
            },
            {
                "id": "1149",
                "location": "Fifth Avenue (age restricted 19+)",
                "slug": "fifth-avenue-cinemas-age-restricted-19",
            },
            {"id": "1415", "location": "6", "slug": "famous-players-6-cinemas"},
            {
                "id": "1129",
                "location": "Victoria",
                "slug": "cineplex-odeon-victoria-cinemas",
            },
            {
                "id": "1417",
                "location": "SilverCity Victoria",
                "slug": "silvercity-victoria-cinemas",
            },
            {
                "id": "1146",
                "location": "Westshore",
                "slug": "cineplex-odeon-westshore-cinemas",
            },
            {"id": "1141", "location": "Nanaimo", "slug": "galaxy-cinemas-nanaimo"},
        ],
    },
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
}

MOVIE_EXPERIENCE_ATTRIBUTE_EMOJIS = {
    "ULTRA 2D": "<:landmarklaserultra:1438620427382689905>",
    "ULTRA 3D": "<:landmarklaserultra3d:1453763621757779979>",
    "CC": "<:landmarkcc:1438620425231007938>",
    "DVS": "<:landmarkdvs:1438620426074067056>",
    "Recliner": "<:landmarkrecliner:1438620431312617543>",
    "Premiere": "<:landmarkpremiere:1438620429358075933>",
    "Loungers": "<:landmarklounger:1438620428229804052>",
    "Shout Out": "<:landmarkshoutout:1438620432293953667>",
    "2D": "<:landmark2d:1438620424177975316>",
    "3D": "<:cineplex3d:1485081204112883896>",
    "LUXE 2D": "<:landmarkluxe:1438624990562881716>",
    "LUXE 3D": "<:landmarkluxe3d:1453769019264860212>",
    "18+": "<:landmark18:1438624988318924902>",
    "EnglishSub": "<:landmarkenglishsub:1438624989262647356>",
    "SpecialEvt": "<:landmarkspecialevent:1453763623603278008>",
    "Big Screen": "<:landmarkbigscreenrewind:1453763620713533618>",
    "HFR": "<:highframerate:1453768384419467435>",
    "UltraAVX": "<:cineplexultraavx:1485081212237119689>",
    "D-BOX": "<:cineplexdbox:1485081205593477324>",
    "Dolby Atmos": "<:cineplexdolby:1485081206608498890>",
    "IMAX": "<:cinepleximax:1485081208013590528>",
    "4DX": "<:cineplex4dx:1485081205115195402>",
    "Laser Projection": "<:cineplexlaserprojection:1485081208923750610>",
    "Regular": "<:cineplexregular:1485081211117240491>",
    "VIP 19+ Recliner": "<:cineplexvip19plus:1485081213453733950>",
}

MOVIE_EXPERIENCE_ATTRIBUTE_IGNORES = [
    "CC",
    "DVS",
]

MOVIE_EXPERIENCE_ATTRIBUTE_ORDER_OVERRIDES = [
    "2D",
    "3D",
]

UNICODE_WHITESPACE = {"2": "\u2002", "4": "\u2003"}

UNDER_CONSTRUCTION_EMBED = EmbedReply(
    "🚧🏗️ Command Under Construction 👷🛠️",
    "None",
    True,
    url="https://i.breia.net/V6DVc85F.mp4",
).set_image(url="https://i.breia.net/ph7sELj9.png")

OWNER_ONLY_EMBED = EmbedReply(
    "🛑🪪 Owner Only Command 🪪🛑",
    "None",
    True,
    url="https://i.breia.net/aKS9yXVK.mp4",
).set_image(url="https://i.breia.net/V6j1Qhqu.png")
