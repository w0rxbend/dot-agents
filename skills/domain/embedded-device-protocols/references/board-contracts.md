# Board and hardware contracts

Verify environment names in platformio.ini before running build target. Existing examples show guessing “ESP32” is unsafe:

| Public project evidence | Existing contract | Consequence for edits |
|---|---|---|
| [chillmate configuration](https://github.com/w0rxbend/chillmate/blob/5874cc2c4899cef1f07d54a03454973fe773d674/platformio.ini) | espressif32, nodemcu-32s, Arduino | Match symbolic pins to this variant and wired motor outputs. |
| [paranoid configuration](https://github.com/w0rxbend/paranoid/blob/f0e61198351fe7050baf8732fd5f2d8d2b005aca/platformio.ini) | ststm32, bluepill_f103c8, ST-Link; documented CS32 clone TAPID override | Keep board-specific upload setting until actual silicon/debugger evidence supports change. |
| [macropad configuration](https://github.com/w0rxbend/macropad-greycode/blob/4c3fd6331deb626d473d8b943d4b202fed9531f9/platformio.ini) | atmelavr, ATmega32u4, 16 MHz, Arduino, USB VID/PID | HID behavior and bootloader/upload access are part of compatibility. |

Pin rename can change physical behavior even if compilation succeeds. Check board variant definition, voltage capabilities, shared peripherals, boot/strapping functions, wiring. Do not introduce another project's camera pin map or inferred schematic. Official [PlatformIO configuration reference](https://docs.platformio.org/en/latest/projectconf/index.html) explains environment selection. Electrical details: use version-appropriate board/framework docs.

In [macropad source](https://github.com/w0rxbend/macropad-greycode/blob/4c3fd6331deb626d473d8b943d4b202fed9531f9/src/main.cpp) interrupt and main loop both touch rotary state. Keypad transitions send Keyboard.press/release. Keep interrupt work short; avoid allocation, serial output, I2C or NeoPixel transmission in ISR. `volatile` does not guarantee atomic multi-byte snapshot on 8-bit AVR. Use appropriate critical section and restore interrupt state. Test press/release pairing and layer transitions so reset/teardown cannot leave modifier held.

Consider blocking waits, heap allocation in tight loops, timer wraparound and peripheral timing in context. Elapsed millis comparisons: use unsigned subtraction within interval assumptions, not naive absolute deadline comparison. Motor or relay actuation commands: specify safe startup/output states and authorized observation to check them. Inspect board's existing tests first. PlatformIO's scaffold test/README is not executed test suite.

Report firmware build, host parser unit tests, hardware flashing and physical observation separately. Prefer repo's existing `pio run -e <verified-env>` or wrapper. Upload target is additional action, not synonym for build.
