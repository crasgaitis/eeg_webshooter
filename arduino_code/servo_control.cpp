#include <Servo.h>

Servo myservo;
int pos = 0;

void setup() {
  myservo.attach(8);  // attach the servo to pin 8
}

void loop() {
  while (true) {
    myservo.write(pos);  // move to current position
    delay(500);          // wait for servo to reach the position

    // flip between 0 and 180
    if (pos == 0) {
      pos = 180;
    } else {
      pos = 0;
    }
  }
}