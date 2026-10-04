# Measurements and shared configuration

## Values and units travel together

Keep an optional measurement separate from a valid zero. AirGradient firmware variants expose aliases, nested JSON, compensated versus raw temperature/humidity, and negative missing-sensor sentinels. Preserve each project's documented alias precedence. Temperature can legitimately be negative, while a negative particulate/CO2 sentinel should not grade as clean air.

Determine TVOC/NOx units from the **alias actually selected**, not from whether some index field exists elsewhere in the payload. A payload can contain both concentration and index readings. Check scaling/conversion for each accepted alias instead of assuming similar names share units. Explicit AQI and derived PM2.5 AQI must follow the project's precedence and calculator. Do not merge thresholds from the Prometheus dashboard into the device client without proving the same units and semantics. See [sensor alias, unit, optional-value, and receive-time mapping](https://github.com/worxbend/airgradient-android/blob/f25ec0419cc1ff2d590b2de4b84d1485877967c0/app/src/main/java/dev/worxbend/airgradient/data/airgradient/mapper/AirGradientMeasureMapper.kt) and [observability metric names, units, and display bands](https://github.com/worxbend/airgradient-observability/blob/6e2b2c65ca6c9fbb7ea0ad9020e349126c77077c/app/backend/internal/metrics/definitions.go).

Track when a value was measured, received, last successfully fetched, or read from cache. These timestamps are not interchangeable. A refresh failure should preserve last-known data with visible age/error rather than silently renewing its freshness. Browser charts should keep gaps and unknown readings distinct from a numeric baseline.

## Preserve shared file ownership

The desktop JSON file is shared with CLI and GNOME clients. Locate the current XDG path rules and field ownership; don't invent a separate config location for the same settings. Updates to one owned field must retain unknown sibling fields introduced by another version or client.

AirGradient CLI merges raw JSON, uses atomic replacement, and reports repairs from tolerant reads. Its read-modify-write guard uses size/mtime fingerprints, which reduce lost-update exposure but are neither a true compare-and-set nor an advisory lock; same-size edits within timestamp granularity and the check-to-rename window remain limits. Preserve conflict errors and accurate claims. `:save` from a session without a URL deliberately leaves a newly stored URL intact rather than writing null. See [shared config merge and conflict behavior](https://github.com/worxbend/airgradient-cli/blob/938207e0e8b6662f839b9b8f56e38c605946c899/src/config/store.rs).

Desktop durable settings intentionally exclude current runtime readings. Unknown theme IDs load with fallback rather than making a newer theme unusable to an older app. Keep configured refresh bounds and defaults consistent across parser, UI, runtime, and tests instead of altering only one field. See [durable settings and typed refresh interval](https://github.com/worxbend/airgradient-desktop/blob/d58f3a291441dbca4dedec24cfd611a46c38514f/src/config.rs).

GNOME GJS file access is async because synchronous I/O blocks the shell's rendering loop. Its pure normalization code is tested in Node and its GIO boundary handles cancellation separately from first-run defaults. Ensure a new write path preserves unknown fields; do not assume every existing client already provides identical merge/conflict guarantees. See [async GIO adapter and normalization boundary](https://github.com/worxbend/airgradient-gnome-extension/blob/f1fbc34a3bc3bc8fd8835cf4017a3df58e86fc1a/desktopConfigStore.js).

## Contract fixtures

Cover missing/null/zero readings, negative sentinels, concentration plus index simultaneously, compensated alias preference, malformed numeric values, units in labels, and stale-cache/error states. For shared config, test preservation of unfamiliar nested fields and the chosen concurrent-write policy using temporary files. Use explicit fixture units and artificial hostnames; never encode a user's LAN address in a public test.
