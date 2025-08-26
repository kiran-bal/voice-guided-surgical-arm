#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// Wi-Fi credentials
const char* ssid = "";
const char* password = "";

// Create server on port 80
WebServer server(80);

// Servo setup (same as your original code)
Servo servo1;
Servo servo3; 
Servo servo4; 
Servo servo5;
Servo clawServo;

const int servo1Pin = 13;
const int servo3Pin = 14;
const int servo4Pin = 27;
const int servo5Pin = 12;
const int clawPin   = 26;

const int baseServoMin = 0;
const int baseServoMax = 180;
const int angleMin = 0;
const int angleMax = 125;
const int clawClose = 60;
const int clawOpen = 120;

int tolerance = 5;    
int lastFeedback = 0;

void handleCommand() {
  if (!server.hasArg("value")) {
    server.send(400, "text/plain", "Missing value");
    return;
  }

  String cmd = server.arg("value");
  Serial.println("Received command: " + cmd);

  if (cmd == "A" || cmd == "a" || cmd == "a0") {
    runSequence(180);
  } else if (cmd == "B" || cmd == "b" || cmd == "b0") {
    runSequence(150);
  }

  server.send(200, "text/plain", "OK");
}

void setup() {
  Serial.begin(115200);
  Serial.println("Connecting to Wi-Fi...");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connected to Wi-Fi");
  Serial.print("📡 ESP32 IP: ");
  Serial.println(WiFi.localIP());

  servo1.attach(servo1Pin);
  clawServo.attach(clawPin);
  servo3.attach(servo3Pin);
  servo4.attach(servo4Pin);
  servo5.attach(servo5Pin);

  // Web server routes
  server.on("/cmd", HTTP_GET, handleCommand);
  server.begin();
}

void loop() {
  server.handleClient();
}

// === Servo control functions ===
void moveServoTo(Servo &servo, int startAngle, int endAngle, const char* name) {
  int step = (endAngle > startAngle) ? 1 : -1;
  for (int pos = startAngle; pos != endAngle + step; pos += step) {
    servo.write(pos);
    Serial.printf("%s moving to: %d°\n", name, pos);
    delay(25);
  }
}

void openClaw() {
  Serial.println("Claw opening...");
  clawServo.write(clawOpen);
}

void closeClaw() {
  Serial.println("Claw closing...");
  int step = (clawClose > clawOpen) ? 1 : -1;
  for (int pos = clawOpen; pos != clawClose + step; pos += step) {
    clawServo.write(pos);
    delay(40);

    if (lastFeedback == pos && tolerance != 0) {
      tolerance--;
    } 
    if (lastFeedback == pos && tolerance == 0) {
      Serial.println("Obstacle detected! Stopping claw.");
      break;
    }
    lastFeedback = pos;
  }
}

void runSequence(int baseEndPosition) {
  moveServoTo(servo1, 0, baseEndPosition, "Servo 1");
  openClaw();
  moveServoTo(servo3, angleMin, angleMax, "Servo 3");
  moveServoTo(servo5, 110, 160, "Servo 5");
  closeClaw();
  moveServoTo(servo3, angleMax, angleMin, "Servo 3");
  moveServoTo(servo1, baseEndPosition, 0, "Servo 1");
  moveServoTo(servo3, angleMin, angleMax, "Servo 3");
  openClaw();
  moveServoTo(servo5, 160, 110, "Servo 5");
  moveServoTo(servo3, angleMin, 0, "Servo 3");
}
