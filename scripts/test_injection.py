#!/usr/bin/env python3
"""
PSA Injection Vulnerability Tests
Tests text_engine.py TextAnonymizer against various attack vectors
to verify PII is properly anonymized even with adversarial input.
"""

import sys
import os
import time

# Ensure scripts/ is on the path so we can import text_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_engine import TextAnonymizer

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

results = []


def check(test_name: str, anonymized: str, must_not_contain: list, original: str = ""):
    """
    PASS if none of the must_not_contain strings survive in the output.
    FAIL if any of them remain verbatim.
    """
    escaped = []
    for token in must_not_contain:
        if token in anonymized:
            escaped.append(token)

    if escaped:
        print(f"FAIL  {test_name}")
        for t in escaped:
            print(f"       PII survived: {repr(t)}")
        results.append(False)
    else:
        print(f"PASS  {test_name}")
        results.append(True)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_null_bytes():
    """1. Null bytes embedded in text."""
    engine = TextAnonymizer()
    text = "Jo\x00\u00e3o da Silva CPF 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "Null bytes: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )
    # Also verify the name part -- note: null byte may break name regex
    # We check whether the original CPF leaked; that is the critical PII.


def test_fullwidth_unicode():
    """2a. Fullwidth Latin characters (U+FF10..U+FF5A)."""
    engine = TextAnonymizer()
    # Fullwidth "Joao da Silva" -- these are NOT standard ASCII/Latin letters
    text = "\uff2a\uff4f\uff41\uff4f da Silva CPF 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "Fullwidth Unicode: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )


def test_zero_width_spaces():
    """2b. Zero-width spaces inserted inside name and CPF."""
    engine = TextAnonymizer()
    # Zero-width space (U+200B) in the name
    text = "Jo\u00e3o\u200Bda\u200BSilva CPF 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "Zero-width spaces: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )


def test_zero_width_in_cpf():
    """2c. Zero-width spaces inside the CPF digits themselves."""
    engine = TextAnonymizer()
    text = "Jo\u00e3o da Silva CPF 123.456\u200B.789-00"
    out = engine.anonymize(text)
    # The CPF regex expects digits and separators -- a ZWSP may cause it to NOT match.
    # If the CPF survives, that is a vulnerability.
    check(
        "Zero-width spaces inside CPF: CPF anonymized",
        out,
        ["123.456"],  # partial check: at least the leading digits should be gone
        text,
    )


def test_very_long_string():
    """3. Very long string with PII at the end."""
    engine = TextAnonymizer()
    text = "A" * 1_000_000 + " CPF 123.456.789-00"
    start = time.time()
    out = engine.anonymize(text)
    elapsed = time.time() - start
    check(
        "Very long string (1M chars): CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )
    # Also report timing -- if > 30s, it's a practical DoS vector
    if elapsed > 30:
        print(f"FAIL  Very long string: took {elapsed:.1f}s (DoS risk)")
        results.append(False)
    else:
        print(f"PASS  Very long string: completed in {elapsed:.1f}s")
        results.append(True)


def test_newline_injection():
    """4. Newline splitting name from CPF."""
    engine = TextAnonymizer()
    text = "Nome: Jo\u00e3o da Silva\nCPF: 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "Newline injection: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )
    check(
        "Newline injection: name anonymized",
        out,
        ["Jo\u00e3o da Silva"],
        text,
    )


def test_rtl_override():
    """5. RTL override characters wrapping name."""
    engine = TextAnonymizer()
    text = "\u202eJo\u00e3o da Silva\u202c CPF 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "RTL override: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )


def test_html_entities():
    """6. HTML entities in plain text (not decoded)."""
    engine = TextAnonymizer()
    text = "Jo&atilde;o da Silva CPF 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "HTML entities: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )
    # The name with HTML entity likely won't match the name regex.
    # Check if the raw "Jo&atilde;o da Silva" survives -- that would be a leak.
    # This is informational: the name regex expects real letters, not HTML entities.
    has_name = "Jo&atilde;o da Silva" in out
    if has_name:
        print(f"WARN  HTML entities: name with entity survived (regex miss)")
    else:
        print(f"PASS  HTML entities: name portion handled")


def test_bom_marker():
    """7. BOM (Byte Order Mark) at start of content."""
    engine = TextAnonymizer()
    text = "\ufeffJo\u00e3o da Silva CPF 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "BOM marker: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )
    check(
        "BOM marker: name anonymized",
        out,
        ["Jo\u00e3o da Silva"],
        text,
    )


def test_sql_injection_in_values():
    """8. SQL-like injection payload alongside PII."""
    engine = TextAnonymizer()
    text = "'; DROP TABLE users; -- Jo\u00e3o da Silva CPF 123.456.789-00"
    out = engine.anonymize(text)
    check(
        "SQL injection payload: CPF anonymized",
        out,
        ["123.456.789-00"],
        text,
    )
    check(
        "SQL injection payload: name anonymized",
        out,
        ["Jo\u00e3o da Silva"],
        text,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print("PSA Injection Vulnerability Tests -- text_engine.py")
    print("=" * 65)
    print()

    test_null_bytes()
    print()
    test_fullwidth_unicode()
    print()
    test_zero_width_spaces()
    print()
    test_zero_width_in_cpf()
    print()
    test_very_long_string()
    print()
    test_newline_injection()
    print()
    test_rtl_override()
    print()
    test_html_entities()
    print()
    test_bom_marker()
    print()
    test_sql_injection_in_values()
    print()

    # Summary
    total = len(results)
    passed = sum(results)
    failed = total - passed
    print("=" * 65)
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 65)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
