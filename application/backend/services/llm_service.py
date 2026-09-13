"""
LLM Service for processing surgical instructions.
Supports OpenAI, Ollama, and OpenRouter providers.
"""

import json
import logging
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, ValidationError

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI as OpenRouterChat

from ..config import Config
from ..prompts import SurgicalPrompts, get_prompt_config, PROMPT_CONFIGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolAction(BaseModel):
    """Model for LLM response structure."""
    tool: Optional[str] = Field(None, description="Surgical tool to use")
    action: Optional[str] = Field(None, description="Action to perform")
    handedness: Optional[str] = Field(None, description="Handedness (left/right)")


def detect_doctor(instruction: str, profiles: Dict[str, Dict[str, str]]) -> Optional[str]:
    """Return the first configured doctor whose name appears in the instruction."""
    lowered = instruction.lower()
    for doctor in profiles:
        if doctor.lower() in lowered:
            return doctor
    return None


def extract_json_block(raw: str) -> str:
    """Strip markdown fences and surrounding prose from an LLM reply, leaving the JSON object."""
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return text.strip()


def parse_tool_action(raw: str) -> ToolAction:
    """Validate an LLM reply into a ToolAction. Raises ValidationError / JSONDecodeError."""
    return ToolAction.model_validate_json(extract_json_block(raw))


class LLMService:
    """Service for processing surgical instructions using various LLM providers."""
    
    def __init__(self):
        """Initialize the LLM service with the configured provider."""
        self.provider = Config.LLM_PROVIDER
        self.model = Config.LLM_MODEL
        self.doctor_profiles = Config.DOCTOR_PROFILES
        self.prompt_config = get_prompt_config("default")
        self.llm = self._initialize_llm()
        self.prompt = self._build_prompt()
        self.chain = self.prompt | self.llm
        
        logger.info(f"✅ LLM Service initialized with provider: {self.provider}, model: {self.model}")
    
    def _initialize_llm(self) -> Any:
        """Initialize the LLM based on the configured provider."""
        if self.provider == "openai":
            if not Config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return ChatOpenAI(
                model=self.model,
                api_key=Config.OPENAI_API_KEY,
                temperature=0.1
            )
        
        elif self.provider == "ollama":
            return ChatOllama(
                model=self.model,
                format="json",
                temperature=0.1
            )
        
        elif self.provider == "openrouter":
            if not Config.OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY is required for OpenRouter provider")
            return OpenRouterChat(
                model=self.model,
                api_key=Config.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.1
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the prompt template for surgical instruction processing."""
        return SurgicalPrompts.build_main_prompt()
    
    def process_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Process a surgical instruction and return structured output.
        
        Args:
            instruction: The surgical instruction text
            
        Returns:
            Dictionary containing tool, action, and handedness
        """
        try:
            logger.info(f"🔄 Processing instruction: {instruction}")
            
            detected_doctor = detect_doctor(instruction, self.doctor_profiles)
            
            if not detected_doctor:
                logger.warning("⚠️ No doctor detected in instruction")
                return {
                    "tool": None,
                    "action": None,
                    "handedness": None,
                    "error": "No doctor detected in instruction"
                }
            
            # Get handedness for detected doctor
            handedness = self.doctor_profiles[detected_doctor]["handedness"]
            
            # Process with LLM
            response = self.chain.invoke({
                "input": instruction,
                "handedness": self.doctor_profiles
            })
            
            raw = response.content if hasattr(response, 'content') else str(response)
            result = parse_tool_action(raw)
            
            # Convert to dict
            result_dict = {
                "tool": result.tool,
                "action": result.action,
                "handedness": result.handedness,
                "doctor": detected_doctor
            }
            
            logger.info(f"✅ LLM result: {result_dict}")
            return result_dict
            
        except ValidationError as e:
            logger.error(f"❌ Validation error: {e}")
            return {
                "tool": None,
                "action": None,
                "handedness": None,
                "error": f"Validation error: {str(e)}"
            }
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return {
                "tool": None,
                "action": None,
                "handedness": None,
                "error": f"JSON decode error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {
                "tool": None,
                "action": None,
                "handedness": None,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def set_prompt_config(self, config_name: str) -> None:
        """
        Change the prompt configuration.
        
        Args:
            config_name: Name of the prompt configuration to use
        """
        self.prompt_config = get_prompt_config(config_name)
        self.prompt = self._build_prompt()
        self.chain = self.prompt | self.llm
        logger.info(f"🔄 LLM Service prompt configuration changed to: {config_name}")
    
    def get_available_prompt_configs(self) -> list:
        """
        Get list of available prompt configurations.
        
        Returns:
            List of available configuration names
        """
        return list(PROMPT_CONFIGS.keys())
