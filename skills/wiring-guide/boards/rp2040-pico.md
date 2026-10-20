# Raspberry Pi Pico (RP2040, 3.3 V)

Pin notes to check before drawing. Pico W and Pico 2 differ where noted; check their own datasheets.

- Physical pins are numbered 1–40. With the USB connector at the top, pin 1 (GP0) is top left, pins 1–20 run down the left edge and 21–40 run up the right edge.
- On a breadboard the two pin rows are 0.7 in (7 holes) apart, so they sit in columns c and h, d and i, or e and j. c/h leaves two free holes on each side (a–b and i–j).
- Lying sideways with USB to the left, on a board with column j at the top: pins 1–20 run left to right along the a side (pin 1 nearest USB), and pins 40–21 run left to right along the j side (pin 40 nearest USB).
- GND is on pins 3, 8, 13, 18, 23, 28, 33, 38: every fifth pin, easy to count by hand.
- Power pins on the right, top: 40 VBUS (USB 5 V), 39 VSYS, 37 3V3_EN, 36 3V3(OUT). Power 3.3 V parts from pin 36.
- 3.3 V logic. The GPIOs are not 5 V tolerant.
- GPIO drive strength defaults to 4 mA (settable to 2, 8 or 12 mA). Keep an LED to a few mA: 330 Ω gives about 4 mA for a red LED.
- Analog inputs: GP26, GP27, GP28 (ADC0–2). Pin 33 is AGND, 35 is ADC_VREF.
- GP23, GP24, GP25 and GP29 are used on the board and are not on the header. GP25 is the on-board LED on the Pico; on the Pico W the LED is on the wireless chip instead.

## Sources
- Raspberry Pi Pico datasheet (pinout, power pins, on-board GPIO use): https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
- RP2040 datasheet (GPIO electrical limits): https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
