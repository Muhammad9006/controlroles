"""Country names, ISO codes and regions used to label job locations worldwide."""

# name -> (ISO2, ISO3, region). Names are what the website shows.
COUNTRIES = {
    # Middle East
    "Saudi Arabia": ("SA", "SAU", "Middle East"), "UAE": ("AE", "ARE", "Middle East"), "Qatar": ("QA", "QAT", "Middle East"),
    "Kuwait": ("KW", "KWT", "Middle East"), "Bahrain": ("BH", "BHR", "Middle East"), "Oman": ("OM", "OMN", "Middle East"),
    "Jordan": ("JO", "JOR", "Middle East"), "Lebanon": ("LB", "LBN", "Middle East"), "Iraq": ("IQ", "IRQ", "Middle East"),
    "Israel": ("IL", "ISR", "Middle East"), "Turkey": ("TR", "TUR", "Middle East"), "Egypt": ("EG", "EGY", "Africa"),
    # Europe
    "United Kingdom": ("GB", "GBR", "Europe"), "Ireland": ("IE", "IRL", "Europe"), "France": ("FR", "FRA", "Europe"),
    "Germany": ("DE", "DEU", "Europe"), "Netherlands": ("NL", "NLD", "Europe"), "Belgium": ("BE", "BEL", "Europe"),
    "Luxembourg": ("LU", "LUX", "Europe"), "Spain": ("ES", "ESP", "Europe"), "Portugal": ("PT", "PRT", "Europe"),
    "Italy": ("IT", "ITA", "Europe"), "Switzerland": ("CH", "CHE", "Europe"), "Austria": ("AT", "AUT", "Europe"),
    "Denmark": ("DK", "DNK", "Europe"), "Sweden": ("SE", "SWE", "Europe"), "Norway": ("NO", "NOR", "Europe"),
    "Finland": ("FI", "FIN", "Europe"), "Poland": ("PL", "POL", "Europe"), "Czech Republic": ("CZ", "CZE", "Europe"),
    "Romania": ("RO", "ROU", "Europe"), "Greece": ("GR", "GRC", "Europe"), "Hungary": ("HU", "HUN", "Europe"),
    "Bulgaria": ("BG", "BGR", "Europe"), "Croatia": ("HR", "HRV", "Europe"), "Serbia": ("RS", "SRB", "Europe"),
    "Slovakia": ("SK", "SVK", "Europe"), "Estonia": ("EE", "EST", "Europe"), "Latvia": ("LV", "LVA", "Europe"),
    "Lithuania": ("LT", "LTU", "Europe"), "Cyprus": ("CY", "CYP", "Europe"), "Malta": ("MT", "MLT", "Europe"), "Ukraine": ("UA", "UKR", "Europe"), "North Macedonia": ("MK", "MKD", "Europe"),
    # North America
    "United States": ("US", "USA", "North America"), "Canada": ("CA", "CAN", "North America"),
    "Mexico": ("MX", "MEX", "Latin America"),
    # Latin America
    "Brazil": ("BR", "BRA", "Latin America"), "Chile": ("CL", "CHL", "Latin America"), "Colombia": ("CO", "COL", "Latin America"),
    "Peru": ("PE", "PER", "Latin America"), "Argentina": ("AR", "ARG", "Latin America"), "Panama": ("PA", "PAN", "Latin America"),
    "Puerto Rico": ("PR", "PRI", "Latin America"), "Dominican Republic": ("DO", "DOM", "Latin America"),
    "Ecuador": ("EC", "ECU", "Latin America"), "Costa Rica": ("CR", "CRI", "Latin America"),
    # Asia Pacific
    "Australia": ("AU", "AUS", "Asia Pacific"), "New Zealand": ("NZ", "NZL", "Asia Pacific"), "India": ("IN", "IND", "Asia Pacific"),
    "Singapore": ("SG", "SGP", "Asia Pacific"), "Malaysia": ("MY", "MYS", "Asia Pacific"), "Philippines": ("PH", "PHL", "Asia Pacific"),
    "Indonesia": ("ID", "IDN", "Asia Pacific"), "Thailand": ("TH", "THA", "Asia Pacific"), "Vietnam": ("VN", "VNM", "Asia Pacific"),
    "Hong Kong": ("HK", "HKG", "Asia Pacific"), "Macau": ("MO", "MAC", "Asia Pacific"), "Timor-Leste": ("TL", "TLS", "Asia Pacific"), "China": ("CN", "CHN", "Asia Pacific"), "Japan": ("JP", "JPN", "Asia Pacific"),
    "South Korea": ("KR", "KOR", "Asia Pacific"), "Taiwan": ("TW", "TWN", "Asia Pacific"), "Pakistan": ("PK", "PAK", "Asia Pacific"),
    "Bangladesh": ("BD", "BGD", "Asia Pacific"), "Sri Lanka": ("LK", "LKA", "Asia Pacific"), "Kazakhstan": ("KZ", "KAZ", "Asia Pacific"),
    "Uzbekistan": ("UZ", "UZB", "Asia Pacific"), "Papua New Guinea": ("PG", "PNG", "Asia Pacific"), "Guam": ("GU", "GUM", "Asia Pacific"),
    "Georgia (country)": ("GE", "GEO", "Europe"), "Azerbaijan": ("AZ", "AZE", "Europe"),
    # Africa
    "South Africa": ("ZA", "ZAF", "Africa"), "Morocco": ("MA", "MAR", "Africa"), "Algeria": ("DZ", "DZA", "Africa"),
    "Tunisia": ("TN", "TUN", "Africa"), "Nigeria": ("NG", "NGA", "Africa"), "Kenya": ("KE", "KEN", "Africa"),
    "Ghana": ("GH", "GHA", "Africa"), "Ethiopia": ("ET", "ETH", "Africa"), "Tanzania": ("TZ", "TZA", "Africa"),
    "Mozambique": ("MZ", "MOZ", "Africa"), "Namibia": ("NA", "NAM", "Africa"), "Senegal": ("SN", "SEN", "Africa"), "Côte d'Ivoire": ("CI", "CIV", "Africa"),
    "Rwanda": ("RW", "RWA", "Africa"), "Benin": ("BJ", "BEN", "Africa"), "Angola": ("AO", "AGO", "Africa"), "Uganda": ("UG", "UGA", "Africa"), "Zambia": ("ZM", "ZMB", "Africa"),
}
# Countries the board does not list. They stay recognised above so their roles are identified and left out.
EXCLUDED_COUNTRIES = {"Israel"}

REGION_ORDER = ["Middle East", "Europe", "North America", "Asia Pacific", "Africa", "Latin America"]

CODES = {}
for _name, (_a2, _a3, _r) in COUNTRIES.items():
    CODES[_a2] = _name
    CODES[_a3] = _name

# Other spellings seen in careers systems -> website name
ALIASES = {
    "united arab emirates": "UAE", "kingdom of saudi arabia": "Saudi Arabia", "ksa": "Saudi Arabia",
    "uk": "United Kingdom", "great britain": "United Kingdom", "england": "United Kingdom", "scotland": "United Kingdom",
    "wales": "United Kingdom", "northern ireland": "United Kingdom", "usa": "United States", "united states of america": "United States",
    "u.s.": "United States", "republic of korea": "South Korea", "korea": "South Korea", "türkiye": "Turkey", "turkiye": "Turkey",
    "czechia": "Czech Republic", "deutschland": "Germany", "nederland": "Netherlands", "schweiz": "Switzerland", "suisse": "Switzerland", "españa": "Spain", "ivory coast": "Côte d'Ivoire", "viet nam": "Vietnam", "hong kong sar": "Hong Kong", "macao": "Macau", "macau sar": "Macau",
}

# Cities that often appear without a country
CITIES = {
    "Saudi Arabia": ["riyadh", "jeddah", "dammam", "khobar", "al khobar", "dhahran", "jubail", "yanbu", "neom", "tabuk",
                     "tabouk", "abha", "medina", "madinah", "makkah", "mecca", "alula", "al ula", "qiddiya", "diriyah",
                     "trojena", "oxagon", "taif", "hail", "qassim", "jazan", "khafji"],
    "UAE": ["dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "fujairah", "al ain"],
    "Qatar": ["doha", "lusail", "al wakrah"], "Kuwait": ["kuwait city"], "Bahrain": ["manama"],
    "Oman": ["muscat", "duqm", "salalah", "sohar"],
    "United Kingdom": ["london", "manchester", "birmingham", "glasgow", "edinburgh", "leeds", "bristol", "cardiff"],
    "United States": ["new york", "houston", "dallas", "chicago", "los angeles", "denver", "washington, dc"],
    "Canada": ["toronto", "calgary", "edmonton", "vancouver", "montreal", "montréal", "ottawa"],
    "Australia": ["sydney", "melbourne", "brisbane", "perth", "adelaide", "gold coast"],
    "India": ["bengaluru", "bangalore", "mumbai", "noida", "gurugram", "gurgaon", "chennai", "pune", "hyderabad", "new delhi"],
    "Egypt": ["cairo"], "Jordan": ["amman"], "Israel": ["tel aviv", "tel-aviv", "holon", "jerusalem"],
}

US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH "
                "OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())


GCC = {"Saudi Arabia", "UAE", "Qatar", "Kuwait", "Bahrain", "Oman"}


def region_of(country):
    """One region per country, no overlaps: the Gulf (GCC) is separate from the rest of the Middle East."""
    r = COUNTRIES.get(country, (None, None, "Other"))[2]
    if country in GCC:
        return "GCC"
    return "Middle East (non-GCC)" if r == "Middle East" else r

CA_PROVINCES = set("AB BC MB NB NL NS ON PE QC SK YT NT NU".split())
AU_STATES = {"nsw", "vic", "qld", "tas", "act", "new south wales", "victoria", "queensland", "western australia",
             "south australia", "tasmania", "northern territory", "australian capital territory"}
# Place names that contain a country name but are somewhere else; checked before country names.
REGION_NAMES = {
    "new south wales": "Australia", "western australia": "Australia", "south australia": "Australia", "queensland": "Australia",
    "new mexico": "United States", "new jersey": "United States", "new york": "United States", "new hampshire": "United States",
    "georgia, usa": "United States", "atlanta": "United States", "british columbia": "Canada", "ontario": "Canada",
    "alberta": "Canada", "quebec": "Canada", "québec": "Canada", "nova scotia": "Canada", "manitoba": "Canada", "saskatchewan": "Canada",
    "texas": "United States", "california": "United States", "florida": "United States", "virginia": "United States",
    "indianapolis": "United States", "puerto rico": "Puerto Rico",
}
