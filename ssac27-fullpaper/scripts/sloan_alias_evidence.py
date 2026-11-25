"""Scoped identity evidence: fixture anchors, provider birth dates and ACB IDs.

Threats: target-only profiles, name collisions, wrong fixtures, mutable captures.
"""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import adjudicate_sloan_acb_sources as acb  # noqa: E402
from src.data.scrapers.proballers.base import request_approved_proballers_url  # noqa: E402

PROTOCOL = (
    ROOT / "docs/research/sloan-evidence-completion-preregistration-2026-09-17.md"
)
STATUS = "VERIFIED_PROVIDER_ID_DOB"


def provider_capture(url, cache, *, collect=False):
    if not re.fullmatch(
        r"https://www\.proballers\.com/basketball/(?:player|game)/\d+/[^/?#]+", url
    ):
        raise ValueError("unsupported provider evidence URL")
    cache = Path(cache)
    key = acb.sha(url.encode())[:24]
    meta_path, body_path = cache / (key + ".json"), cache / (key + ".html")
    if not meta_path.exists():
        if not collect:
            raise ValueError("missing provider capture: " + url)
        cache.mkdir(parents=True, exist_ok=True)
        response = request_approved_proballers_url(
            url,
            requests.get,
            headers={
                "User-Agent": (
                    "IsocourtBot/1.0 (+https://isocourt.com; contact-withheld@example.invalid)"
                )
            },
            timeout=25,
        )
        payload = response.content
        meta = dict(
            url=url,
            final_url=response.url,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            http_status=response.status_code,
            sha256=acb.sha(payload),
        )
        body_path.write_bytes(payload)
        acb.dump(meta_path, meta)
        time.sleep(1)
    meta, payload = json.loads(meta_path.read_text()), body_path.read_bytes()
    if meta.get("url") != url or meta.get("sha256") != acb.sha(payload):
        raise ValueError("provider capture hash or URL mismatch")
    final = urlparse(meta.get("final_url", ""))
    requested = urlparse(url)
    if (
        meta.get("http_status") != 200
        or final.scheme != "https"
        or final.hostname != requested.hostname
        or final.path.split("/")[:4] != requested.path.split("/")[:4]
    ):
        raise ValueError("provider evidence unavailable or identity-changing redirect")
    return payload, meta


def fixture_anchor(payload, expected, raw, team):
    soup = BeautifulSoup(payload, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    match = re.search(r" - ([A-Z][a-z]{2} \d{1,2}, \d{4}) - Game recap", title)
    if (
        not match
        or datetime.strptime(match[1], "%b %d, %Y").date().isoformat()
        != expected["date"]
    ):
        raise ValueError("provider fixture date mismatch")
    teams = re.split(
        r"\s+Vs\s+", soup.h1.get_text(" ", strip=True) if soup.h1 else "", flags=re.I
    )
    if len(teams) != 2 or [acb.club(t) for t in teams] != [
        acb.club(expected[x + "_team"]) for x in ("home", "away")
    ]:
        raise ValueError("provider fixture clubs mismatch")
    candidates = []
    for anchor in soup.select("table a[href]"):
        previous = anchor.find_previous(["h2", "h3"])
        if (
            acb.norm(anchor.get_text(" ", strip=True)) == acb.norm(raw)
            and previous
            and acb.club(previous.get_text(" ", strip=True)) == acb.club(team)
        ):
            href = urljoin("https://www.proballers.com", anchor["href"])
            if re.fullmatch(
                r"https://www\.proballers\.com/basketball/player/\d+/[^/]+", href
            ):
                candidates.append(href)
    if len(candidates) != 1:
        raise ValueError("missing or nonunique provider player anchor")
    return candidates[0]


def provider_profile(payload, raw):
    soup = BeautifulSoup(payload, "html.parser")
    heading = soup.select_one("h1.identity__name")
    if heading is None:
        raise ValueError("provider identity heading missing")
    for element in heading.select(".stats"):
        element.decompose()
    displayed = heading.get_text(" ", strip=True)
    if acb.norm(displayed) != acb.norm(raw):
        raise ValueError("provider raw name mismatch")
    bios = [
        p.get_text(" ", strip=True)
        for p in soup.select("p")
        if p.strong and "is a basketball player" in p.strong.get_text(" ", strip=True)
    ]
    if len(bios) != 1:
        raise ValueError("provider identity biography missing or ambiguous")
    match = re.search(r"born on ([A-Z][a-z]+ \d{1,2}, \d{4})", bios[0])
    if not match:
        raise ValueError("provider DOB missing")
    return dict(
        displayed_name=displayed,
        birth_date=datetime.strptime(match[1], "%B %d, %Y").date().isoformat(),
        full_name=bios[0].split(" is a basketball player")[0],
    )


def official_profile(payload, official_name):
    if acb.norm(official_name) not in {acb.norm(n) for n in acb.profile_names(payload)}:
        raise ValueError("official profile name mismatch")
    text = BeautifulSoup(payload, "html.parser").get_text(" ", strip=True)
    matches = re.findall(r"Fecha nacimiento (\d{2}/\d{2}/\d{4})", text)
    if len(frozenset(matches)) != 1:
        raise ValueError("official DOB missing or ambiguous")
    return datetime.strptime(matches[0], "%d/%m/%Y").date().isoformat()


def verify_one(record, inputs, provider_cache, official_cache, hashes=None):
    evidence = {}

    def check(url, payload, meta):
        if hashes is not None and hashes.get(url) != acb.sha(payload):
            raise ValueError("pinned evidence hash mismatch")
        evidence[url] = meta

    player_urls = []
    if not record.get("fixtures"):
        raise ValueError("alias has no fixture scope")
    for game_id, url in record["fixtures"].items():
        if str(game_id) not in urlparse(url).path.split("/"):
            raise ValueError("provider fixture ID mismatch")
        expected = inputs["fixtures"][game_id]
        payload, meta = provider_capture(url, provider_cache)
        check(url, payload, meta)
        player_urls.append(
            fixture_anchor(payload, expected, record["raw"], record["club"])
        )
        payload, meta = acb.get_capture(expected["url"], official_cache)
        check(expected["url"], payload, meta)
        fixture = acb.parse_fixture(payload, expected)
        players = fixture["teams"][acb.club(record["club"])]["players"]
        matches = [p for p in players if p["official_id"] == record["official_id"]]
        if (
            len(matches) != 1
            or matches[0]["player_url"] != record["official_profile_url"]
        ):
            raise ValueError("official roster/profile mismatch")
    if frozenset(player_urls) != {record["provider_profile_url"]}:
        raise ValueError("provider ID varies across fixture scope")
    url = record["provider_profile_url"]
    payload, meta = provider_capture(url, provider_cache)
    check(url, payload, meta)
    profile = provider_profile(payload, record["raw"])
    url = record["official_profile_url"]
    payload, meta = acb.get_capture(url, official_cache)
    check(url, payload, meta)
    dob = official_profile(payload, record["official_name"])
    if profile["birth_date"] != dob:
        raise ValueError("provider/official DOB mismatch")
    return {
        **record,
        "status": STATUS,
        "provider_id": urlparse(record["provider_profile_url"]).path.split("/")[3],
        "birth_date": dob,
        "provider_identity": profile,
        "evidence": evidence,
    }


def verify_manifest(path, provider_cache, official_cache):
    manifest = json.loads(Path(path).read_text())
    inputs_path = Path(official_cache) / "inputs.json"
    if manifest.get("schema_version") != 1 or manifest.get(
        "official_inputs_sha256"
    ) != acb.sha(inputs_path.read_bytes()):
        raise ValueError("alias manifest or official input hash mismatch")
    inputs = json.loads(inputs_path.read_text())
    if manifest.get("protocol_sha256") != acb.sha(PROTOCOL.read_bytes()):
        raise ValueError("registered alias protocol mismatch")
    expected = {
        (r["raw"], acb.club(r["club"]), r["official_id"])
        for r in json.loads(acb.ALIASES.read_text())["aliases"]
    }
    actual = [
        (r["raw"], acb.club(r["club"]), r["official_id"]) for r in manifest["aliases"]
    ]
    if frozenset(actual) != expected or len(actual) != len(expected):
        raise ValueError("frozen alias population mismatch")
    # Check all bytes even when a known conflict ends identity replay early.
    for url, digest in manifest["capture_hashes"].items():
        payload, _ = (
            provider_capture(url, provider_cache)
            if urlparse(url).hostname == "www.proballers.com"
            else acb.get_capture(url, official_cache)
        )
        if digest != acb.sha(payload):
            raise ValueError("pinned evidence hash mismatch")
    rows = []
    for record in manifest["aliases"]:
        try:
            verified = verify_one(
                record,
                inputs,
                provider_cache,
                official_cache,
                manifest["capture_hashes"],
            )
        except ValueError as exc:
            if record.get("status") != "UNRESOLVED" or record.get("reason") != str(exc):
                raise
        else:
            if record.get("status") != STATUS:
                raise ValueError("stored unresolved alias no longer reproduces")
            rows.append(verified)
    keys = [(r["raw"], acb.club(r["club"])) for r in rows]
    if len(frozenset(keys)) != len(keys):
        raise ValueError("duplicate alias scope")
    return dict(zip(keys, rows, strict=True))


def collect(raw_root, official_cache, provider_cache, output):
    output = Path(output)
    if output.exists():
        raise ValueError("refuse to replace alias evidence manifest")
    inputs_path = Path(official_cache) / "inputs.json"
    inputs = json.loads(inputs_path.read_text())
    rel = "proballers/spain-acb/2025/games_spain-acb_2025.parquet"
    schedule_path = Path(raw_root) / rel
    if acb.sha(schedule_path.read_bytes()) != inputs["raw_hashes"][rel]:
        raise ValueError("frozen provider schedule hash changed")
    schedule = pd.read_parquet(schedule_path).set_index("game_id")
    diagnosis = json.loads((acb.SOURCE / "source_diagnosis.json").read_text())
    results = []
    for alias in json.loads(acb.ALIASES.read_text())["aliases"]:
        ids = sorted(
            {
                r["game_id"]
                for r in diagnosis["field_disagreements"]
                if r["player_name"] == alias["raw"] and r["team"] == alias["club"]
            }
        )
        record = {k: alias[k] for k in ("raw", "club", "official_id", "official_name")}
        record["season"] = 2025
        record["fixtures"] = {gid: str(schedule.loc[gid, "game_url"]) for gid in ids}
        for gid, url in record["fixtures"].items():
            payload, _ = provider_capture(url, provider_cache, collect=True)
            player_url = fixture_anchor(
                payload, inputs["fixtures"][gid], alias["raw"], alias["club"]
            )
            if (
                "provider_profile_url" in record
                and record["provider_profile_url"] != player_url
            ):
                raise ValueError("provider profile changes within scoped alias")
            record["provider_profile_url"] = player_url
            official_payload, _ = acb.get_capture(
                inputs["fixtures"][gid]["url"], official_cache
            )
            fixture = acb.parse_fixture(official_payload, inputs["fixtures"][gid])
            record["official_profile_url"] = next(
                p["player_url"]
                for p in fixture["teams"][acb.club(alias["club"])]["players"]
                if p["official_id"] == alias["official_id"]
            )
        provider_capture(record["provider_profile_url"], provider_cache, collect=True)
        try:
            results.append(verify_one(record, inputs, provider_cache, official_cache))
        except ValueError as exc:
            urls = [
                *record["fixtures"].values(),
                record["provider_profile_url"],
                record["official_profile_url"],
                *[inputs["fixtures"][g]["url"] for g in record["fixtures"]],
            ]
            retained = {}
            for url in urls:
                payload, meta = (
                    provider_capture(url, provider_cache)
                    if "proballers.com" in url
                    else acb.get_capture(url, official_cache)
                )
                retained[url] = meta
            provider_payload, _ = provider_capture(
                record["provider_profile_url"], provider_cache
            )
            official_payload, _ = acb.get_capture(
                record["official_profile_url"], official_cache
            )
            results.append(
                {
                    **record,
                    "status": "UNRESOLVED",
                    "reason": str(exc),
                    "provider_identity": provider_profile(
                        provider_payload, record["raw"]
                    ),
                    "official_birth_date": official_profile(
                        official_payload, record["official_name"]
                    ),
                    "evidence": retained,
                }
            )
    manifest = dict(
        schema_version=1,
        scope=(
            "Only listed raw names, clubs, seasons and fixtures; "
            "not a longitudinal person crosswalk"
        ),
        protocol_sha256=acb.sha(PROTOCOL.read_bytes()),
        generator_sha256=acb.sha(Path(__file__).read_bytes()),
        official_inputs_sha256=acb.sha(inputs_path.read_bytes()),
        aliases=results,
        capture_hashes={
            u: m["sha256"] for r in results for u, m in r["evidence"].items()
        },
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    acb.dump(output, manifest)
    verify_manifest(output, provider_cache, official_cache)
    print(
        json.dumps(
            {
                "verified_aliases": sum(r["status"] == STATUS for r in results),
                "unresolved_aliases": sum(r["status"] != STATUS for r in results),
                "fixtures": len({g for r in results for g in r["fixtures"]}),
                "output": str(output),
            }
        )
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-root", type=Path, required=True)
    p.add_argument("--official-cache", type=Path, required=True)
    p.add_argument("--provider-cache", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    collect(a.raw_root, a.official_cache, a.provider_cache, a.out)


if __name__ == "__main__":
    main()
