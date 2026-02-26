# Test framework patterns

Quick reference for writing bug reproduction tests in common frameworks.

## Python

### pytest (recommended)

```python
# tests/test_module.py
import pytest
from myapp.module import function_under_test

def test_bug_description():
    """
    Bug: [describe the bug]
    Expected: [expected behavior]
    Actual: [actual buggy behavior]
    """
    # Arrange
    input_data = "problematic input"

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_value

# For exceptions
def test_should_not_crash_on_bad_input():
    with pytest.raises(ValueError, match="expected error"):
        function_under_test(bad_input)

# For async
@pytest.mark.asyncio
async def test_async_bug():
    result = await async_function()
    assert result is not None

# Parametrized for multiple cases
@pytest.mark.parametrize("input,expected", [
    ("case1", "result1"),
    ("case2", "result2"),
])
def test_multiple_cases(input, expected):
    assert function_under_test(input) == expected
```

**Run commands:**
```bash
pytest tests/test_module.py::test_bug_description -v
pytest tests/test_module.py -v  # All tests in file
pytest -x  # Stop on first failure
pytest --tb=short  # Shorter tracebacks
```

### unittest

```python
import unittest
from myapp.module import function_under_test

class TestBugFix(unittest.TestCase):
    def test_bug_description(self):
        """Bug: [description]"""
        result = function_under_test("input")
        self.assertEqual(result, expected)

    def test_should_raise_on_invalid(self):
        with self.assertRaises(ValueError):
            function_under_test(None)
```

**Run commands:**
```bash
python -m unittest tests.test_module.TestBugFix.test_bug_description
python -m unittest discover tests/
```

## JavaScript / TypeScript

### Jest

```javascript
// __tests__/module.test.js
const { functionUnderTest } = require('../src/module');

describe('Module', () => {
  describe('functionUnderTest', () => {
    it('should handle edge case without crashing', () => {
      // Bug: crashes on empty input
      const result = functionUnderTest('');

      expect(result).toBeDefined();
      expect(result.error).toBeNull();
    });

    it('should throw on invalid input', () => {
      expect(() => {
        functionUnderTest(null);
      }).toThrow('Invalid input');
    });
  });
});

// Async
it('should fetch data correctly', async () => {
  const result = await asyncFunction();
  expect(result.data).toHaveLength(3);
});

// With mocks
jest.mock('../src/api');
it('should handle API error', async () => {
  api.fetch.mockRejectedValue(new Error('Network error'));

  const result = await functionUnderTest();

  expect(result.error).toBe('Network error');
});
```

**Run commands:**
```bash
npm test -- --grep "should handle edge case"
npm test -- __tests__/module.test.js
npm test -- --watch  # Watch mode
```

### Vitest

```typescript
// src/module.test.ts
import { describe, it, expect, vi } from 'vitest';
import { functionUnderTest } from './module';

describe('functionUnderTest', () => {
  it('handles empty array without crashing', () => {
    // Bug: TypeError when array is empty
    const result = functionUnderTest([]);

    expect(result).toEqual([]);
  });
});
```

**Run commands:**
```bash
npx vitest run src/module.test.ts
npx vitest --reporter=verbose
```

### Mocha + Chai

```javascript
const { expect } = require('chai');
const { functionUnderTest } = require('../src/module');

describe('Module', function() {
  it('should handle special characters', function() {
    const result = functionUnderTest('test@#$%');
    expect(result).to.be.a('string');
    expect(result).to.not.include('undefined');
  });
});
```

## Go

```go
// module_test.go
package mypackage

import (
    "testing"
)

func TestBugDescription(t *testing.T) {
    // Bug: function panics on nil input
    result, err := FunctionUnderTest(nil)

    if err == nil {
        t.Error("expected error for nil input")
    }
    if result != nil {
        t.Errorf("expected nil result, got %v", result)
    }
}

// Table-driven tests
func TestMultipleCases(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"empty string", "", "default"},
        {"special chars", "@#$", "sanitized"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := FunctionUnderTest(tt.input)
            if result != tt.expected {
                t.Errorf("got %s, want %s", result, tt.expected)
            }
        })
    }
}
```

**Run commands:**
```bash
go test -v -run TestBugDescription
go test ./... -v
go test -race ./...  # Check for race conditions
```

## Rust

```rust
// src/module.rs or tests/module_test.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bug_description() {
        // Bug: panics on empty vec
        let result = function_under_test(vec![]);

        assert!(result.is_ok());
        assert_eq!(result.unwrap(), expected);
    }

    #[test]
    #[should_panic(expected = "invalid input")]
    fn test_panics_on_invalid() {
        function_under_test(invalid_input);
    }
}
```

**Run commands:**
```bash
cargo test test_bug_description -- --nocapture
cargo test -- --test-threads=1
```

## Ruby (RSpec)

```ruby
# spec/module_spec.rb
require 'module'

RSpec.describe Module do
  describe '#function_under_test' do
    it 'handles nil input without crashing' do
      # Bug: NoMethodError on nil
      result = described_class.function_under_test(nil)

      expect(result).to be_nil
    end

    it 'raises ArgumentError for invalid type' do
      expect {
        described_class.function_under_test(123)
      }.to raise_error(ArgumentError, /expected string/)
    end
  end
end
```

**Run commands:**
```bash
rspec spec/module_spec.rb:10  # Line number
rspec --example "handles nil"
```

## PHP (PHPUnit)

```php
<?php
// tests/ModuleTest.php
use PHPUnit\Framework\TestCase;

class ModuleTest extends TestCase
{
    public function testBugDescription(): void
    {
        // Bug: returns null instead of empty array
        $result = functionUnderTest([]);

        $this->assertIsArray($result);
        $this->assertEmpty($result);
    }

    public function testThrowsOnInvalid(): void
    {
        $this->expectException(InvalidArgumentException::class);
        functionUnderTest(null);
    }
}
```

**Run commands:**
```bash
./vendor/bin/phpunit --filter testBugDescription
./vendor/bin/phpunit tests/ModuleTest.php
```
