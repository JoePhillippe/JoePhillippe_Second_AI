"""
Protocol Manager Module
Loads and manages protocol data from JSON files
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional


class ProtocolManager:
    """Manages loading and accessing protocol data"""

    def __init__(self, base_path: str = None):
        """
        Initialize the ProtocolManager

        Args:
            base_path: Base path to the data/protocols directory. Defaults to ../data/protocols relative to this file.
        """
        if base_path is None:
            # Get path relative to this file
            current_dir = Path(__file__).parent.parent
            base_path = current_dir / "data" / "protocols"

        self.base_path = Path(base_path)

        # Storage for loaded protocols
        self.protocols: Dict[str, Dict] = {}

        # Load protocols on initialization
        self.load_all_protocols()

    def load_all_protocols(self) -> None:
        """
        Load all JSON files from data/protocols/ folder
        Stores protocol data indexed by slug
        """
        if not self.base_path.exists():
            print(f"Warning: Protocols directory not found at {self.base_path}")
            return

        for file_path in self.base_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    protocol_data = json.load(f)
                    slug = protocol_data.get("slug")
                    if slug:
                        self.protocols[slug] = protocol_data
                    else:
                        print(f"Warning: Protocol file {file_path} missing 'slug' field")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON in {file_path}: {e}")
            except Exception as e:
                print(f"Error loading protocol {file_path}: {e}")

    def get_all_protocols(self) -> List[Dict]:
        """
        Get a list of all protocol summaries

        Returns:
            List of protocol dictionaries with summary information
        """
        summaries = []
        for slug, protocol in self.protocols.items():
            summaries.append({
                "name": protocol.get("name", "Unknown"),
                "slug": slug,
                "category": protocol.get("category", "Uncategorized"),
                "description": protocol.get("description", ""),
                "exam_weight": protocol.get("exam_weight", "Medium")
            })

        # Sort by category, then by name
        summaries.sort(key=lambda x: (x["category"], x["name"]))
        return summaries

    def get_protocol(self, slug: str) -> Optional[Dict]:
        """
        Get full protocol data for a specific protocol

        Args:
            slug: The protocol slug (e.g., "tcp-ip", "ospf")

        Returns:
            Protocol data dictionary, or None if not found
        """
        return self.protocols.get(slug)

    def get_related_protocols(self, slug: str) -> List[Dict]:
        """
        Get related protocol data for a specific protocol

        Args:
            slug: The protocol slug

        Returns:
            List of related protocol dictionaries
        """
        protocol = self.get_protocol(slug)
        if not protocol:
            return []

        related_slugs = protocol.get("related_protocols", [])
        related = []

        for related_slug in related_slugs:
            related_protocol = self.get_protocol(related_slug)
            if related_protocol:
                related.append({
                    "name": related_protocol.get("name", "Unknown"),
                    "slug": related_slug,
                    "category": related_protocol.get("category", "Uncategorized")
                })

        return related

    def get_protocols_by_category(self) -> Dict[str, List[Dict]]:
        """
        Get all protocols grouped by category

        Returns:
            Dictionary with categories as keys and lists of protocols as values
        """
        by_category = {}

        for protocol in self.get_all_protocols():
            category = protocol["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(protocol)

        return by_category

    def protocol_exists(self, slug: str) -> bool:
        """
        Check if a protocol exists

        Args:
            slug: The protocol slug

        Returns:
            True if protocol exists, False otherwise
        """
        return slug in self.protocols
