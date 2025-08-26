"""
Prompts configuration for the Surgical Assistant application.
Centralized location for all LLM prompts and templates.
"""

from langchain_core.prompts import ChatPromptTemplate


class SurgicalPrompts:
    """Collection of prompts for surgical assistant LLM interactions."""
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        Get the main system prompt for surgical instruction processing.
        
        Returns:
            System prompt string
        """
        return """You are a surgical assistant robot.
Extract tool, action, and handedness from the given instruction.

Rules:
- If incision is mentioned and no tool specified → scalpel
- If stitch is mentioned and no tool specified → scissors
- Use handedness from doctor profiles: {handedness}
- Output must be valid JSON with exactly these fields: tool, action, handedness

Output JSON format: {{"tool": "...", "action": "...", "handedness": "..."}}

Example inputs and outputs:
- "hi sarath, you can start the incision" → {{"tool": "scalpel", "action": "incision", "handedness": "right"}}
- "kiran, please stitch the wound" → {{"tool": "scissors", "action": "stitch", "handedness": "left"}}
- "sarath, use the forceps to grasp the tissue" → {{"tool": "forceps", "action": "grasp", "handedness": "right"}}
- "kiran, make an incision with the scalpel" → {{"tool": "scalpel", "action": "incision", "handedness": "left"}}

Important:
- Similar words to stiching such as switching, switch, start city etc shall be consider as stiching
- Similar words to incision such as in session, insition shll be consider as incision
- Always include the doctor's name in the instruction
- Extract the specific tool mentioned or infer from the action
- Use the correct handedness based on the doctor profile
- Return only valid JSON, no additional text or explanations
"""

    @staticmethod
    def get_instruction_prompt() -> str:
        """
        Get the instruction prompt template.
        
        Returns:
            Instruction prompt string
        """
        return "Instruction: {input}"

    @staticmethod
    def get_validation_prompt() -> str:
        """
        Get a prompt for validating and correcting JSON output.
        
        Returns:
            Validation prompt string
        """
        return """You are a JSON validator for surgical assistant responses.
The following response should be valid JSON with exactly these fields: tool, action, handedness

If the response is not valid JSON, fix it and return only the corrected JSON.
If the response is valid JSON, return it as-is.

Response to validate: {response}

Return only the valid JSON, no explanations."""

    @staticmethod
    def get_error_recovery_prompt() -> str:
        """
        Get a prompt for recovering from parsing errors.
        
        Returns:
            Error recovery prompt string
        """
        return """The previous response had a JSON parsing error.
Please provide a valid JSON response for the surgical instruction.

Original instruction: {instruction}
Doctor profiles: {handedness}

Return only valid JSON with format: {{"tool": "...", "action": "...", "handedness": "..."}}"""

    @staticmethod
    def build_main_prompt() -> ChatPromptTemplate:
        """
        Build the main prompt template for surgical instruction processing.
        
        Returns:
            Configured ChatPromptTemplate
        """
        return ChatPromptTemplate.from_messages([
            ("system", SurgicalPrompts.get_system_prompt()),
            ("human", SurgicalPrompts.get_instruction_prompt())
        ])

    @staticmethod
    def get_doctor_detection_prompt() -> str:
        """
        Get a prompt for detecting doctor names in instructions.
        
        Returns:
            Doctor detection prompt string
        """
        return """Extract the doctor's name from the surgical instruction.
Available doctors: {doctors}

Instruction: {instruction}

Return only the doctor's name, or "unknown" if no doctor is mentioned."""

    @staticmethod
    def get_action_classification_prompt() -> str:
        """
        Get a prompt for classifying surgical actions.
        
        Returns:
            Action classification prompt string
        """
        return """Classify the surgical action mentioned in the instruction.
Common actions: incision, stitch, grasp, cut, suture, remove, insert, examine

Instruction: {instruction}

Return only the action name, or "unknown" if no clear action is mentioned."""

    @staticmethod
    def get_tool_extraction_prompt() -> str:
        """
        Get a prompt for extracting surgical tools.
        
        Returns:
            Tool extraction prompt string
        """
        return """Extract the surgical tool mentioned in the instruction.
Common tools: scalpel, scissors, forceps, needle, clamp, retractor, probe

If no tool is mentioned but an action is specified:
- incision → scalpel
- stitch/suture → scissors
- grasp/hold → forceps

Instruction: {instruction}
Action: {action}

Return only the tool name, or "unknown" if no tool can be determined."""


# Prompt configurations for different scenarios
PROMPT_CONFIGS = {
    "default": {
        "system_prompt": SurgicalPrompts.get_system_prompt(),
        "temperature": 0.1,
        "max_tokens": 150
    },
    "detailed": {
        "system_prompt": SurgicalPrompts.get_system_prompt() + "\n\nProvide detailed reasoning for tool and action selection.",
        "temperature": 0.2,
        "max_tokens": 300
    },
    "conservative": {
        "system_prompt": SurgicalPrompts.get_system_prompt() + "\n\nBe conservative in tool selection. If uncertain, choose the most common tool for the action.",
        "temperature": 0.05,
        "max_tokens": 100
    }
}


def get_prompt_config(config_name: str = "default") -> dict:
    """
    Get prompt configuration by name.
    
    Args:
        config_name: Name of the prompt configuration
        
    Returns:
        Dictionary containing prompt configuration
    """
    return PROMPT_CONFIGS.get(config_name, PROMPT_CONFIGS["default"])
