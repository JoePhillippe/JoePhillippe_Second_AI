"""
Config Guide Module
Loads and indexes Cisco configuration guide content (router and switch)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


class ConfigGuideManager:
    """Manages loading and searching of Cisco configuration guides"""

    def __init__(self, base_path: str = None):
        """
        Initialize the ConfigGuideManager

        Args:
            base_path: Base path to the data directory. Defaults to ../data relative to this file.
        """
        if base_path is None:
            # Get path relative to this file
            current_dir = Path(__file__).parent.parent
            base_path = current_dir / "data" / "config_guides"

        self.base_path = Path(base_path)
        self.router_path = self.base_path / "router"
        self.switch_path = self.base_path / "switch"

        # Storage for loaded guides
        self.guides: Dict[str, Dict[str, str]] = {
            "router": {},
            "switch": {}
        }

        # Load guides on initialization
        self.load_all_guides()

    def load_all_guides(self) -> None:
        """
        Load all .txt and .md files from router/ and switch/ folders
        Stores content indexed by device type and filename
        """
        # Load router guides
        if self.router_path.exists():
            for file_path in self.router_path.glob("*"):
                if file_path.suffix in [".txt", ".md"]:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            topic = file_path.stem  # filename without extension
                            self.guides["router"][topic] = content
                    except Exception as e:
                        print(f"Error loading router guide {file_path}: {e}")

        # Load switch guides
        if self.switch_path.exists():
            for file_path in self.switch_path.glob("*"):
                if file_path.suffix in [".txt", ".md"]:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            topic = file_path.stem
                            self.guides["switch"][topic] = content
                    except Exception as e:
                        print(f"Error loading switch guide {file_path}: {e}")

    def search_guides(self, keywords: List[str]) -> List[Dict[str, str]]:
        """
        Search all guides for content matching the given keywords

        Args:
            keywords: List of keywords to search for

        Returns:
            List of dictionaries with matching sections containing:
            - device_type: "router" or "switch"
            - topic: The guide topic/filename
            - content: The relevant section of text
        """
        if not self.guides["router"] and not self.guides["switch"]:
            return [{
                "device_type": "placeholder",
                "topic": "No guides loaded",
                "content": "No Cisco configuration guides have been loaded yet. Please add .txt or .md files to data/config_guides/router/ and data/config_guides/switch/."
            }]

        results = []

        # Search both router and switch guides
        for device_type in ["router", "switch"]:
            for topic, content in self.guides[device_type].items():
                # Check if any keyword appears in the content (case-insensitive)
                content_lower = content.lower()
                if any(keyword.lower() in content_lower for keyword in keywords):
                    # Extract relevant sections (paragraphs containing keywords)
                    relevant_sections = self._extract_relevant_sections(content, keywords)
                    if relevant_sections:
                        results.append({
                            "device_type": device_type,
                            "topic": topic,
                            "content": relevant_sections
                        })

        return results if results else [{
            "device_type": "none",
            "topic": "No matches",
            "content": "No configuration guide sections found matching the provided keywords."
        }]

    def get_guide_section(self, device_type: str, topic: str) -> Optional[str]:
        """
        Get a specific configuration guide section

        Args:
            device_type: "router" or "switch"
            topic: The guide topic/filename

        Returns:
            The guide content, or None if not found
        """
        if not self.guides["router"] and not self.guides["switch"]:
            return "No Cisco configuration guides have been loaded yet. Please add .txt or .md files to data/config_guides/router/ and data/config_guides/switch/."

        if device_type not in ["router", "switch"]:
            return None

        return self.guides[device_type].get(topic)

    def _extract_relevant_sections(self, content: str, keywords: List[str], context_lines: int = 3) -> str:
        """
        Extract sections of text that contain the keywords with surrounding context

        Args:
            content: The full text content
            keywords: Keywords to search for
            context_lines: Number of lines before/after to include for context

        Returns:
            Extracted relevant sections
        """
        lines = content.split('\n')
        relevant_line_indices = set()

        # Find lines containing keywords
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in keywords):
                # Add this line and surrounding context
                for j in range(max(0, i - context_lines), min(len(lines), i + context_lines + 1)):
                    relevant_line_indices.add(j)

        if not relevant_line_indices:
            return ""

        # Extract sections
        sorted_indices = sorted(relevant_line_indices)
        sections = []
        current_section = []

        for i, idx in enumerate(sorted_indices):
            if i > 0 and idx > sorted_indices[i-1] + 1:
                # Gap detected, save current section and start new one
                sections.append('\n'.join(current_section))
                current_section = []
            current_section.append(lines[idx])

        # Add final section
        if current_section:
            sections.append('\n'.join(current_section))

        return '\n...\n'.join(sections)

    def get_all_topics(self) -> Dict[str, List[str]]:
        """
        Get a list of all available guide topics by device type

        Returns:
            Dictionary with device types as keys and lists of topics as values
        """
        return {
            "router": list(self.guides["router"].keys()),
            "switch": list(self.guides["switch"].keys())
        }
