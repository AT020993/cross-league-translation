"""Registered, immutable ACB adjudication of the frozen Sloan discrepancy list.

Threat controls: complete discrepancy population, fixture date/club/score checks,
official club-scoped IDs, labeled complete-game columns, shooting/rebound checks,
hash-verified captures and explicit unresolved states. No model or raw-file edits.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/research/artifacts/sloan-source-revalidation-2026-09-07"
PROTOCOL = ROOT / "docs/research/sloan-gap-closure-protocol-2026-09-17.md"
ALIASES = ROOT / "docs/research/sloan-acb-identity-aliases-2026-09-17.json"
HEADERS = [
    "Jugador",
    "Min",
    "Pts",
    "T2",
    "T2%",
    "T3",
    "T3%",
    "TL",
    "TL%",
    "RO",
    "RD",
    "RT",
    "As",
    "Pér",
    "Rec",
    "Tap",
    "TR",
    "Mat",
    "Fp",
    "Fr",
    "+/-",
    "Val",
]
MONTHS = (
    "enero febrero marzo abril mayo junio julio agosto septiembre "
    "octubre noviembre diciembre"
).split()
CLUBS = {
    "Kosner Baskonia": "Baskonia",
    "Baskonia Vitoria-Gasteiz": "Baskonia",
    "Asisa Joventut": "Joventut Badalona",
    "Zaragoza": "Casademont Zaragoza",
    "Tenerife": "La Laguna Tenerife",
    "Gran Canaria": "Dreamland Gran Canaria",
    "Unicaja Malaga": "Unicaja",
    "FC Barcelona": "Barça",
    "San Pablo Burgos": "Recoletas Salud San Pablo Burgos",
    "Rio Breogan": "Río Breogán",
    "Basquet Girona": "Bàsquet Girona",
}
FIELDS = {
    "points": "Pts",
    "rebounds": "RT",
    "offensive_rebounds": "RO",
    "defensive_rebounds": "RD",
    "assists": "As",
    "turnovers": "Pér",
    "steals": "Rec",
    "blocks": "Tap",
    "plus_minus": "+/-",
}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def norm(value):
    text = unicodedata.normalize("NFKD", str(value))
    return re.sub(r"[^a-z0-9]", "", text.encode("ascii", "ignore").decode().lower())


def club(value):
    return norm(CLUBS.get(value, value))


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def get_capture(url, cache, *, collect=False):
    """Read immutable cached evidence; no retry, impersonation or auth bypass."""
    cache = Path(cache)
    key = sha(url.encode())[:24]
    meta_path, body_path = cache / f"{key}.json", cache / f"{key}.html"
    if not meta_path.exists():
        if not collect:
            raise ValueError(f"missing capture: {url}")
        cache.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat()
        try:
            response = requests.get(url, timeout=25)
            payload = response.content
            meta = {
                "url": url,
                "final_url": response.url,
                "retrieved_at_utc": stamp,
                "http_status": response.status_code,
                "sha256": sha(payload),
            }
        except requests.RequestException as exc:
            payload = b""
            meta = {
                "url": url,
                "retrieved_at_utc": stamp,
                "http_status": None,
                "error": type(exc).__name__,
                "sha256": sha(payload),
            }
        body_path.write_bytes(payload)
        dump(meta_path, meta)
        time.sleep(1)
    meta, payload = json.loads(meta_path.read_text()), body_path.read_bytes()
    if meta.get("url") != url or meta.get("sha256") != sha(payload):
        raise ValueError(f"capture identity/hash mismatch: {url}")
    if meta.get("http_status") != 200:
        raise ValueError(f"source unavailable: HTTP {meta.get('http_status')}: {url}")
    final = urlparse(meta.get("final_url", url))
    if final.scheme != "https" or final.hostname not in (
        "acb.com",
        "www.acb.com",
        "live.acb.com",
    ):
        raise ValueError("capture redirected outside official ACB source")
    return payload, meta


def read_stat(cells):
    values = dict(zip(HEADERS, cells, strict=True))
    stats = {}
    for field, label in FIELDS.items():
        stats[field] = int(values[label])
    for label, prefix in (("T2", "fg2"), ("T3", "fg3"), ("TL", "ft")):
        parts = re.fullmatch(r"(\d+)\s*/\s*(\d+)", values[label])
        if not parts:
            raise ValueError(f"malformed shooting cell: {label}")
        made, attempted = map(int, parts.groups())
        if made > attempted:
            raise ValueError("made exceeds attempted")
        stats[prefix + "_made"], stats[prefix + "_attempted"] = made, attempted
    # Proballers' stored fg_* columns mean TWO-point shots, as documented in
    # build_league_factors.py. Do not compare them to total field goals.
    stats["fg_made"] = stats["fg2_made"]
    stats["fg_attempted"] = stats["fg2_attempted"]
    if (
        stats["points"]
        != 2 * stats["fg2_made"] + 3 * stats["fg3_made"] + stats["ft_made"]
    ):
        raise ValueError("points do not reconcile to shooting")
    if stats["rebounds"] != stats["offensive_rebounds"] + stats["defensive_rebounds"]:
        raise ValueError("rebounds do not reconcile")
    if any(value < 0 for key, value in stats.items() if key != "plus_minus"):
        raise ValueError("negative count")
    stats["pir"] = (
        sum(stats[x] for x in ("points", "rebounds", "assists", "steals", "blocks"))
        - stats["fg_attempted"]
        + stats["fg_made"]
        - stats["fg3_attempted"]
        + stats["fg3_made"]
        - stats["ft_attempted"]
        + stats["ft_made"]
        - stats["turnovers"]
    )
    # Val is ACB valuation, not EFF. It is retained separately, never substituted.
    stats["acb_valuation"] = int(values["Val"])
    raw_minutes = values["Min"].strip()
    if raw_minutes:
        match = re.fullmatch(r"(\d+):([0-5]\d)", raw_minutes)
        if not match:
            raise ValueError("malformed MM:SS")
        minutes, seconds = map(int, match.groups())
        stats["minutes"] = minutes + seconds / 60
    else:
        stats["minutes"] = None
    stats["minutes_text"] = raw_minutes
    return stats


def parse_fixture(payload, expected):
    """Require complete-game labeled tables and exact fixture identity."""
    soup = BeautifulSoup(payload, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if "Estadísticas del Partido" not in title:
        raise ValueError("not an official statistics page")
    full_text = soup.get_text(" ", strip=True)
    date = datetime.fromisoformat(expected["date"])
    date_pattern = rf"\b{date.day}\s+{MONTHS[date.month - 1]}\s+{date.year}\b"
    if not re.search(date_pattern, full_text, re.I):
        raise ValueError("fixture date mismatch")
    if "Final" not in full_text or "Liga Endesa" not in full_text:
        raise ValueError("fixture is not a completed Liga Endesa game")
    teams = {}
    for table in soup.select('table[class*="MatchTeamStatisticsTable"]'):
        headers = [x.get_text(" ", strip=True) for x in table.select("thead th")]
        if not any(headers):  # Explicit empty loading skeleton; never a zero roster.
            continue
        if headers != HEADERS:
            raise ValueError("unrecognized statistics headers")
        wrapper = table.parent.parent
        logo = wrapper.select_one('img[class*="titleLogo"]')
        if not logo or not logo.get("alt"):
            raise ValueError("missing official table club")
        team_name = logo["alt"]
        rows, totals, extra = [], None, None
        for tr in table.select("tbody tr"):
            cells = [
                td.get_text(" ", strip=True)
                for td in tr.find_all("td", recursive=False)
            ]
            if len(cells) != len(HEADERS):
                raise ValueError("malformed statistics row")
            stats = read_stat(cells)
            if cells[0] == "Totales":
                totals = stats
                continue
            if cells[0] == "Equipo":
                extra = stats
                continue
            link = tr.select_one('a[href*="/jugadores/"]')
            if not link:
                raise ValueError("player row lacks official identity link")
            url = link["href"]
            parsed = urlparse(url)
            match = re.search(r"/jugadores/(.+)-(\d+)$", parsed.path)
            if parsed.hostname not in ("acb.com", "www.acb.com") or not match:
                raise ValueError("invalid official identity URL")
            rows.append(
                {
                    "official_id": match[2],
                    "official_slug": match[1],
                    "player_url": url,
                    "display": cells[0],
                    "stats": stats,
                }
            )
        if not rows or totals is None or extra is None:
            raise ValueError("missing players, team residual or total row")
        if len({r["official_id"] for r in rows}) != len(rows):
            raise ValueError("duplicate official player ID within club")
        for field in (
            *FIELDS,
            "fg_made",
            "fg_attempted",
            "fg3_made",
            "fg3_attempted",
            "ft_made",
            "ft_attempted",
        ):
            if sum(r["stats"][field] for r in rows) + extra[field] != totals[field]:
                raise ValueError(f"team {team_name} does not reconcile: {field}")
        durations = [
            r["stats"]["minutes"] for r in rows if r["stats"]["minutes"] is not None
        ]
        total_minutes = sum(durations)
        overtime = round((total_minutes - 200) / 25)
        if overtime < 0 or abs(total_minutes - (200 + 25 * overtime)) > 0.1:
            raise ValueError(
                "minutes do not describe a complete regulation/overtime game"
            )
        result = {
            "name": team_name,
            "players": rows,
            "total": totals,
            "total_minutes": total_minutes,
        }
        key = club(team_name)
        if key in teams and teams[key] != result:
            raise ValueError("disagreeing duplicate responsive tables")
        teams[key] = result
    expected_teams = {club(expected["home_team"]), club(expected["away_team"])}
    if set(teams) != expected_teams or len(expected_teams) != 2:
        raise ValueError(f"fixture club mismatch: {list(teams)}")
    for side in ("home", "away"):
        if (
            teams[club(expected[f"{side}_team"])]["total"]["points"]
            != expected[f"{side}_score"]
        ):
            raise ValueError("fixture score mismatch")
    return {"teams": teams, "title": title, "date": expected["date"]}


def profile_names(payload):
    soup = BeautifulSoup(payload, "html.parser")
    names = [x.get_text(" ", strip=True) for x in soup.select("h1")]
    if soup.title:
        names.append(soup.title.get_text().split("|")[0].strip())
    return names


def find_player(name, team, fixture, profiles, *, verified_aliases=None, game_id=None):
    candidates = fixture["teams"].get(club(team), {}).get("players", [])
    aliases = json.loads(ALIASES.read_text())["aliases"]
    accepted = []
    for player in candidates:
        names = {
            norm(player["official_slug"]),
            *(norm(x) for x in profiles.get(player["official_id"], [])),
        }
        if norm(name) in names:
            accepted.append({**player, "identity_status": "EXACT_OFFICIAL_NAME"})
            continue
        for alias in aliases:
            if (
                alias["raw"] == name
                and club(alias["club"]) == club(team)
                and alias["official_id"] == player["official_id"]
                and norm(alias["official_name"])
                in {norm(x) for x in profiles.get(player["official_id"], [])}
            ):
                verified = (verified_aliases or {}).get((name, club(team)))
                if (
                    verified
                    and verified.get("status") == "VERIFIED_PROVIDER_ID_DOB"
                    and verified.get("official_id") == player["official_id"]
                    and game_id in verified.get("fixtures", {})
                ):
                    accepted.append(
                        {**player, "identity_status": "VERIFIED_PROVIDER_ID_DOB"}
                    )
                    break
                # The target profile confirms its own name, not the raw alias.
                # Preserve a candidate for inspection without certifying identity.
                accepted.append(
                    {
                        **player,
                        "identity_status": "MANUAL_ALIAS",
                        "alias_review": alias,
                    }
                )
                break
    if len(accepted) != 1:
        raise ValueError(f"identity unverified: {name} / {team}")
    return accepted[0]


def fixture_inputs(raw_root, diagnosis):
    """Freeze schedule locators; verify both sources against frozen hashes."""
    preparation = json.loads((SOURCE / "preparation_manifest.json").read_text())
    file_hashes = {}
    for record in preparation["raw_inputs"]:
        path = Path(record["source_file"])
        if (
            path.parent.name == "2025"
            and path.name == "player_stats_spain-acb_2025.parquet"
        ):
            relative = path.as_posix().split("/data/raw/", 1)[1]
            candidate = Path(raw_root) / relative
            if sha(candidate.read_bytes()) != record["sha256"]:
                raise ValueError(f"frozen raw source changed: {relative}")
            file_hashes[relative] = record["sha256"]
    if len(file_hashes) != 2:
        raise ValueError("missing either frozen Spanish source tree")
    ids = {r["game_id"] for r in diagnosis["field_disagreements"]}
    ids.update(r["game_id"] for r in diagnosis["identity_collisions"])
    tables = []
    for prefix in ("proballers", "_inactive_leagues/proballers"):
        p = Path(raw_root) / prefix / "spain-acb/2025/games_spain-acb_2025.parquet"
        file_hashes[str(p.relative_to(raw_root))] = sha(p.read_bytes())
        df = pd.read_parquet(p)
        selected = df.loc[df.game_id.astype(str).isin(ids)].copy()
        tables.append(selected)
    fixtures = {}
    for game_id in sorted(ids):
        records = []
        for frame in tables:
            chosen = frame.loc[frame.game_id.astype(str).eq(game_id)]
            if len(chosen) != 1:
                raise ValueError(f"missing or duplicate schedule key: {game_id}")
            row = chosen.iloc[0]
            records.append(
                {
                    key: int(row[key]) if key.endswith("_score") else str(row[key])
                    for key in (
                        "date",
                        "home_team",
                        "away_team",
                        "home_score",
                        "away_score",
                    )
                }
            )
        if records[0] != records[1]:
            raise ValueError(f"schedule sources disagree: {game_id}")
        fixture = records[0]
        fixture["date"] = (
            datetime.strptime(fixture["date"], "%b %d, %Y").date().isoformat()
        )
        # Discovery only: the common offset locates a candidate, never verifies it.
        # parse_fixture separately requires date, both clubs, score and game scope.
        candidate_id = int(game_id) - 729111
        slug = "-vs-".join(
            re.sub(
                r"[^a-z0-9]+",
                "-",
                unicodedata.normalize("NFKD", fixture[f"{side}_team"])
                .encode("ascii", "ignore")
                .decode()
                .lower(),
            ).strip("-")
            for side in ("home", "away")
        )
        fixture["url"] = (
            f"https://live.acb.com/es/partidos/{slug}-{candidate_id}/estadisticas"
        )
        fixture["candidate_locator_basis"] = (
            "offset from three verified cross-provider fixtures; identity not assumed"
        )
        fixtures[game_id] = fixture
    return {
        "fixtures": fixtures,
        "raw_hashes": file_hashes,
        "diagnosis_sha256": sha((SOURCE / "source_diagnosis.json").read_bytes()),
    }


def classify_values(field, official, values):
    if official is None:
        return "UNRESOLVED", [], "official value is undefined or unreported"
    matches = [v["_priority"] for v in values if v["value"] == official]
    if matches:
        return "RESOLVED", matches, "exact official count or duration"
    if field == "minutes":
        # Whole-minute data cannot encode official seconds. Distinguish representation
        # from source selection rather than silently flooring the replacement.
        projections = {int(official), int(official + 0.5)}
        supported = [v["_priority"] for v in values if v["value"] in projections]
        if len(supported) == 1:
            return (
                "RESOLVED",
                supported,
                "one source compatible with whole-minute precision; "
                "preserve official seconds",
            )
        if supported:
            return (
                "REPRESENTATION_ONLY",
                supported,
                "rounding convention cannot identify a unique source",
            )
    return "RESOLVED_NEITHER", [], "neither saved value matches official evidence"


def field_disposition(player, field, values):
    """Only verified name matches can resolve a disputed field or source."""
    official = player["stats"].get(field)
    status, supported, reason = classify_values(field, official, values)
    if player.get("identity_status") not in (
        "EXACT_OFFICIAL_NAME",
        "VERIFIED_PROVIDER_ID_DOB",
    ):
        return {
            "status": "IDENTITY_REVIEW_REQUIRED",
            "identity_status": player.get("identity_status", "UNKNOWN"),
            "candidate_official_id": player["official_id"],
            "candidate_player_url": player["player_url"],
            "candidate_official_value": official,
            "candidate_comparison": {
                "status": status,
                "supported_priorities": supported,
                "reason": reason,
            },
            "alias_review": player.get("alias_review"),
            "reason": "The official target name is verified, but the raw alias "
            "link is not independently verified; no source choice is resolved.",
        }
    return {
        "status": status,
        "identity_status": player["identity_status"],
        "official_value": official,
        "official_id": player["official_id"],
        "player_url": player["player_url"],
        "supported_priorities": supported,
        "reason": reason,
    }


def load_verified_aliases(alias_evidence, provider_cache, official_cache):
    if alias_evidence is None:
        return {}
    from scripts.sloan_alias_evidence import verify_manifest

    if provider_cache is None:
        raise ValueError("alias evidence requires provider capture directory")
    return verify_manifest(alias_evidence, provider_cache, official_cache)


def audit(
    cache,
    out,
    *,
    raw_root=None,
    collect=False,
    report_dir=None,
    alias_evidence=None,
    provider_cache=None,
):
    cache, out = Path(cache), Path(out)
    verified_aliases = load_verified_aliases(alias_evidence, provider_cache, cache)
    if out.exists() and any(out.iterdir()):
        raise ValueError("output must be new or empty")
    diagnosis = json.loads((SOURCE / "source_diagnosis.json").read_text())
    inputs_path = cache / "inputs.json"
    if not inputs_path.exists():
        if raw_root is None or not collect:
            raise ValueError("first collection needs raw_root")
        cache.mkdir(parents=True, exist_ok=True)
        dump(inputs_path, fixture_inputs(raw_root, diagnosis))
    inputs = json.loads(inputs_path.read_text())
    if inputs["diagnosis_sha256"] != sha(
        (SOURCE / "source_diagnosis.json").read_bytes()
    ):
        raise ValueError("diagnosis changed")
    expected = {
        x["game_id"]
        for x in diagnosis["field_disagreements"] + diagnosis["identity_collisions"]
    }
    if set(inputs["fixtures"]) != expected:
        raise ValueError("fixture population changed")
    parsed, problems, evidence, profiles = {}, {}, {}, {}
    for game_id, fixture in inputs["fixtures"].items():
        try:
            payload, meta = get_capture(fixture["url"], cache, collect=collect)
            parsed[game_id] = parse_fixture(payload, fixture)
            evidence[fixture["url"]] = meta
        except (ValueError, KeyError, TypeError) as exc:
            problems[game_id] = str(exc)
        print(
            f"fixture {game_id}: "
            f"{'verified' if game_id in parsed else problems[game_id]}",
            flush=True,
        )
    # Only request identity profiles needed for otherwise-unmatched disputed names.
    for item in diagnosis["field_disagreements"]:
        fixture = parsed.get(item["game_id"])
        if fixture is None:
            continue
        try:
            find_player(item["player_name"], item["team"], fixture, profiles)
            continue
        except ValueError:
            pass
        players = fixture["teams"].get(club(item["team"]), {}).get("players", [])
        surnames = [norm(x) for x in item["player_name"].split()[-1].split("-")]
        # This expands page discovery only. Final identity still needs a full
        # name on the official profile. A manual alias stays a review candidate.
        candidates = [
            p
            for p in players
            if any(
                x in norm(p["official_slug"]) or x in norm(p["display"])
                for x in surnames
            )
        ]
        for player in candidates:
            if player["official_id"] in profiles:
                continue
            try:
                payload, meta = get_capture(
                    player["player_url"], cache, collect=collect
                )
                profiles[player["official_id"]] = profile_names(payload)
                evidence[player["player_url"]] = meta
            except ValueError:
                profiles[player["official_id"]] = []
    rows = []
    for number, item in enumerate(diagnosis["field_disagreements"], 1):
        result = {
            "finding": number,
            **{key: item[key] for key in ("game_id", "player_name", "team", "field")},
            "saved_values": item["values"],
            "status": "UNRESOLVED",
        }
        try:
            if item["game_id"] in problems:
                raise ValueError(problems[item["game_id"]])
            player = find_player(
                item["player_name"],
                item["team"],
                parsed[item["game_id"]],
                profiles,
                verified_aliases=verified_aliases,
                game_id=item["game_id"],
            )
            result.update(
                field_disposition(player, item["field"], item["values"]),
                source_url=inputs["fixtures"][item["game_id"]]["url"],
            )
        except ValueError as exc:
            result["reason"] = str(exc)
        rows.append(result)
    collisions = []
    for item in diagnosis["identity_collisions"]:
        record = {
            "game_id": item["game_id"],
            "name": item["normalized_name"],
            "status": "UNRESOLVED",
        }
        try:
            if item["game_id"] in problems:
                raise ValueError(problems[item["game_id"]])
            identity = {}
            for row in item["rows"]:
                player = find_player(
                    row["player_name"], row["team"], parsed[item["game_id"]], profiles
                )
                if player["identity_status"] != "EXACT_OFFICIAL_NAME":
                    raise ValueError("manual alias identity review required")
                identity[row["team"]] = {
                    "official_id": player["official_id"],
                    "url": player["player_url"],
                }
            if (
                len(identity) != 2
                or len({v["official_id"] for v in identity.values()}) != 2
            ):
                raise ValueError("distinct people not established")
            record.update(
                status="RESOLVED_DISTINCT_PEOPLE",
                identities=identity,
                source_url=inputs["fixtures"][item["game_id"]]["url"],
                correction="club-scoped official identities; "
                "never merge the shared display name",
            )
        except ValueError as exc:
            record["reason"] = str(exc)
        collisions.append(record)
    summary = {
        "schema_version": 2,
        "scope": "frozen 2025 discrepancies only; originals and models unchanged",
        "diagnosis_sha256": inputs["diagnosis_sha256"],
        "inputs_sha256": sha(inputs_path.read_bytes()),
        "protocol_sha256": sha(PROTOCOL.read_bytes()),
        "aliases_sha256": sha(ALIASES.read_bytes()),
        "code_sha256": sha(Path(__file__).read_bytes()),
        "disagreements": len(rows),
        "dispositions": dict(Counter(r["status"] for r in rows)),
        "identity_collisions": collisions,
        "fixtures_requested": len(expected),
        "fixtures_verified": len(parsed),
        "fixture_problems": problems,
        "reconciliation": (
            "verified fixtures pass score, shooting, rebounds, "
            "player/team totals and full-game minutes"
        ),
        "model_fitting": "NOT_RUN",
        "raw_files_modified": False,
        "evidence": evidence,
    }
    if alias_evidence is not None:
        from scripts.sloan_alias_evidence import PROTOCOL as alias_protocol

        summary["alias_evidence_sha256"] = sha(Path(alias_evidence).read_bytes())
        summary["alias_protocol_sha256"] = sha(alias_protocol.read_bytes())
        summary["verified_aliases"] = len(verified_aliases)
        summary["alias_scope"] = (
            "Only listed fixture/name/club links; no longitudinal crosswalk"
        )
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "decisions.json", rows)
    summary["decisions_sha256"] = sha((out / "decisions.json").read_bytes())
    summary["official_values_observed"] = sum(
        r.get("official_value") is not None for r in rows
    )
    summary["candidate_values_pending_identity"] = sum(
        r["status"] == "IDENTITY_REVIEW_REQUIRED"
        and r.get("candidate_official_value") is not None
        for r in rows
    )
    summary["supported_sources"] = {
        str(priority): sum(r.get("supported_priorities") == [priority] for r in rows)
        for priority in (0, 1)
    }
    summary["field_definition"] = (
        "fg_made/fg_attempted are two-point shots in the saved Proballers schema; "
        "EFF subtracts two-point, three-point and free-throw misses separately."
    )
    dump(out / "summary.json", summary)
    unresolved = [
        r
        for r in rows
        if r["status"]
        in ("UNRESOLVED", "REPRESENTATION_ONLY", "IDENTITY_REVIEW_REQUIRED")
    ]
    dump(out / "unresolved.json", unresolved)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "disagreements",
                    "dispositions",
                    "fixtures_verified",
                    "fixture_problems",
                )
            }
        ),
        flush=True,
    )
    if report_dir is not None:
        write_report(summary, Path(report_dir))
    return summary


def write_report(summary, destination):
    """Publish only provenance/aggregate disposition; field values stay local."""
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("report directory must be new or empty")
    destination.mkdir(parents=True, exist_ok=True)
    dump(destination / "summary.json", summary)
    states = "\n".join(
        f"| {status} | {count} |"
        for status, count in sorted(summary["dispositions"].items())
    )
    lines = [
        "# Official ACB adjudication — 17 September 2026",
        "",
        "Generated by scripts/adjudicate_sloan_acb_sources.py. "
        "This is source evidence, not human approval or a model rerun.",
        "",
        "## Specification",
        "",
        "| Field | Declaration |",
        "| --- | --- |",
        "| Unit | A frozen disputed field or same-name collision |",
        "| Population | Every field disagreement and identity collision in "
        "the 7 September diagnosis |",
        "| Estimator | Exact official-count comparison; MM:SS retained |",
        "| Null | No inferential null; missing evidence remains unresolved |",
        "| Filter | Entire frozen population, independent of forecast results |",
        "| Key | Fixture date, both clubs, score, official club/player ID |",
        "| Uncertainty | Saved whole-minute rounding, manual identity aliases, "
        "source version and reviewer acceptance |",
        "| Threats | Wrong fixture, partial game, homonyms, rating/shooting "
        "schema mismatch, incomplete collection |",
        "",
        "## Complete disposition",
        "",
        f"Verified {summary['fixtures_verified']} of "
        f"{summary['fixtures_requested']} official fixtures; inspected "
        f"{summary['disagreements']} disagreements. Official values associated "
        f"with verified identities: {summary['official_values_observed']}; "
        f"candidate values with unresolved alias identity: "
        f"{summary['candidate_values_pending_identity']}.",
        "",
        "| Disposition | Count |",
        "| --- | --- |",
        states,
        "",
        "RESOLVED identifies exact count support or a uniquely compatible "
        "whole-minute representation. REPRESENTATION_ONLY retains the official "
        "duration but does not choose between two compatible rounding "
        "conventions. IDENTITY_REVIEW_REQUIRED preserves candidate-profile "
        "values without resolving the raw alias or choosing a saved source. "
        "None is an unreported zero.",
        "",
        "Unique saved-source support counts: active (priority 0) = "
        f"{summary['supported_sources']['0']}; inactive (priority 1) = "
        f"{summary['supported_sources']['1']}.",
        "",
        "The same-name Jaime Fernandez collisions are retained in summary.json "
        "with distinct club-scoped ACB IDs. "
        + (
            f"Independent provider fixture/profile and official DOB replay verifies "
            f"{summary['verified_aliases']} of five aliases. "
            f"{summary['candidate_values_pending_identity']} fields retain "
            "unresolved alias identities and do not choose a saved source. "
            "The alias manifest preserves contrary birth dates for Wes Vanbeck "
            "([birthdate withheld]). The scope is the listed raw names, "
            "clubs and fixtures; it is not a longitudinal person crosswalk."
            if "verified_aliases" in summary
            else "All five documented aliases remain provisional; their candidate "
            "fields require independent alias evidence or human verification. "
            "An official profile confirms the target name only, and the alias "
            "file's basis and evidence_url remain review leads."
        ),
        "",
        "## Meaning and limits",
        "",
        "Both raw player-file hashes match the frozen September 7 manifest. "
        "Every accepted fixture passes date, clubs, score, labeled whole-game "
        "columns, shooting, rebound, player/team totals and total-minute checks. "
        "Candidate URL IDs were discovery locators only. ACB Val is kept "
        "separate from EFF. " + summary["field_definition"],
        "",
        "This records the computational evidence and remaining identity gaps "
        "for the listed 2025 disagreements. It does not certify undisputed "
        "records or prove a complete season. The September 7 official repair "
        "evidence for the "
        "2018 negative-minute records remains a separate preserved artifact. "
        "Raw files, historical source variants, model results and the "
        "September 12 forecast lock were not changed.",
        "",
        "Disputed 2025 domestic records are beyond the source/factor cutoffs "
        "for the 2020–2025 newcomer benchmark, whose latest domestic source "
        "season is 2024. The pooled historical pair description includes "
        "2025, so the same statement does not excuse its identity issues. "
        "A new corrected pooled-pair calculation or future forecast requires "
        "a separately registered propagation and revalidation. No such model "
        "or pair-count rerun is claimed here.",
        "",
        "## Replay and provenance",
        "",
        "All capture URLs, retrieval times and content hashes are in summary.json. "
        "Exact corrected field values and durations are in the hash-pinned "
        "local decisions.json. Raw HTML and schedule locators stay in the local "
        "capture directory; they are required for offline replay. They are not "
        "included in the public repository allowlist.",
        "",
        "```bash",
        "python scripts/adjudicate_sloan_acb_sources.py --cache /path/to/captures "
        "--out /new/private/output --report-dir /new/report",
        "```",
        "",
        "Human acceptance of the source evidence and the final candidate "
        "remains pending. No publication, contact or submission is implied.",
        "",
    ]
    (destination / "report.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--collect", action="store_true")
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--alias-evidence", type=Path)
    parser.add_argument("--provider-cache", type=Path)
    args = parser.parse_args()
    audit(
        args.cache,
        args.out,
        raw_root=args.raw_root,
        collect=args.collect,
        report_dir=args.report_dir,
        alias_evidence=args.alias_evidence,
        provider_cache=args.provider_cache,
    )


if __name__ == "__main__":
    main()
