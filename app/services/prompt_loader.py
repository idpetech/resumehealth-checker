"""
Simple prompt loader service for individual prompt files.
This replaces the complex JSON parsing with simple file reading.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    """Loads prompts from individual markdown files."""
    
    def __init__(self, prompts_dir: str = "app/data/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache = {}
    
    def _load_prompt_file(self, filename: str) -> Optional[Dict[str, str]]:
        """Load a single prompt file and parse it into components."""
        if filename in self._cache:
            return self._cache[filename]
        
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            logger.error(f"Prompt file not found: {file_path}")
            return None
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse markdown sections
            sections = {}
            current_section = None
            current_content = []
            
            for line in content.split('\n'):
                line = line.strip()
                
                if line.startswith('# '):
                    # Main title - skip
                    continue
                elif line.startswith('## '):
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    # Start new section
                    current_section = line[3:].lower().replace(' ', '_')
                    current_content = []
                elif line and current_section:
                    current_content.append(line)
            
            # Save last section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Extract system and user prompts
            result = {
                'system_prompt': sections.get('system_prompt', ''),
                'user_prompt': sections.get('user_prompt', ''),
                'tone_guidelines': sections.get('tone_guidelines', '').split('\n') if sections.get('tone_guidelines') else []
            }
            
            self._cache[filename] = result
            logger.info(f"✅ Loaded prompt file: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error loading prompt file {filename}: {e}")
            return None
    
    def get_resume_analysis_prompt(self, is_premium: bool = False) -> Dict[str, str]:
        """Get resume analysis prompt (free or premium)."""
        filename = f"resume_analysis_{'premium' if is_premium else 'free'}.md"
        return self._load_prompt_file(filename) or {}
    
    def get_job_fit_prompt(self, is_premium: bool = False) -> Dict[str, str]:
        """Get job fit analysis prompt (free or premium)."""
        filename = f"job_fit_{'premium' if is_premium else 'free'}.md"
        return self._load_prompt_file(filename) or {}
    
    def get_cover_letter_prompt(self, is_premium: bool = False) -> Dict[str, str]:
        """Get cover letter prompt (free or premium)."""
        filename = f"cover_letter_{'premium' if is_premium else 'free'}.md"
        return self._load_prompt_file(filename) or {}
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
        logger.info("Prompt cache cleared")

# Global instance
prompt_loader = PromptLoader()
