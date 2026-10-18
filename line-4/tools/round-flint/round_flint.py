#!/usr/bin/env python3
"""Check a decimal display after exact dimensional conversion and rounding."""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import re
import sys

from engine import Parser, Quantity, UnitError, dimensions, exact_decimal


MODES = ("half-even", "half-away", "toward-zero", "floor", "ceiling")
MAX_PLACES = 18
MAX_CLAIM = 700


def rounded_integer(value: Fraction, mode: str) -> tuple[int, bool]:
    """Round a scaled rational; the flag identifies an exact halfway case."""
    if mode not in MODES:
        raise ValueError("unknown rounding mode")
    whole, remainder = divmod(abs(value.numerator), value.denominator)
    sign = -1 if value < 0 else 1
    halfway = 2 * remainder == value.denominator
    if mode == "floor":
        return value.numerator // value.denominator, halfway
    if mode == "ceiling":
        return -((-value.numerator) // value.denominator), halfway
    increment = False
    if mode in ("half-even", "half-away"):
        increment = (2 * remainder > value.denominator or
                     (halfway and (mode == "half-away" or whole % 2 == 1)))
    return sign * (whole + increment), halfway


def fixed_decimal(integer: int, places: int) -> str:
    digits = str(abs(integer)).zfill(places + 1)
    display = digits if places == 0 else digits[:-places] + "." + digits[-places:]
    return ("-" if integer < 0 else "") + display


def calculate(expression: str, target: str, places: int = 2,
              mode: str = "half-even", expect: str | None = None) -> dict:
    if type(places) is not int or not 0 <= places <= MAX_PLACES:
        raise ValueError(f"places must be an integer in 0..{MAX_PLACES}")
    if mode not in MODES:
        raise ValueError("unknown rounding mode")
    if not isinstance(expression, str) or not isinstance(target, str):
        raise ValueError("expression and target must be strings")
    result = Parser(expression).parse()
    unit = Parser(target, target=True).parse()
    if unit.value <= 0:
        raise ValueError("target must have a positive scale")
    if unit.dims != result.dims:
        raise ValueError("target dimensions do not match result dimensions")
    value = Parser.bounded(Quantity(result.value / unit.value, result.dims), 0).value
    scale = 10 ** places
    # Apply the inherited exact arithmetic budget to new intermediates too.
    scaled = Parser.bounded(Quantity(value * scale, result.dims), 0).value
    integer, halfway = rounded_integer(scaled, mode)
    displayed = Fraction(integer, scale)
    error = Parser.bounded(Quantity(displayed - value, result.dims), 0).value
    error_base = Parser.bounded(Quantity(error * unit.value, result.dims), 0).value
    output = {
        "schema": "round-flint/v1",
        "expression": expression,
        "unit": target,
        "base_unit": dimensions(result.dims),
        "exact_value": exact_decimal(value),
        "places": places,
        "mode": mode,
        "rounded": fixed_decimal(integer, places),
        "quantum": exact_decimal(Fraction(1, scale)),
        "halfway": halfway,
        "error": exact_decimal(error),
        "error_base_value": exact_decimal(error_base),
    }
    if expect is not None:
        # A display claim is deliberately narrower than an expression. Precision
        # is part of the claim, so 1.2 is not a two-decimal display of 1.20.
        if not isinstance(expect, str) or len(expect) > MAX_CLAIM:
            raise ValueError("claim must be a decimal string of at most 700 characters")
        pattern = r"-?(?:0|[1-9][0-9]*)"
        if places:
            pattern += r"\.[0-9]{" + str(places) + "}"
        if re.fullmatch(pattern, expect, flags=re.ASCII) is None:
            raise ValueError("claim must be a plain decimal with exactly the requested places")
        if expect.startswith("-") and Fraction(expect) == 0:
            raise ValueError("negative zero is not a canonical display claim")
        output["check"] = {"claim": expect, "matches": expect == output["rounded"]}
    return output


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("expression")
    cli.add_argument("--to", required=True, metavar="UNIT")
    cli.add_argument("--places", type=int, default=2)
    cli.add_argument("--mode", choices=MODES, default="half-even")
    cli.add_argument("--expect", help="decimal display claim in the target unit")
    args = cli.parse_args(argv)
    try:
        output = calculate(args.expression, args.to, args.places, args.mode, args.expect)
    except (ValueError, UnitError) as exc:
        print(f"round-flint: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 1 if "check" in output and not output["check"]["matches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
