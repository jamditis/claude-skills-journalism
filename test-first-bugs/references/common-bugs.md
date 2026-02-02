# Common bug patterns and test strategies

## Null / None / Undefined handling

**Symptoms:** TypeError, NullPointerException, "undefined is not a function"

**Test strategy:**
```python
def test_handles_none_input():
    result = function(None)
    assert result is not None  # or appropriate default

def test_handles_missing_key():
    data = {}  # Missing expected key
    result = function(data)
    assert result == default_value
```

**Common fixes:**
- Add null checks at function entry
- Use optional chaining (`?.` in JS/TS)
- Provide default values
- Use `get()` with defaults for dict/object access

## Off-by-one errors

**Symptoms:** IndexError, missing first/last item, extra iteration

**Test strategy:**
```python
def test_first_element():
    result = function([1, 2, 3])
    assert result[0] == 1  # Verify first element handled

def test_last_element():
    result = function([1, 2, 3])
    assert result[-1] == 3  # Verify last element handled

def test_single_element():
    result = function([1])
    assert len(result) == 1

def test_empty_collection():
    result = function([])
    assert result == []
```

## String encoding issues

**Symptoms:** UnicodeDecodeError, garbled text, "?" characters

**Test strategy:**
```python
def test_handles_unicode():
    result = function("café ñ 日本語")
    assert "café" in result

def test_handles_emoji():
    result = function("Hello 👋 World")
    assert "👋" in result

def test_handles_special_chars():
    result = function("test@#$%^&*()")
    assert result is not None
```

## Race conditions

**Symptoms:** Intermittent failures, data corruption, deadlocks

**Test strategy:**
```python
import threading
import concurrent.futures

def test_concurrent_access():
    results = []

    def worker():
        results.append(function())

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert all(r is not None for r in results)
```

## Date/time bugs

**Symptoms:** Wrong timezone, off-by-one day, DST issues

**Test strategy:**
```python
from datetime import datetime, timezone
import freezegun  # or time-machine

@freezegun.freeze_time("2024-03-10 02:30:00")  # DST transition
def test_handles_dst_transition():
    result = function()
    assert result.hour in (2, 3)  # Depends on expected behavior

def test_handles_timezone():
    utc_time = datetime.now(timezone.utc)
    result = function(utc_time)
    # Verify timezone preserved or converted correctly

def test_handles_leap_year():
    date = datetime(2024, 2, 29)  # Leap year
    result = function(date)
    assert result is not None
```

## Floating point precision

**Symptoms:** 0.1 + 0.2 != 0.3, comparison failures

**Test strategy:**
```python
import math

def test_float_calculation():
    result = function(0.1, 0.2)
    assert math.isclose(result, 0.3, rel_tol=1e-9)

def test_currency_calculation():
    # Use Decimal for money
    from decimal import Decimal
    result = function(Decimal("10.99"), Decimal("5.01"))
    assert result == Decimal("16.00")
```

## Memory leaks / resource exhaustion

**Symptoms:** OOM errors, file handle exhaustion, slow degradation

**Test strategy:**
```python
import tracemalloc

def test_no_memory_leak():
    tracemalloc.start()

    for _ in range(1000):
        function()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < 100_000_000  # 100MB threshold

def test_file_handles_closed():
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    for _ in range(100):
        function()

    # Should not leak file descriptors
```

## SQL injection / input validation

**Symptoms:** Security vulnerability, unexpected query results

**Test strategy:**
```python
def test_sql_injection_attempt():
    malicious_input = "'; DROP TABLE users; --"
    result = function(malicious_input)
    # Should sanitize or reject, not execute
    assert "DROP" not in str(result)

def test_xss_attempt():
    malicious_input = "<script>alert('xss')</script>"
    result = function(malicious_input)
    assert "<script>" not in result
```

## Async / Promise handling

**Symptoms:** Unhandled promise rejection, callback not called

**Test strategy:**
```javascript
it('handles async error correctly', async () => {
  // Bug: unhandled rejection
  await expect(asyncFunction()).rejects.toThrow('Expected error');
});

it('resolves within timeout', async () => {
  const result = await Promise.race([
    asyncFunction(),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), 5000)
    )
  ]);
  expect(result).toBeDefined();
});
```

## State mutation bugs

**Symptoms:** Unexpected side effects, stale data, wrong order

**Test strategy:**
```python
def test_does_not_mutate_input():
    original = [1, 2, 3]
    input_copy = original.copy()

    function(original)

    assert original == input_copy  # Input unchanged

def test_returns_new_object():
    obj = {"key": "value"}
    result = function(obj)

    assert result is not obj  # Different object
    assert result == expected
```

## Configuration / environment bugs

**Symptoms:** Works locally, fails in production

**Test strategy:**
```python
import os
from unittest.mock import patch

def test_handles_missing_env_var():
    with patch.dict(os.environ, {}, clear=True):
        result = function()
        assert result == default_value

def test_handles_different_env():
    with patch.dict(os.environ, {"ENV": "production"}):
        result = function()
        # Verify production behavior
```

## Error message preservation

**Symptoms:** Generic error, lost context, unhelpful message

**Test strategy:**
```python
def test_error_includes_context():
    try:
        function(bad_input)
        assert False, "Should have raised"
    except CustomError as e:
        assert "bad_input" in str(e)
        assert e.original_error is not None
```

## Pagination / limit bugs

**Symptoms:** Missing items, duplicates, infinite loop

**Test strategy:**
```python
def test_pagination_no_duplicates():
    all_results = []
    page = 1
    while True:
        results = function(page=page, limit=10)
        if not results:
            break
        all_results.extend(results)
        page += 1

    # No duplicates
    assert len(all_results) == len(set(r.id for r in all_results))

def test_large_offset():
    result = function(page=10000, limit=10)
    assert isinstance(result, list)  # Should not error
```
