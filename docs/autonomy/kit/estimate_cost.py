#!/usr/bin/env python3
"""Estimate what the autonomous issue-workhorse loop costs before you arm it.

It turns the dials in COSTS.md into numbers: it reads the cadence, effort, and
timeout from a config.yaml (or flags), works out how many sessions a day that
fires, and prints a monthly cost range for subscription billing vs a metered
API key — so the gap COSTS.md describes comes out as a concrete number.

  python3 estimate_cost.py config.yaml
  python3 estimate_cost.py --cron "*/15 7-19 * * *" --work-effort high
  python3 estimate_cost.py --config config.example.yaml --avg-session-minutes 25

The numbers below the divider are ASSUMPTIONS, not a quote. Plans and token
prices move, and real token use swings widely with prompt caching and how much
each session actually does. Edit the PRICES table to match your own plans and
your observed per-session token use. The same table lives in cost-estimator.html;
keep the two in sync.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

# ===========================================================================
# PRICE ASSUMPTIONS  --  edit these to match your own plans and usage.
# Checked roughly 2026-06. Treat as a starting point to verify, not a quote.
# The HTML calculator (cost-estimator.html) carries the same numbers.
# ===========================================================================

# Flat monthly subscription fees, in USD. A subscription run costs nothing extra
# until you hit the plan's limits, so these are fixed regardless of cadence.
SUBSCRIPTION_PLANS_USD = {
    "worker": 100.0,  # the coding agent on a flat plan (e.g. a Claude plan)
    "reviewer": 20.0,  # the reviewer via a ChatGPT login (Codex)
}

# Metered token price, USD per 1,000,000 tokens, blended across input + output.
# Output is pricier than input and prompt caching makes input far cheaper, so
# these are deliberately rough mid-points. Lower them if you rely on caching.
METERED_BLENDED_USD_PER_MTOK = {
    "worker": 12.0,  # an Opus-class coding model
    "reviewer": 5.0,  # a cheaper review-class model
}

# Tokens the WORKER bills per active minute, as a (low, high) band per effort
# tier. This is the softest assumption in the file — an agent streams tool
# results, file reads, and reasoning, so per-minute volume varies a lot. These
# are order-of-magnitude envelopes; replace them with what you actually observe.
WORKER_TOKENS_PER_MIN = {
    "low": (3_000, 9_000),
    "medium": (5_000, 14_000),
    "high": (8_000, 22_000),
    "xhigh": (12_000, 30_000),
    "max": (18_000, 42_000),
}

# Tokens the REVIEWER bills per pass, as a (low, high) band, before the effort
# multiplier below. A pass reads the diff plus surrounding context.
REVIEW_TOKENS_PER_PASS = (15_000, 60_000)

# How much each effort tier scales the reviewer's per-pass token use.
REVIEW_EFFORT_MULTIPLIER = {
    "low": 1.0,
    "medium": 1.4,
    "high": 2.0,
    "xhigh": 2.6,
    "max": 3.2,
}

# Calendar assumption: average days in a month.
DAYS_PER_MONTH = 30.4

# Defaults for dials that are not in config.yaml.
DEFAULT_AVG_SESSION_MINUTES = 30.0
DEFAULT_MAX_PASSES = 3
VALID_EFFORTS = tuple(WORKER_TOKENS_PER_MIN.keys())

# ===========================================================================
# Cron cadence  ->  runs per day
# ===========================================================================

# crontab(5) accepts three-letter names in the day-of-week field (SUN..SAT,
# case-insensitive). Only the day-of-week field is expanded here — the month
# field is never parsed (cron_unsupported_restrictions refuses any month
# restriction, named or numeric, because the estimator doesn't model it), so a
# month-name table would be unreachable.
CRON_DOW_NAMES = {
    "SUN": 0,
    "MON": 1,
    "TUE": 2,
    "WED": 3,
    "THU": 4,
    "FRI": 5,
    "SAT": 6,
}


def parse_cron_field(
    field_text: str, lo: int, hi: int, names: dict[str, int] | None = None
) -> set[int]:
    """Expand one cron field into the set of values it matches within [lo, hi].

    Handles "*", lists ("a,b"), ranges ("a-b"), and steps ("*/n", "a-b/n"). When
    a names map is given (e.g. SUN..SAT for day-of-week), named tokens resolve
    through it, case-insensitively, on either side of a range.
    """

    def to_int(token: str) -> int:
        token = token.strip()
        if names and token.upper() in names:
            return names[token.upper()]
        try:
            return int(token)
        except ValueError:
            raise ValueError(
                f"cron field {field_text!r} has an unrecognized value: {token!r}"
            ) from None

    values: set[int] = set()
    for part in field_text.split(","):
        part = part.strip()
        if not part:
            continue
        step = 1
        if "/" in part:
            base, step_text = part.split("/", 1)
            step = int(step_text)
            if step <= 0:
                raise ValueError(f"cron step must be positive: {part!r}")
        else:
            base = part

        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            start_text, end_text = base.split("-", 1)
            start, end = to_int(start_text), to_int(end_text)
            # In the day-of-week field Sunday has two encodings, 0 and 7. The
            # names map resolves SUN -> 0, so a range ending in Sunday (e.g.
            # FRI-SUN -> 5-0, or numeric 5-0) reads as start > end. cron lets
            # Sunday also be the high alias 7, so lift the end to hi to keep the
            # range ordered — "FRI-SUN" then folds to {5,6,0} exactly like the
            # numeric "5-7". Only the day-of-week field passes a names map, and
            # its caller folds 7 -> 0, so this stays scoped to that field.
            if names and start > end and end == lo:
                end = hi
        else:
            start = end = to_int(base)

        if start < lo or end > hi or start > end:
            raise ValueError(f"cron field {field_text!r} out of range [{lo},{hi}]")
        values.update(range(start, end + 1, step))
    if not values:
        raise ValueError(f"cron field matched nothing: {field_text!r}")
    return values


def cron_runs_per_active_day(expr: str) -> int:
    """Sessions fired on a day the schedule is active: minute count x hour count."""
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(
            f"expected a 5-field cron expression, got {len(fields)}: {expr!r}"
        )
    minute, hour = fields[0], fields[1]
    minutes = parse_cron_field(minute, 0, 59)
    hours = parse_cron_field(hour, 0, 23)
    return len(minutes) * len(hours)


def cron_active_days_per_week(expr: str) -> int:
    """How many days a week the schedule runs, read from the day-of-week field.

    cron day-of-week is 0-6 with 0 = Sunday; 7 is also Sunday. "*" means daily.
    Only this field is read for weekday gating; day-of-month/month are assumed
    unrestricted (a warning is printed elsewhere if they are not).
    """
    dow = expr.split()[4]
    if dow.strip() == "*":
        return 7
    # Parse against 0-7 (cron allows both 0 and 7 for Sunday), then fold 7 -> 0
    # on the integer set. Normalizing before the parse — dow.replace("7", "0") —
    # would corrupt ranges like "1-7" into the invalid "1-0".
    days = {d % 7 for d in parse_cron_field(dow, 0, 7, CRON_DOW_NAMES)}
    return len(days)


def cron_unsupported_restrictions(expr: str) -> list[str]:
    """Day-of-month / month restrictions this estimator does not model."""
    fields = expr.split()
    notes = []
    if fields[2].strip() != "*":
        notes.append(f"day-of-month is {fields[2]!r}")
    if fields[3].strip() != "*":
        notes.append(f"month is {fields[3]!r}")
    return notes


# ===========================================================================
# Cost model
# ===========================================================================


@dataclass
class Inputs:
    cron: str
    work_effort: str
    review_effort: str
    avg_session_minutes: float
    max_passes: int
    days_per_month: float = DAYS_PER_MONTH
    review_enabled: bool = True
    wake_enabled: bool = True


@dataclass
class Estimate:
    runs_per_active_day: int
    active_days_per_week: int
    runs_per_month: float
    subscription_monthly_usd: float
    metered_per_run_usd: tuple[float, float]
    metered_monthly_usd: tuple[float, float]


def _validate_effort(name: str, value: str) -> str:
    value = (value or "").lower()
    if value not in VALID_EFFORTS:
        raise ValueError(
            f"{name} must be one of {', '.join(VALID_EFFORTS)}; got {value!r}"
        )
    return value


def metered_cost_per_run(inputs: Inputs) -> tuple[float, float]:
    """(low, high) USD for one session billed against a metered API key."""
    work_lo, work_hi = WORKER_TOKENS_PER_MIN[inputs.work_effort]
    worker_tokens_lo = work_lo * inputs.avg_session_minutes
    worker_tokens_hi = work_hi * inputs.avg_session_minutes
    worker_price = METERED_BLENDED_USD_PER_MTOK["worker"] / 1_000_000

    # review.enabled: false means the review pass doesn't run, so it bills nothing.
    passes = inputs.max_passes if inputs.review_enabled else 0
    pass_lo, pass_hi = REVIEW_TOKENS_PER_PASS
    mult = REVIEW_EFFORT_MULTIPLIER[inputs.review_effort]
    review_tokens_lo = pass_lo * mult * passes
    review_tokens_hi = pass_hi * mult * passes
    review_price = METERED_BLENDED_USD_PER_MTOK["reviewer"] / 1_000_000

    low = worker_tokens_lo * worker_price + review_tokens_lo * review_price
    high = worker_tokens_hi * worker_price + review_tokens_hi * review_price
    return low, high


def estimate(inputs: Inputs) -> Estimate:
    inputs.work_effort = _validate_effort("work_effort", inputs.work_effort)
    inputs.review_effort = _validate_effort("review_effort", inputs.review_effort)
    if inputs.avg_session_minutes <= 0:
        raise ValueError("avg_session_minutes must be positive")
    if inputs.review_enabled and inputs.max_passes <= 0:
        raise ValueError("max_passes must be positive when review is enabled")
    if inputs.days_per_month <= 0:
        raise ValueError("days_per_month must be positive")

    # schedule.wake.enabled: false means the loop never fires, so it runs zero
    # times and bills zero metered tokens. Short-circuit before reading cadence —
    # a disabled schedule's cron is moot. The per-run figure stays informational
    # ("if you turned it on..."); the subscription line is left to issue #110
    # (a plan you hold whether or not this loop uses it).
    if not inputs.wake_enabled:
        return Estimate(
            runs_per_active_day=0,
            active_days_per_week=0,
            runs_per_month=0.0,
            subscription_monthly_usd=sum(SUBSCRIPTION_PLANS_USD.values()),
            metered_per_run_usd=metered_cost_per_run(inputs),
            metered_monthly_usd=(0.0, 0.0),
        )

    per_active_day = cron_runs_per_active_day(inputs.cron)
    active_days = cron_active_days_per_week(inputs.cron)

    # day-of-month and month aren't modelled. Rather than report a monthly total
    # that's off by an order of magnitude — "0 9 1 * *" runs once a month, but
    # minute x hour x day-of-week reads it as ~30 — refuse the schedule and say
    # why, instead of printing a confident wrong number with a footnote.
    restrictions = cron_unsupported_restrictions(inputs.cron)
    if restrictions:
        raise ValueError(
            "cron restricts " + " and ".join(restrictions) + ". This estimator "
            "reads cadence from minute, hour, and day-of-week only, so its "
            "monthly total would be wrong for this schedule. Estimate one "
            "without a day-of-month or month restriction, or work it out by hand."
        )

    runs_per_month = per_active_day * (active_days / 7.0) * inputs.days_per_month
    subscription = sum(SUBSCRIPTION_PLANS_USD.values())
    run_lo, run_hi = metered_cost_per_run(inputs)
    monthly = (run_lo * runs_per_month, run_hi * runs_per_month)

    return Estimate(
        runs_per_active_day=per_active_day,
        active_days_per_week=active_days,
        runs_per_month=runs_per_month,
        subscription_monthly_usd=subscription,
        metered_per_run_usd=(run_lo, run_hi),
        metered_monthly_usd=monthly,
    )


# ===========================================================================
# Config loading + CLI
# ===========================================================================


def load_config(path: str) -> dict:
    """Read the kit's config.yaml. PyYAML is optional; without it, use flags."""
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - environment-specific
        raise SystemExit(
            "PyYAML is not installed, so --config can't be read. Either "
            "`pip install pyyaml`, or pass the dials as flags "
            "(--cron, --work-effort, --review-effort, --max-passes)."
        ) from exc
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _switch_on(value: object) -> bool:
    """A config switch defaults on; only an explicit falsey value turns it off."""
    return value is None or bool(value)


def inputs_from_config(cfg: dict) -> dict:
    """Pull the dials this estimator cares about out of a parsed config dict."""
    schedule = cfg.get("schedule") or {}
    wake = schedule.get("wake") or {}
    timeouts = schedule.get("timeouts") or {}
    model = cfg.get("model") or {}
    review = cfg.get("review") or {}
    nudges = cfg.get("nudges") or {}
    out = {}
    # Test "is not None" (key present), not truthiness — else an explicit
    # review.max_passes: 0 reads as absent and the bad value never reaches the
    # validation in estimate(), exactly the trap the CLI path also had.
    if wake.get("cron") is not None:
        out["cron"] = wake["cron"]
    # schedule.wake.enabled: false turns the whole loop off -> zero runs, $0
    # metered. Presence check so an absent key defaults on downstream.
    if wake.get("enabled") is not None:
        out["wake_enabled"] = bool(wake["enabled"])
    if model.get("work_effort") is not None:
        out["work_effort"] = model["work_effort"]
    if model.get("review_effort") is not None:
        out["review_effort"] = model["review_effort"]
    if review.get("max_passes") is not None:
        out["max_passes"] = int(review["max_passes"])
    # Review actually runs only when BOTH switches are on: review.enabled gates
    # the machinery, and nudges.review gates whether the wake prompt even asks
    # for it (reference/wake.reference.py appends the review block only when
    # nudges.review is truthy). Either one off means no review tokens are billed.
    review_on = review.get("enabled")
    nudge_on = nudges.get("review")
    if review_on is not None or nudge_on is not None:
        out["review_enabled"] = _switch_on(review_on) and _switch_on(nudge_on)
    # hard_minutes is a ceiling on session length, not the average. It caps the
    # assumed average when it's tighter than the default (see resolve_inputs).
    if timeouts.get("hard_minutes") is not None:
        out["hard_minutes"] = int(timeouts["hard_minutes"])
    return out


def _money(value: float) -> str:
    return f"${value:,.0f}" if value >= 100 else f"${value:,.2f}"


def format_report(inputs: Inputs, est: Estimate, *, source: str) -> str:
    lo_run, hi_run = est.metered_per_run_usd
    lo_mo, hi_mo = est.metered_monthly_usd
    gap_lo = lo_mo / est.subscription_monthly_usd if est.subscription_monthly_usd else 0
    gap_hi = hi_mo / est.subscription_monthly_usd if est.subscription_monthly_usd else 0
    active_note = (
        ""
        if est.active_days_per_week == 7
        else f"  ({est.active_days_per_week} days/week)"
    )
    review_note = (
        f"review up to {inputs.max_passes} passes"
        if inputs.review_enabled
        else "review disabled"
    )
    cadence_note = "" if inputs.wake_enabled else "   (schedule disabled — 0 runs)"
    lines = [
        "Autonomy loop cost estimate",
        f"  source            {source}",
        f"  cadence (cron)    {inputs.cron}{cadence_note}",
        f"  work / review     {inputs.work_effort} / {inputs.review_effort} effort",
        f"  avg session       {inputs.avg_session_minutes:g} min   ({review_note})",
        "",
        f"  runs/active day   {est.runs_per_active_day}{active_note}",
        f"  runs/month        {est.runs_per_month:,.0f}",
        "",
        "Subscription billing (flat plans)",
        f"  monthly           {_money(est.subscription_monthly_usd)}"
        "   (until plan limits; ~$0 marginal per run)",
        "",
        "Metered API billing (pay per token)",
        f"  per run           {_money(lo_run)} – {_money(hi_run)}",
        f"  monthly           {_money(lo_mo)} – {_money(hi_mo)}",
        "",
        f"Gap: metered runs about {gap_lo:,.0f}x – {gap_hi:,.0f}x the flat plans "
        "at this cadence.",
    ]
    lines += [
        "",
        "Price assumptions (USD) — edit at the top of estimate_cost.py to fit your plans:",
        f"  subscription/mo   worker {_money(SUBSCRIPTION_PLANS_USD['worker'])}, "
        f"reviewer {_money(SUBSCRIPTION_PLANS_USD['reviewer'])}",
        f"  metered $/Mtok    worker {METERED_BLENDED_USD_PER_MTOK['worker']:g}, "
        f"reviewer {METERED_BLENDED_USD_PER_MTOK['reviewer']:g} (blended in+out)",
        f"  worker tokens/min ({inputs.work_effort}) "
        f"{WORKER_TOKENS_PER_MIN[inputs.work_effort][0]:,}"
        f"–{WORKER_TOKENS_PER_MIN[inputs.work_effort][1]:,}",
        "",
        "These are rough order-of-magnitude assumptions, not a quote. Plans and "
        "token prices move,",
        "and real token use swings with prompt caching and task size. Calibrate "
        "with your own numbers.",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estimate the autonomy loop's monthly cost: subscription vs metered.",
    )
    parser.add_argument(
        "config",
        nargs="?",
        help="path to config.yaml (positional shorthand for --config)",
    )
    parser.add_argument("--config", dest="config_opt", help="path to config.yaml")
    parser.add_argument("--cron", help="cron cadence, overrides the config")
    parser.add_argument("--work-effort", help=f"one of {', '.join(VALID_EFFORTS)}")
    parser.add_argument("--review-effort", help=f"one of {', '.join(VALID_EFFORTS)}")
    parser.add_argument(
        "--avg-session-minutes",
        type=float,
        help=f"average minutes a session runs (default {DEFAULT_AVG_SESSION_MINUTES:g})",
    )
    parser.add_argument("--max-passes", type=int, help="review passes per session")
    parser.add_argument(
        "--days-per-month",
        type=float,
        default=DAYS_PER_MONTH,
        help=f"days in a month (default {DAYS_PER_MONTH})",
    )
    return parser


def resolve_inputs(args: argparse.Namespace) -> tuple[Inputs, str]:
    cfg_path = args.config_opt or args.config
    values: dict = {}
    source = "flags"
    if cfg_path:
        values.update(inputs_from_config(load_config(cfg_path)))
        source = cfg_path
    # Flag overrides win over the config file. Test "is not None" (was the flag
    # passed?), not truthiness — otherwise an explicit --max-passes 0 or
    # --avg-session-minutes 0 is falsy, gets silently dropped for the default,
    # and the positive-value checks in estimate() never see the bad value.
    if args.cron is not None:
        values["cron"] = args.cron
    if args.work_effort is not None:
        values["work_effort"] = args.work_effort
    if args.review_effort is not None:
        values["review_effort"] = args.review_effort
    if args.max_passes is not None:
        values["max_passes"] = args.max_passes
    if args.avg_session_minutes is not None:
        values["avg_session_minutes"] = args.avg_session_minutes

    if "cron" not in values:
        # A disabled schedule never fires, so its cadence is moot — fill a
        # placeholder so estimate() can short-circuit to 0 runs instead of
        # demanding a cron the user rightly left out. Only an ENABLED loop with
        # no cadence is an error.
        if values.get("wake_enabled", True):
            raise SystemExit(
                "no cadence given. Pass a config.yaml with schedule.wake.cron, or --cron."
            )
        values["cron"] = "(disabled)"
    # An explicit average always wins. Otherwise start from the default and let a
    # hard timeout pull it down when the timeout is tighter than that default —
    # a 15-minute cap can't average 30 minutes a session.
    if "avg_session_minutes" in values:
        avg_session_minutes = values["avg_session_minutes"]
    else:
        avg_session_minutes = DEFAULT_AVG_SESSION_MINUTES
        if "hard_minutes" in values:
            avg_session_minutes = min(avg_session_minutes, values["hard_minutes"])
    inputs = Inputs(
        cron=values["cron"],
        work_effort=values.get("work_effort", "high"),
        review_effort=values.get("review_effort", "low"),
        avg_session_minutes=avg_session_minutes,
        max_passes=values.get("max_passes", DEFAULT_MAX_PASSES),
        days_per_month=args.days_per_month,
        review_enabled=values.get("review_enabled", True),
        wake_enabled=values.get("wake_enabled", True),
    )
    return inputs, source


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        inputs, source = resolve_inputs(args)
        est = estimate(inputs)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(format_report(inputs, est, source=source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
