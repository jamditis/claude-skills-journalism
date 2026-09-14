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
