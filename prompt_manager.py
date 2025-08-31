"""
Dynamic Prompt Management System
Handles loading, caching, and hot-swapping of AI prompts
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """Manages externalized AI prompts with hot-reload capabilities"""
    
    def __init__(self, prompts_file: str = "prompts/prompts.json"):
        self.prompts_file = prompts_file
        self.prompts_cache = {}
        self.last_modified = 0
        self.load_prompts()
    
    def load_prompts(self) -> Dict[str, Any]:
        """Load prompts from JSON file with caching"""
        try:
            # Check if file has been modified
            current_modified = os.path.getmtime(self.prompts_file)
            
            if current_modified > self.last_modified or not self.prompts_cache:
                logger.info(f"Loading prompts from {self.prompts_file}")
                
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self.prompts_cache = json.load(f)
                
                self.last_modified = current_modified
                logger.info(f"Loaded prompts version: {self.prompts_cache.get('metadata', {}).get('version', 'unknown')}")
                
            return self.prompts_cache
            
        except FileNotFoundError:
            logger.error(f"Prompts file not found: {self.prompts_file}")
            return self._get_fallback_prompts()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompts file: {e}")
            return self._get_fallback_prompts()
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            return self._get_fallback_prompts()
    
    def get_prompt(self, product: str, tier: str, version: str = "latest") -> Dict[str, Any]:
        """Get specific prompt configuration"""
        prompts = self.load_prompts()  # Always check for updates
        
        try:
            prompt_config = prompts[product][tier]
            logger.info(f"Retrieved prompt: {product}.{tier} v{prompt_config.get('version', 'unknown')}")
            return prompt_config
        except KeyError:
            logger.error(f"Prompt not found: {product}.{tier}")
            return self._get_fallback_prompt(product, tier)
    
    def format_prompt(self, product: str, tier: str, **kwargs) -> str:
        """Format prompt with dynamic variables"""
        prompt_config = self.get_prompt(product, tier)
        user_prompt = prompt_config.get('user_prompt', '')
        
        try:
            formatted_prompt = user_prompt.format(**kwargs)
            return formatted_prompt
        except KeyError as e:
            logger.error(f"Missing variable for prompt formatting: {e}")
            return user_prompt  # Return unformatted as fallback
    
    def get_system_prompt(self, product: str, tier: str) -> str:
        """Get system prompt for AI model"""
        prompt_config = self.get_prompt(product, tier)
        return prompt_config.get('system_prompt', '')
    
    def get_tone_guidelines(self, product: str, tier: str) -> list:
        """Get tone guidelines for reference"""
        prompt_config = self.get_prompt(product, tier)
        return prompt_config.get('tone_guidelines', [])
    
    def reload_prompts(self) -> bool:
        """Force reload prompts from file"""
        try:
            self.last_modified = 0  # Force reload
            self.load_prompts()
            logger.info("Prompts reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading prompts: {e}")
            return False
    
    def _get_fallback_prompts(self) -> Dict[str, Any]:
        """Fallback prompts in case of file loading issues"""
        return {
            "metadata": {"version": "fallback", "description": "Emergency fallback prompts"},
            "resume_analysis": {
                "free": {
                    "version": "fallback",
                    "system_prompt": "You are a helpful career coach providing resume feedback.",
                    "user_prompt": "Please analyze this resume: {resume_text}"
                }
            }
        }
    
    def _get_fallback_prompt(self, product: str, tier: str) -> Dict[str, Any]:
        """Fallback for specific missing prompts"""
        return {
            "version": "fallback",
            "system_prompt": f"You are a helpful assistant providing {product} {tier} analysis.",
            "user_prompt": "Please provide analysis based on the input provided."
        }
    
    def validate_prompts(self) -> Dict[str, list]:
        """Validate prompt structure and return any issues"""
        issues = {"errors": [], "warnings": []}
        prompts = self.load_prompts()
        
        # Expected structure validation
        expected_products = ["resume_analysis", "job_fit", "cover_letter"]
        expected_tiers = ["free", "premium"]
        
        for product in expected_products:
            if product not in prompts:
                issues["errors"].append(f"Missing product: {product}")
                continue
                
            for tier in expected_tiers:
                if tier not in prompts[product]:
                    issues["errors"].append(f"Missing tier: {product}.{tier}")
                    continue
                
                prompt_config = prompts[product][tier]
                required_fields = ["system_prompt", "user_prompt", "version"]
                
                for field in required_fields:
                    if field not in prompt_config:
                        issues["errors"].append(f"Missing field: {product}.{tier}.{field}")
                
                # Check for placeholder variables
                user_prompt = prompt_config.get("user_prompt", "")
                if "{resume_text}" not in user_prompt:
                    issues["warnings"].append(f"No resume_text placeholder in: {product}.{tier}")
        
        return issues
    
    def get_prompt_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded prompts"""
        prompts = self.load_prompts()
        stats = {
            "total_products": 0,
            "total_prompts": 0,
            "versions": {},
            "last_updated": prompts.get("metadata", {}).get("last_updated", "unknown"),
            "file_size": os.path.getsize(self.prompts_file) if os.path.exists(self.prompts_file) else 0
        }
        
        for product in ["resume_analysis", "job_fit", "cover_letter"]:
            if product in prompts:
                stats["total_products"] += 1
                for tier in ["free", "premium"]:
                    if tier in prompts[product]:
                        stats["total_prompts"] += 1
                        version = prompts[product][tier].get("version", "unknown")
                        if version not in stats["versions"]:
                            stats["versions"][version] = 0
                        stats["versions"][version] += 1
        
        return stats


# Global instance for use throughout the application
prompt_manager = PromptManager()

# Convenience functions for easy imports
def get_prompt(product: str, tier: str) -> Dict[str, Any]:
    """Global function to get prompts"""
    return prompt_manager.get_prompt(product, tier)

def format_prompt(product: str, tier: str, **kwargs) -> str:
    """Global function to format prompts"""
    return prompt_manager.format_prompt(product, tier, **kwargs)

def get_system_prompt(product: str, tier: str) -> str:
    """Global function to get system prompts"""
    return prompt_manager.get_system_prompt(product, tier)

def reload_prompts() -> bool:
    """Global function to reload prompts"""
    return prompt_manager.reload_prompts()