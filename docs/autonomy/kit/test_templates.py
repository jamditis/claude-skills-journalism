"""Static checks for the scheduler templates.

The macOS and Windows recipes cannot be run end to end on the Linux box this kit
was built on (issue #104), but the templates are still text files with structure
that must hold before anyone spends real Mac or Windows time on them. These
checks run anywhere Python does and catch the failure modes that would otherwise
only surface on the target OS:

- the launchd plist must be well-formed and carry the keys launchd needs;
- the Task Scheduler script must use the documented registration form, keep its
  self-bounding timeout wrapper, and embed a well-formed, correctly ordered Task
  XML (the XSD rejects out-of-order trigger children).

They do not replace the hardware run #104 asks for; they keep the templates from
regressing before that run happens.
"""

import plistlib
import re
import xml.dom.minidom
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

TEMPLATES = Path(__file__).parent / "templates"
PLIST = TEMPLATES / "launchd.plist.example"
PS1 = TEMPLATES / "task-scheduler.ps1.example"


def test_launchd_plist_is_well_formed_xml():
    # Catches the class of defect that "--" inside an XML comment is: strict
    # parsers (expat, libxml2) reject the whole document. A raw DOM parse is the
    # spec-conformant check; plistlib below is the semantic one.
    xml.dom.minidom.parse(str(PLIST))


def test_launchd_plist_parses_and_has_required_keys():
    data = plistlib.loads(PLIST.read_bytes())
    for key in ("Label", "ProgramArguments", "StartCalendarInterval"):
        assert key in data, f"launchd plist is missing {key}"
    assert data["Label"], "Label must be non-empty"
    assert isinstance(data["ProgramArguments"], list) and data["ProgramArguments"]


def test_launchd_schedule_is_a_nonempty_list_of_hourly_dicts():
    data = plistlib.loads(PLIST.read_bytes())
    schedule = data["StartCalendarInterval"]
    assert isinstance(schedule, list) and schedule, "StartCalendarInterval must be a non-empty array"
    for entry in schedule:
        assert isinstance(entry, dict) and "Hour" in entry


def _ps1_text():
    return PS1.read_text()


def test_tasksched_uses_documented_xml_registration_form():
    text = _ps1_text()
    assert "Register-ScheduledTask" in text
    assert "-Xml" in text, "registration must use the documented Register-ScheduledTask -Xml form"


def test_tasksched_avoids_the_undocumented_repetition_idiom():
    # The template's comment explains why the old idiom is wrong, so plain
    # ".Repetition" appears in prose. What must not appear is an actual
    # assignment onto a trigger object ($trigger.Repetition = ...), the pattern
    # observed not to repeat for daily triggers.
    text = _ps1_text()
    assert not re.search(r"\$\w+\.Repetition\s*=", text), (
        "found a .Repetition assignment; use the documented -Xml <Repetition> form instead"
    )


def test_tasksched_keeps_the_self_bounding_timeout_wrapper():
    # Windows has no `timeout --foreground`, so the wake bounds itself with a
    # job plus a kill timer that re-raises a bad exit (issue #104, PR #109).
    text = _ps1_text()
    for marker in ("Start-Job", "Wait-Job", "Stop-Job", "throw"):
        assert marker in text, f"timeout wrapper is missing {marker}"


def _localname(tag):
    return tag.rsplit("}", 1)[-1]


def _embedded_task_xml():
    """Return the Task XML from the PowerShell here-string ($xml = @" ... "@)."""
    match = re.search(r'@"\r?\n(.*?)\r?\n"@', _ps1_text(), re.DOTALL)
    assert match, "could not find the $xml here-string in the template"
    return match.group(1)


def _embedded_task_root():
    """Parse the embedded Task XML and return its root element.

    ElementTree rejects a unicode string that carries an encoding declaration,
    so parse the document body without the prolog; structure is what matters.
    """
    body = _embedded_task_xml()
    body_without_prolog = re.sub(r"^\s*<\?xml.*?\?>", "", body, count=1, flags=re.DOTALL)
    return ET.fromstring(body_without_prolog)


def test_embedded_task_xml_is_well_formed():
    body = _embedded_task_xml()
    assert body.lstrip().startswith("<?xml"), "Task XML should keep its declaration"
    _embedded_task_root()  # raises if the body is not well-formed


def test_embedded_task_xml_trigger_children_are_in_xsd_order():
    # The Task Scheduler XSD fixes the CalendarTrigger child order; out-of-order
    # children make Register-ScheduledTask reject the whole task. The template's
    # own comment pins this order, so pin it in a test too.
    root = _embedded_task_root()

    trigger = next(
        (el for el in root.iter() if _localname(el.tag) == "CalendarTrigger"), None
    )
    assert trigger is not None, "no CalendarTrigger in the embedded Task XML"
    order = [_localname(child.tag) for child in trigger]
    assert order == ["Enabled", "StartBoundary", "Repetition", "ScheduleByDay"], (
        f"CalendarTrigger children out of XSD order: {order}"
    )


def test_embedded_task_xml_action_context_names_a_defined_principal():
    # The template warns that Actions Context must name a defined Principal id,
    # or Register-ScheduledTask rejects the task (task-scheduler.ps1.example
    # documents this next to the trigger-order rule). Guard it the same way:
    # an unmatched Context is a silent, Windows-only failure otherwise.
    root = _embedded_task_root()

    principal_ids = {
        el.get("id")
        for el in root.iter()
        if _localname(el.tag) == "Principal" and el.get("id")
    }
    contexts = [
        el.get("Context")
        for el in root.iter()
        if _localname(el.tag) == "Actions" and el.get("Context")
    ]
    assert contexts, "the Actions element should name a Context"
    for context in contexts:
        assert context in principal_ids, (
            f"Actions Context {context!r} names no defined Principal id {sorted(principal_ids)}"
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
