import datetime
import requests
import speech_recognition as sr
import json
from typing import Optional, Dict
from pydantic import BaseModel, Field, ValidationError
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import cv2
import numpy as np

import os
os.environ["ALSA_LOG_LEVEL"] = "0"

# ---------------- CONFIG ---------------- #
USE_ESP32 = False        # set False to run without ESP32
USE_CAMERA = False       # set False to run without camera
INPUT_MODE = "typed"    # "voice" or "typed"
ESP32_IP = "http://192.168.0.131"  # replace with your ESP32

DOCTOR_PROFILES = {
    "sarath": {"handedness": "right"},
    "kiran": {"handedness": "left"}
}

# Command dictionary mapping
COMMAND_MAP = {
    "incision": "a",
    "stitch": "b",
    "object_detected": "c"
}

# ---------------- CAMERA UTILS ---------------- #
def detect_object(pixels_per_cm=None):
    cap = cv2.VideoCapture(2)
    if not cap.isOpened():
        return {"error": "Could not open webcam"}

    ret, frame = cap.read()
    cap.release()
    if not ret:
        return {"error": "Failed to capture image"}

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green, upper_green = np.array([35, 40, 40]), np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = {"object_detected": False}
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 1000:
            x, y, w, h = cv2.boundingRect(largest)
            result["object_detected"] = True
            # result["height"] = h if not pixels_per_cm else round(h / pixels_per_cm, 2)
    return result


# ---------------- SURGICAL ASSISTANT ---------------- #
class ToolAction(BaseModel):
    tool: Optional[str] = Field(None)
    action: Optional[str] = Field(None)
    handedness: Optional[str] = Field(None)


class SurgicalAssistant:
    def __init__(self, esp32_ip: str, doctor_profiles: Dict[str, Dict[str, str]]):
        self.esp32_ip = esp32_ip
        self.doctor_profiles = doctor_profiles
        self.tool_history = []
        self.llm = ChatOllama(model="qwen2.5:1.5b", format="json")
        self.prompt = self._build_prompt()
        self.chain = self.prompt | self.llm

    def _build_prompt(self) -> ChatPromptTemplate:
        system_prompt = """You are a surgical assistant robot.
        Extract tool, action, and handedness. If incision is mentioned and no tool → scalpel.
        If stitch is mentioned and no tool → scissors.
        Use handedness from doctor profiles: {handedness}
        Output JSON {{"tool": "...", "action": "...", "handedness": "..."}}"""
        return ChatPromptTemplate.from_messages([("system", system_prompt)])

    def obtain_input(self) -> Optional[str]:
        if INPUT_MODE == "voice":
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("🎤 Listening...")
                audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio)
                print(f"✅ You said: {text}")
                return text.lower()
            except Exception as e:
                print(f"❌ Speech error: {e}")
                return None
        elif INPUT_MODE == "typed":
            text = input("⌨️ Type your command: ")
            return text.lower()
        else:
            print("❌ Invalid INPUT_MODE config")
            return None

    def interpret_instruction(self, instruction: str) -> Optional[ToolAction]:
        try:
            response = self.chain.invoke({"input": instruction, "handedness": self.doctor_profiles})
            json_str = response.content if hasattr(response, "content") else response
            return ToolAction.model_validate_json(json_str)
        except ValidationError as e:
            print("❌ Validation error:", e)
            return None

    def send_to_esp32(self, letter: str):
        if not USE_ESP32:
            print(f"🚫 Skipped ESP32 send (would send: {letter})")
            return
        try:
            response = requests.get(f"{self.esp32_ip}/", params={"cmd": letter})
            print(f"📡 ESP32 response: {response.text}")
        except Exception as e:
            print(f"❌ ESP32 send failed: {e}")

    def log_action(self, action: ToolAction):
        entry = {
            "time": datetime.datetime.now().isoformat(),
            "tool": action.tool,
            "action": action.action,
            "hand": action.handedness,
        }
        self.tool_history.append(entry)
        print(f"📘 Logged: {entry}")


# ---------------- MAIN WORKFLOW ---------------- #
def main():
    assistant = SurgicalAssistant(esp32_ip=ESP32_IP, doctor_profiles=DOCTOR_PROFILES)

    while True:
        text = assistant.obtain_input()
        if not text:
            continue

        # Step 1: Check doctor profiles
        for doctor in DOCTOR_PROFILES:
            if doctor in text:
                print(f"👨‍⚕️ Doctor {doctor} detected")
                action = assistant.interpret_instruction(text)
                if action and action.action:
                    # Step 2: Map action to command
                    if action.action in COMMAND_MAP:
                        letter = COMMAND_MAP[action.action]
                        assistant.send_to_esp32(letter)
                        assistant.log_action(action)

        # Step 3: Camera condition
        if USE_CAMERA:
            detection = detect_object()
            if detection.get("object_detected"):
                print("📷 Object detected")
                assistant.send_to_esp32(COMMAND_MAP["object_detected"])

        # Step 4: Wait for confirmation
        print("➡️ Say/Type 'yes' to continue listening...")
        confirm = assistant.obtain_input()
        if confirm != "yes":
            print("👋 Exiting workflow")
            break


if __name__ == "__main__":
    main()
