#!/usr/bin/env bash
# Sequential test scanner — runs tests one-by-one until pollution is detected.
# Usage: ./find-polluter.sh <file_or_dir_to_check> <test_pattern>
# Example: ./find-polluter.sh '.git' 'src/**/*.test.ts'

set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 <file_to_check> <test_pattern>"
  echo "Example: $0 '.git' 'src/**/*.test.ts'"
  exit 1
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"

echo "🔍 Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo ""

# Get list of test files. Normalize the user-supplied pattern so it matches
# find's ./-prefixed output: strip a leading "./" or "/", collapse "**" to
# "*" (find's -path doesn't reliably treat ** as globstar), then prepend
# "*/" so the pattern matches paths like "./src/foo.test.ts".
NORMALIZED_PATTERN="${TEST_PATTERN#./}"
NORMALIZED_PATTERN="${NORMALIZED_PATTERN#/}"
NORMALIZED_PATTERN="${NORMALIZED_PATTERN//\*\*/\*}"
NORMALIZED_PATTERN="*/$NORMALIZED_PATTERN"

mapfile -t TEST_FILES < <(find . -type f -path "$NORMALIZED_PATTERN" 2>/dev/null | sort)
TOTAL=${#TEST_FILES[@]}

if [ "$TOTAL" -eq 0 ]; then
  echo "❌ No test files matched pattern: $TEST_PATTERN"
  echo "   (find -path tried: $NORMALIZED_PATTERN)"
  exit 1
fi

echo "Found $TOTAL test files"
echo ""

COUNT=0
for TEST_FILE in "${TEST_FILES[@]}"; do
  COUNT=$((COUNT + 1))

  # Skip if pollution already exists
  if [ -e "$POLLUTION_CHECK" ]; then
    echo "⚠️  Pollution already exists before test $COUNT/$TOTAL"
    echo "   Skipping: $TEST_FILE"
    continue
  fi

  echo "[$COUNT/$TOTAL] Testing: $TEST_FILE"

  # Run the test
  npm test "$TEST_FILE" > /dev/null 2>&1 || true

  # Check if pollution appeared
  if [ -e "$POLLUTION_CHECK" ]; then
    echo ""
    echo "🎯 FOUND POLLUTER!"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    echo ""
    echo "Pollution details:"
    ls -la "$POLLUTION_CHECK"
    echo ""
    echo "To investigate:"
    echo "  npm test $TEST_FILE    # Run just this test"
    echo "  cat $TEST_FILE         # Review test code"
    exit 1
  fi
done

echo ""
echo "✅ No polluter found - all tests clean!"
exit 0
