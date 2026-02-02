/**
 * Example: Bug reproduction test in JavaScript (Jest)
 *
 * Bug reported: "Array filter crashes when items have null properties"
 *
 * Expected: Filter should skip items with null properties gracefully
 * Actual: TypeError: Cannot read property 'name' of null
 */

// Assume this is the buggy code
// const { filterByName } = require('../src/utils');

// Mock the buggy function for demonstration
const filterByName = (items, searchTerm) => {
  // BUGGY: doesn't handle null items
  return items.filter((item) => item.name.toLowerCase().includes(searchTerm.toLowerCase()));
};

describe('filterByName - Bug reproduction', () => {
  /**
   * Bug: Function crashes when array contains null items
   * Issue: #456
   * Reported: 2026-02-01
   *
   * These tests should FAIL before the fix and PASS after.
   */

  describe('null handling bugs', () => {
    it('should not crash when array contains null items', () => {
      // Bug: TypeError on null item
      const items = [{ name: 'Alice' }, null, { name: 'Bob' }];

      // Should not throw
      expect(() => {
        filterByName(items, 'alice');
      }).not.toThrow();
    });

    it('should not crash when item.name is null', () => {
      // Bug: TypeError on null property
      const items = [{ name: 'Alice' }, { name: null }, { name: 'Bob' }];

      expect(() => {
        filterByName(items, 'alice');
      }).not.toThrow();
    });

    it('should not crash when item.name is undefined', () => {
      const items = [{ name: 'Alice' }, { id: 123 }, { name: 'Bob' }];

      expect(() => {
        filterByName(items, 'alice');
      }).not.toThrow();
    });

    it('should skip null items and return valid matches', () => {
      const items = [{ name: 'Alice' }, null, { name: 'Alicia' }, { name: 'Bob' }];

      const result = filterByName(items, 'ali');

      // Should find Alice and Alicia, skipping null
      expect(result).toHaveLength(2);
      expect(result.map((r) => r.name)).toEqual(['Alice', 'Alicia']);
    });
  });

  describe('empty input handling', () => {
    it('should handle empty array', () => {
      const result = filterByName([], 'test');

      expect(result).toEqual([]);
    });

    it('should handle empty search term', () => {
      const items = [{ name: 'Alice' }, { name: 'Bob' }];

      // Empty string should match all (or none, depending on intended behavior)
      const result = filterByName(items, '');

      expect(Array.isArray(result)).toBe(true);
    });
  });
});

describe('filterByName - Regression tests', () => {
  /**
   * Ensure the fix doesn't break normal functionality
   */

  it('should find items by partial name match', () => {
    const items = [{ name: 'Alice' }, { name: 'Bob' }, { name: 'Alicia' }];

    const result = filterByName(items, 'ali');

    expect(result).toHaveLength(2);
  });

  it('should be case-insensitive', () => {
    const items = [{ name: 'ALICE' }, { name: 'bob' }];

    const result = filterByName(items, 'alice');

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('ALICE');
  });

  it('should return empty array when no matches', () => {
    const items = [{ name: 'Alice' }, { name: 'Bob' }];

    const result = filterByName(items, 'Charlie');

    expect(result).toEqual([]);
  });
});

// Run with: npm test -- --grep "filterByName"
// Or: npx jest examples/js-bug-test.js
