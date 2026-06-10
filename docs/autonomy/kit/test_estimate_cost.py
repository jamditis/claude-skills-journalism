"""Tests for estimate_cost.py.

The cron cases are pinned to the reference numbers COSTS.md publishes
("hourly during work hours is ~13 runs a day; every 15 minutes is ~50"; the
high end is "~100 sessions a day"), so the estimator and the prose can't drift.

Run:  python3 -m pytest docs/autonomy/kit/test_estimate_cost.py -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import estimate_cost as ec  # noqa: E402


# --- cron cadence, anchored to COSTS.md -----------------------------------


@pytest.mark.parametrize(
    "expr, per_day, days_per_week",
    [
        ("5 7-19 * * *", 13, 7),  # COSTS.md: hourly, work hours ~= 13/day
        ("*/15 7-19 * * *", 52, 7),  # COSTS.md: every 15 min, work hours ~= 50
        ("*/15 * * * *", 96, 7),  # COSTS.md high end: ~100 sessions a day
        ("0 * * * *", 24, 7),  # hourly, around the clock
        ("0 9-17 * * 1-5", 9, 5),  # work hours, weekdays only
        ("0 0 * * *", 1, 7),  # once a day
        ("0,30 7-19 * * *", 26, 7),  # twice an hour, work hours
    ],
)
def test_cron_reference_cadences(expr, per_day, days_per_week):
    assert ec.cron_runs_per_active_day(expr) == per_day
    assert ec.cron_active_days_per_week(expr) == days_per_week


def test_dow_7_is_sunday_like_0():
    # 0 and 7 both mean Sunday, so they collapse to one day.
    assert ec.cron_active_days_per_week("0 9 * * 0,7") == 1
    assert ec.cron_active_days_per_week("0 9 * * 6,0") == 2


def test_dow_ranges_containing_seven():
    # A range that ends at 7 must not be string-mangled into "1-0". "1-7" spans
    # Mon..Sun, and 7 folds onto Sunday (= 0), so it's all 7 days.
    assert ec.cron_active_days_per_week("0 9 * * 1-7") == 7
    # "5-7" is Fri, Sat, Sun = 3 days.
    assert ec.cron_active_days_per_week("0 9 * * 5-7") == 3
    # "6-7" is Sat, Sun = 2 days.
    assert ec.cron_active_days_per_week("0 9 * * 6-7") == 2


def test_dow_named_weekdays():
    # crontab(5) accepts SUN..SAT names in the day-of-week field.
    assert ec.cron_active_days_per_week("5 7-19 * * MON-FRI") == 5
    assert ec.cron_active_days_per_week("0 9 * * SAT,SUN") == 2
    assert ec.cron_active_days_per_week("0 9 * * SUN") == 1  # SUN = 0
    # Case-insensitive, and a named range folds the same way numbers do.
    assert ec.cron_active_days_per_week("0 9 * * mon-fri") == 5


def test_dow_named_range_ending_in_sunday():
    # SUN resolves to 0, so a range ending in Sunday (FRI-SUN) reads as 5-0.
    # cron lets Sunday also be 7, so it must fold like the numeric "5-7" rather
    # than raise. FRI-SUN = Fri, Sat, Sun = 3 days.
    assert ec.cron_active_days_per_week("0 9 * * FRI-SUN") == 3
    # MON-SUN spans the whole week = 7 days.
    assert ec.cron_active_days_per_week("0 9 * * MON-SUN") == 7
    # SAT-SUN (and its numeric twin 6-0) is the weekend = 2 days.
    assert ec.cron_active_days_per_week("0 9 * * SAT-SUN") == 2
    assert ec.cron_active_days_per_week("0 9 * * 6-0") == 2
    # SUN-SAT is the forward whole-week range and stays 7 days (no lift needed).
    assert ec.cron_active_days_per_week("0 9 * * SUN-SAT") == 7
    # A genuinely backwards range that does not end in Sunday still raises.
    with pytest.raises(ValueError, match=r"out of range"):
        ec.cron_active_days_per_week("0 9 * * WED-MON")


def test_dow_unknown_name_rejected():
    with pytest.raises(ValueError, match="unrecognized value"):
        ec.cron_active_days_per_week("0 9 * * FUNDAY")


def test_names_only_apply_where_passed():
    # Minute/hour fields get no names map, so a name there is still rejected.
    with pytest.raises(ValueError):
        ec.parse_cron_field("MON", 0, 59)
    assert ec.parse_cron_field("MON-FRI", 0, 7, ec.CRON_DOW_NAMES) == {1, 2, 3, 4, 5}


@pytest.mark.parametrize(
    "field, lo, hi, expected",
    [
        ("*", 0, 5, {0, 1, 2, 3, 4, 5}),
        ("*/2", 0, 6, {0, 2, 4, 6}),
        ("1-3", 0, 59, {1, 2, 3}),
        ("0-10/5", 0, 59, {0, 5, 10}),
        ("7,9,11", 0, 23, {7, 9, 11}),
        ("5", 0, 59, {5}),
    ],
)
def test_parse_cron_field(field, lo, hi, expected):
    assert ec.parse_cron_field(field, lo, hi) == expected


@pytest.mark.parametrize("bad", ["99", "7-2", "-1", "", "*/0"])
def test_parse_cron_field_rejects_bad(bad):
    with pytest.raises(ValueError):
        ec.parse_cron_field(bad, 0, 23)


def test_cron_requires_five_fields():
    with pytest.raises(ValueError):
        ec.cron_runs_per_active_day("0 * * *")


def test_unsupported_restrictions_flagged():
    assert ec.cron_unsupported_restrictions("0 9 1 * *")  # day-of-month set
    assert ec.cron_unsupported_restrictions("0 9 * 6 *")  # month set
    assert ec.cron_unsupported_restrictions("0 9 * * *") == []


@pytest.mark.parametrize("cron", ["0 9 1 * *", "0 9 * 6 *", "0 9 1 6 *"])
def test_estimate_refuses_unsupported_restrictions(cron):
    # A day-of-month or month restriction would make the monthly total wrong, so
    # estimate() refuses rather than print a confident wrong number.
    with pytest.raises(ValueError, match="day-of-month|month"):
        ec.estimate(_inputs(cron=cron))


def test_estimate_allows_day_of_week_restriction():
    # day-of-week IS modelled, so it must not be swept up by the refusal.
    est = ec.estimate(_inputs(cron="0 9-17 * * 1-5"))
    assert est.runs_per_active_day == 9
    assert est.active_days_per_week == 5


# --- cost model ------------------------------------------------------------


def _inputs(**kw):
    base = dict(
        cron="5 7-19 * * *",
        work_effort="high",
        review_effort="low",
        avg_session_minutes=30.0,
        max_passes=3,
    )
    base.update(kw)
    return ec.Inputs(**base)


def test_subscription_is_flat_regardless_of_cadence():
    sparse = ec.estimate(_inputs(cron="0 0 * * *"))
    dense = ec.estimate(_inputs(cron="*/15 * * * *"))
    assert sparse.subscription_monthly_usd == dense.subscription_monthly_usd
    assert sparse.subscription_monthly_usd == sum(ec.SUBSCRIPTION_PLANS_USD.values())


def test_metered_monthly_scales_with_runs():
    sparse = ec.estimate(_inputs(cron="0 0 * * *"))  # 1/day
    dense = ec.estimate(_inputs(cron="0 * * * *"))  # 24/day
    assert dense.runs_per_month == pytest.approx(sparse.runs_per_month * 24)
    assert dense.metered_monthly_usd[0] == pytest.approx(
        sparse.metered_monthly_usd[0] * 24
    )


def test_higher_work_effort_costs_more_per_run():
    low = ec.metered_cost_per_run(_inputs(work_effort="low"))
    high = ec.metered_cost_per_run(_inputs(work_effort="max"))
    assert high[0] > low[0]
    assert high[1] > low[1]


def test_more_passes_costs_more():
    one = ec.metered_cost_per_run(_inputs(max_passes=1))
    three = ec.metered_cost_per_run(_inputs(max_passes=3))
    assert three[0] > one[0]


def test_longer_session_costs_more():
    short = ec.metered_cost_per_run(_inputs(avg_session_minutes=10))
    long = ec.metered_cost_per_run(_inputs(avg_session_minutes=60))
    assert long[0] > short[0]


def test_range_low_below_high():
    run_lo, run_hi = ec.metered_cost_per_run(_inputs())
    assert run_lo < run_hi


def test_weekday_gating_reduces_monthly_runs():
    daily = ec.estimate(_inputs(cron="0 9-17 * * *"))
    weekdays = ec.estimate(_inputs(cron="0 9-17 * * 1-5"))
    assert weekdays.runs_per_month == pytest.approx(daily.runs_per_month * 5 / 7)


def test_invalid_effort_rejected():
    with pytest.raises(ValueError):
        ec.estimate(_inputs(work_effort="turbo"))


def test_nonpositive_session_rejected():
    with pytest.raises(ValueError):
        ec.estimate(_inputs(avg_session_minutes=0))


@pytest.mark.parametrize("days", [0, -3])
def test_nonpositive_days_per_month_rejected(days):
    # A zero or negative calendar would yield zero/negative runs and cost.
    with pytest.raises(ValueError, match="days_per_month"):
        ec.estimate(_inputs(days_per_month=days))


@pytest.mark.parametrize(
    "flag, value",
    [
        ("--max-passes", "0"),
        ("--avg-session-minutes", "0"),
        ("--days-per-month", "0"),
        ("--days-per-month", "-5"),
    ],
)
def test_cli_rejects_explicit_invalid_overrides(flag, value):
    # An explicit invalid override must be rejected (exit 2), not silently
    # swapped for the default because 0 is falsy.
    assert ec.main(["--cron", "0 * * * *", flag, value]) == 2


# --- config extraction + end to end ---------------------------------------


def test_inputs_from_config_reads_the_dials():
    cfg = {
        "schedule": {
            "wake": {"cron": "5 7-19 * * *"},
            "timeouts": {"hard_minutes": 90},
        },
        "model": {"work_effort": "high", "review_effort": "low"},
        "review": {"max_passes": 2},
    }
    got = ec.inputs_from_config(cfg)
    assert got["cron"] == "5 7-19 * * *"
    assert got["work_effort"] == "high"
    assert got["review_effort"] == "low"
    assert got["max_passes"] == 2
    assert got["hard_minutes"] == 90


def test_inputs_from_config_tolerates_missing_sections():
    assert ec.inputs_from_config({}) == {}


def test_inputs_from_config_preserves_explicit_zero_max_passes():
    # review.max_passes: 0 must survive as 0, not be dropped by a truthiness
    # check the way the CLI path used to drop --max-passes 0.
    assert ec.inputs_from_config({"review": {"max_passes": 0}})["max_passes"] == 0


def test_inputs_from_config_reads_review_enabled():
    assert (
        ec.inputs_from_config({"review": {"enabled": False}})["review_enabled"] is False
    )
    assert (
        ec.inputs_from_config({"review": {"enabled": True}})["review_enabled"] is True
    )
    # Absent enabled key defaults to on (handled downstream), so it's not emitted.
    assert "review_enabled" not in ec.inputs_from_config({"review": {}})


def test_inputs_from_config_nudge_off_disables_review():
    # nudges.review gates whether the wake prompt asks for review at all, so it
    # disables review the same way review.enabled does — even with enabled true.
    assert (
        ec.inputs_from_config({"nudges": {"review": False}})["review_enabled"] is False
    )
    assert (
        ec.inputs_from_config(
            {"review": {"enabled": True}, "nudges": {"review": False}}
        )["review_enabled"]
        is False
    )
    # Both switches explicitly on -> review on.
    assert (
        ec.inputs_from_config(
            {"review": {"enabled": True}, "nudges": {"review": True}}
        )["review_enabled"]
        is True
    )


def test_inputs_from_config_reads_wake_enabled():
    cfg = {"schedule": {"wake": {"cron": "5 7-19 * * *", "enabled": False}}}
    got = ec.inputs_from_config(cfg)
    assert got["wake_enabled"] is False
    assert got["cron"] == "5 7-19 * * *"
    # Absent enabled key defaults to on downstream, so it's not emitted.
    assert "wake_enabled" not in ec.inputs_from_config(
        {"schedule": {"wake": {"cron": "5 7-19 * * *"}}}
    )


def test_disabled_wake_zeroes_runs_and_monthly():
    on = ec.estimate(_inputs(wake_enabled=True))
    off = ec.estimate(_inputs(wake_enabled=False))
    assert on.runs_per_month > 0
    assert off.runs_per_month == 0
    assert off.metered_monthly_usd == (0.0, 0.0)
    # Per-run stays informational ("if you turned it on..."), so it's unchanged.
    assert off.metered_per_run_usd == on.metered_per_run_usd


def test_disabled_wake_skips_cron_restriction_refusal():
    # A disabled loop's cadence is moot, so an otherwise-unsupported cron does not
    # raise — it just reports zero runs.
    est = ec.estimate(_inputs(cron="0 9 1 * *", wake_enabled=False))
    assert est.runs_per_month == 0


def test_format_report_notes_disabled_schedule():
    inputs = _inputs(wake_enabled=False)
    report = ec.format_report(inputs, ec.estimate(inputs), source="flags")
    assert "schedule disabled" in report


def test_disabled_review_zeroes_review_cost():
    on = ec.metered_cost_per_run(_inputs(review_enabled=True))
    off = ec.metered_cost_per_run(_inputs(review_enabled=False))
    assert off[0] < on[0]
    assert off[1] < on[1]
    # With review off, max_passes is irrelevant — it bills no review tokens.
    assert ec.metered_cost_per_run(_inputs(review_enabled=False, max_passes=99)) == off


def test_disabled_review_allows_zero_max_passes():
    # max_passes 0 is moot when review is off, so estimate() accepts it; it's
    # rejected only when review is enabled.
    est = ec.estimate(_inputs(review_enabled=False, max_passes=0))
    assert est.metered_per_run_usd[0] > 0  # worker cost still present
    with pytest.raises(ValueError, match="max_passes"):
        ec.estimate(_inputs(review_enabled=True, max_passes=0))


def test_format_report_notes_disabled_review():
    inputs = _inputs(review_enabled=False)
    report = ec.format_report(inputs, ec.estimate(inputs), source="flags")
    assert "review disabled" in report


def test_example_config_round_trips_through_estimate():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "config.example.yaml")
    if not os.path.exists(path):  # pragma: no cover
        pytest.skip("config.example.yaml not present")
    pytest.importorskip("yaml")
    values = ec.inputs_from_config(ec.load_config(path))
    inputs = ec.Inputs(
        cron=values["cron"],
        work_effort=values.get("work_effort", "high"),
        review_effort=values.get("review_effort", "low"),
        avg_session_minutes=ec.DEFAULT_AVG_SESSION_MINUTES,
        max_passes=values.get("max_passes", ec.DEFAULT_MAX_PASSES),
    )
    est = ec.estimate(inputs)
    # The example cadence is "5 7-19 * * *" -> 13/day, matching COSTS.md.
    assert est.runs_per_active_day == 13
    assert est.runs_per_month == pytest.approx(13 * ec.DAYS_PER_MONTH)
    assert est.subscription_monthly_usd == sum(ec.SUBSCRIPTION_PLANS_USD.values())
    assert est.metered_monthly_usd[1] > est.metered_monthly_usd[0] > 0


def _write_config(tmp_path, cfg):
    yaml = pytest.importorskip("yaml")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return str(path)


def test_config_explicit_zero_max_passes_rejected(tmp_path):
    # The config path must reject review.max_passes: 0 too, not just the CLI.
    path = _write_config(
        tmp_path,
        {"schedule": {"wake": {"cron": "0 * * * *"}}, "review": {"max_passes": 0}},
    )
    assert ec.main([path]) == 2


def test_config_review_disabled_lowers_cost(tmp_path):
    # review.enabled: false flows through to a lower metered estimate.
    yaml = pytest.importorskip("yaml")
    base = {"schedule": {"wake": {"cron": "0 * * * *"}}}
    on_path = tmp_path / "on.yaml"
    on_path.write_text(yaml.safe_dump(base))
    off_path = tmp_path / "off.yaml"
    off_path.write_text(yaml.safe_dump({**base, "review": {"enabled": False}}))
    on, _ = ec.resolve_inputs(ec.build_parser().parse_args([str(on_path)]))
    off, _ = ec.resolve_inputs(ec.build_parser().parse_args([str(off_path)]))
    assert on.review_enabled is True
    assert off.review_enabled is False
    assert (
        ec.estimate(off).metered_per_run_usd[0] < ec.estimate(on).metered_per_run_usd[0]
    )


def test_disabled_wake_without_cron_reports_zero(tmp_path):
    # wake.enabled: false with no cron must NOT fail "no cadence given" — the
    # cadence is moot when the loop is off, so it estimates 0 runs.
    path = _write_config(tmp_path, {"schedule": {"wake": {"enabled": False}}})
    inputs, _ = ec.resolve_inputs(ec.build_parser().parse_args([path]))
    assert inputs.wake_enabled is False
    assert ec.estimate(inputs).runs_per_month == 0
    assert ec.main([path]) == 0  # prints a report, doesn't error


def test_enabled_wake_without_cron_still_errors(tmp_path):
    # An ENABLED loop with no cadence is still an error — the placeholder only
    # applies when the schedule is off.
    path = _write_config(tmp_path, {"schedule": {"wake": {"enabled": True}}})
    with pytest.raises(SystemExit):
        ec.resolve_inputs(ec.build_parser().parse_args([path]))


def test_hard_timeout_caps_average_session(tmp_path):
    # A 10-minute hard cap is tighter than the 30-minute default average, so it
    # pulls the assumed average down — the timeout dial has to do something.
    path = _write_config(
        tmp_path,
        {"schedule": {"wake": {"cron": "0 * * * *"}, "timeouts": {"hard_minutes": 10}}},
    )
    args = ec.build_parser().parse_args([path])
    inputs, _ = ec.resolve_inputs(args)
    assert inputs.avg_session_minutes == 10


def test_loose_hard_timeout_leaves_default_average(tmp_path):
    # A 90-minute cap is looser than the 30-minute default, so the default stands.
    path = _write_config(
        tmp_path,
        {"schedule": {"wake": {"cron": "0 * * * *"}, "timeouts": {"hard_minutes": 90}}},
    )
    args = ec.build_parser().parse_args([path])
    inputs, _ = ec.resolve_inputs(args)
    assert inputs.avg_session_minutes == ec.DEFAULT_AVG_SESSION_MINUTES


def test_explicit_avg_flag_overrides_hard_timeout(tmp_path):
    # An explicit --avg-session-minutes wins even over a tighter timeout.
    path = _write_config(
        tmp_path,
        {"schedule": {"wake": {"cron": "0 * * * *"}, "timeouts": {"hard_minutes": 5}}},
    )
    args = ec.build_parser().parse_args([path, "--avg-session-minutes", "45"])
    inputs, _ = ec.resolve_inputs(args)
    assert inputs.avg_session_minutes == 45


def test_tighter_timeout_lowers_metered_cost(tmp_path):
    # The wiring should be visible in the bill, not just the inputs.
    tight = _write_config(
        tmp_path,
        {"schedule": {"wake": {"cron": "0 * * * *"}, "timeouts": {"hard_minutes": 5}}},
    )
    tight_inputs, _ = ec.resolve_inputs(ec.build_parser().parse_args([tight]))
    default_inputs = ec.Inputs(
        cron="0 * * * *",
        work_effort=tight_inputs.work_effort,
        review_effort=tight_inputs.review_effort,
        avg_session_minutes=ec.DEFAULT_AVG_SESSION_MINUTES,
        max_passes=tight_inputs.max_passes,
    )
    tight_run = ec.metered_cost_per_run(tight_inputs)
    default_run = ec.metered_cost_per_run(default_inputs)
    assert tight_run[0] < default_run[0]
    assert tight_run[1] < default_run[1]


def test_format_report_shows_required_numbers():
    inputs = _inputs()
    est = ec.estimate(inputs)
    report = ec.format_report(inputs, est, source="flags")
    assert "runs/month" in report
    assert "Subscription billing" in report
    assert "Metered API billing" in report
    assert "Price assumptions" in report
