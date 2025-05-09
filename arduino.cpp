#include <Servo.h>
#include <SoftwareSerial.h>

Servo ESC;

void setup() {
  // put your setup code here, to run once:
  ESC.attach(9, 1000, 2000); // pin, min pulse width, max pulse width (ms)
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  String cmd = Serial.readStringUntil('\n')
  float potValue = cmd.toFloat();

  // Clamp potValue between 0 and 1
  if (potValue < 0) potValue = 0;
  if (potValue > 1) potValue = 1;

  int escValue = map(potValue * 100, 0, 100, 0, 180);  // convert float range 0–1 to 0–180
  ESC.write(escValue);

  Serial.print("Received: ");
  Serial.print(potValue);
  Serial.print(" -> Mapped: ");
  Serial.println(escValue);
}
