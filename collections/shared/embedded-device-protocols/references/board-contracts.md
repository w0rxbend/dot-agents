# Board and hardware contracts

Verify environment names in platformio.ini before invoking a build target. Existing examples demonstrate why guessing “ESP32” is unsafe:

| Public project evidence | Existing contract | Consequence for edits |
|---|---|---|
| [chillmate configuration](https://github.com/w0rxbend/chillmate/blob/5874cc2c4899cef1f07d54a03454973fe773d674/platformio.ini) | espressif32, nodemcu-32s, Arduino | Match symbolic pins to this variant and the wired motor outputs. |
| [paranoid configuration](https://github.com/w0rxbend/paranoid/blob/f0e61198351fe7050baf8732fd5f2d8d2b005aca/platformio.ini) | ststm32, bluepill_f103c8, ST-Link; documented CS32 clone TAPID override | Preserve the board-specific upload setting until actual silicon/debugger evidence supports a change. |
| [macropad configuration](https://github.com/w0rxbend/macropad-greycode/blob/4c3fd6331deb626d473d8b943d4b202fed9531f9/platformio.ini) | atmelavr, ATmega32u4, 16 MHz, Arduino, USB VID/PID | HID behavior and bootloader/upload access are part of compatibility. |

A pin rename can change physical behavior even if compilation succeeds. Check the board variant's definition, voltage capabilities, shared peripherals, boot/strapping functions, and wiring. Do not introduce another project's camera pin map or an inferred schematic. The official [PlatformIO configuration reference](https://docs.platformio.org/en/latest/projectconf/index.html) explains environment selection; use version-appropriate board/framework documentation for electrical details.

In the [macropad source](https://github.com/w0rxbend/macropad-greycode/blob/4c3fd6331deb626d473d8b943d4b202fed9531f9/src/main.cpp) rotary state is touched by an interrupt and the main loop, while keypad transitions send Keyboard.press/release. Keep interrupt work short and avoid allocating, serial output, I2C, or NeoPixel transmission in the ISR. `volatile` does not guarantee an atomic multi-byte snapshot on an 8-bit AVR; choose an appropriate critical section and restore interrupt state. Test press/release pairing and layer transitions so reset/teardown cannot leave a modifier held.

Consider blocking waits, heap allocation in tight loops, timer wraparound, and peripheral timing in context. For elapsed millis comparisons use unsigned subtraction within the interval assumptions; do not replace it with a naive absolute deadline comparison. Where hardware commands actuate motors or relays, specify safe startup/output states and the authorized observation needed to check them. Inspect the board's existing tests first; PlatformIO's scaffold test/README is not an executed test suite.

Keep firmware build, host parser unit tests, hardware flashing and physical observation distinct in the report. Prefer the repo's existing `pio run -e <verified-env>` or wrapper; an upload target is an additional action, not a synonym for build.
