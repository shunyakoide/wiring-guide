# Arduino Uno R3, Nano, Mega 2560 (AVR, 5 V)

Pin notes to check before drawing. Confirm against the sources below; clones can differ.

## Uno R3
- Upper header, counted from the USB end: SCL, SDA, AREF, GND, D13, D12, D11, D10, D9, D8. Then a gap, then D7 … D0.
- Lower header, counted from the USB end: (no pin), IOREF, RESET, 3.3V, 5V, GND, GND, VIN. Then A0 … A5.
- D0 and D1 are the USB serial port. Anything wired to them can block uploads; leave them free.
- D13 also drives the on-board "L" LED.
- I2C is A4 = SDA, A5 = SCL (the same signals as the SDA/SCL pins by AREF).
- Per-pin current: 20 mA is a safe working limit, 40 mA is the absolute maximum. Drive motors, relays and LED strips through a transistor or driver.

## Nano (ATmega328P)
- Same pin functions as the Uno: D0/D1 serial, A4 = SDA, A5 = SCL.
- A6 and A7 are analog input only. They cannot be used as digital pins.

## Mega 2560
- I2C is D20 = SDA, D21 = SCL (not A4/A5).
- D0/D1 are the USB serial port; Serial1–3 are on D14–D19.

## Sources
- Arduino Uno Rev3: https://docs.arduino.cc/hardware/uno-rev3/
- Arduino Nano: https://docs.arduino.cc/hardware/nano/
- Arduino Mega 2560 Rev3: https://docs.arduino.cc/hardware/mega-2560/
- ATmega328P (electrical characteristics, I/O pin current): https://www.microchip.com/en-us/product/atmega328p
