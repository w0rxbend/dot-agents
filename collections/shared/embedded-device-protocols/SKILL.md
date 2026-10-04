---
name: embedded-device-protocols
description: Change or diagnose ESP32 camera and LED-device wire protocols, Arduino/PlatformIO firmware, STM32 board configuration, and AVR USB HID while preserving framing, buffer ownership, and hardware identity.
license: MIT
---

Identify the exact board, framework/platform versions, pin mapping, transport peer, and build environment from checked-out configuration. This portfolio includes ESP32/ESP8266, an STM32-compatible BluePill clone, and ATmega32u4 USB HID. A shared Arduino API does not make their GPIO, interrupt, memory, timing, or upload behavior interchangeable.

Read [references/board-contracts.md](references/board-contracts.md) for hardware/build changes and [references/camera-and-wire.md](references/camera-and-wire.md) for camera transport, frame parsing, or device/server compatibility. Read only the relevant path. Keep each protocol's opcodes, framing and status behavior separate; “TCP camera” and “matrix controller” are not protocol definitions.

Trace ownership explicitly: capture allocates/borrows a buffer, a slot or queue transfers it, a sender consumes it, and one owner releases it on success and every failure path. Track whether a pointer is reused by the driver. Make retries and backpressure decisions before borrowing scarce hardware resources where possible. A network retry must not repeat a physical action whose execution is unknown.

Use offline packet vectors, fake short-read/short-write transports, native parser tests, and compile checks before hardware tests. Build success proves toolchain compatibility, not correct electrical behavior or device timing. Flashing, USB HID output, relay/motor actuation, and live camera/network checks need an authorized target and bounded check; never run them as incidental validation of an unrelated source edit.

Report the tested layer and remaining physical assumptions. For performance work record capture rate, successful send rate, dropped/stale frames, send time, reconnect delay and memory/buffer availability separately. Prefer bounded latest-frame delivery for a latency-sensitive live preview; use reliable retention only when the application actually requires every frame and the storage/backpressure design supports it.
