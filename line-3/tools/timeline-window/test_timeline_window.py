"""Focused offline checks for verified half-open incident windows."""

import unittest

import replay
import timeline_window as window


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.pack = replay.make_pack([
            ("front.log", b"2026-10-18T10:00:00Z begin\n2026-10-18T10:00:02Z accepted\nundated diagnostic\n"),
            ("back.log", b"2026-10-18T10:00:04Z done\n"),
        ], ignore_unmatched=True, clock_uncertainty_ms=250)

    def test_possible_overlap_and_explicit_omission(self):
        result = window.inspect(self.pack, "2026-10-18T10:00:02Z", "2026-10-18T10:00:04Z")
        self.assertEqual(result["counts"]["possible_overlap"], 2)
        self.assertEqual(result["counts"]["contained"], 0)
        self.assertEqual(result["counts"]["outside"], 1)
        self.assertEqual(result["counts"]["omitted_lines_total"], 1)
        self.assertEqual([item["event"]["source"] for item in result["events"]],
                         ["front.log", "back.log"])

    def test_half_open_endpoint_and_precision(self):
        pack = replay.make_pack([("x", b"2026-10-18T10:00:00Z first\n2026-10-18T10:00:01Z second\n")])
        result = window.inspect(pack, "2026-10-18T10:00:01Z", "2026-10-18T10:00:02Z")
        self.assertEqual(result["counts"]["matching"], 1)
        self.assertEqual(result["events"][0]["event"]["line"], 2)
        self.assertEqual(result["events"][0]["classification"], "contained")

    def test_limit_never_hides_totals(self):
        result = window.inspect(self.pack, "2026-10-18T10:00:02Z", "2026-10-18T10:00:04Z", 0)
        self.assertEqual(result["counts"]["matching"], 2)
        self.assertEqual(result["counts"]["not_shown"], 2)
        self.assertEqual(result["counts"]["omitted_lines_not_shown"], 1)
        self.assertEqual(result["events"], [])

    def test_tampered_pack_rejected_before_query(self):
        self.pack["timeline"]["events"][0]["message"] = "fabricated"
        with self.assertRaises(replay.ReplayError):
            window.inspect(self.pack, "2026-10-18T10:00:00Z", "2026-10-18T10:00:10Z")

    def test_bad_boundaries_and_limit(self):
        for start, end in [("2026-10-18T10:00:02Z", "2026-10-18T10:00:02Z"),
                           ("2026-10-18T10:00:02", "2026-10-18T10:00:04Z"),
                           ("2026-10-18T10:00:02+24:00", "2026-10-18T10:00:04Z")]:
            with self.subTest(start=start):
                with self.assertRaises(replay.ReplayError):
                    window.inspect(self.pack, start, end)
        with self.assertRaises(replay.ReplayError):
            window.inspect(self.pack, "2026-10-18T10:00:02Z", "2026-10-18T10:00:04Z", 201)

    def test_offset_boundaries_normalize(self):
        result = window.inspect(self.pack, "2026-10-18T12:00:02+02:00", "2026-10-18T12:00:04+02:00")
        self.assertEqual(result["query"]["start_utc_inclusive"], "2026-10-18T10:00:02Z")
        self.assertEqual(result["counts"]["matching"], 2)


    def test_filters_preserve_citations_and_accounting(self):
        import copy
        before = copy.deepcopy(self.pack)
        result = window.inspect(self.pack, "2026-10-18T10:00:02Z", "2026-10-18T10:00:04Z",
                                source="front.log", contains="accepted")
        counts = result["counts"]
        self.assertEqual((counts["window_matching"], counts["matching"],
                          counts["excluded_by_filter"], counts["outside"]), (2, 1, 1, 1))
        event = result["events"][0]["event"]
        original = next(e for e in self.pack["timeline"]["events"]
                        if e["source"] == "front.log" and e["line"] == 2)
        self.assertEqual(event, original)
        self.assertEqual(self.pack, before)
        self.assertEqual(result["undated_lines"], self.pack["timeline"]["omitted"])

    def test_filter_is_literal_case_sensitive_and_exact_source(self):
        for source, contains in [("front", None), (None, "Accepted"),
                                 (None, ".*"), ("missing.log", None),
                                 ("back.log", "accepted")]:
            with self.subTest(source=source, contains=contains):
                result = window.inspect(self.pack, "2026-10-18T10:00:02Z",
                                        "2026-10-18T10:00:04Z", source=source, contains=contains)
                self.assertEqual(result["counts"]["matching"], 0)
                self.assertEqual(result["counts"]["excluded_by_filter"], 2)
                self.assertEqual(result["counts"]["omitted_lines_total"], 1)

    def test_filtered_zero_limit_keeps_totals(self):
        result = window.inspect(self.pack, "2026-10-18T10:00:02Z",
                                "2026-10-18T10:00:04Z", 0, contains="accepted")
        self.assertEqual(result["counts"]["not_shown"], 1)
        self.assertEqual(result["counts"]["excluded_by_filter"], 1)
        self.assertEqual(result["events"], [])

    def test_nonmatching_filter_does_not_bypass_verification(self):
        self.pack["timeline"]["events"][0]["message"] = "forged"
        with self.assertRaises(replay.ReplayError):
            window.inspect(self.pack, "2026-10-18T10:00:02Z", "2026-10-18T10:00:04Z",
                           source="absent", contains="absent")

    def test_invalid_filter_types_and_lengths(self):
        for key in ("source", "contains"):
            for value in ("", "x" * 4097, True, 1, []):
                with self.subTest(key=key, value=type(value).__name__):
                    with self.assertRaises(replay.ReplayError):
                        window.inspect(self.pack, "2026-10-18T10:00:02Z",
                                       "2026-10-18T10:00:04Z", **{key: value})

    def test_unicode_literal_without_normalization(self):
        pack = replay.make_pack([("../inert.log", "2026-10-18T10:00:02Z café [x]\n".encode())])
        for needle, expected in [("café", 1), ("cafe\u0301", 0), ("[x]", 1), ("[xy]", 0)]:
            result = window.inspect(pack, "2026-10-18T10:00:02Z", "2026-10-18T10:00:03Z",
                                    source="../inert.log", contains=needle)
            self.assertEqual(result["counts"]["matching"], expected)


if __name__ == "__main__":
    unittest.main()
