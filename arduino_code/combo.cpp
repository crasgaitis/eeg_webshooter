#include <Servo.h>
#include <SoftwareSerial.h>

Servo myservo;
Servo ESC;

void setup() {
  myservo.attach(8);             // Attach servo arm to pin 8
  ESC.attach(9, 1000, 2000);     // Attach ESC to pin 9 (1000–2000 µs pulse range)
  myservo.write(90);              // Start servo at 90 degrees
  Serial.begin(9600);            // Begin serial communication
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    float inputValue = cmd.toFloat();

      // Clamp potValue between 0 and 1
    if (inputValue > 0.01) {
      if (inputValue < 0) inputValue = 0;
      if (inputValue > 1) inputValue = 1;

      int escValue = map(inputValue * 100, 0, 100, 0, 180); 

      myservo.write(180);
      delay(100); 

      ESC.write(escValue);
      delay(1000);

      ESC.write(0);

      myservo.write(90);
      delay(300);  
    }
  }
}
