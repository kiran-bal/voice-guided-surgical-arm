/*
 * ASTRA Enhanced Surgical Assistant ESP32 Code
 * Handles enhanced command format with handedness: a0l, a0r, a1l, a1r, b0l, b0r, b1l, b1r, d0l, d0r, d1l, d1r, e0l, e0r, e1l, e1r, x
 * 
 * Commands:
 * - a0l/a0r: Incision without object detection (left/right handed)
 * - a1l/a1r: Incision with object detection (left/right handed)
 * - b0l/b0r: Stitch without object detection (left/right handed)
 * - b1l/b1r: Stitch with object detection (left/right handed)
 * - d0l/d0r: Grasp without object detection (left/right handed)
 * - d1l/d1r: Grasp with object detection (left/right handed)
 * - e0l/e0r: Cut without object detection (left/right handed)
 * - e1l/e1r: Cut with object detection (left/right handed)
 * - x: No operation (no valid action detected)
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YourWiFiSSID";
const char* password = "YourWiFiPassword";

// Server Configuration
WebServer server(80);
const int serverPort = 80;

// Pin Configuration for Servos/Motors
const int SERVO_INCISION_PIN = 13;    // Servo for incision movement
const int SERVO_STITCH_PIN = 14;      // Servo for stitching movement
const int SERVO_GRASP_PIN = 15;       // Servo for grasping movement
const int SERVO_CUT_PIN = 16;         // Servo for cutting movement
const int SERVO_ROTATE_PIN = 17;      // Servo for rotation movement

// LED Indicators
const int LED_STATUS_PIN = 2;         // Built-in LED for status
const int LED_OBJECT_PIN = 4;         // LED for object detection status
const int LED_COMMAND_PIN = 5;        // LED for command execution

// Movement Configuration
const int MOVEMENT_DELAY = 1000;      // Delay between movements (ms)
const int SERVO_MIN_POS = 0;          // Minimum servo position
const int SERVO_MAX_POS = 180;        // Maximum servo position
const int SERVO_MID_POS = 90;         // Middle servo position

// Command tracking
String lastCommand = "";
bool objectDetected = false;
int commandCount = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("🤖 ASTRA Enhanced Surgical Assistant Starting...");
  
  // Initialize pins
  initializePins();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup web server
  setupWebServer();
  
  // Start server
  server.begin();
  Serial.println("✅ Web server started");
  Serial.println("🌐 Server IP: " + WiFi.localIP().toString());
  
  // Initial status
  updateStatusLED(true);
  Serial.println("🚀 ASTRA Enhanced Surgical Assistant Ready!");
}

void loop() {
  server.handleClient();
  delay(10);
}

void initializePins() {
  // Initialize servo pins (if using PWM)
  // Note: For actual servo control, you might need a servo library
  pinMode(SERVO_INCISION_PIN, OUTPUT);
  pinMode(SERVO_STITCH_PIN, OUTPUT);
  pinMode(SERVO_GRASP_PIN, OUTPUT);
  pinMode(SERVO_CUT_PIN, OUTPUT);
  pinMode(SERVO_ROTATE_PIN, OUTPUT);
  
  // Initialize LED pins
  pinMode(LED_STATUS_PIN, OUTPUT);
  pinMode(LED_OBJECT_PIN, OUTPUT);
  pinMode(LED_COMMAND_PIN, OUTPUT);
  
  // Set initial LED states
  digitalWrite(LED_STATUS_PIN, LOW);
  digitalWrite(LED_OBJECT_PIN, LOW);
  digitalWrite(LED_COMMAND_PIN, LOW);
  
  Serial.println("✅ Pins initialized");
}

void connectToWiFi() {
  Serial.print("📡 Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✅ WiFi connected successfully!");
    Serial.println("📶 IP Address: " + WiFi.localIP().toString());
    updateStatusLED(true);
  } else {
    Serial.println();
    Serial.println("❌ WiFi connection failed!");
    updateStatusLED(false);
  }
}

void setupWebServer() {
  // Main command endpoint
  server.on("/", HTTP_GET, handleCommand);
  
  // Status endpoint
  server.on("/status", HTTP_GET, handleStatus);
  
  // Test endpoint
  server.on("/test", HTTP_GET, handleTest);
  
  // 404 handler
  server.onNotFound(handleNotFound);
  
  Serial.println("✅ Web server routes configured");
}

void handleCommand() {
  String command = server.hasArg("cmd") ? server.arg("cmd") : "";
  
  if (command.length() > 0) {
    Serial.println("📥 Received command: " + command);
    executeCommand(command);
    
    // Send response
    DynamicJsonDocument doc(200);
    doc["success"] = true;
    doc["command"] = command;
    doc["executed"] = true;
    doc["timestamp"] = millis();
    
    String response;
    serializeJson(doc, response);
    
    server.send(200, "application/json", response);
  } else {
    server.send(400, "application/json", "{\"error\": \"No command provided\"}");
  }
}

void handleStatus() {
  DynamicJsonDocument doc(300);
  doc["status"] = "ready";
  doc["wifi_connected"] = WiFi.status() == WL_CONNECTED;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["last_command"] = lastCommand;
  doc["object_detected"] = objectDetected;
  doc["command_count"] = commandCount;
  doc["uptime"] = millis();
  
  String response;
  serializeJson(doc, response);
  
  server.send(200, "application/json", response);
}

void handleTest() {
  DynamicJsonDocument doc(200);
  doc["status"] = "ok";
  doc["message"] = "ASTRA Enhanced Surgical Assistant is running";
  doc["version"] = "2.0";
  
  String response;
  serializeJson(doc, response);
  
  server.send(200, "application/json", response);
}

void handleNotFound() {
  server.send(404, "application/json", "{\"error\": \"Endpoint not found\"}");
}

void executeCommand(String command) {
  commandCount++;
  lastCommand = command;
  
  Serial.println("🎯 Executing command: " + command);
  updateCommandLED(true);
  
  // Determine if object is detected based on command
  objectDetected = command.endsWith("1");
  updateObjectLED(objectDetected);
  
  if (command == "a0l") {
    executeIncision(false, 'l');
  } else if (command == "a0r") {
    executeIncision(false, 'r');
  } else if (command == "a1l") {
    executeIncision(true, 'l');
  } else if (command == "a1r") {
    executeIncision(true, 'r');
  } else if (command == "b0l") {
    executeStitch(false, 'l');
  } else if (command == "b0r") {
    executeStitch(false, 'r');
  } else if (command == "b1l") {
    executeStitch(true, 'l');
  } else if (command == "b1r") {
    executeStitch(true, 'r');
  } else if (command == "d0l") {
    executeGrasp(false, 'l');
  } else if (command == "d0r") {
    executeGrasp(false, 'r');
  } else if (command == "d1l") {
    executeGrasp(true, 'l');
  } else if (command == "d1r") {
    executeGrasp(true, 'r');
  } else if (command == "e0l") {
    executeCut(false, 'l');
  } else if (command == "e0r") {
    executeCut(false, 'r');
  } else if (command == "e1l") {
    executeCut(true, 'l');
  } else if (command == "e1r") {
    executeCut(true, 'r');
  } else if (command == "x") {
    Serial.println("✅ No valid action detected for command 'x'");
  } else {
    Serial.println("❌ Unknown command: " + command);
  }
  
  updateCommandLED(false);
  Serial.println("✅ Command execution completed");
}

void executeIncision(bool withObject, char handedness) {
  Serial.println("🔪 Executing incision" + String(withObject ? " with object" : "") + " (handedness: " + handedness + ")");
  
  // Step 1: Position for incision based on handedness
  if (handedness == 'l') {
    // Left-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS - 15);
    Serial.println("🤚 Left-handed positioning");
  } else {
    // Right-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS + 15);
    Serial.println("🤚 Right-handed positioning");
  }
  delay(MOVEMENT_DELAY);
  
  // Step 2: Perform incision movement
  moveServo(SERVO_INCISION_PIN, SERVO_MAX_POS);
  delay(MOVEMENT_DELAY);
  
  // Step 3: Return to neutral
  moveServo(SERVO_INCISION_PIN, SERVO_MID_POS);
  delay(MOVEMENT_DELAY);
  
  if (withObject) {
    // Additional precision movement for object detection
    Serial.println("🎯 Precision adjustment for object");
    moveServo(SERVO_INCISION_PIN, SERVO_MAX_POS - 20);
    delay(500);
    moveServo(SERVO_INCISION_PIN, SERVO_MID_POS);
  }
  
  Serial.println("✅ Incision completed");
}

void executeStitch(bool withObject, char handedness) {
  Serial.println("🪡 Executing stitch" + String(withObject ? " with object" : "") + " (handedness: " + handedness + ")");
  
  // Step 1: Position for stitching based on handedness
  if (handedness == 'l') {
    // Left-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS + 15);
    Serial.println("🤚 Left-handed positioning");
  } else {
    // Right-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS + 45);
    Serial.println("🤚 Right-handed positioning");
  }
  delay(MOVEMENT_DELAY);
  
  // Step 2: Perform stitching movement
  moveServo(SERVO_STITCH_PIN, SERVO_MAX_POS);
  delay(MOVEMENT_DELAY);
  
  // Step 3: Return to neutral
  moveServo(SERVO_STITCH_PIN, SERVO_MID_POS);
  delay(MOVEMENT_DELAY);
  
  if (withObject) {
    // Additional precision movement for object detection
    Serial.println("🎯 Precision adjustment for object");
    moveServo(SERVO_STITCH_PIN, SERVO_MAX_POS - 15);
    delay(500);
    moveServo(SERVO_STITCH_PIN, SERVO_MID_POS);
  }
  
  Serial.println("✅ Stitch completed");
}

void executeGrasp(bool withObject, char handedness) {
  Serial.println("�� Executing grasp" + String(withObject ? " with object" : "") + " (handedness: " + handedness + ")");
  
  // Step 1: Position for grasping based on handedness
  if (handedness == 'l') {
    // Left-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS - 35);
    Serial.println("🤚 Left-handed positioning");
  } else {
    // Right-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS - 5);
    Serial.println("🤚 Right-handed positioning");
  }
  delay(MOVEMENT_DELAY);
  
  // Step 2: Perform grasping movement
  moveServo(SERVO_GRASP_PIN, SERVO_MAX_POS);
  delay(MOVEMENT_DELAY);
  
  // Step 3: Hold position briefly
  delay(1000);
  
  // Step 4: Return to neutral
  moveServo(SERVO_GRASP_PIN, SERVO_MID_POS);
  delay(MOVEMENT_DELAY);
  
  if (withObject) {
    // Additional precision movement for object detection
    Serial.println("🎯 Precision adjustment for object");
    moveServo(SERVO_GRASP_PIN, SERVO_MAX_POS - 10);
    delay(500);
    moveServo(SERVO_GRASP_PIN, SERVO_MID_POS);
  }
  
  Serial.println("✅ Grasp completed");
}

void executeCut(bool withObject, char handedness) {
  Serial.println("✂️ Executing cut" + String(withObject ? " with object" : "") + " (handedness: " + handedness + ")");
  
  // Step 1: Position for cutting based on handedness
  if (handedness == 'l') {
    // Left-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS - 5);
    Serial.println("🤚 Left-handed positioning");
  } else {
    // Right-handed positioning
    moveServo(SERVO_ROTATE_PIN, SERVO_MID_POS + 25);
    Serial.println("🤚 Right-handed positioning");
  }
  delay(MOVEMENT_DELAY);
  
  // Step 2: Perform cutting movement
  moveServo(SERVO_CUT_PIN, SERVO_MAX_POS);
  delay(MOVEMENT_DELAY);
  
  // Step 3: Return to neutral
  moveServo(SERVO_CUT_PIN, SERVO_MID_POS);
  delay(MOVEMENT_DELAY);
  
  if (withObject) {
    // Additional precision movement for object detection
    Serial.println("🎯 Precision adjustment for object");
    moveServo(SERVO_CUT_PIN, SERVO_MAX_POS - 25);
    delay(500);
    moveServo(SERVO_CUT_PIN, SERVO_MID_POS);
  }
  
  Serial.println("✅ Cut completed");
}



void moveServo(int pin, int position) {
  // Clamp position to valid range
  position = constrain(position, SERVO_MIN_POS, SERVO_MAX_POS);
  
  // For PWM servo control (simplified)
  // In a real implementation, you'd use a servo library
  analogWrite(pin, map(position, 0, 180, 0, 255));
  
  Serial.println("🔄 Moving servo " + String(pin) + " to position " + String(position));
}

void updateStatusLED(bool status) {
  digitalWrite(LED_STATUS_PIN, status ? HIGH : LOW);
}

void updateObjectLED(bool detected) {
  digitalWrite(LED_OBJECT_PIN, detected ? HIGH : LOW);
}

void updateCommandLED(bool executing) {
  digitalWrite(LED_COMMAND_PIN, executing ? HIGH : LOW);
}

