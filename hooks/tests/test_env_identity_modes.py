"""Issue254: inspect the identity used by the actual git operation."""
import pytest
from test_no_ai_attribution import run, assert_allowed, assert_blocked


@pytest.mark.parametrize("command", [
    "GIT_AUTHOR_NAME=Claude git commit --author='Jane Doe <jane@example.com>' -m Fix",
    "GIT_AUTHOR_NAME=Claude env -i git commit -m Fix",
    "GIT_AUTHOR_NAME=Claude env -i bash -c 'git commit -m Fix'",
    "GIT_AUTHOR_NAME=Claude GIT_COMMITTER_NAME=Claude git merge --abort",
    "GIT_AUTHOR_NAME=Claude GIT_COMMITTER_NAME=Claude git merge --quit",
    "GIT_AUTHOR_NAME=Claude git commit -C HEAD",
    "GIT_AUTHOR_NAME=Claude git commit -c HEAD",
    "GIT_AUTHOR_NAME=Claude git commit --amend --no-edit",
    "GIT_AUTHOR_NAME=Claude git commit --reuse-message=HEAD",
])
def test_unused_ambient_identity_is_allowed(command):
    assert_allowed(run(command))


@pytest.mark.parametrize("command", [
    "GIT_AUTHOR_NAME=Claude git commit -m Fix",
    "env -i GIT_AUTHOR_NAME=Claude git commit -m Fix",
    "env -i GIT_AUTHOR_NAME=Claude bash -c 'git commit -m Fix'",
    "GIT_COMMITTER_NAME=Claude git commit --author='Jane Doe <jane@example.com>' -m Fix",
    "GIT_COMMITTER_NAME=Claude git commit -C HEAD",
    "GIT_AUTHOR_NAME=Claude git commit -C HEAD --reset-author",
    "GIT_AUTHOR_NAME=Claude git merge topic",
])
def test_effective_tool_identity_remains_blocked(command):
    assert_blocked(run(command))


@pytest.mark.parametrize("command", [
    "EMAIL=claude@anthropic.com git commit --author='Jane Doe <jane@example.com>' -m Fix",
    "EMAIL=claude@anthropic.com git commit -C HEAD",
    "EMAIL=claude@anthropic.com git commit --amend --no-edit",
])
def test_email_fallback_is_always_checked_for_the_committer(command):
    assert_blocked(run(command))


@pytest.mark.parametrize("command", [
    "GIT_AUTHOR_NAME=Claude git commit -m --author",
    "GIT_AUTHOR_NAME=Claude git commit -m --dry-run",
    "GIT_AUTHOR_NAME=Claude git commit --date --author -m Fix",
    "GIT_COMMITTER_NAME=Claude git merge --no-ff -m --abort topic",
    "GIT_COMMITTER_NAME=Claude git merge --strategy --quit topic",
])
def test_option_values_are_not_treated_as_identity_modes(command):
    assert_blocked(run(command))


@pytest.mark.parametrize("command", [
    "GIT_AUTHOR_NAME=Claude git commit --amend --no-amend -m Fix",
    "GIT_COMMITTER_NAME=Claude git merge --abort --no-abort topic",
])
def test_negated_identity_modes_restore_normal_identity_checks(command):
    assert_blocked(run(command))


@pytest.mark.parametrize("command", [
    "GIT_AUTHOR_NAME=Claude git commit --no-amend --amend --no-edit",
    "GIT_AUTHOR_NAME=Claude git commit -C HEAD --reset-author --no-reset-author",
    "GIT_COMMITTER_NAME=Claude git commit --no-dry-run --dry-run -m Fix",
    "GIT_COMMITTER_NAME=Claude git merge --no-abort --abort",
])
def test_final_positive_identity_mode_still_allows_recovery(command):
    assert_allowed(run(command))


@pytest.mark.parametrize("command", [
    "GIT_AUTHOR_NAME=Claude git commit -C HEAD --no-reset-author --reset-author",
    "GIT_COMMITTER_NAME=Claude git commit --dry-run --no-dry-run -m Fix",
])
def test_final_identity_writing_mode_remains_blocked(command):
    assert_blocked(run(command))
