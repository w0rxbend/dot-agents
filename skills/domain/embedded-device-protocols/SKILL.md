---
name: embedded-device-protocols
description: Change or diagnose ESP32 camera and LED-device wire protocols, Arduino/PlatformIO firmware, STM32 board configuration, and AVR USB HID while preserving framing, buffer ownership, and hardware identity.
license: MIT
---

From checked-out configuration, identify exact board, framework/platform versions, pin mapping, transport peer and build environment. Portfolio: ESP32/ESP8266, STM32-compatible BluePill clone, ATmega32u4 USB HID. Shared Arduino API does not make their GPIO, interrupt, memory, timing or upload behavior interchangeable.

Hardware/build changes: read [references/board-contracts.md](references/board-contracts.md). Camera transport, frame parsing, device/server compatibility: read [references/camera-and-wire.md](references/camera-and-wire.md). Read only relevant path. Keep each protocol's opcodes, framing and status behavior separate. “TCP camera” and “matrix controller” are not protocol definitions.

Trace ownership: capture allocates/borrows buffer, slot or queue transfers it, sender consumes it, one owner releases it on success and every failure path. Track whether driver reuses pointer. Where possible, decide retries and backpressure before borrowing scarce hardware resources. Network retry must not repeat physical action whose execution is unknown.

Before hardware tests, use offline packet vectors, fake short-read/short-write transports, native parser tests and compile checks. Build success proves toolchain compatibility, not electrical correctness or device timing. Flashing, USB HID output, relay/motor actuation and live camera/network checks need authorized target and bounded check. Never run them as incidental validation of unrelated source edit.

Report tested layer and remaining physical assumptions. Performance work: record separately capture rate, successful send rate, dropped/stale frames, send time, reconnect delay, memory/buffer availability. Latency-sensitive live preview: prefer bounded latest-frame delivery. Use reliable retention only when application needs every frame and storage/backpressure design supports it.
