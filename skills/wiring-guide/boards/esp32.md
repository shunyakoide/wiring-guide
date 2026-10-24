# ESP32 (ESP32-WROOM-32 / DevKitC, 3.3 V)

Pin notes to check before drawing. These apply to the original ESP32 only. ESP32-S2, S3, C3 and C6 have different pins; do not use this file for them.

- 3.3 V logic. The pins are not 5 V tolerant: a 5 V signal needs a level shifter or a divider.
- GPIO34, 35, 36 (VP), 39 (VN) are input only and have no internal pull-up or pull-down. A button on them needs an external resistor.
- GPIO6–11 are wired to the module's flash. Never use them.
- Strapping pins are read at reset, so what is wired to them can stop the board from booting:
  - GPIO0: low at reset enters download mode (the BOOT button pulls it low).
  - GPIO2: must be low or floating to enter download mode.
  - GPIO12 (MTDI): high at reset selects 1.8 V flash and stops 3.3 V-flash modules from booting. Avoid pull-ups on it.
  - GPIO5 and GPIO15 (MTDO): avoid parts that pull them at reset.
- ADC2 (GPIO0, 2, 4, 12–15, 25–27) cannot be read while Wi-Fi is on. Use ADC1 (GPIO32–39) for analog inputs.
- GPIO1 (TX) and GPIO3 (RX) are the USB serial port. Leave them free.
- GPIO16 and GPIO17 are free only on boards with an ESP32-WROOM or SOLO-1 module; ESP32-WROVER boards use them inside.

## DevKitC V4 headers
Pin 1 is at the antenna end and pin 19 at the USB end. Counted from the USB end:
- J2: 5V, CMD, D3, D2, IO13, GND, IO12, IO14, IO27, IO26, IO25, IO33, IO32, IO35, IO34, VN (IO39), VP (IO36), EN, 3V3.
- J3: CLK, D0, D1, IO15, IO2, IO0, IO4, IO16, IO17, IO5, IO18, IO19, GND, IO21, RX (IO3), TX (IO1), IO22, IO23, GND.
- CLK, D0–D3 and CMD are the flash pins (GPIO6–11).

## Sources
- ESP32-DevKitC V4 user guide (header tables J2/J3, pin layout, GPIO16/17 on WROVER): https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html
- ESP32 Series Datasheet (pin list, strapping pins): https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf
- ESP-IDF GPIO (input-only pins, flash pins, strapping pins): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html
- ESP-IDF ADC (ADC2 and Wi-Fi): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/adc_oneshot.html
