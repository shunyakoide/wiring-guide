// Prints the address of every I2C device on the board's default SDA/SCL pins.
#include <Wire.h>

void setup() {
  Serial.begin(115200);
  while (!Serial) {}  // boards with native USB wait for the serial monitor
  Wire.begin();
}

void loop() {
  int found = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("found 0x");
      if (addr < 16) Serial.print('0');
      Serial.println(addr, HEX);
      found++;
    }
  }
  if (found == 0) Serial.println("no I2C device: check SDA/SCL, power, GND and pull-ups");
  Serial.println("---");
  delay(3000);
}
