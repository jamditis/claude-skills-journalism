#!/bin/bash
# Find test infrastructure in a project
# Usage: ./find-tests.sh [directory]

DIR="${1:-.}"

echo "=== Test Infrastructure Discovery ==="
echo "Scanning: $DIR"
echo ""

# Find test directories
echo "📁 Test directories:"
find "$DIR" -type d \( -name "tests" -o -name "test" -o -name "__tests__" -o -name "spec" \) 2>/dev/null | grep -v node_modules | grep -v venv | head -10
echo ""

# Find test files by pattern
echo "📄 Test files (sample):"
find "$DIR" \( \
  -name "test_*.py" -o \
  -name "*_test.py" -o \
  -name "*.test.js" -o \
  -name "*.test.ts" -o \
  -name "*.test.jsx" -o \
  -name "*.test.tsx" -o \
  -name "*.spec.js" -o \
  -name "*.spec.ts" -o \
  -name "*_test.go" \
\) 2>/dev/null | grep -v node_modules | grep -v venv | head -20
echo ""

# Check for test config files
echo "⚙️ Test configuration:"
for config in pytest.ini pyproject.toml setup.cfg jest.config.js jest.config.ts vitest.config.js vitest.config.ts .mocharc.js .mocharc.json karma.conf.js; do
  if [ -f "$DIR/$config" ]; then
    echo "  ✓ $config"
  fi
done
echo ""

# Check package.json for test scripts
if [ -f "$DIR/package.json" ]; then
  echo "📦 npm test scripts:"
  grep -A5 '"scripts"' "$DIR/package.json" | grep -E '"test|"jest|"vitest|"mocha' | head -5
  echo ""
fi

# Check for test dependencies
if [ -f "$DIR/package.json" ]; then
  echo "📦 Test dependencies:"
  grep -E '"jest"|"vitest"|"mocha"|"chai"|"@testing-library"' "$DIR/package.json" | head -5
fi

if [ -f "$DIR/requirements.txt" ]; then
  echo "🐍 Python test dependencies:"
  grep -E "^pytest|^unittest|^nose" "$DIR/requirements.txt"
fi

if [ -f "$DIR/pyproject.toml" ]; then
  echo "🐍 Python test dependencies (pyproject.toml):"
  grep -E "pytest|unittest" "$DIR/pyproject.toml" | head -5
fi

echo ""
echo "=== Suggested test command ==="

# Suggest test command based on what was found
if [ -f "$DIR/package.json" ] && grep -q '"test"' "$DIR/package.json"; then
  echo "npm test"
elif [ -f "$DIR/pytest.ini" ] || [ -f "$DIR/pyproject.toml" ]; then
  echo "pytest"
elif find "$DIR" -name "*_test.go" 2>/dev/null | grep -q .; then
  echo "go test ./..."
else
  echo "Could not determine test command. Check project documentation."
fi
