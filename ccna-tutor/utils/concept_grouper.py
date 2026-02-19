"""
Concept Grouper Module
AI-powered grouping of exam questions by concept to reduce redundancy
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic


class ConceptGrouper:
    """
    Groups exam questions by underlying concept using AI analysis
    Detects redundant questions that test the same fact in different ways
    """

    def __init__(self, api_key: Optional[str] = None, groups_dir: str = None):
        """
        Initialize the ConceptGrouper

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var
            groups_dir: Directory for storing concept groups. Defaults to ../data/concept_groups/
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: ANTHROPIC_API_KEY not set. Concept grouping will use cached data only.")
        self.model = "claude-sonnet-4-20250514"

        if groups_dir is None:
            current_dir = Path(__file__).parent.parent
            groups_dir = current_dir / "data" / "concept_groups"

        self.groups_dir = Path(groups_dir)
        self.groups_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for loaded groups
        self.groups: Dict[str, List[Dict]] = {}  # protocol_slug -> list of group dicts
        self.manual_overrides: Dict[str, str] = {}  # question_id -> group_id

        # Load manual overrides if they exist
        self._load_manual_overrides()

    def _load_manual_overrides(self):
        """Load manual group overrides from JSON file"""
        overrides_path = self.groups_dir / "manual_overrides.json"
        if overrides_path.exists():
            try:
                with open(overrides_path, 'r', encoding='utf-8') as f:
                    self.manual_overrides = json.load(f)
                print(f"Loaded {len(self.manual_overrides)} manual overrides")
            except Exception as e:
                print(f"Error loading manual overrides: {e}")

    def analyze_and_group(self, questions_by_protocol: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Analyze questions and group by concept using AI

        Args:
            questions_by_protocol: Dict mapping protocol_slug to list of question dicts

        Returns:
            Dict mapping protocol_slug to list of concept group dicts
        """
        all_groups = {}

        for protocol_slug, questions in questions_by_protocol.items():
            if not questions:
                continue

            print(f"\nAnalyzing {len(questions)} questions for protocol: {protocol_slug}")

            # Format questions for AI analysis
            questions_text = self._format_questions_for_analysis(questions)

            # Send to Claude for analysis
            try:
                groups = self._call_ai_for_grouping(protocol_slug, questions_text, questions)
                all_groups[protocol_slug] = groups
                print(f"Created {len(groups)} concept groups for {protocol_slug}")

                # Save to cache
                self.save_groups(protocol_slug, groups)

                # Store in memory
                self.groups[protocol_slug] = groups

            except Exception as e:
                print(f"Error analyzing {protocol_slug}: {e}")
                # Create individual groups as fallback
                fallback_groups = self._create_individual_groups(questions)
                all_groups[protocol_slug] = fallback_groups
                self.groups[protocol_slug] = fallback_groups

        return all_groups

    def _format_questions_for_analysis(self, questions: List[Dict]) -> str:
        """Format questions as text for AI analysis"""
        formatted = []

        for q in questions:
            q_text = f"ID: {q['id']}\n"
            q_text += f"Question: {q['question_text']}\n"
            q_text += "Choices:\n"
            for letter, choice in sorted(q['choices'].items()):
                marker = "*" if letter == q['correct_answer'] else " "
                q_text += f"  {marker}{letter.upper()}. {choice}\n"
            formatted.append(q_text)

        return "\n---\n".join(formatted)

    def _call_ai_for_grouping(self, protocol_slug: str, questions_text: str, questions: List[Dict]) -> List[Dict]:
        """Call Claude API to analyze and group questions"""
        if not self.client:
            raise ValueError("No API key configured — cannot call AI for grouping")

        prompt = f"""Analyze these CCNA exam questions for the protocol: {protocol_slug}

Your task: Group questions that test the SAME specific fact or concept. Questions belong in the same group if a student who truly understands the tested concept could answer ALL of them. Watch for these patterns:

1. SAME CONCEPT, DIFFERENT WORDING: Questions that ask the same thing with different phrasing
2. QUESTION-ANSWER SWAP: Questions where what's in the question stem of one becomes an answer choice in another, and vice versa. Example:
   - "What is the AD of OSPF?" (answer: 110)
   - "Which protocol has AD of 110?" (answer: OSPF)
   These test the IDENTICAL fact from opposite directions.
3. SAME FACT, DIFFERENT CONTEXT: Questions embedding the same core fact in different scenarios

For each group, identify:
- The specific concept/fact being tested (one sentence)
- Which questions belong in this group (by question ID)
- Confidence level: HIGH (clearly same concept) or MEDIUM (related but may test different nuances)

Questions that are unique (not redundant with any other) should each be their own group of 1.

Return your answer as JSON:
{{
  "concept_groups": [
    {{
      "group_id": "ospf_admin_distance",
      "concept": "OSPF default administrative distance is 110",
      "question_ids": ["q001", "q005", "q023"],
      "confidence": "HIGH"
    }}
  ]
}}

Here are the questions to analyze:

{questions_text}

Return ONLY the JSON, no other text."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse JSON response
        response_text = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            if response_text.startswith("json"):
                response_text = "\n".join(response_text.split("\n")[1:])

        try:
            result = json.loads(response_text)
            groups = result.get("concept_groups", [])

            # Apply manual overrides
            groups = self._apply_manual_overrides(groups, questions)

            return groups
        except json.JSONDecodeError as e:
            print(f"Error parsing AI response: {e}")
            print(f"Response was: {response_text[:200]}")
            raise

    def _apply_manual_overrides(self, groups: List[Dict], questions: List[Dict]) -> List[Dict]:
        """Apply manual overrides to concept groups"""
        if not self.manual_overrides:
            return groups

        # Build map of question_id -> group
        q_to_group = {}
        for group in groups:
            for qid in group.get("question_ids", []):
                q_to_group[qid] = group

        # Apply overrides
        for qid, override_group_id in self.manual_overrides.items():
            if qid in q_to_group:
                # Remove from current group
                current_group = q_to_group[qid]
                current_group["question_ids"].remove(qid)

                # Add to override group (or create new one)
                override_group = next((g for g in groups if g["group_id"] == override_group_id), None)
                if override_group:
                    if qid not in override_group["question_ids"]:
                        override_group["question_ids"].append(qid)
                else:
                    # Create new group
                    groups.append({
                        "group_id": override_group_id,
                        "concept": "Manually grouped",
                        "question_ids": [qid],
                        "confidence": "MANUAL"
                    })

        # Remove empty groups
        groups = [g for g in groups if g.get("question_ids")]

        return groups

    def _create_individual_groups(self, questions: List[Dict]) -> List[Dict]:
        """Create individual groups (fallback when AI analysis fails)"""
        groups = []
        for q in questions:
            groups.append({
                "group_id": f"individual_{q['id']}",
                "concept": q['question_text'][:100] + "...",
                "question_ids": [q['id']],
                "confidence": "INDIVIDUAL"
            })
        return groups

    def save_groups(self, protocol_slug: str, groups: List[Dict]):
        """Save concept groups to JSON file"""
        filepath = self.groups_dir / f"{protocol_slug}.json"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "protocol": protocol_slug,
                    "groups": groups,
                    "total_groups": len(groups),
                    "total_questions": sum(len(g.get("question_ids", [])) for g in groups)
                }, f, indent=2)

            print(f"Saved {len(groups)} groups to {filepath}")
        except Exception as e:
            print(f"Error saving groups: {e}")

    def load_groups(self, protocol_slug: str) -> Optional[List[Dict]]:
        """Load cached concept groups from JSON file"""
        filepath = self.groups_dir / f"{protocol_slug}.json"

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                groups = data.get("groups", [])
                self.groups[protocol_slug] = groups
                return groups
        except Exception as e:
            print(f"Error loading groups for {protocol_slug}: {e}")
            return None

    def get_groups_by_protocol(self, protocol_slug: str) -> List[Dict]:
        """
        Get all concept groups for a protocol with question counts

        Returns:
            List of group dicts with added 'group_size' field
        """
        groups = self.groups.get(protocol_slug, [])

        # Add group_size to each group
        enriched_groups = []
        for group in groups:
            enriched_group = group.copy()
            enriched_group['group_size'] = len(group.get('question_ids', []))
            enriched_groups.append(enriched_group)

        return enriched_groups

    def get_random_question_from_group(self, protocol_slug: str, group_id: str) -> Optional[str]:
        """
        Get a random question ID from a group

        Args:
            protocol_slug: The protocol slug
            group_id: The concept group ID

        Returns:
            Question ID or None if group not found
        """
        groups = self.groups.get(protocol_slug, [])
        group = next((g for g in groups if g.get('group_id') == group_id), None)

        if not group:
            return None

        question_ids = group.get('question_ids', [])
        if not question_ids:
            return None

        return random.choice(question_ids)

    def get_remaining_questions_in_group(self, protocol_slug: str, group_id: str, exclude_id: str) -> List[str]:
        """
        Get other question IDs in the same group

        Args:
            protocol_slug: The protocol slug
            group_id: The concept group ID
            exclude_id: Question ID to exclude

        Returns:
            List of question IDs (excluding the specified one)
        """
        groups = self.groups.get(protocol_slug, [])
        group = next((g for g in groups if g.get('group_id') == group_id), None)

        if not group:
            return []

        question_ids = group.get('question_ids', [])
        return [qid for qid in question_ids if qid != exclude_id]

    def enrich_questions_with_groups(self, protocol_slug: str, questions: List[Dict]) -> List[Dict]:
        """
        Add concept_group and group_size fields to questions

        Args:
            protocol_slug: The protocol slug
            questions: List of question dicts to enrich

        Returns:
            Enriched questions with concept_group and group_size fields
        """
        groups = self.groups.get(protocol_slug, [])

        # Build map of question_id -> group
        q_to_group = {}
        for group in groups:
            for qid in group.get("question_ids", []):
                q_to_group[qid] = group

        # Enrich questions
        enriched = []
        for q in questions:
            q_copy = q.copy()
            group = q_to_group.get(q['id'])

            if group:
                q_copy['concept_group'] = group['group_id']
                q_copy['group_size'] = len(group.get('question_ids', []))
            else:
                q_copy['concept_group'] = None
                q_copy['group_size'] = 1

            enriched.append(q_copy)

        return enriched
