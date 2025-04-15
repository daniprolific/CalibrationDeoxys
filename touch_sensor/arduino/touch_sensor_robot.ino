#include <Servo.h>
Servo myservo;  // create servo object to control a servo

int pinProbe = A0;
int pinLed = 13;
int pinServo = 9; 

boolean state;
int stateValue;
boolean prevState;
boolean ledState;
int touchDetected = 0; // 1 if touch detected, 0 otherwise
int lastStateValue = 0; // For detecting changes in stateValue

void setup() {
  pinMode(pinProbe, INPUT);
  pinMode(pinLed, OUTPUT);
  myservo.attach(pinServo);
  Serial.begin(9600);
}

void loop() {
  // Handle serial commands
  if (Serial.available()) {
    char cmd = Serial.read();
    
    if (cmd == '1') {
      myservo.write(10);
      touchDetected = 0;
    } else if (cmd == '2') {
      myservo.write(90);
    } else if (cmd == 't') {
      Serial.print("TouchDetected: ");
      Serial.println(touchDetected);
    }
    
    // Flush remaining characters including newline
    while (Serial.available() && Serial.read() != '\n') {}
  }

  // Touch detection logic
  state = digitalRead(pinProbe);
  stateValue = analogRead(pinProbe);

  // Detect physical state change
  if (prevState != state) {
    prevState = state;
    if (state) {
      ledState = !ledState;
      //digitalWrite(pinLed, ledState);
      myservo.write(90);
      touchDetected = 1;
      Serial.println("TouchDetected: 1");
      lastStateValue = stateValue;
    }
  }
}