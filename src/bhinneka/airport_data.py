"""
Airport database for comprehensive airport search functionality.
"""

from typing import Dict, List, Tuple

# Major airports database: (code, name, city, country)
MAJOR_AIRPORTS: List[Tuple[str, str, str, str]] = [
    # North America
    ("LAX", "Los Angeles International Airport", "Los Angeles", "United States"),
    ("JFK", "John F. Kennedy International Airport", "New York", "United States"),
    ("LGA", "LaGuardia Airport", "New York", "United States"),
    ("EWR", "Newark Liberty International Airport", "Newark", "United States"),
    ("ORD", "O'Hare International Airport", "Chicago", "United States"),
    ("MDW", "Midway International Airport", "Chicago", "United States"),
    ("DFW", "Dallas/Fort Worth International Airport", "Dallas", "United States"),
    ("DAL", "Dallas Love Field", "Dallas", "United States"),
    ("DEN", "Denver International Airport", "Denver", "United States"),
    ("LAS", "Harry Reid International Airport", "Las Vegas", "United States"),
    ("PHX", "Phoenix Sky Harbor International Airport", "Phoenix", "United States"),
    ("SEA", "Seattle-Tacoma International Airport", "Seattle", "United States"),
    ("SFO", "San Francisco International Airport", "San Francisco", "United States"),
    ("SJC", "San Jose International Airport", "San Jose", "United States"),
    ("MIA", "Miami International Airport", "Miami", "United States"),
    ("FLL", "Fort Lauderdale-Hollywood International Airport", "Fort Lauderdale", "United States"),
    ("MCO", "Orlando International Airport", "Orlando", "United States"),
    ("ATL", "Hartsfield-Jackson Atlanta International Airport", "Atlanta", "United States"),
    ("CLT", "Charlotte Douglas International Airport", "Charlotte", "United States"),
    ("IAH", "George Bush Intercontinental Airport", "Houston", "United States"),
    ("HOU", "William P. Hobby Airport", "Houston", "United States"),
    ("MSP", "Minneapolis-Saint Paul International Airport", "Minneapolis", "United States"),
    ("DTW", "Detroit Metropolitan Wayne County Airport", "Detroit", "United States"),
    ("PHL", "Philadelphia International Airport", "Philadelphia", "United States"),
    ("BWI", "Baltimore/Washington International Airport", "Baltimore", "United States"),
    ("DCA", "Ronald Reagan Washington National Airport", "Washington", "United States"),
    ("IAD", "Washington Dulles International Airport", "Washington", "United States"),
    ("BOS", "Logan International Airport", "Boston", "United States"),
    ("YYZ", "Toronto Pearson International Airport", "Toronto", "Canada"),
    ("YVR", "Vancouver International Airport", "Vancouver", "Canada"),
    ("YUL", "Montréal-Trudeau International Airport", "Montreal", "Canada"),
    # Europe
    ("LHR", "Heathrow Airport", "London", "United Kingdom"),
    ("LGW", "Gatwick Airport", "London", "United Kingdom"),
    ("STN", "Stansted Airport", "London", "United Kingdom"),
    ("LTN", "Luton Airport", "London", "United Kingdom"),
    ("CDG", "Charles de Gaulle Airport", "Paris", "France"),
    ("ORY", "Orly Airport", "Paris", "France"),
    ("FRA", "Frankfurt Airport", "Frankfurt", "Germany"),
    ("MUC", "Munich Airport", "Munich", "Germany"),
    ("AMS", "Amsterdam Airport Schiphol", "Amsterdam", "Netherlands"),
    ("MAD", "Adolfo Suárez Madrid-Barajas Airport", "Madrid", "Spain"),
    ("BCN", "Barcelona-El Prat Airport", "Barcelona", "Spain"),
    ("FCO", "Leonardo da Vinci-Fiumicino Airport", "Rome", "Italy"),
    ("MXP", "Milan Malpensa Airport", "Milan", "Italy"),
    ("ZUR", "Zurich Airport", "Zurich", "Switzerland"),
    ("VIE", "Vienna International Airport", "Vienna", "Austria"),
    ("CPH", "Copenhagen Airport", "Copenhagen", "Denmark"),
    ("ARN", "Stockholm Arlanda Airport", "Stockholm", "Sweden"),
    ("OSL", "Oslo Airport", "Oslo", "Norway"),
    ("HEL", "Helsinki Airport", "Helsinki", "Finland"),
    ("WAW", "Warsaw Chopin Airport", "Warsaw", "Poland"),
    ("PRG", "Václav Havel Airport Prague", "Prague", "Czech Republic"),
    ("BUD", "Budapest Ferenc Liszt International Airport", "Budapest", "Hungary"),
    ("ATH", "Athens International Airport", "Athens", "Greece"),
    ("IST", "Istanbul Airport", "Istanbul", "Turkey"),
    ("SVO", "Sheremetyevo International Airport", "Moscow", "Russia"),
    ("LED", "Pulkovo Airport", "St. Petersburg", "Russia"),
    # Asia Pacific
    ("NRT", "Narita International Airport", "Tokyo", "Japan"),
    ("HND", "Haneda Airport", "Tokyo", "Japan"),
    ("KIX", "Kansai International Airport", "Osaka", "Japan"),
    ("ICN", "Incheon International Airport", "Seoul", "South Korea"),
    ("GMP", "Gimpo International Airport", "Seoul", "South Korea"),
    ("PEK", "Beijing Capital International Airport", "Beijing", "China"),
    ("PKX", "Beijing Daxing International Airport", "Beijing", "China"),
    ("PVG", "Shanghai Pudong International Airport", "Shanghai", "China"),
    ("SHA", "Shanghai Hongqiao International Airport", "Shanghai", "China"),
    ("CAN", "Guangzhou Baiyun International Airport", "Guangzhou", "China"),
    ("SZX", "Shenzhen Bao'an International Airport", "Shenzhen", "China"),
    ("HKG", "Hong Kong International Airport", "Hong Kong", "Hong Kong"),
    ("TPE", "Taiwan Taoyuan International Airport", "Taipei", "Taiwan"),
    ("TSA", "Taipei Songshan Airport", "Taipei", "Taiwan"),
    ("SIN", "Singapore Changi Airport", "Singapore", "Singapore"),
    ("KUL", "Kuala Lumpur International Airport", "Kuala Lumpur", "Malaysia"),
    ("BKK", "Suvarnabhumi Airport", "Bangkok", "Thailand"),
    ("DMK", "Don Mueang International Airport", "Bangkok", "Thailand"),
    ("CGK", "Soekarno-Hatta International Airport", "Jakarta", "Indonesia"),
    ("DPS", "Ngurah Rai International Airport", "Denpasar", "Indonesia"),
    ("MNL", "Ninoy Aquino International Airport", "Manila", "Philippines"),
    ("SYD", "Sydney Kingsford Smith Airport", "Sydney", "Australia"),
    ("MEL", "Melbourne Airport", "Melbourne", "Australia"),
    ("BNE", "Brisbane Airport", "Brisbane", "Australia"),
    ("PER", "Perth Airport", "Perth", "Australia"),
    ("AKL", "Auckland Airport", "Auckland", "New Zealand"),
    # Middle East & Africa
    ("DXB", "Dubai International Airport", "Dubai", "United Arab Emirates"),
    ("AUH", "Abu Dhabi International Airport", "Abu Dhabi", "United Arab Emirates"),
    ("DOH", "Hamad International Airport", "Doha", "Qatar"),
    ("KWI", "Kuwait International Airport", "Kuwait City", "Kuwait"),
    ("RUH", "King Khalid International Airport", "Riyadh", "Saudi Arabia"),
    ("JED", "King Abdulaziz International Airport", "Jeddah", "Saudi Arabia"),
    ("CAI", "Cairo International Airport", "Cairo", "Egypt"),
    ("JNB", "O.R. Tambo International Airport", "Johannesburg", "South Africa"),
    ("CPT", "Cape Town International Airport", "Cape Town", "South Africa"),
    # South America
    ("GRU", "São Paulo-Guarulhos International Airport", "São Paulo", "Brazil"),
    ("GIG", "Rio de Janeiro-Galeão International Airport", "Rio de Janeiro", "Brazil"),
    ("EZE", "Ezeiza International Airport", "Buenos Aires", "Argentina"),
    ("SCL", "Arturo Merino Benítez International Airport", "Santiago", "Chile"),
    ("LIM", "Jorge Chávez International Airport", "Lima", "Peru"),
    ("BOG", "El Dorado International Airport", "Bogotá", "Colombia"),
]

# Create indices for fast searching
CODE_INDEX: Dict[str, Tuple[str, str, str, str]] = {
    code: (code, name, city, country) for code, name, city, country in MAJOR_AIRPORTS
}
NAME_INDEX: Dict[str, List[Tuple[str, str, str, str]]] = {}
CITY_INDEX: Dict[str, List[Tuple[str, str, str, str]]] = {}

# Build search indices
for code, name, city, country in MAJOR_AIRPORTS:
    # Index by airport name words
    name_words = name.lower().replace("-", " ").replace("'", "").split()
    for word in name_words:
        if word not in NAME_INDEX:
            NAME_INDEX[word] = []
        NAME_INDEX[word].append((code, name, city, country))

    # Index by city name
    city_lower = city.lower()
    if city_lower not in CITY_INDEX:
        CITY_INDEX[city_lower] = []
    CITY_INDEX[city_lower].append((code, name, city, country))


def search_airports_local(query: str, limit: int = 10) -> List[Tuple[str, str, str, str]]:
    """
    Search airports using local database.

    Args:
        query: Search query (airport code, name, or city)
        limit: Maximum number of results

    Returns:
        List of tuples (code, name, city, country)
    """
    if not query:
        return []

    query_lower = query.lower().strip()
    results = []
    seen_codes = set()

    # 1. Direct code match (highest priority)
    if query_lower.upper() in CODE_INDEX:
        airport = CODE_INDEX[query_lower.upper()]
        results.append(airport)
        seen_codes.add(airport[0])

    # 2. City name matches
    if query_lower in CITY_INDEX:
        for airport in CITY_INDEX[query_lower]:
            if airport[0] not in seen_codes:
                results.append(airport)
                seen_codes.add(airport[0])

    # 3. Partial matches in airport names
    for word, airports in NAME_INDEX.items():
        if query_lower in word:
            for airport in airports:
                if airport[0] not in seen_codes:
                    results.append(airport)
                    seen_codes.add(airport[0])

    # 4. Partial matches in city names
    for city, airports in CITY_INDEX.items():
        if query_lower in city:
            for airport in airports:
                if airport[0] not in seen_codes:
                    results.append(airport)
                    seen_codes.add(airport[0])

    return results[:limit]
