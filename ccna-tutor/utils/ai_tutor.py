"""
AI Tutor Module
Anthropic API integration with tutoring logic
"""

import os
from typing import Dict, List, Optional
from anthropic import Anthropic
from .config_guide import ConfigGuideManager


class CCNATutor:
    """
    CCNA Tutor with specific teaching methodology using Cisco configuration guides
    """

    SYSTEM_PROMPT = """You are an expert CCNA tutor. Your ONLY authoritative references are the Cisco configuration guides for routers and switches. You do NOT use third-party CCNA training books or websites as sources — these often contain misconceptions because their authors cannot review the actual CCNA exam.

Your students have completed three courses in a network administrator degree program. They understand basic networking terms and device configuration. Do not explain at a beginner level.

YOUR TEACHING METHOD:
A human remembers information best when forced to focus on one very small specific detail that is framed within a larger understanding of a network protocol. You use this principle in all interactions.

WHEN A STUDENT ANSWERS INCORRECTLY:
1. Do NOT reveal the correct answer yet
2. Give a combination of:
   - The broad concept the question is testing (the larger protocol understanding)
   - Specific details from the Cisco configuration guide that point toward the answer (the small detail to focus on)
3. Let the student try again

WHEN A STUDENT ANSWERS CORRECTLY:
1. Confirm they are correct
2. Explain WHY each of the other answer choices is incorrect
3. Reference specific Cisco configuration guide details for why the correct answer is right and the others are wrong
4. This reinforces learning by eliminating misconceptions about the wrong answers

IMPORTANT: Many CCNA training resources teach information that contradicts or oversimplifies what Cisco's own documentation says. When relevant, call this out as a common misconception."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CCNA Tutor

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set or api_key not provided")

        self.client = Anthropic(api_key=self.api_key)
        self.config_manager = ConfigGuideManager()
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 1500

    def get_config_context(self, question_data: Dict) -> str:
        """
        Search configuration guides for relevant sections based on question content

        Args:
            question_data: Dictionary containing question information with keys:
                - question: The question text
                - topic: Optional topic/protocol name
                - keywords: Optional list of keywords

        Returns:
            Relevant configuration guide content as a string
        """
        # Extract keywords from question data
        keywords = []

        if "keywords" in question_data and question_data["keywords"]:
            keywords.extend(question_data["keywords"])

        if "topic" in question_data and question_data["topic"]:
            keywords.append(question_data["topic"])

        # Extract potential keywords from question text
        if "question" in question_data:
            # Simple keyword extraction - could be enhanced with NLP
            question_text = question_data["question"]
            # Look for protocol names, common networking terms
            common_terms = ["OSPF", "EIGRP", "BGP", "RIP", "STP", "VLAN", "ACL", "NAT",
                          "routing", "switching", "port", "interface", "IP", "subnet"]
            for term in common_terms:
                if term.lower() in question_text.lower():
                    keywords.append(term)

        # Search guides if we have keywords
        if keywords:
            results = self.config_manager.search_guides(keywords)
            if results:
                # Format the results into a context string
                context_parts = []
                for result in results[:3]:  # Limit to top 3 results
                    if result["device_type"] != "placeholder" and result["device_type"] != "none":
                        context_parts.append(
                            f"From {result['device_type']} guide on {result['topic']}:\n{result['content']}"
                        )
                return "\n\n".join(context_parts) if context_parts else "No relevant configuration guide content found."

        return "No configuration guide content available for this topic yet."

    def handle_wrong_answer(
        self,
        question_data: Dict,
        student_answer: str,
        config_context: str,
        attempt_number: int = 1
    ) -> str:
        """
        Handle an incorrect answer by providing hints without revealing the answer

        Args:
            question_data: Dictionary with question info (question, options, correct_answer)
            student_answer: The student's incorrect answer
            config_context: Relevant Cisco configuration guide content
            attempt_number: Which attempt this is (for progressive hints)

        Returns:
            AI-generated hint combining broad concept and config guide details
        """
        try:
            hint_strength = "subtle" if attempt_number == 1 else "more specific" if attempt_number == 2 else "very specific"

            user_message = f"""The student answered this question INCORRECTLY:

Question: {question_data.get('question', 'N/A')}

Answer options:
{self._format_options(question_data.get('options', []))}

Student's answer: {student_answer}
Correct answer: {question_data.get('correct_answer', 'N/A')}

This is attempt #{attempt_number}. Provide a {hint_strength} hint.

Relevant Cisco configuration guide content:
{config_context}

Give a hint that combines:
1. The broad concept this question tests
2. Specific details from the Cisco configuration guide above that point toward the answer

Do NOT reveal the correct answer yet. Let the student try again."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating hint: {str(e)}"

    def handle_correct_answer(
        self,
        question_data: Dict,
        student_answer: str,
        config_context: str
    ) -> str:
        """
        Handle a correct answer by explaining why it's right and why others are wrong

        Args:
            question_data: Dictionary with question info (question, options, correct_answer)
            student_answer: The student's correct answer
            config_context: Relevant Cisco configuration guide content

        Returns:
            AI-generated explanation of correct answer and why others are incorrect
        """
        try:
            user_message = f"""The student answered this question CORRECTLY:

Question: {question_data.get('question', 'N/A')}

Answer options:
{self._format_options(question_data.get('options', []))}

Student's correct answer: {student_answer}

Relevant Cisco configuration guide content:
{config_context}

Confirm they are correct, then explain:
1. WHY their answer is correct (reference the config guide)
2. WHY each of the other answer choices is incorrect (reference the config guide)
3. If applicable, mention common misconceptions from third-party CCNA training materials"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating explanation: {str(e)}"

    def explain_concept(
        self,
        protocol_name: str,
        specific_topic: str,
        config_context: str
    ) -> str:
        """
        Explain a concept using the configuration guide as authority

        Args:
            protocol_name: Name of the protocol (e.g., "OSPF", "STP")
            specific_topic: Specific topic to explain (e.g., "neighbor formation", "port states")
            config_context: Relevant Cisco configuration guide content

        Returns:
            AI-generated explanation based on config guides
        """
        try:
            user_message = f"""Explain the following networking concept to a student:

Protocol: {protocol_name}
Specific Topic: {specific_topic}

Relevant Cisco configuration guide content:
{config_context}

Use the Cisco configuration guide content as your ONLY authoritative source. Focus on one small specific detail within the larger protocol understanding, as this helps students remember best.

If the config guide contradicts common third-party CCNA training materials, point this out as a common misconception."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error explaining concept: {str(e)}"

    # ==================== Practice (Questions-First) Methods ====================

    HINT_SYSTEM_PROMPT = """You are a CCNA tutor helping a student who answered incorrectly.

SOURCE HIERARCHY (use in this priority order):
1. PRIMARY — Cisco configuration guides for routers and switches (provided below as context)
2. SECONDARY — Official Cisco websites and documentation (cisco.com, Cisco Learning Network)
3. TERTIARY — Third-party CCNA books (Wendell Odom, Todd Lammle, etc.) only to add depth to concepts already established by sources 1 and 2

Always ground your hint in the configuration guide first. You may layer in additional context from Cisco websites or CCNA books to deepen understanding, but the config guide is the foundation.

Rules:
- Do NOT reveal the correct answer
- Give a hint that connects the broad networking concept to a specific detail, starting with the configuration guide
- On attempt 1: Give a broader conceptual hint
- On attempt 2: Give a more specific hint that narrows it down without giving it away
- Keep hints to 2-3 sentences
- Reference sources naturally (e.g., "The Cisco configuration guide describes this feature as..." or "Cisco's documentation notes that...")
- Never say "the answer is" or directly identify the correct option"""

    EXPLAIN_CORRECT_SYSTEM_PROMPT = """You are a CCNA tutor explaining why an answer is correct.

SOURCE HIERARCHY (use in this priority order):
1. PRIMARY — Cisco configuration guides for routers and switches (provided below as context)
2. SECONDARY — Official Cisco websites and documentation (cisco.com, Cisco Learning Network)
3. TERTIARY — Third-party CCNA books (Wendell Odom, Todd Lammle, etc.) only to add depth to concepts already established by sources 1 and 2

Always start explanations grounded in the configuration guide. Layer in Cisco website references and third-party book context to add depth and reinforce the concept — but the config guide is always the foundation. If a third-party book contradicts the configuration guide, the configuration guide wins.

Rules:
- First explain WHY the correct answer is right, referencing the configuration guide
- Then explain WHY EACH wrong answer is incorrect — this is critical
- Many third-party study materials teach incorrect reasoning, so be precise about why wrong answers are wrong
- Add depth by connecting to broader concepts from Cisco docs or CCNA books (e.g., "The configuration guide specifies X, and as Odom's CCNA guide explains, this matters because...")
- Reference sources naturally — cite which tier you're drawing from
- Keep the explanation clear and direct — these students have completed 3 networking courses, don't over-simplify
- Total explanation should be 4-8 sentences"""

    EXPLAIN_FAILED_SYSTEM_PROMPT = """You are a CCNA tutor explaining the correct answer after a student exhausted their attempts.

SOURCE HIERARCHY (use in this priority order):
1. PRIMARY — Cisco configuration guides for routers and switches (provided below as context)
2. SECONDARY — Official Cisco websites and documentation (cisco.com, Cisco Learning Network)
3. TERTIARY — Third-party CCNA books (Wendell Odom, Todd Lammle, etc.) only to add depth to concepts already established by sources 1 and 2

Always start explanations grounded in the configuration guide. Layer in Cisco website references and third-party book context to add depth and reinforce the concept — but the config guide is always the foundation. If a third-party book contradicts the configuration guide, the configuration guide wins.

Rules:
- Acknowledge this was a tricky question without being condescending
- Clearly state the correct answer
- Explain WHY the correct answer is right, referencing the configuration guide
- Explain WHY EACH wrong answer is incorrect
- Add depth by connecting to broader concepts from Cisco docs or CCNA books
- Reference sources naturally — cite which tier you're drawing from
- Keep the explanation clear and direct — these students have completed 3 networking courses, don't over-simplify
- Total explanation should be 4-8 sentences"""

    def generate_hint(
        self,
        question_data: Dict,
        wrong_answer: str,
        attempt_number: int,
        config_guide_context: str
    ) -> str:
        """
        Generate a progressive hint for a wrong answer using 3-tier source hierarchy.

        Args:
            question_data: Dict with question, options, correct_answer
            wrong_answer: The student's incorrect answer
            attempt_number: Which attempt this is (1 = broad hint, 2 = specific hint)
            config_guide_context: Relevant Cisco configuration guide content
        """
        try:
            hint_level = "broader conceptual" if attempt_number == 1 else "more specific, narrowing it down"

            user_message = f"""Question: {question_data.get('question', 'N/A')}

Answer options:
{self._format_options(question_data.get('options', []))}

Student's wrong answer: {wrong_answer}
Correct answer (DO NOT REVEAL): {question_data.get('correct_answer', 'N/A')}

This is attempt #{attempt_number}. Give a {hint_level} hint.

Cisco configuration guide context:
{config_guide_context}"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.HINT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating hint: {str(e)}"

    def explain_correct_answer(
        self,
        question_data: Dict,
        correct_answer: str,
        wrong_answers: List[str],
        config_guide_context: str
    ) -> str:
        """
        Explain why the correct answer is right and why each wrong answer is wrong.

        Args:
            question_data: Dict with question, options, correct_answer
            correct_answer: The correct answer text
            wrong_answers: List of wrong answer texts
            config_guide_context: Relevant Cisco configuration guide content
        """
        try:
            wrong_list = "\n".join(f"- {wa}" for wa in wrong_answers)

            user_message = f"""Question: {question_data.get('question', 'N/A')}

Answer options:
{self._format_options(question_data.get('options', []))}

Correct answer: {correct_answer}

Wrong answers to explain:
{wrong_list}

Cisco configuration guide context:
{config_guide_context}

Explain why the correct answer is right, then explain why EACH wrong answer is incorrect."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.EXPLAIN_CORRECT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating explanation: {str(e)}"

    def explain_after_failed_attempts(
        self,
        question_data: Dict,
        student_attempts: List[str],
        config_guide_context: str
    ) -> str:
        """
        Reveal and explain the correct answer after student exhausted attempts.

        Args:
            question_data: Dict with question, options, correct_answer
            student_attempts: List of the student's attempted answers
            config_guide_context: Relevant Cisco configuration guide content
        """
        try:
            attempts_str = ", ".join(student_attempts) if student_attempts else "none recorded"

            user_message = f"""Question: {question_data.get('question', 'N/A')}

Answer options:
{self._format_options(question_data.get('options', []))}

Correct answer: {question_data.get('correct_answer', 'N/A')}
Student's attempted answers: {attempts_str}

Cisco configuration guide context:
{config_guide_context}

The student was unable to find the correct answer. Reveal and explain it fully."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.EXPLAIN_FAILED_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}]
            )

            return message.content[0].text

        except Exception as e:
            return f"Error generating explanation: {str(e)}"

    def _format_options(self, options: List[str]) -> str:
        """
        Format answer options for display

        Args:
            options: List of answer option strings

        Returns:
            Formatted string of options
        """
        if not options:
            return "No options provided"

        formatted = []
        labels = ['A', 'B', 'C', 'D', 'E', 'F']
        for i, option in enumerate(options):
            label = labels[i] if i < len(labels) else str(i+1)
            formatted.append(f"{label}. {option}")

        return "\n".join(formatted)
