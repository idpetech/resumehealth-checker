"""
Template Service

This module handles loading and rendering HTML templates.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateService:
    """Service for loading and serving HTML templates"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self._template_cache = {}
    
    def load_template(self, template_name: str) -> str:
        """Load a template file and cache it"""
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        template_path = self.template_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found at {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cache the template
            self._template_cache[template_name] = content
            logger.info(f"Loaded template: {template_name} ({len(content)} characters)")
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            raise
    
    def get_index_html(self) -> str:
        """Get the main index.html template"""
        return self.load_template("index.html")
    
    def clear_cache(self):
        """Clear the template cache (useful for development)"""
        self._template_cache.clear()
        logger.info("Template cache cleared")

# Global template service instance
template_service = TemplateService()