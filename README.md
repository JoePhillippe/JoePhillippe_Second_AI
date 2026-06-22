# CCNA Tutor AI Agent — Claude Code Prompt Guide (v3)

## Project Overview

Build a Flask-based AI tutoring agent for CCNA exam prep, hosted on Render.com, using Anthropic API. Students have completed three courses in a network administrator degree program and have a working understanding of networking terms and configurations. The AI tutor uses Cisco's own configuration guides as the authoritative source — not third-party training materials that may introduce misconceptions.

Key design principle: The exam question bank contains many questions that test the same concept with slightly different wording — sometimes swapping what's in the question stem versus the answer choices. Students get bored repeating nearly identical questions. The AI groups these by concept and only presents one per group, letting students choose to go deeper or move on.

---

## Before You Start — Project Setup Prompt

> **Paste this into Claude Code first to establish the project context:**

```
I'm building a CCNA exam tutoring AI agent as a Flask web application. Here is the project plan:

- Python/Flask web app hosted on Render.com
- Anthropic API for AI tutoring (API key stored as environment variable ANTHROPIC_API_KEY)
- GitHub repository connected to VS Code (repo is already set up)
- Test bank of CCNA questions will be provided as input files
- Cisco configuration guides (router and switch) will be provided as reference documents
- Each network protocol gets its own study page
- Final feature: lab launcher page for Cisco Packet Tracer labs

IMPORTANT CONTEXT:
- Students have completed 3 courses in a network admin degree program. They are NOT beginners.
- The AI tutor's PRIMARY authority is the Cisco configuration guides for switches and routers — NOT third-party CCNA training books.
- Questions must be presented EXACTLY as written in the exam guide — same wording, same answer format.
- The exam question bank has many redundant questions testing the same concept with different wording. These must be grouped by concept so students aren't bored by repetition.
- Students all share the same login — no individual student tracking.

Project structure should be:
ccna-tutor/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── render.yaml               # Render.com deployment config
├── .gitignore
├── templates/
│   ├── base.html             # Base template with nav
│   ├── index.html            # Landing/home page
│   ├── protocol.html         # Protocol study page template
│   ├── quiz.html             # Quiz page template
│   └── labs.html             # Packet Tracer lab launcher
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── data/
│   ├── test_bank/            # CCNA exam guide question files go here
│   ├── protocols/            # Protocol subject files go here
│   ├── config_guides/
│   │   ├── router/           # Router configuration guide sections
│   │   └── switch/           # Switch configuration guide sections
│   ├── labs/                 # Lab definitions
│   └── concept_groups/       # Generated concept group mappings (cached)
├── utils/
│   ├── __init__.py
│   ├── question_parser.py    # Parses test bank files
│   ├── concept_grouper.py    # AI-powered concept grouping of questions
│   ├── ai_tutor.py           # Anthropic API integration with tutoring logic
│   ├── protocol_manager.py   # Manages protocol content
│   └── config_guide.py       # Loads and indexes Cisco config guide content
└── README.md

Please initialize this project structure now. Create all folders and placeholder files. Use Python 3.11+. Do NOT install anything or write application logic yet — just set up the skeleton.
```

---

## Step 1 — Landing Page (Verify Flask Runs)

```
Step 1: Build the landing/home page for the CCNA Tutor app.

Requirements:
- app.py: Create a minimal Flask app with a single route "/" that renders index.html
- templates/base.html: Base template with:
  - Clean, professional nav bar with app title "CCNA Tutor"
  - Nav links: Home, Protocols (dropdown placeholder), Quiz, Labs
  - Footer with "Powered by Anthropic Claude | References: Cisco Configuration Guides"
  - Use Bootstrap 5 CDN for styling
  - Mobile responsive
- templates/index.html: Extends base.html with:
  - Welcome message: "CCNA Exam Preparation — Guided by Cisco Configuration Guides"
  - Brief explanation that this tutor uses official Cisco configuration guides as the authoritative source
  - Note that students should have completed foundational networking coursework
  - 3 card sections: "Study Protocols", "Practice Exam Questions", "Packet Tracer Labs"
  - Each card has a brief description and a button (links can be "#" for now)
- static/css/style.css: Custom styles — dark blue (#1a365d) and teal (#2c7a7b) for Cisco branding
- requirements.txt: flask, gunicorn, anthropic
- render.yaml: Configure for Render.com deployment with:
  - Build command: pip install -r requirements.txt
  - Start command: gunicorn app:app
  - Environment variable placeholder for ANTHROPIC_API_KEY

Test: Run "flask run" and verify the home page loads at localhost:5000 with working nav and styled cards.
```

---

## Step 2 — Cisco Configuration Guide Loader + AI Tutor Core

```
Step 2: Build the configuration guide loader and the AI tutor with the correct teaching methodology.

PART A — Configuration Guide Loader (utils/config_guide.py):

I will place Cisco configuration guide text files in data/config_guides/router/ and data/config_guides/switch/. These are the AUTHORITATIVE reference for all tutoring.

Build a class ConfigGuideManager:
- Method: load_all_guides() -> reads all .txt/.md files from router/ and switch/ folders
- Method: search_guides(keywords) -> returns relevant sections matching keywords
- Method: get_guide_section(device_type, topic) -> returns specific config guide content
  - device_type is "router" or "switch"
- Stores guide content in memory indexed by device type and topic keywords
- If no config guides are present yet, returns a placeholder message

PART B — AI Tutor (utils/ai_tutor.py):

Build a class CCNATutor with this SPECIFIC teaching methodology:

System prompt:
"""
You are an expert CCNA tutor. Your ONLY authoritative references are the Cisco configuration guides for routers and switches. You do NOT use third-party CCNA training books or websites as sources — these often contain misconceptions because their authors cannot review the actual CCNA exam.

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

IMPORTANT: Many CCNA training resources teach information that contradicts or oversimplifies what Cisco's own documentation says. When relevant, call this out as a common misconception.
"""

Methods:
- __init__: Initialize Anthropic client, load config guide manager, set system prompt
- handle_wrong_answer(question_data, student_answer, config_context, attempt_number) -> returns hints combining broad concept + config guide details WITHOUT revealing correct answer. Each attempt gives progressively more specific hints.
- handle_correct_answer(question_data, student_answer, config_context) -> returns explanation of why correct + why each wrong answer is incorrect, referencing config guides
- explain_concept(protocol_name, specific_topic, config_context) -> explains using config guide as authority
- get_config_context(question_data) -> searches config guides for relevant sections based on question content
- Uses claude-sonnet-4-20250514 model
- Max tokens 1500
- Error handling for API failures

Add a test route in app.py at "/test-ai" for verification.

Test: Run flask and visit /test-ai to verify the AI responds with hints that reference config guide concepts without revealing the answer.
```

---

## Step 3 — Protocol Pages (Start with TCP/IP)

```
Step 3: Build the protocol study page system, starting with ONE protocol as a proof of concept.

First protocol: TCP/IP (Transmission Control Protocol / Internet Protocol)

Requirements:
1. utils/protocol_manager.py:
   - A class ProtocolManager that loads protocol data from data/protocols/ folder
   - Each protocol is a JSON file with structure:
     {
       "name": "TCP/IP",
       "slug": "tcp-ip",
       "category": "Transport & Internet Layer",
       "description": "Brief description",
       "key_topics": ["Three-way handshake", "Port numbers", "TCP vs UDP", "IP addressing"],
       "config_guide_refs": {
         "router": ["ip routing configuration", "tcp parameters"],
         "switch": []
       },
       "common_misconceptions": [
         "Many training materials oversimplify TCP window sizing — the Cisco config guide shows how window scaling actually works in IOS"
       ],
       "exam_weight": "High",
       "related_protocols": ["dns", "dhcp"]
     }
   - Method: get_all_protocols() -> list of protocol summaries
   - Method: get_protocol(slug) -> full protocol data
   - Method: get_related_protocols(slug) -> returns related protocol data

2. Create data/protocols/tcp-ip.json with accurate CCNA content

3. templates/protocol.html that extends base.html:
   - Shows protocol name, category, exam weight badge, and related protocols as links
   - Lists key topics as clickable items
   - Section: "Common Misconceptions" — warnings about bad info from non-Cisco sources
   - Section: "Configuration Guide References"
   - "Ask the Tutor" chat box at the bottom using fetch() to POST /api/ask
   - "Practice Exam Questions" button linking to quiz page for this protocol

4. Add Flask routes:
   - GET /protocols -> list all protocols page
   - GET /protocol/<slug> -> individual protocol study page
   - POST /api/ask -> JSON endpoint with AI tutor + config guide context

5. Update nav bar and home page links

Test: Visit /protocol/tcp-ip, type a question in the chat box, verify AI response references config guide details.
```

---

## Step 4 — Add All Core CCNA Protocols

```
Step 4: Add JSON data files for ALL core CCNA protocols. Each JSON file must include config_guide_refs, common_misconceptions, and related_protocols.

Protocols to create:
1. tcp-ip.json (exists from Step 3)
2. ospf.json - Open Shortest Path First
3. eigrp.json - Enhanced Interior Gateway Routing Protocol
4. stp.json - Spanning Tree Protocol
5. vlan.json - Virtual LANs
6. dhcp.json - Dynamic Host Configuration Protocol
7. dns.json - Domain Name System
8. nat-pat.json - NAT / PAT
9. acl.json - Access Control Lists
10. ipsec-vpn.json - IPSec VPN
11. ipv6.json - IPv6 Addressing and Routing
12. wireless.json - Wireless Networking (802.11)
13. ethernet.json - Ethernet and Switching Fundamentals
14. bgp.json - Border Gateway Protocol basics
15. snmp-syslog.json - Network Management Protocols

Update the protocols list page:
- Group by category (Routing, Switching/L2, Services, Security, Other)
- Exam weight colored badges (High=red, Medium=yellow, Low=green)
- Multi-Protocol indicator for protocols that commonly share exam questions
- Each protocol links to its study page

Test: Visit /protocols and verify all 15 display grouped with badges and working links.
```

---

## Step 5 — Test Bank Question Parser

```
Step 5: Build the test bank question parser.

CRITICAL: Questions must be stored and displayed EXACTLY as written in the exam guide. No paraphrasing.

Build utils/question_parser.py:

1. Class QuestionParser that parses questions from text files:

   Format A (Numbered with lettered answers):
   1. What protocol operates at Layer 3?
   a) Ethernet
   b) IP
   c) TCP
   d) HTTP
   Answer: b

   Format B (Asterisk marking correct answer):
   What is the default administrative distance of OSPF?
   A. 90
   B. 100
   *C. 110
   D. 120

2. Each parsed question becomes a dict:
   {
     "id": "q001",
     "question_text": "...",
     "question_text_original": "...",
     "choices": {"a": "...", "b": "...", "c": "...", "d": "..."},
     "choices_original": {"a": "...", "b": "...", "c": "...", "d": "..."},
     "correct_answer": "b",
     "protocol_tags": [],
     "multi_protocol": false,
     "concept_group": null
   }

   The _original fields preserve exact exam wording and must NEVER be modified.
   The concept_group field will be filled in Step 5B by the concept grouper.

3. Methods:
   - parse_file(filepath) -> list of question dicts
   - tag_questions(questions, protocols_list) -> adds protocol_tags; sets multi_protocol=true when 2+ protocols
   - get_questions_by_protocol(protocol_slug) -> filtered list (multi-protocol questions appear in ALL relevant protocols)
   - get_multi_protocol_questions() -> questions tagged with 2+ protocols
   - get_all_questions() -> all parsed questions

4. On app startup, parse all files in data/test_bank/ and tag automatically

Test routes:
- GET /api/questions/<protocol_slug> -> JSON list of questions
- GET /api/questions/multi-protocol -> all multi-protocol questions

Test: Place a sample test bank file, restart app, verify tagging at /api/questions/tcp-ip.
```

---

## Step 5B — Concept Grouping (AI-Powered Redundancy Detection)

> **This is the key new step. Run this AFTER Step 5 and AFTER loading your test bank.**

```
Step 5B: Build the AI-powered concept grouper that detects redundant questions testing the same fact.

CONTEXT: The CCNA exam question bank intentionally contains many questions testing the same concept worded differently. The exam designers do this so students must understand the concept, not just memorize one question. Some questions even swap what's in the question stem versus the answer choices. For example:
  - Question A: "What is the default administrative distance of OSPF?" Answer: 110
  - Question B: "Which routing protocol has a default administrative distance of 110?" Answer: OSPF
  Both test the SAME fact: OSPF administrative distance = 110

Students get bored answering the same concept repeatedly. We need to group these, show ONE per group, and let students choose if they want more from the same group.

Build utils/concept_grouper.py:

1. Class ConceptGrouper:

   Method: analyze_and_group(questions_by_protocol) -> dict of concept groups
   
   This method uses the Anthropic API to analyze questions and find groups. For each protocol:
   
   a) Send the questions to Claude with this prompt:
   """
   Analyze these CCNA exam questions for the protocol: {protocol_name}
   
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
   {
     "concept_groups": [
       {
         "group_id": "ospf_admin_distance",
         "concept": "OSPF default administrative distance is 110",
         "question_ids": ["q001", "q005", "q023"],
         "confidence": "HIGH"
       }
     ]
   }
   """
   
   b) Use claude-sonnet-4-20250514 for this analysis
   c) Process one protocol at a time to stay within token limits
   d) Handle questions tagged to multiple protocols: a question can appear in groups under EACH of its tagged protocols

   Method: save_groups(groups, filepath) -> saves to data/concept_groups/{protocol_slug}.json
   Method: load_groups(protocol_slug) -> loads cached groups from JSON file
   Method: get_random_question_from_group(group_id) -> returns one random question from the group
   Method: get_remaining_questions_in_group(group_id, exclude_id) -> returns other questions in same group
   Method: get_groups_by_protocol(protocol_slug) -> returns all concept groups for a protocol with question counts

2. CACHING STRATEGY:
   - Concept grouping is EXPENSIVE (many API calls to analyze the full question bank)
   - Run it ONCE and cache results to data/concept_groups/ as JSON files
   - On app startup: load cached groups if they exist, skip AI analysis
   - Provide a Flask route POST /admin/regroup that re-runs the AI grouping (for when new questions are added)
   - Provide a Flask route POST /admin/regroup/<protocol_slug> to regroup just one protocol

3. Add to the question data model:
   - Each question dict gets: "concept_group": "ospf_admin_distance" (filled from cached groups)
   - Each question dict gets: "group_size": 3 (how many questions share this group)

4. MANUAL OVERRIDE SUPPORT:
   - Create data/concept_groups/manual_overrides.json where I can manually assign questions to groups
   - Manual overrides take priority over AI-generated groups
   - Format: {"q001": "my_custom_group_id", "q005": "my_custom_group_id"}

Test: After loading test bank questions, run the grouper on one protocol (e.g., OSPF). 
  - Visit GET /api/concept-groups/ospf to see the groups
  - Verify that question-answer swapped pairs are in the same group
  - Verify each question has a concept_group assigned
  - Verify the cached JSON file was created in data/concept_groups/
```

---

## Step 6 — Quiz Page (With Concept Group Flow)

```
Step 6: Build the interactive quiz page with concept grouping and the full tutoring methodology.

THE QUIZ FLOW MUST WORK EXACTLY LIKE THIS:

1. Student starts quiz for a protocol (or "Multi-Protocol" or "All")
2. The quiz engine selects ONE random question from EACH concept group for that protocol
   - This gives the student coverage of ALL concepts without boring repetition
   - Question selection is random so each session feels different (remember: no individual student tracking, shared login)
3. Student sees the question displayed EXACTLY as written in the exam guide
4. Student selects an answer and clicks Submit

5. IF WRONG:
   - Page shows "Incorrect" — does NOT show the correct answer
   - AI tutor provides:
     a) The broad concept this question is testing
     b) A specific detail from the Cisco configuration guide as a hint
     c) If applicable: a note about common misconceptions from training materials
   - Student gets "Try Again" button
   - Each wrong attempt gets a NEW, progressively more specific hint
   
6. IF CORRECT (on any attempt):
   - Page shows "Correct!" with green highlight
   - AI tutor provides:
     a) WHY the correct answer is correct, referencing Cisco config guide
     b) WHY each other answer is INCORRECT, one by one, referencing config guide
     c) If applicable: misconception warnings
   - THEN the student sees a prompt:
     "This concept has [N-1] more exam questions with different wording. Want to try another question on the same concept, or move to a different topic?"
     - Button: "More on this concept" -> loads another random question from the SAME concept group
     - Button: "Next topic" -> moves to a question from the NEXT concept group
   - If the student already answered all questions in this concept group, say "You've covered all [N] variations of this concept!" and auto-advance

7. For multi-protocol questions, show badges indicating which protocols are involved

QUIZ SUMMARY AT END:
- Overall score (first-attempt accuracy)
- Concept groups the student got right on first try
- Concept groups that needed multiple attempts (these are weak areas)
- "Review Weak Areas" links to relevant protocol study pages
- Number of concept groups covered vs total available
- No individual student data is stored — summary is session-only

Requirements:
1. templates/quiz.html extending base.html:
   - Protocol selector dropdown (pre-selected if coming from ?protocol=tcp-ip)
   - Option for "Multi-Protocol Questions" and "All Concepts"
   - "Start Quiz" button
   - Quiz interface:
     - Shows one question at a time in EXACT exam format
     - Concept group indicator: "Concept 3 of 12" (not question number — concept number)
     - Multiple choice radio buttons matching exact exam answer wording
     - Submit / Try Again flow
     - After correct answer: "More on this concept" / "Next topic" choice
     - Multi-protocol badges on applicable questions
   - Progress bar by concept groups covered
   - Score tracker: first-attempt correct / total concepts
   - End-of-quiz summary with weak concept areas

2. Flask routes:
   - GET /quiz -> quiz page
   - GET /api/quiz/start/<protocol_slug> -> returns a quiz session:
     {
       "session_id": "random-uuid",
       "protocol": "ospf",
       "concept_groups": [
         {
           "group_id": "ospf_admin_distance",
           "concept": "OSPF default administrative distance is 110",
           "question": { ...one random question from group... },
           "group_size": 3
         },
         ...
       ],
       "total_concepts": 12
     }
   - POST /api/quiz/submit -> takes {session_id, question_id, student_answer, attempt_number}
     - If wrong: returns {correct: false, hint: "...", attempt: N}
     - If correct: returns {correct: true, explanation: "...", attempts_needed: N, more_in_group: 2}
   - GET /api/quiz/group-question/<group_id>?exclude=q001,q005 -> returns another random question from the same concept group, excluding ones already seen

3. JavaScript in static/js/quiz.js:
   - Manages concept-group-based quiz flow
   - Presents questions in exact exam format
   - Handles wrong/retry/correct cycle
   - Shows "more on this concept" / "next topic" choice after correct
   - Random question selection is done server-side (so each session is different)
   - Tracks first-attempt accuracy by concept group
   - Generates session-only summary (nothing persisted)

4. Update protocol.html and home page links

Test: Start a quiz for OSPF.
  - Verify you get one question per concept (not all redundant questions)
  - Answer wrong — verify hint without answer
  - Answer correct — verify explanation + "More on this concept" option
  - Click "More on this concept" — verify you get a DIFFERENT question testing the same fact
  - Finish quiz — verify summary shows concept coverage and weak areas
  - Restart quiz — verify you get DIFFERENT random questions from the same groups
```

---

## Step 7 — Lab Launcher Page

```
Step 7: Build the Packet Tracer lab launcher page.

Context: Students use Cisco Packet Tracer. They have NetAcad accounts at netacad.com. Labs are .pkt files opened in Packet Tracer.

Requirements:
1. Create data/labs/labs.json with 8-10 labs covering different protocols and difficulties (Beginner, Intermediate, Advanced). Each lab includes:
   - id, title, protocols (list), difficulty, description, objectives
   - config_guide_sections (which Cisco config guide sections are relevant)
   - estimated_time, pkt_filename, netacad_link

2. templates/labs.html extending base.html:
   - Filter bar: by protocol, by difficulty
   - Lab cards in a grid:
     - Title, difficulty badge, protocol badges, config guide references
     - Estimated time, description
     - Expandable objectives list
     - "Launch in Packet Tracer" button with login instructions (netacad.com)
     - "Ask Tutor About This Lab" chat — AI pre-prompted with lab objectives + config guide sections

3. Flask routes:
   - GET /labs -> labs page
   - POST /api/lab-help -> takes {lab_id, question}, returns AI help with config guide context

4. JavaScript: filtering, expand/collapse, lab chat
5. Update home page and nav

Test: Visit /labs, filter by protocol, ask "What IOS commands do I need?" for a lab — verify AI references config guide.
```

---

## Step 8 — Polish and Deploy

```
Step 8: Final polish and Render.com deployment prep.

1. Error handling:
   - Custom 404 and 500 pages
   - Anthropic API rate limit handling with user message
   - try/except around all API calls
   - If config guides not loaded, show clear message
   - If concept groups not yet generated, quiz falls back to random questions without grouping

2. Loading states:
   - Spinner when waiting for AI responses
   - "Your tutor is reviewing your answer..." on quiz
   - Disable buttons during API calls

3. Health and admin routes:
   - GET /health -> {"status": "ok", "config_guides_loaded": bool, "questions_loaded": N, "protocols_loaded": N, "concept_groups_cached": bool}
   - POST /admin/regroup -> re-run AI concept grouping for all protocols (protected with a simple key from env var ADMIN_KEY)
   - POST /admin/regroup/<protocol_slug> -> regroup one protocol

4. render.yaml: ANTHROPIC_API_KEY + ADMIN_KEY env vars, Python 3.11, health check

5. README.md:
   - Project description with teaching methodology explanation
   - How to run locally
   - How to deploy on Render.com
   - How to add test bank questions (exact exam format)
   - How to add Cisco config guides
   - How to add protocols
   - How to run concept grouping (first time and after adding questions)
   - How to add manual group overrides
   - How to add labs

6. .gitignore: __pycache__, .env, venv/, .pkt files
7. Security: no hardcoded API keys

Test checklist:
- Home page loads
- All protocols display with misconception warnings
- Quiz: concept-group-based flow works end to end
- Redundant questions grouped — only one shown per concept
- "More on this concept" gives different wording of same concept
- Random selection changes between sessions
- Multi-protocol questions appear in all relevant protocols
- Labs page filters and AI gives config-guide commands
- /health shows resource counts
- Manual group overrides work
Git push and deploy to Render.com.
```

---

## Prompt for Loading Config Guides

> **Use AFTER Step 2 when you have the Cisco configuration guide documents ready:**

```
I've placed Cisco configuration guide files in data/config_guides/:
- data/config_guides/router/ contains: [list your files]
- data/config_guides/switch/ contains: [list your files]

Process these files:
1. Load and index all content by device type and topic
2. Show me a summary of topics covered for router and switch
3. Show which protocol JSON files have config_guide_refs that match loaded content
4. Show which protocols are MISSING config guide coverage
```

---

## Prompt for Loading Test Bank

> **Use AFTER Step 5:**

```
I've placed my exam guide test bank file(s) in data/test_bank/:
- [list your files]

Process these files:
1. Parse all questions preserving EXACT original wording — do not modify any text
2. Show me: total questions found, parsing errors if any
3. Tag all questions to protocols — show breakdown per protocol
4. Show all multi-protocol questions and which protocols each spans
5. Show any untaggable questions for review
6. Verify original text preserved character-for-character
```

---

## Prompt for Running Concept Grouping

> **Use AFTER loading test bank (Step 5B). This costs API tokens — run once, then use cache.**

```
Run the concept grouper on all protocols in the test bank.

For each protocol:
1. Send its questions to the AI for concept analysis
2. Detect groups including QUESTION-ANSWER SWAPS (where the question in one becomes the answer in another)
3. Save results to data/concept_groups/{protocol_slug}.json
4. Show me a summary for each protocol:
   - Total questions
   - Number of concept groups formed
   - Largest group (most redundant concept)
   - Any questions the AI was unsure about (MEDIUM confidence)
   - Questions that appear in groups under multiple protocols

After all protocols are done, show me:
- Total concept groups across all protocols
- Average group size (how much redundancy exists)
- Any groups I should manually review (MEDIUM confidence ones)
```

---

## Prompt for Manual Group Review

> **Use AFTER concept grouping if you want to verify or fix groups:**

```
Show me the concept groups for protocol: [protocol name]

For each group, show:
1. The concept being tested
2. All questions in the group (full text)
3. The AI's confidence level

I want to review these and tell you if any questions are mis-grouped. I can also provide manual overrides.
```

---

## Tips for Working with Claude Code

1. **One prompt at a time** — Copy one step, let Claude Code finish, test it, then move to the next.

2. **If something breaks**:
   ```
   When I run flask, I get this error: [paste error]. Fix this.
   ```

3. **To verify the full tutoring + grouping flow**:
   ```
   Test the complete quiz flow for OSPF:
   1. Start a quiz — confirm one question per concept group, not all redundant questions
   2. Answer one wrong — confirm hint without answer revealed
   3. Answer correctly — confirm explanation of all wrong answers using config guides
   4. Click "More on this concept" — confirm different question on same concept
   5. Restart quiz — confirm random selection gives different questions
   Show me the full interaction at each step.
   ```

4. **To fix AI tutor responses**:
   ```
   The AI tutor responses need adjustment. The problem is: [describe issue].
   Fix the system prompt and methods in utils/ai_tutor.py.
   ```

5. **To fix concept grouping mistakes**:
   ```
   The concept grouper put these questions in the same group but they test different concepts:
   - Question [id]: [paste question]
   - Question [id]: [paste question]
   
   Split them into separate groups. Add this to manual_overrides.json.
   ```

   OR:
   ```
   These questions should be in the same group but the AI put them in different groups:
   - Question [id]: [paste question] (currently in group: X)
   - Question [id]: [paste question] (currently in group: Y)
   
   Merge them into one group. Add to manual_overrides.json.
   ```

6. **To add more protocols, labs, or questions** — same as v2 tips, plus:
   ```
   I've added new questions to the test bank. Re-run concept grouping for protocol: [name]. Preserve existing manual overrides.
   ```
