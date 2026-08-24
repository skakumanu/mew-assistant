# Locale files

One file per locale. `en.json` is the contract: every key that exists in
`en.json` must exist in every other file, with the same named placeholders.

Rules that come from the design:

* **Locale comes from the device**, never from the content of a message.
  `Accept-Language` first, then an explicit per-user override recorded in
  `UserLocale` (`source` says which). `app/utils/language_detector.py` and
  `app/voice/language_detector.py` sniff text for the *voice* pipeline; they
  must not be used to pick UI locale.
* **Every generated sentence is a template with named placeholders.** Nothing
  is concatenated at the call site, so word order survives translation.
* **Reason codes resolve through `reasons.*`.** The database stores codes
  (`min_notice`, `latest_end`, ...), never rendered sentences, so one parked
  request reads correctly for a parent in Spanish and a provider in English.
* `meta.dir` drives RTL. `meta.clock` drives 12h/24h formatting.
* Weekend days and time zone come from the ruleset, not from this file, so a
  Friday–Saturday weekend works untouched.

## Translation status

| Locale | Status |
| --- | --- |
| `en` | Source of truth. |
| `es` | Reviewed against the design prototype. |
| `hi` | **Unreviewed machine-quality translation — needs a native speaker before shipping.** |
| `ar` | **Unreviewed machine-quality translation — needs a native speaker before shipping.** RTL verified. |
