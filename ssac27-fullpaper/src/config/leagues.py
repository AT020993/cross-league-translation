"""Central league registry — single source of truth for all competition metadata.

Every module that needs competition codes, names, data directories, or feature
flags should import from here instead of hardcoding values.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LeagueConfig:
    """Configuration for a single league/competition.

    Parameters
    ----------
    code : str
        Short competition code used in data columns (``_competition``).
    name : str
        Full display name.
    short_name : str
        2-3 letter abbreviation for tight UI spaces.
    data_source : str
        PBP scraper identifier — used by ``data_scheduler.py`` to route
        fetches to the correct scraper.  Leagues with ``proballers_league``
        set additionally load boxscores/games from Proballers via
        ``collect_proballers_parquet()``.
    data_dir : str
        Subdirectory name under ``data/raw/``.
    features : frozenset[str]
        Capabilities: ``boxscores``, ``pbp``, ``live``, ``analytics``,
        ``shots``, ``games``, ``metadata``.
    schedule_check : str
        API used by the scheduler to detect new games.
    country : str
        Country where the league is based (e.g. ``"Spain"``).
        ``"International"`` for pan-European competitions (EL, EC, BCL).
    governing_body : str
        Abbreviation of the federation that governs this competition
        (e.g. ``"FEB"``, ``"Euroleague Basketball"``, ``"FIBA Europe"``).
    proballers_league : str | None
        Proballers slug (e.g. ``"spain-acb"``) for boxscores/games loading.
        When set, ``data_source`` still identifies the PBP scraper while
        Proballers provides boxscores and game results.
    has_data : bool
        ``False`` hides leagues from ``/api/leagues`` when no data exists.
    is_active : bool
        ``False`` for leagues we have historical data for but no longer
        actively scrape/maintain.  Used by agent context builders to scope
        team stats to currently maintained leagues by default — prevents
        stale ACB/BCL data from leaking into EuroLeague answers.

    """

    code: str
    name: str
    short_name: str
    data_source: str
    data_dir: str
    features: frozenset[str]
    schedule_check: str
    tier: int = 3
    expected_games: int = 200
    keywords: tuple[str, ...] = ()
    country: str = ""
    governing_body: str = ""
    proballers_league: str | None = None
    has_data: bool = True
    is_active: bool = True


# Data source pattern:
# - euroleague_api: Official API (boxscores, PBP, shots, games, live)
# - segev_stats / acb / bcl / bbl / fiba_livestats: Dedicated PBP scrapers
# - Leagues with proballers_league additionally load boxscores + games from
#   Proballers (scraped via `src.data.scrapers.proballers`).
#   PBP comes from the dedicated scraper, boxscores/games from Proballers.
LEAGUE_REGISTRY: dict[str, LeagueConfig] = {
    "E": LeagueConfig(
        code="E",
        name="EuroLeague",
        short_name="EL",
        data_source="euroleague_api",
        data_dir="euroleague",
        features=frozenset(
            {"boxscores", "pbp", "live", "analytics", "shots", "games", "metadata"},
        ),
        schedule_check="euroleague_api",
        tier=1,
        expected_games=290,
        # "euroliga" is the Spanish / Hebrew-transliteration form users type.
        # ATI-3767: "euro-league" too; the substring detectors read each
        # separator as its own keyword ("Mike James in the Euro-League" went
        # unscoped while the phase and citation regexes read it).
        keywords=("euroleague", "euro league", "euro-league", "euroliga", "יורוליג"),
        country="International",
        governing_body="Euroleague Basketball",
    ),
    "U": LeagueConfig(
        code="U",
        name="EuroCup",
        short_name="EC",
        data_source="euroleague_api",
        data_dir="eurocup",
        features=frozenset(
            {"boxscores", "pbp", "live", "analytics", "shots", "games", "metadata"},
        ),
        schedule_check="euroleague_api",
        tier=1,
        expected_games=200,
        keywords=("eurocup", "euro cup", "euro-cup"),
        country="International",
        governing_body="Euroleague Basketball",
    ),
    "ISR": LeagueConfig(
        code="ISR",
        name="Israel BSL",
        short_name="BSL",
        data_source="segev_stats",
        data_dir="israel-bsl",
        features=frozenset({"pbp", "boxscores", "games"}),
        schedule_check="segev_stats",
        tier=2,
        expected_games=184,
        # Hebrew names of the league (ATI-3368 review): "the last game of
        # Maccabi in ליגת העל" read as no league and answered a EuroLeague game.
        keywords=(
            "israel",
            "bsl",
            "winner league",
            # ATI-3470: the transliterated Hebrew names. "Show the Ligat Winner
            # standings" named no league, and "Ligat" fuzzy-matched a player.
            "ligat winner",
            "ligat ha'al",
            "ligat haal",
            # ATI-3475 review: the other ways the name is typed. Detection is a
            # substring scan, so each separator is its own keyword.
            "ligat ha al",
            "ligat ha-al",
            "ligat ha’al",
            "israeli",
            "ליגת העל",
            "ליגת ווינר",
            "ליגת וינר",
        ),
        country="Israel",
        governing_body="IBBA",
        proballers_league="israel-bsl",
    ),
    # --- FIBA LiveStats leagues ---
    "GRE": LeagueConfig(
        code="GRE",
        name="Greek Basket League A1",
        short_name="GBL",
        data_source="fiba_livestats",
        data_dir="greece-a1",
        features=frozenset({"pbp"}),
        schedule_check="fiba_livestats",
        tier=2,
        expected_games=200,
        keywords=("greece", "greek", "a1"),
        country="Greece",
        governing_body="EOK",
        has_data=False,
    ),
    "SWE": LeagueConfig(
        code="SWE",
        name="Swedish Basketball League",
        short_name="SBL",
        data_source="fiba_livestats",
        data_dir="sweden-sbl",
        features=frozenset({"pbp"}),
        schedule_check="fiba_livestats",
        keywords=("sweden", "swedish", "sbl"),
        country="Sweden",
        governing_body="SBBF",
        has_data=False,
    ),
    "GBR": LeagueConfig(
        code="GBR",
        name="British Basketball League",
        short_name="BBL",
        data_source="fiba_livestats",
        data_dir="england-bbl",
        features=frozenset({"pbp"}),
        schedule_check="fiba_livestats",
        keywords=("british",),
        country="United Kingdom",
        governing_body="BBF",
        has_data=False,
    ),
    "ROU": LeagueConfig(
        code="ROU",
        name="Romanian Liga Nationala",
        short_name="RLN",
        data_source="fiba_livestats",
        data_dir="romania-liga",
        features=frozenset({"pbp"}),
        schedule_check="fiba_livestats",
        keywords=("romania", "romanian"),
        country="Romania",
        governing_body="FRB",
        has_data=False,
    ),
    "LUX": LeagueConfig(
        code="LUX",
        name="Luxembourg Total League",
        short_name="LTL",
        data_source="fiba_livestats",
        data_dir="luxembourg-total",
        features=frozenset({"pbp"}),
        schedule_check="fiba_livestats",
        keywords=("luxembourg",),
        country="Luxembourg",
        governing_body="FLBB",
        has_data=False,
    ),
    "KOS": LeagueConfig(
        code="KOS",
        name="Kosovo Superliga",
        short_name="KSL",
        data_source="fiba_livestats",
        data_dir="kosovo-superliga",
        features=frozenset({"pbp"}),
        schedule_check="fiba_livestats",
        keywords=("kosovo",),
        country="Kosovo",
        governing_body="FBK",
        has_data=False,
    ),
    # --- ACB / Liga Endesa ---
    # Historical data only — not actively scraped/maintained.
    "ACB": LeagueConfig(
        code="ACB",
        name="Liga Endesa",
        short_name="ACB",
        data_source="acb",
        data_dir="spain-acb",
        features=frozenset({"pbp", "boxscores", "games"}),
        schedule_check="acb",
        tier=1,
        expected_games=302,
        keywords=("acb", "liga endesa", "spain", "spanish league", "spanish domestic"),
        country="Spain",
        governing_body="FEB",
        proballers_league="spain-acb",
        is_active=False,
    ),
    # --- BCL (Basketball Champions League) ---
    # Historical data only — not actively scraped/maintained.
    "BCL": LeagueConfig(
        code="BCL",
        name="Basketball Champions League",
        short_name="BCL",
        data_source="bcl",
        data_dir="bcl",
        features=frozenset({"pbp", "boxscores", "games"}),
        schedule_check="bcl",
        tier=2,
        expected_games=220,
        keywords=("bcl", "champions league"),
        country="International",
        governing_body="FIBA Europe",
        proballers_league="bcl",
        is_active=False,
    ),
    # --- German BBL (easyCredit Basketball Bundesliga) ---
    # Historical data only — not actively scraped/maintained.
    "DEU": LeagueConfig(
        code="DEU",
        name="easyCredit BBL",
        short_name="BBL",
        data_source="bbl",
        data_dir="germany-bbl",
        features=frozenset({"pbp"}),
        schedule_check="bbl",
        tier=2,
        expected_games=200,
        keywords=("bundesliga", "germany"),
        country="Germany",
        governing_body="DBB",
        is_active=False,
    ),
}


# Every ``LeagueConfig.keywords`` entry is classified as exactly one of these
# (guard: ``tests/test_config/test_leagues.py``). A DEMONYM names a
# nationality, not a league — "vs Greek teams" or "an Israeli player" is a
# player/opponent filter, so it must not override the league a resolved
# entity actually plays in (ATI-3033 follow-up). ``detect_pbp_competition``
# still matches both kinds; only ``detect_named_league_competition`` masks the
# demonyms. Country NOUNS ("greece", "israel") stay league words: "in Israel"
# reads as the domestic league far more often than as a nationality.
DEMONYM_KEYWORDS: frozenset[str] = frozenset(
    {"israeli", "greek", "swedish", "british", "romanian"}
)
LEAGUE_NAME_KEYWORDS: frozenset[str] = frozenset(
    {
        "euroleague",
        "euro league",
        "euro-league",
        "euroliga",
        "יורוליג",
        "eurocup",
        "euro cup",
        "euro-cup",
        "israel",
        "bsl",
        "winner league",
        "ligat winner",
        "ligat ha'al",
        "ligat haal",
        "ligat ha al",
        "ligat ha-al",
        "ligat ha’al",
        "ליגת העל",
        "ליגת ווינר",
        "ליגת וינר",
        "greece",
        "a1",
        "sweden",
        "sbl",
        "romania",
        "luxembourg",
        "kosovo",
        "acb",
        "liga endesa",
        "spain",
        "spanish league",
        "spanish domestic",
        "bcl",
        "champions league",
        "bundesliga",
        "germany",
    }
)

#: League-name words that ARE a player's name token in the registries
#: (players + aliases, checked 2026-10-13: SPAIN, KYLE), so they stay
#: resolvable and may read as part of a person's name.
LEAGUE_WORDS_THAT_NAME_PLAYERS: frozenset[str] = frozenset({"spain"})


def league_name_words(min_length: int = 4) -> frozenset[str]:
    """Lower-case words of every ``LEAGUE_NAME_KEYWORDS`` entry.

    ATI-3470: the one source for "this token is a league word, not a name".
    The resolver's noise vocabulary and the "does the query name a person?"
    vocabulary both read it; the second copy drifted (LIGAT / WINNER missing)
    and "Who led the Ligat Winner in scoring?" read as an unresolved player
    and refused. An apostrophe word is listed both as typed ("ha'al") and
    bare ("haal"), since the consumers tokenise differently. Words shorter
    than *min_length* and words in ``LEAGUE_WORDS_THAT_NAME_PLAYERS`` are
    left out.
    """
    import re

    words: set[str] = set()
    for keyword in LEAGUE_NAME_KEYWORDS:
        for token in re.findall(r"[a-z][a-z']*", keyword):
            bare = token.replace("'", "")
            if len(bare) >= min_length:
                words.update({token, bare})
    return frozenset(words - LEAGUE_WORDS_THAT_NAME_PLAYERS)


# Leagues the agent does NOT answer for and the registry does not carry
# (ATI-3113). ``LEAGUE_REGISTRY`` only knows the leagues we scrape, so a
# question naming any other league ("top scorer in Liga Leumit", "VTB League
# rebounds") matched no guard, competition finalization defaulted it to
# EuroLeague — or matched "israeli"/"bsl" to Israel BSL — and the wrong board
# rendered with no disclosure. Display label (article-ready: it is rendered as
# "The user asked about <label>") -> regex fragments, each ``\b``-anchored and
# matched case-insensitively by ``detect_uncovered_league``.
#
# League NAMES only, never demonyms or country nouns: "Turkish players in the
# EuroLeague" and "vs teams from Greece" are in-scope filters. Short tokens that
# read as ordinary English are anchored to a league context ("pro a league",
# never bare "pro a" — "he turned pro a year ago"). ACB / BCL / German
# Bundesliga are registry leagues with ``is_active=False`` and refuse through
# ``detect_inactive_league``; ABA is in ``_OUT_OF_SCOPE_RE`` — not duplicated.
UNCOVERED_LEAGUE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Liga Leumit (Israel's second division)": (
        r"liga\s+leumit",
        r"leumit",
        r"liga\s+artzit",
        r"israel(?:i|'s)?\s+national\s+league",
    ),
    "the Turkish Basketball Super League": (
        r"turkish\s+(?:basketball\s+)?(?:super\s+)?(?:league|lig)",
        r"turkish\s+bsl",
        r"bsl\s+turkey",
        r"basketbol\s+s[uü]per\s+ligi",
    ),
    "the French LNB Pro A": (
        r"lnb",
        r"pro\s+a\s+(?:league|season|standings|leaders?|scor\w*|stats|mvp)",
        r"betclic\s+[eé]lite",
        r"french\s+(?:basketball\s+)?(?:league|pro\s+a)",
    ),
    "the Italian Lega Basket Serie A": (
        r"lega\s+basket",
        r"lba",
        r"serie\s+a",
        r"italian\s+(?:basketball\s+)?league",
    ),
    "the VTB United League": (
        r"vtb",
        r"russian\s+(?:basketball\s+)?(?:super\s+)?league",
    ),
    "the Lithuanian LKL": (
        r"lkl",
        r"lithuanian\s+(?:basketball\s+)?league",
    ),
    "the ABA (Adriatic) League": (r"adriatic\s+league",),
    "the Polish PLK": (
        r"plk",
        r"orlen\s+basket\s+liga",
        r"polish\s+(?:basketball\s+)?league",
    ),
    "the Greek Basket League": (
        r"greek\s+(?:basket(?:ball)?\s+)?league",
        r"basket\s+league\s+a1",
        r"heba\s+a1",
    ),
    "the German BBL": (
        r"german\s+(?:bbl|league|basketball\s+league)",
        r"easycredit\s+bbl",
    ),
}


# Active leagues — currently scraped, validated, and trusted as source of
# truth.  Anything outside this set is historical/archival data that should
# not be mixed into agent answers by default.  Derived from ``is_active``
# so it stays in sync with the registry.
ACTIVE_LEAGUES: frozenset[str] = frozenset(
    code for code, league in LEAGUE_REGISTRY.items() if league.is_active
)

# The competitions the agent ANSWERS for — EuroLeague, EuroCup, Israel BSL.
# Narrower than ``ACTIVE_LEAGUES``, which also carries leagues we scrape but
# do not answer about (GRE, SWE, ...). Ordered for stable user-facing copy.
ANSWER_SCOPE_COMPETITIONS: tuple[str, ...] = ("E", "U", "ISR")


def get_active_leagues(*, include_inactive: bool = False) -> dict[str, LeagueConfig]:
    """Return leagues with ``is_active=True`` and ``has_data=True``.

    Pass ``include_inactive=True`` for archival builds that explicitly
    want historical-only leagues (ACB / BCL / DEU) included. The default
    strict filter prevents silent registry corruption from stale raw
    directories that shouldn't feed live agent answers (ATI-1521).
    """
    if include_inactive:
        return {code: cfg for code, cfg in LEAGUE_REGISTRY.items() if cfg.has_data}
    return {
        code: cfg
        for code, cfg in LEAGUE_REGISTRY.items()
        if cfg.is_active and cfg.has_data
    }


def get_leagues_with_data(*, include_inactive: bool = False) -> dict[str, LeagueConfig]:
    """Return leagues that have scraped data (``has_data=True``).

    Pass ``include_inactive=True`` to include historical-only leagues.
    Unlike :func:`get_active_leagues`, this helper does NOT require
    ``is_active`` — use it when the caller wants everything with a raw
    directory on disk regardless of active status.
    """
    return {
        code: cfg
        for code, cfg in LEAGUE_REGISTRY.items()
        if cfg.has_data and (include_inactive or cfg.is_active)
    }


def canonical_competition_code(cfg: LeagueConfig | str) -> str:
    """Return the canonical 1-3 char competition code for a league.

    Accepts a :class:`LeagueConfig`, a slug string (``"spain-acb"`` /
    data dir), a registry code (``"ISR"``), or a league short name
    (``"BSL"``, ``"EL"``) and returns the registry ``code``. Falls back
    to the uppercase input when nothing is registered. Use this to
    normalize competition identifiers at the resolver boundary so slugs
    and short names never leak into comparisons against stored
    ``_competition`` codes (``E``, ``U``, ``ISR``).

    Resolution order: registry codes win over short-name aliases
    (``"ACB"`` is both — same league, so it cannot flip), and a short
    name resolves only when it is UNIQUE across the registry — ``"BBL"``
    names both GBR (England) and DEU (Germany), so it passes through
    unchanged rather than silently picking one. PR #1218 r2 (ATI-2209):
    entities carried ``"BSL"`` while BSL PBP rows store ``"ISR"``;
    comparing the raw value scoped every PBP fact-block route to zero
    rows and refused queries the data could answer.
    """
    if isinstance(cfg, LeagueConfig):
        return cfg.code
    for league in LEAGUE_REGISTRY.values():
        if league.proballers_league == cfg or league.data_dir == cfg:
            return league.code
    upper = cfg.upper()
    if upper in LEAGUE_REGISTRY:
        return upper
    short_name_matches = [
        league.code
        for league in LEAGUE_REGISTRY.values()
        if league.short_name.upper() == upper
    ]
    if len(short_name_matches) == 1:
        return short_name_matches[0]
    return upper


def get_league(code: str) -> LeagueConfig:
    """Look up a league by code. Raises ``KeyError`` if not found."""
    return LEAGUE_REGISTRY[code]


def get_leagues_with_feature(feature: str) -> list[LeagueConfig]:
    """Return all leagues that support a given feature."""
    return [lg for lg in LEAGUE_REGISTRY.values() if feature in lg.features]


def get_league_by_data_dir(data_dir: str) -> LeagueConfig | None:
    """Look up a league by its data directory name.

    Returns ``None`` if no league matches.
    """
    for league in LEAGUE_REGISTRY.values():
        if league.data_dir == data_dir:
            return league
    return None


def get_data_dir_to_code() -> dict[str, str]:
    """Return ``{data_dir: code}`` mapping derived from registry."""
    return {league.data_dir: league.code for league in LEAGUE_REGISTRY.values()}


def get_code_to_data_dir() -> dict[str, str]:
    """Return ``{code: data_dir}`` mapping derived from registry."""
    return {league.code: league.data_dir for league in LEAGUE_REGISTRY.values()}


def get_competition_labels() -> dict[str, str]:
    """Return ``{code: name}`` mapping for all leagues with data."""
    return {
        league.code: league.name
        for league in LEAGUE_REGISTRY.values()
        if league.has_data
    }


def competition_label(code: str) -> str:
    """The answer label of competition *code*: its registry ``name``.

    ATI-3767: every surface that names a competition reads this (or
    :func:`get_competition_labels`) instead of a hand-kept ``{"E":
    "EuroLeague", ...}`` dict; twelve such dicts had drifted ("Israeli BSL",
    "BSL", "Champions League"). Unlike :func:`get_competition_labels` it
    covers leagues without data too (GRE, SWE, ...), and it reads a short name
    or data dir (``"BSL"``, ``"israel-bsl"``) as its code. An unregistered code
    comes back as itself.
    """
    league = LEAGUE_REGISTRY.get(canonical_competition_code(code))
    return league.name if league is not None else code


#: The separators one keyword is typed with ("euro league", "euroleague",
#: "euro-league"; "ligat ha'al", "ligat ha-al", "ligat haal").
_KEYWORD_SEPARATOR = r"[\s\-'’]*"


#: The one-letter Hebrew prefixes ("in", "to", "from", "the", "and", ...) glued
#: to the next word: "בליגת העל" is "in the Ligat Ha'Al".
_HEBREW_PREFIX = "[בהוכלמש]?"


def _keyword_pattern(keyword: str) -> str:
    """One registry keyword as a regex: every separator variant, no case, and
    for a Hebrew name its glued prefix letter."""
    tokens = [t for t in re.split(r"[\s\-'’]+", keyword) if t]
    body = _KEYWORD_SEPARATOR.join(re.escape(t) for t in tokens)
    if tokens and "\u0590" <= tokens[0][0] <= "\u05ff":
        return _HEBREW_PREFIX + body
    return body


def competition_mention_fragment(
    codes: tuple[str, ...] | None = None, *, demonyms: bool = False
) -> str:
    """The regex alternation that names a competition in a question (ATI-3767).

    Built from ``LeagueConfig.keywords`` of *codes* (every registry league
    when None), each whole-word, with the whitespace / hyphen / apostrophe
    variants generated in one place. Demonyms ("israeli", "greek") name a
    nationality more often than a league, so they are left out unless
    *demonyms* (see :data:`DEMONYM_KEYWORDS`). A non-capturing group, ready to
    embed in a larger pattern; compile it with ``re.IGNORECASE``.
    """
    return _mention_fragment(codes, demonyms)


@functools.cache
def _mention_fragment(codes: tuple[str, ...] | None, demonyms: bool) -> str:
    wanted = codes if codes is not None else tuple(LEAGUE_REGISTRY)
    keywords = sorted(
        {
            kw
            for code in wanted
            for kw in LEAGUE_REGISTRY[canonical_competition_code(code)].keywords
            if demonyms or kw not in DEMONYM_KEYWORDS
        },
        key=len,
        reverse=True,
    )
    body = "|".join(_keyword_pattern(kw) for kw in keywords)
    return rf"(?<!\w)(?:{body})(?!\w)"


@functools.cache
def competition_mention_re(
    codes: tuple[str, ...] | None = None, *, demonyms: bool = False
) -> re.Pattern[str]:
    """:func:`competition_mention_fragment`, compiled case-insensitively."""
    return re.compile(competition_mention_fragment(codes, demonyms=demonyms), re.I)


#: Every spelling of the EuroLeague and the EuroCup (ATI-3767): the two
#: competitions most detectors name together, as one embeddable fragment.
EUROLEAGUE_OR_EUROCUP_MENTION = competition_mention_fragment(("E", "U"))


def competitions_named(text: str, *, demonyms: bool = False) -> frozenset[str]:
    """The registry codes whose names *text* mentions (ATI-3767).

    Whole words, any separator ("Euro League", "Euro-League", "EuroLeague"),
    demonyms only when asked. The one detector every hand-written league
    regex is migrating to.
    """
    if not text:
        return frozenset()
    return frozenset(
        code
        for code, league in LEAGUE_REGISTRY.items()
        if league.keywords
        and competition_mention_re((code,), demonyms=demonyms).search(text)
    )
