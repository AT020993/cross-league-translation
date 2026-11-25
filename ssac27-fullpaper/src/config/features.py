"""Centralized feature flags — single source of truth.

All ``ENABLE_*`` flags read from environment variables at import time.
Default is ON (``"1"``) unless noted. Set ``=0`` to disable.

Import from here instead of reading ``os.environ`` in individual modules.

Hot reload
----------
Call ``reload_flags()`` or hit ``POST /api/ops/feature-flags/reload``
to re-read all flags from the current environment without restarting.
``get_flag_status()`` returns the full flag→value mapping for dashboards.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flag definitions: (module_attr, env_var, default_value)
# ---------------------------------------------------------------------------

_FLAG_DEFS: list[tuple[str, str, str]] = [
    # DGA (default ON)
    ("ENABLE_FACT_BLOCKS", "ENABLE_FACT_BLOCKS", "1"),
    # ATI-3900: the rewriter names every route from one vocabulary table
    # (src/agent/route_vocabulary.py), its labels reach the router, and it is
    # skipped only on a complete deterministic parse. Off = the legacy prompt,
    # schema, label map and skip, byte-identical (ATI-3411's rewriter
    # research replays against them).
    ("ENABLE_ROUTE_VOCABULARY_REWRITER", "ENABLE_ROUTE_VOCABULARY_REWRITER", "1"),
    # Anti-hallucination (default varies)
    ("ENABLE_NEURAL_VERIFIER", "ENABLE_NEURAL_VERIFIER", "0"),
    ("ENABLE_CONFORMAL_ABSTENTION", "ENABLE_CONFORMAL_ABSTENTION", "0"),
    ("ENABLE_GATEWAY_NO_WORSE_GUARD", "ENABLE_GATEWAY_NO_WORSE_GUARD", "1"),
    ("ENABLE_SCOPE_DISCLOSURE_HARDENING", "ENABLE_SCOPE_DISCLOSURE_HARDENING", "1"),
    # V5 Frozen Answer + Presentation Contract pipeline is the canonical path
    # (PR #502, default-on since 2026-05-01) and no longer flag-gated — the
    # build/observe/cache-key/extractor-tagging/scoped-chunks/prompt-anchor/
    # presentation/answer-planner/style-aware sub-flags were inlined in
    # ATI-2566. ENABLE_FROZEN_CONTRACT_BLOCKING is a LEGACY boolean kept for
    # back-compat (1 → block_safe_routes, explicit 0 → observe_only). Since
    # ATI-2541 (2026-07-02) the no-config default mode is block_safe_routes —
    # see contracts/blocking_policy.py::_resolve_mode; this flag's "0" default
    # means "defer to FROZEN_CONTRACT_BLOCKING_MODE / DEFAULT_BLOCKING_MODE",
    # not "blocking off".
    ("ENABLE_FROZEN_CONTRACT_BLOCKING", "ENABLE_FROZEN_CONTRACT_BLOCKING", "0"),
    # Deployment (default ON locally, OFF on Railway — ATI-1491)
    ("ENABLE_SCHEDULER", "ENABLE_SCHEDULER", "1"),
    # Cost control (default ON locally, OFF on Railway). When OFF, the 60 s
    # live-games background poll is skipped entirely — lets Railway's
    # serverless sleep trigger actually fire (it requires 10 min of no
    # outbound traffic). Live endpoints still work; they refresh on demand.
    ("ENABLE_LIVE_POLL", "ENABLE_LIVE_POLL", "1"),
    # Outbound collection from proballers.com (default OFF since 2026-09-03,
    # ATI-2956). Their Legal Notice requires written authorisation; the site
    # has returned 403 to every automated fetch since ~9 Jan 2026; and Amir
    # told them in writing on 2026-09-03 that automated collection has stopped.
    # The gate sits in ProballersBaseScraper._fetch_page so EVERY caller --
    # scheduler, pipeline step, slug audit, a manual CLI run -- refuses.
    ("ENABLE_PROBALLERS_SCRAPE", "ENABLE_PROBALLERS_SCRAPE", "0"),
    # ATI-1718: real-time Slack alert on rating="down" feedback.
    # Default OFF in dev so the test suite + local runs don't pollute
    # the production #agent-feedback channel; flip ON in Railway via
    # env var so the on-call sees thumbs-downs the same minute the
    # user submits them.
    ("ENABLE_BAD_FEEDBACK_SLACK", "ENABLE_BAD_FEEDBACK_SLACK", "0"),
    # ATI-1734: deterministic stat-producing templates must fail closed when
    # ``evidence_identity`` / ``AnswerScope`` / ``QueryContract`` invariants
    # are missing. Default OFF — observe-mode telemetry only. Flip ON per
    # route once the route coverage matrix shows full scope+evidence support.
    ("ENABLE_TEMPLATE_FAIL_CLOSED", "ENABLE_TEMPLATE_FAIL_CLOSED", "0"),
    # ATI-2248: when a stat-leaderboard ask produces NO grounded extraction
    # (ExtractionSkipped — no data / empty filtered frame / unrecognised stat),
    # refuse with a structured insufficient-evidence answer instead of letting
    # the LLM free-narrate unverified numbers (the numeric verifier no-ops with
    # no fact block). Default ON — the discriminator is strictly safe (no
    # grounded leaderboard exists), with an OFF escape hatch for rollback.
    ("ENABLE_LEADERBOARD_FAIL_CLOSED", "ENABLE_LEADERBOARD_FAIL_CLOSED", "1"),
    # Phase 1 of the 2026-05-22 brainstorm — route Expert tier to Gemini
    # 3.5 Flash instead of Gemini 3.1 Pro. Default OFF; flip ON after the
    # shadow-soak comparison meets the §6.2 acceptance gate. See
    # ``docs/plans/specs/done/flash-3-5-expert-upgrade.md``.
    ("ENABLE_FLASH_3_5_EXPERT", "ENABLE_FLASH_3_5_EXPERT", "0"),
    # Shadow mode — run BOTH 3.1 Pro (authoritative) and 3.5 Flash
    # (logged-only) on Expert queries in parallel. Pro response is what
    # the user sees; 3.5 Flash response is written to a dedicated DuckDB
    # file for offline comparison. Default OFF. No-op when the authority
    # swap (ENABLE_FLASH_3_5_EXPERT) is already ON.
    ("ENABLE_FLASH_3_5_EXPERT_SHADOW", "ENABLE_FLASH_3_5_EXPERT_SHADOW", "0"),
    # Email delivery (Resend). Default OFF — dark merge. Flip ON only after the
    # isocourt.com domain is verified in Resend and RESEND_API_KEY is set.
    ("ENABLE_EMAIL_DELIVERY", "ENABLE_EMAIL_DELIVERY", "0"),
    # ATI-2758: on a Gemini MONTHLY SPEND CAP exhaustion (not ordinary 429
    # throttling), serve the answer from DeepSeek V4-Flash via Fireworks
    # instead of hard-downing. Default OFF — with it off, behaviour is
    # byte-identical to today, which a test asserts.
    #
    # Flipping this ON accepts that user queries transit a US third party
    # (Fireworks) for the duration of the outage. Amir's recorded decision on
    # ATI-2758 is ACCEPT with SILENT degradation, which is exactly why the
    # telemetry stamp and the Slack state-change alert are load-bearing here
    # rather than nice-to-haves: they are the only signal a vendor switch
    # happened. See docs/DEPLOYMENT.md § Degraded LLM mode.
    ("ENABLE_GEMINI_EXHAUSTION_FALLBACK", "ENABLE_GEMINI_EXHAUSTION_FALLBACK", "0"),
    # Route/answer cache (Option C, agent-quality-rootcause 2026-06-23). Default
    # ON. Set ENABLE_ROUTE_CACHE=0 to force QueryCache.lookup to always miss, so
    # route byte-stability can be proven cache-off vs cache-on (the determinism
    # harness the cache-fix PR #1373 shipped without).
    ("ENABLE_ROUTE_CACHE", "ENABLE_ROUTE_CACHE", "1"),
    # ATI-2640: one-shot situation-similarity index build on the Railway
    # volume. Default OFF. The seed tar excludes data/agent_memory (gitignored,
    # ~1.3 GB of vectors), so prod refuses the "games similar to X" family until
    # the index exists. Prod's volume DOES carry data/raw, so the container can
    # build its own index. Flip ON for ONE deploy, let the background build
    # finish (tens of minutes), then unset + redeploy (the redeploy is the
    # restart that makes the agent open the now-populated store). The task
    # skips when the store already has vectors, so a health-swap restart inside
    # the flag window doesn't rebuild.
    ("ENABLE_SITUATION_INDEX_ON_BOOT", "ENABLE_SITUATION_INDEX_ON_BOOT", "0"),
    # Player-defence facet decomposition (pre-registration 2026-09-07). Default
    # OFF. When ON, a bare player-defence ask ("how is X's defence") claims the
    # ANALYTICAL route and decomposes deterministically into four lenses —
    # box-score counts, multi-year defensive RAPM, play-by-play defensive
    # events, and the role/impact profile — which one writer combines without
    # issuing a single overall grade. With it OFF the router, decomposer and
    # synthesizer are behaviourally identical to before, which a test asserts
    # against a recorded route table. See
    # docs/research/player-defence-facet-decomposition-preregistration-2026-09-07.md
    ("ENABLE_PLAYER_FACET_COA", "ENABLE_PLAYER_FACET_COA", "0"),
    # ATI-2896: market-watch digest section 3 (translated value flags on the
    # EL/EC scale). Default OFF and fully dark until the ATI-2799 backtest
    # passes; the digest route also strips the section when this is OFF.
    ("ENABLE_MARKET_WATCH_TRANSLATION", "ENABLE_MARKET_WATCH_TRANSLATION", "0"),
    # ATI-3181: one closed-set LLM pick-or-abstain call when the primary player
    # mention ends in a TYPO-origin ambiguity. Default OFF until the alternating
    # A/B (PR body) and the real-traffic miss rate justify it.
    ("ENABLE_LLM_NAME_PICK", "ENABLE_LLM_NAME_PICK", "0"),
    # ATI-3351: league-factor consumers read the 2026-10-10 stage-1 fit by
    # default; ON reads the Sloan SSAC27 table of record instead.
    ("ENABLE_SLOAN_LEAGUE_FACTOR_TABLE", "ENABLE_SLOAN_LEAGUE_FACTOR_TABLE", "0"),
    # Agent core refactor T2: one inherit_scope rule for what a follow-up
    # carries. Default ON since ATI-3646 (#3625).
    ("ENABLE_INHERIT_SCOPE", "ENABLE_INHERIT_SCOPE", "1"),
]

# ---------------------------------------------------------------------------
# Flag docstrings (preserved for IDE hover / help())
# ---------------------------------------------------------------------------

_FLAG_DOCS: dict[str, str] = {
    "ENABLE_PROBALLERS_SCRAPE": "ATI-2956. OFF by default. When OFF, every"
    " Proballers page fetch raises ProballersScrapeDisabledError at the"
    " scraper's single choke point, and the scheduler / pipeline / slug audit"
    " log SKIPPED and exit cleanly. Turn ON only under a written licence.",
    "ENABLE_FACT_BLOCKS": "Emit typed fact blocks from extraction results.",
    "ENABLE_ROUTE_VOCABULARY_REWRITER": (
        "ATI-3900: the rewriter names every route from route_vocabulary, is "
        "skipped only on a complete deterministic parse, and may correct a "
        "specialist route within its family. Off = legacy, byte-identical."
    ),
    "ENABLE_NEURAL_VERIFIER": "NLI-based sentence verification using DeBERTa.",
    "ENABLE_GATEWAY_NO_WORSE_GUARD": "Revert gateway corrections that provably"
    " corrupt the answer (emptied / numbers collapsed / list mangled /"
    " novel numbers).",
    "ENABLE_SCOPE_DISCLOSURE_HARDENING": "Close the wrong_scope silent-drop"
    " leaks: per-disclosure matching (no generic-phrase suppression) +"
    " route-conditional constraint audit disclosures.",
    "ENABLE_CONFORMAL_ABSTENTION": "Conformal risk control: abstain when"
    " P(hallucination) > α.",
    "ENABLE_FROZEN_CONTRACT_BLOCKING": "Convert high-severity contract"
    " violations into blocking refusals after observe soak.",
    "ENABLE_SCHEDULER": "Run APScheduler morning pipeline inside the web process."
    " ON locally (Mac launchd), OFF on Railway to keep the cloud read-only.",
    "ENABLE_LIVE_POLL": "Run the 60 s live-games background poll. ON locally;"
    " set to 0 on Railway so the container can go idle on outbound traffic"
    " (required for Railway's `sleepApplication` to fire — see"
    " https://docs.railway.com/deployments/serverless). Live endpoints still"
    " refresh on demand when users hit them.",
    "ENABLE_BAD_FEEDBACK_SLACK": "ATI-1718. When ON, every rating='down'"
    " feedback POST fires an asynchronous Slack alert to SLACK_QUERIES_CHANNEL"
    " (fallback SLACK_CHANNEL). Defaults OFF so dev/test runs don't pollute"
    " the prod feedback channel.",
    "ENABLE_TEMPLATE_FAIL_CLOSED": "ATI-1734. Stat-producing deterministic"
    " templates refuse to render (return None) when evidence_identity is"
    " missing, AnswerScope is missing, or QueryContract is missing — instead"
    " of emitting numeric prose ungrounded. Default OFF (telemetry only); flip"
    " ON per route after the coverage matrix shows full scope+evidence support.",
    "ENABLE_LEADERBOARD_FAIL_CLOSED": "ATI-2248. When a stat-leaderboard ask"
    " yields ExtractionSkipped (no grounded leaderboard could be computed),"
    " refuse with a structured insufficient-evidence answer instead of letting"
    " the LLM free-narrate unverified numbers (the deterministic numeric"
    " verifier no-ops with no fact block). Default ON; flip OFF to restore the"
    " LLM-narration fallback.",
    "ENABLE_FLASH_3_5_EXPERT": "Phase 1 of the 2026-05-22 brainstorm. When"
    " ON, the EXPERT routing tier targets Gemini 3.5 Flash instead of"
    " Gemini 3.1 Pro, with fallback ladder 3.5 Flash → 3.1 Pro → Flash 3"
    " (Gemma 4 dropped from the ladder 2026-06-19). Default OFF; flip ON"
    " after the shadow-soak comparison"
    " meets the §6.2 acceptance gate. See"
    " docs/plans/specs/done/flash-3-5-expert-upgrade.md.",
    "ENABLE_FLASH_3_5_EXPERT_SHADOW": "Shadow mode for the 2026-05-22 Expert"
    " swap. When ON (and ENABLE_FLASH_3_5_EXPERT is OFF), every Expert-tier"
    " 3.1 Pro generate fires a daemon-thread 3.5 Flash call for offline"
    " comparison. Rows written to data/conversations/shadow_expert.duckdb."
    " No effect on user-facing responses. Default OFF.",
    "ENABLE_GEMINI_EXHAUSTION_FALLBACK": "When ON, a Gemini monthly-spend-cap"
    " exhaustion degrades to DeepSeek V4-Flash (Fireworks) instead of failing"
    " the answer. Fires ONLY on the spend-cap body, never on ordinary 429"
    " throttling. Default OFF. Accepts that user queries transit a US third"
    " party during the outage window — every degraded answer is stamped"
    " provider=fireworks and entering/leaving the mode alerts"
    " #basketball-alerts.",
    "ENABLE_EMAIL_DELIVERY": "When ON (and RESEND_API_KEY is set), org invites"
    " and password-reset links are emailed via Resend. Best-effort: failures"
    " never block invite creation or the forgot-password response. Default OFF.",
    "ENABLE_ROUTE_CACHE": "Route/answer cache. Default ON. Set to 0 to force"
    " QueryCache.lookup to always miss — a determinism/verification lever to"
    " prove route byte-stability with the cache off vs. on.",
    "ENABLE_SITUATION_INDEX_ON_BOOT": "ATI-2640. One-shot: when ON, a"
    " fire-and-forget startup task builds the situation-similarity LanceDB"
    " index on the (persistent) data/ volume so prod can answer the"
    " 'games similar to X' family. Skipped when the store already has"
    " vectors. Default OFF; flip ON for one Railway deploy, verify /api/ops,"
    " then unset + redeploy.",
    "ENABLE_PLAYER_FACET_COA": "Pre-registration 2026-09-07. Default OFF."
    " When ON, a bare player-defence ask ('how is X's defence') claims the"
    " ANALYTICAL route ahead of DEFAULT and decomposes — with no LLM — into"
    " four deterministic lenses: box-score defensive counts, multi-year"
    " defensive RAPM, play-by-play defensive events, and the role/impact"
    " profile. One writer combines them and is forbidden from issuing a"
    " single overall defensive grade, because the lenses routinely disagree.",
    "ENABLE_MARKET_WATCH_TRANSLATION": "ATI-2896. Default OFF. When ON, the"
    " weekly market-watch digest renders section 3, translated value flags on"
    " the EuroLeague/EuroCup scale, and the digest route serves it. Internal"
    " only until the ATI-2799 retrospective backtest passes.",
    "ENABLE_SLOAN_LEAGUE_FACTOR_TABLE": "ATI-3351. Default OFF. Live consumers"
    " of the league-factor table (market-watch section 3) read the 2026-10-10"
    " stage-1 fit (floor_clearing tau^2 + undefined SE for one-informative-"
    "cluster cells). When ON they read the Sloan SSAC27 table of record,"
    " data/processed/translation/league_factors.parquet, which is never"
    " overwritten.",
    "ENABLE_INHERIT_SCOPE": "Agent core refactor T2. Default ON (ATI-3646). When ON,"
    " Phase 1 decides a follow-up's season, span, phase and round with the one"
    " inherit_scope rule (season wording such as 'per game' or 'overall' drops"
    " a carried round; 'those games' keeps it); hidden-event boards apply a"
    " carried phase; a bare board follow-up is league-wide, not the prior"
    " club's, and one answered for a pinned game offers the season board as a"
    " chip.",
    "ENABLE_LLM_NAME_PICK": "ATI-3181. Default OFF. When ON and the primary"
    " player mention ends in a typo-origin ambiguity (near-miss suggestion,"
    " or a phonetic / Hebrew same-score tie), one rewriter-model call with"
    " reasoning off picks a candidate by index or abstains. A pick resolves as"
    " match_kind llm_pick with its own floor and a caveat; an abstain, timeout"
    " or malformed reply leaves the 'Did you mean ...?' clarification.",
}


# ---------------------------------------------------------------------------
# Choice settings: (name, env_var, default, allowed values)
#
# A setting with more than two values cannot live in the boolean _FLAG_DEFS.
# Read with get_choice() at the point of use: it re-reads the environment on
# every call, so there is no stale import-time copy to reload.
# ---------------------------------------------------------------------------
_CHOICE_DEFS: list[tuple[str, str, str, tuple[str, ...]]] = [
    # ATI-3747. The hidden-event layer of PCI ``total_impact``. "legacy" adds
    # the hand-set bonuses of ScoringConfig.hidden_event_bonuses; "off" leaves
    # total_impact box-only (the hidden actions are valued separately, as
    # points beyond the box). Default legacy: the Sloan SSAC27 figures and
    # every published board stay reproducible until Amir approves the flip.
    ("PCI_HIDDEN_LAYER", "PCI_HIDDEN_LAYER", "legacy", ("legacy", "off")),
]


def get_choice(name: str) -> str:
    """Read a choice setting from the environment, validated against its values.

    An unrecognized value logs a warning and falls back to the default, the
    same rule as an unrecognized boolean flag.
    """
    for attr, env_var, default, allowed in _CHOICE_DEFS:
        if attr != name:
            continue
        raw = os.environ.get(env_var)
        if raw is None or not raw.strip():
            return default
        token = raw.strip().lower()
        if token in allowed:
            return token
        logger.warning(
            "Unrecognized value %r for env var %s; falling back to default %r."
            " Use one of %s.",
            raw,
            env_var,
            default,
            "/".join(allowed),
        )
        return default
    raise KeyError(f"unknown choice setting {name!r}")


# Canonical truthy/falsey string tokens for boolean env flags. Case-insensitive.
_TRUE_TOKENS = frozenset({"1", "true", "yes", "on"})
_FALSE_TOKENS = frozenset({"0", "false", "no", "off", ""})


def _coerce_bool(raw: str) -> bool | None:
    """Strictly parse a boolean token. Returns None for an unrecognized value."""
    token = raw.strip().lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    return None


def _read_flag(env_var: str, default: str) -> bool:
    """Read a boolean flag from the environment with strict parsing.

    Accepts ``1/true/yes/on`` (→ True) and ``0/false/no/off``/empty (→ False),
    case-insensitively. An unrecognized value (e.g. a typo) is NOT silently
    treated as enabled — it logs a warning and falls back to ``default``,
    which is parsed by the same strict rules. This closes the unsafe direction
    where ``ENABLE_X=false`` during an incident rollback used to read truthy.
    """
    raw = os.environ.get(env_var)
    if raw is not None:
        parsed = _coerce_bool(raw)
        if parsed is not None:
            return parsed
        logger.warning(
            "Unrecognized boolean value %r for env var %s; falling back to"
            " default %r. Use one of 1/true/yes/on or 0/false/no/off.",
            raw,
            env_var,
            default,
        )
    # Fall back to the default, parsed by the same strict rules. Callers pass
    # "0"/"1", but coerce defensively so a bad default never reads truthy.
    return _coerce_bool(default) is True


def _load_all_flags() -> None:
    """(Re-)read all flags from the current environment into module globals."""
    import src.config.features as _self

    for attr, env_var, default in _FLAG_DEFS:
        setattr(_self, attr, _read_flag(env_var, default))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def reload_flags() -> dict[str, bool]:
    """Re-read all flags from the current environment.

    Returns the new flag→value mapping. Safe to call at runtime — existing
    module-level imports of individual flags will NOT see the change (they
    captured the old bool). Code that needs hot-reload support should call
    ``get_flag("ENABLE_X")`` instead.
    """
    _load_all_flags()
    status = get_flag_status()
    logger.info("Feature flags reloaded: %s", status)
    return status


def get_flag(name: str) -> bool:
    """Read a single flag's current value (hot-reload aware)."""
    import src.config.features as _self

    return getattr(_self, name)


def pin_legacy_rewriter_for_research() -> None:
    """Run the rewriter research harnesses on the legacy rewriter (ATI-3900).

    ATI-3411 / ATI-3358 measure the rewriter as it was when their runs were
    registered; ``ENABLE_ROUTE_VOCABULARY_REWRITER`` (default on) changes its prompt,
    schema and skip. Their entry points call this so a re-run reproduces.
    An explicit ``ENABLE_ROUTE_VOCABULARY_REWRITER`` in the environment wins (a new
    amendment may choose the vocabulary); otherwise the legacy path is pinned,
    and exported so child processes inherit it.
    """
    import os

    if "ENABLE_ROUTE_VOCABULARY_REWRITER" in os.environ:
        return
    os.environ["ENABLE_ROUTE_VOCABULARY_REWRITER"] = "0"
    import src.config.features as _self

    _self.ENABLE_ROUTE_VOCABULARY_REWRITER = False


def get_flag_status() -> dict[str, bool]:
    """Return all flag names and their current values."""
    import src.config.features as _self

    return {attr: getattr(_self, attr) for attr, _, _ in _FLAG_DEFS}


# ---------------------------------------------------------------------------
# Initial load — sets module-level attributes for backward compatibility
# ---------------------------------------------------------------------------
_load_all_flags()
