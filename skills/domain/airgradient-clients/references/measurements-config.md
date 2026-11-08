# Measurements and shared configuration

## Values and units travel together

Optional measurement is not valid zero; keep them separate. AirGradient firmware variants expose aliases, nested JSON, compensated versus raw temperature/humidity, negative missing-sensor sentinels. Preserve each project's documented alias precedence. Negative temperature is legitimate; negative particulate/CO2 sentinel should not grade as clean air.

Pick TVOC/NOx units from **alias actually selected**, not from whether some index field exists elsewhere in payload. Payload can hold both concentration and index readings. Check scaling/conversion per accepted alias; do not assume similar names share units. Explicit AQI and derived PM2.5 AQI must follow project's precedence and calculator. Do not merge Prometheus dashboard thresholds into device client without proving same units and semantics. See [sensor alias, unit, optional-value, and receive-time mapping](https://github.com/worxbend/airgradient-android/blob/f25ec0419cc1ff2d590b2de4b84d1485877967c0/app/src/main/java/dev/worxbend/airgradient/data/airgradient/mapper/AirGradientMeasureMapper.kt) and [observability metric names, units, and display bands](https://github.com/worxbend/airgradient-observability/blob/6e2b2c65ca6c9fbb7ea0ad9020e349126c77077c/app/backend/internal/metrics/definitions.go).

Track when value was measured, received, last successfully fetched, or read from cache; these are not interchangeable. On refresh failure, keep last-known data with visible age/error; do not silently renew freshness. Browser charts keep gaps and unknown readings distinct from numeric baseline.

## Preserve shared file ownership

Desktop JSON file is shared with CLI and GNOME clients. Find current XDG path rules and field ownership; do not invent separate config location for same settings. Updating one owned field must keep unknown sibling fields from other versions or clients.

AirGradient CLI merges raw JSON, replaces atomically, reports repairs from tolerant reads. Its read-modify-write guard uses size/mtime fingerprints: less lost-update exposure, but neither true compare-and-set nor advisory lock. Remaining gaps: same-size edits within timestamp granularity, check-to-rename window. Preserve conflict errors and accurate claims. `:save` from session without URL deliberately keeps newly stored URL; it does not write null. See [shared config merge and conflict behavior](https://github.com/worxbend/airgradient-cli/blob/938207e0e8b6662f839b9b8f56e38c605946c899/src/config/store.rs).

Desktop durable settings intentionally exclude current runtime readings. Unknown theme IDs load with fallback so newer themes do not make settings unusable to older apps. Keep configured refresh bounds and defaults consistent across parser, UI, runtime, tests; do not change only one. See [durable settings and typed refresh interval](https://github.com/worxbend/airgradient-desktop/blob/d58f3a291441dbca4dedec24cfd611a46c38514f/src/config.rs).

GNOME GJS file access is async; synchronous I/O blocks shell rendering loop. Pure normalization code is tested in Node; GIO boundary handles cancellation separately from first-run defaults. New write path must preserve unknown fields; do not assume every existing client already gives identical merge/conflict guarantees. See [async GIO adapter and normalization boundary](https://github.com/worxbend/airgradient-gnome-extension/blob/f1fbc34a3bc3bc8fd8835cf4017a3df58e86fc1a/desktopConfigStore.js).

## Contract fixtures

Cover missing/null/zero readings, negative sentinels, concentration plus index together, compensated alias preference, malformed numeric values, units in labels, and stale-cache/error states. Shared config: test that unfamiliar nested fields survive and chosen concurrent-write policy holds, using temporary files. Use explicit fixture units and artificial hostnames. Never encode user's LAN address in public test.
