from typing import List, Dict, Any, Union, Optional, Literal
from pydantic import BaseModel, Field, model_validator

class Message(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

class OpenAIPrompt(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_messages_roles(self):
        # Validate that at least one message exists
        if not self.messages:
            raise ValueError("At least one message is required")
        
        # Validate roles for OpenAI (system, user, assistant, tool, function)
        valid_roles = {"system", "user", "assistant", "tool", "function"}
        for i, msg in enumerate(self.messages):
            if msg.role not in valid_roles:
                raise ValueError(f"Message at index {i} has invalid role: {msg.role}")
        return self

class AnthropicMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[Dict[str, Any]]]

class AnthropicPrompt(BaseModel):
    messages: List[AnthropicMessage]
    model: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_messages(self):
        # Validate that at least one message exists
        if not self.messages:
            raise ValueError("At least one message is required")
        
        # Additional Anthropic-specific validations can be added here
        return self

# For old Anthropic API format
class OldAnthropicPrompt(BaseModel):
    prompt: str
    model: Optional[str] = None

# Union type for all supported prompt formats
PromptType = Union[OpenAIPrompt, AnthropicPrompt, OldAnthropicPrompt] 

# Prompt Scanning Result Model
class PromptCategory(BaseModel):
    id: str
    name: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_patterns: List[str] = Field(default_factory=list)

class PromptScanResult(BaseModel):
    is_safe: bool = True
    category: Optional[PromptCategory] = None  # Main category (highest confidence)
    all_categories: List[Dict[str, Any]] = Field(default_factory=list)  # All detected categories
    reasoning: str = ""
    token_usage: Dict[str, int] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of scan result for quick viewing"""
        if self.is_safe:
            return f"SAFE | Token usage: {self.token_usage}"
        else:
            category_info = f"Category: {self.category.name}"
            if self.all_categories and len(self.all_categories) > 1:
                category_info += f" and {len(self.all_categories)-1} more"
            return f"UNSAFE | {category_info} | Reasoning: {self.reasoning} | Token usage: {self.token_usage}" 