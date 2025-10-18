from pathlib import Path
from typing import Dict


class TemplateLoader:
    """Load and manage agent templates"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self._cache = {}
    
    def load(self, template_name: str, **kwargs) -> str:
        """
        Load a template and format it with variables
        
        Args:
            template_name: Name of template file (without .txt)
            **kwargs: Variables to inject into template
        
        Returns:
            Formatted template string
        """
        # Check cache
        if template_name not in self._cache:
            template_path = self.template_dir / f"{template_name}.txt"
            
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                self._cache[template_name] = f.read()
        
        # Format with variables
        template = self._cache[template_name]
        return template.format(**kwargs)
    
    def reload(self):
        """Clear cache to reload templates"""
        self._cache.clear()


# Global instance
template_loader = TemplateLoader()