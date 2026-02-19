"""
Question Parser Module
Parses CCNA exam questions from text files in multiple formats
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional


class QuestionParser:
    """
    Parses and manages CCNA exam questions from text files

    Supports two formats:
    Format A - Numbered with separate answer line
    Format B - Asterisk marking correct answer
    """

    def __init__(self, test_bank_dir: str = None):
        """
        Initialize the QuestionParser

        Args:
            test_bank_dir: Directory containing test bank files. Defaults to ../data/test_bank/
        """
        if test_bank_dir is None:
            current_dir = Path(__file__).parent.parent
            test_bank_dir = current_dir / "data" / "test_bank"

        self.test_bank_dir = Path(test_bank_dir)
        self.questions: List[Dict] = []
        self.questions_by_id: Dict[str, Dict] = {}

    def parse_file(self, filepath: str) -> List[Dict]:
        """
        Parse questions from a single text file

        Args:
            filepath: Path to the question file

        Returns:
            List of question dictionaries
        """
        questions = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Only try Format A if file contains "Answer:" lines (avoids slow regex on large files)
            if re.search(r'^Answer:', content, re.MULTILINE):
                format_a_questions = self._parse_format_a(content)
                if format_a_questions:
                    questions.extend(format_a_questions)

            # Try Format B (asterisk marking correct answer)
            format_b_questions = self._parse_format_b(content)
            if format_b_questions:
                questions.extend(format_b_questions)

        except Exception as e:
            print(f"Error parsing file {filepath}: {e}")

        return questions

    def _parse_format_a(self, content: str) -> List[Dict]:
        """
        Parse Format A: Numbered questions with lettered answers and "Answer:" line

        Example:
        1. What protocol operates at Layer 3?
        a) Ethernet
        b) IP
        c) TCP
        d) HTTP
        Answer: b
        """
        questions = []

        # Pattern to match numbered questions
        # Matches: number, question text, choices (a-d or A-D), and Answer line
        pattern = r'(\d+)\.\s+(.+?)\n([a-dA-D][\)\.].*?)(?=Answer:|answer:)'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            question_num = match.group(1)
            question_text = match.group(2).strip()
            choices_block = match.group(3).strip()

            # Find the answer line
            answer_pattern = r'[Aa]nswer:\s*([a-dA-D])'
            answer_match = re.search(answer_pattern, content[match.end():match.end()+50])

            if not answer_match:
                continue

            correct_answer = answer_match.group(1).lower()

            # Parse choices
            choices = self._parse_choices(choices_block)

            if not choices:
                continue

            question_dict = {
                "id": f"q{question_num.zfill(3)}",
                "question_text": question_text,
                "question_text_original": question_text,
                "choices": choices,
                "choices_original": choices.copy(),
                "correct_answer": correct_answer,
                "protocol_tags": [],
                "multi_protocol": False,
                "concept_group": None
            }

            questions.append(question_dict)

        return questions

    def _parse_format_b(self, content: str) -> List[Dict]:
        """
        Parse Format B: Questions with asterisk marking correct answer

        Supports:
        - Questions ending with ? or starting with a number (e.g., "39. ...")
        - 2-6 answer choices (A-F)
        - Multiple correct answers for "Choose two" questions

        Example:
        What is the default administrative distance of OSPF?
        A. 90
        B. 100
        *C. 110
        D. 120
        """
        questions = []
        question_id_counter = 1

        lines = content.split('\n')
        choice_pattern = r'^(\*?)([A-Fa-f])[\.\)]\s+(.+)$'

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this line starts a question
            question_text = None

            # Pattern 1: Numbered question (e.g., "39. A corporate office...")
            numbered_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if numbered_match:
                question_text = numbered_match.group(2)
            # Pattern 2: Line ending with ? (original behavior)
            elif line.endswith('?') and len(line) > 10:
                question_text = line

            if question_text:
                choices = {}
                correct_answers = []

                # Look ahead for answer choices (A-F with optional asterisk)
                j = i + 1

                while j < len(lines):
                    choice_line = lines[j].strip()

                    # Stop at next numbered question
                    if re.match(r'^\d+\.\s+', choice_line):
                        break

                    choice_match = re.match(choice_pattern, choice_line)

                    if choice_match:
                        asterisk = choice_match.group(1)
                        choice_letter = choice_match.group(2).lower()
                        choice_text = choice_match.group(3).strip()

                        choices[choice_letter] = choice_text

                        if asterisk == '*':
                            correct_answers.append(choice_letter)

                        j += 1
                    elif not choice_line:
                        # Empty line - check if more choices follow
                        if j + 1 < len(lines) and re.match(choice_pattern, lines[j + 1].strip()):
                            j += 1
                        else:
                            break
                    else:
                        # Non-choice, non-empty line
                        if not choices:
                            # Continuation of question text before choices start
                            question_text += ' ' + choice_line
                            j += 1
                        else:
                            break

                # Valid question: at least 2 choices and at least one correct answer
                if len(choices) >= 2 and correct_answers:
                    correct_answer = ','.join(sorted(correct_answers))

                    question_dict = {
                        "id": f"qb{str(question_id_counter).zfill(3)}",
                        "question_text": question_text,
                        "question_text_original": question_text,
                        "choices": choices,
                        "choices_original": choices.copy(),
                        "correct_answer": correct_answer,
                        "multi_answer": len(correct_answers) > 1,
                        "protocol_tags": [],
                        "multi_protocol": False,
                        "concept_group": None
                    }

                    questions.append(question_dict)
                    question_id_counter += 1
                    i = j
                    continue

            i += 1

        return questions

    def _parse_choices(self, choices_block: str) -> Dict[str, str]:
        """
        Parse answer choices from a text block

        Args:
            choices_block: Text containing the answer choices

        Returns:
            Dictionary mapping choice letters to choice text
        """
        choices = {}

        # Pattern to match choices: a) or a. followed by text
        pattern = r'([a-fA-F])[\)\.]\s+(.+?)(?=\n[a-fA-F][\)\.]|\Z)'
        matches = re.finditer(pattern, choices_block, re.DOTALL)

        for match in matches:
            letter = match.group(1).lower()
            text = match.group(2).strip()
            choices[letter] = text

        return choices

    def tag_questions(self, questions: List[Dict], protocols_list: List[str]) -> None:
        """
        Tag questions with protocol associations

        Args:
            questions: List of question dictionaries to tag
            protocols_list: List of protocol names/slugs to search for
        """
        for question in questions:
            # Combine question text and choices for searching
            search_text = question["question_text"] + " " + " ".join(question["choices"].values())
            search_text = search_text.lower()

            # Check each protocol
            for protocol in protocols_list:
                if not protocol:  # Skip empty strings
                    continue

                protocol_lower = protocol.lower()

                # Check if protocol name appears in the question (exact or word boundary match)
                # Use word boundaries to avoid false positives
                pattern = r'\b' + re.escape(protocol_lower) + r'\b'
                if re.search(pattern, search_text):
                    if protocol not in question["protocol_tags"]:
                        question["protocol_tags"].append(protocol)
                # Also check for components of compound names (e.g., "TCP" in "TCP/IP")
                elif '/' in protocol_lower:
                    for part in protocol_lower.split('/'):
                        part_pattern = r'\b' + re.escape(part) + r'\b'
                        if re.search(part_pattern, search_text):
                            if protocol not in question["protocol_tags"]:
                                question["protocol_tags"].append(protocol)
                            break

            # Set multi_protocol flag
            question["multi_protocol"] = len(question["protocol_tags"]) >= 2

    def load_all_questions(self, protocols_list: List[str] = None) -> None:
        """
        Load and parse all question files from the test bank directory

        Args:
            protocols_list: Optional list of protocols for tagging
        """
        if not self.test_bank_dir.exists():
            print(f"Warning: Test bank directory not found at {self.test_bank_dir}")
            return

        self.questions = []
        self.questions_by_id = {}

        # Parse all .txt files in the test bank directory
        for file_path in self.test_bank_dir.glob("*.txt"):
            questions = self.parse_file(str(file_path))

            # Extract topic slug from filename (e.g., CCNA_ospf.txt -> ospf)
            filename = file_path.stem  # e.g., "CCNA_ospf"
            file_slug = None
            if filename.startswith("CCNA_"):
                file_slug = filename[5:]  # e.g., "ospf"

            for q in questions:
                # Make IDs unique per file by prefixing with file slug
                if file_slug:
                    q["id"] = f"{file_slug}_{q['id']}"
                    # Tag question with its source topic
                    if file_slug not in q["protocol_tags"]:
                        q["protocol_tags"].append(file_slug)

            self.questions.extend(questions)

        # Also tag by keyword matching if protocol list provided
        if protocols_list:
            self.tag_questions(self.questions, protocols_list)

        # Build ID index
        for question in self.questions:
            self.questions_by_id[question["id"]] = question

        print(f"Loaded {len(self.questions)} questions from {self.test_bank_dir}")

    def get_questions_by_protocol(self, protocol_slug: str) -> List[Dict]:
        """
        Get all questions tagged with a specific protocol
        Multi-protocol questions appear in all relevant protocol lists

        Args:
            protocol_slug: The protocol slug to filter by

        Returns:
            List of questions tagged with this protocol
        """
        # Normalize slug for comparison (handle both "tcp-ip" and "tcp/ip" formats)
        slug_normalized = protocol_slug.lower().replace('-', '/')

        return [
            q for q in self.questions
            if any(
                protocol_slug.lower() == tag.lower() or
                slug_normalized == tag.lower().replace('-', '/')
                for tag in q["protocol_tags"]
            )
        ]

    def get_multi_protocol_questions(self) -> List[Dict]:
        """
        Get all questions tagged with 2 or more protocols

        Returns:
            List of multi-protocol questions
        """
        return [q for q in self.questions if q["multi_protocol"]]

    def get_all_questions(self) -> List[Dict]:
        """
        Get all parsed questions

        Returns:
            List of all questions
        """
        return self.questions

    def get_question_by_id(self, question_id: str) -> Optional[Dict]:
        """
        Get a specific question by ID

        Args:
            question_id: The question ID

        Returns:
            Question dictionary or None if not found
        """
        return self.questions_by_id.get(question_id)
