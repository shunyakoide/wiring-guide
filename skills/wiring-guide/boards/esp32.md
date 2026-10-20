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

## Sources
- ESP32 Series Datasheet (pin list, strapping pins): https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf
- ESP-IDF GPIO (input-only pins, flash pins, strapping pins): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html
- ESP-IDF ADC (ADC2 and Wi-Fi): https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/adc_oneshot.html
