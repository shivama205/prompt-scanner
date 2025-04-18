from typing import List, Dict, Any, Union, Optional, Literal
from pydantic import BaseModel, Field, model_validator
from enum import Enum, auto

class SeverityLevel(str, Enum):
    """Enum for severity levels of safety categories"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

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
    
    def __str__(self) -> str:
        """String representation of category"""
        return f"{self.name} (confidence: {self.confidence:.2f})"

class CategorySeverity(BaseModel):
    """Represents the severity level of a safety category"""
    level: SeverityLevel = SeverityLevel.MEDIUM
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str = ""
    
    @property
    def name(self) -> str:
        """Return the name of the severity level for compatibility"""
        return self.level.value

class PromptScanResult(BaseModel):
    is_safe: bool = True
    category: Optional[PromptCategory] = None  # Main category (highest confidence)
    severity: Optional[CategorySeverity] = None  # Severity of the main category
    all_categories: List[Dict[str, Any]] = Field(default_factory=list)  # All detected categories
    reasoning: str = ""
    token_usage: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata about the scan
    
    @model_validator(mode='after')
    def set_default_severity(self):
        """Set default severity for unsafe content if not provided"""
        if not self.is_safe and self.category and not self.severity:
            self.severity = CategorySeverity(
                level=SeverityLevel.HIGH,
                score=0.8,
                description="Default high severity for unsafe content"
            )
        return self
    
    def __str__(self) -> str:
        """String representation of scan result for quick viewing"""
        if self.is_safe:
            return f"SAFE | Token usage: {self.token_usage}"
        else:
            category_info = f"Category: {self.category.name}"
            severity_info = f" | Severity: {self.severity.level.value}" if self.severity else ""
            if self.all_categories and len(self.all_categories) > 1:
                category_info += f" and {len(self.all_categories)-1} more"
            return f"UNSAFE | {category_info}{severity_info} | Reasoning: {self.reasoning} | Token usage: {self.token_usage}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the scan result to a dictionary for easier API consumption"""
        result = {
            "is_safe": self.is_safe,
            "reasoning": self.reasoning,
            "token_usage": self.token_usage,
            "metadata": self.metadata
        }
        
        if not self.is_safe and self.category:
            result["primary_category"] = {
                "id": self.category.id,
                "name": self.category.name,
                "confidence": self.category.confidence
            }
            
            if self.severity:
                result["severity"] = {
                    "level": self.severity.level.value,
                    "score": self.severity.score,
                    "description": self.severity.description
                }
            
            if self.all_categories:
                result["all_categories"] = self.all_categories
        
        return result
    
    def get_secondary_categories(self) -> List[Dict[str, Any]]:
        """Return all categories except the primary one"""
        if not self.all_categories or len(self.all_categories) <= 1:
            return []
        
        # Skip the first category (primary) and return the rest
        return self.all_categories[1:]
    
    def has_high_confidence_violation(self, threshold: float = 0.8) -> bool:
        """Check if there's a high confidence policy violation"""
        return (not self.is_safe and 
                self.category is not None and 
                self.category.confidence >= threshold)
    
    def get_highest_risk_categories(self, max_count: int = 3) -> List[Dict[str, Any]]:
        """Return the highest confidence categories, limited by max_count"""
        if not self.all_categories:
            return []
        
        # Return sorted categories by confidence, limited by max_count
        return sorted(
            self.all_categories, 
            key=lambda x: x.get("confidence", 0), 
            reverse=True
        )[:max_count]

class CustomGuardrail(BaseModel):
    """Model representing a custom user-defined guardrail"""
    name: str
    type: str  # Examples: "moderation", "privacy", "format", "limit"
    description: str
    patterns: List[Dict[str, Any]] = Field(default_factory=list)
    threshold: Optional[float] = None
    max_tokens: Optional[int] = None
    formats: Optional[List[str]] = None

class CustomCategory(BaseModel):
    """Model representing a custom user-defined content policy category"""
    id: str
    name: str
    description: str
    examples: List[str] = Field(default_factory=list) 