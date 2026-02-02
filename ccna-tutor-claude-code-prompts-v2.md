# CCNA Tutor AI Agent — Claude Code Prompt Guide (v2)

## Project Overview

Build a Flask-based AI tutoring agent for CCNA exam prep, hosted on Render.com, using Anthropic API. Students have completed three courses in a network administrator degree program and have a working understanding of networking terms and configurations. The AI tutor uses Cisco's own configuration guides as the authoritative source — not third-party training materials that may introduce misconceptions.

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
- Students have completed 3 courses in a network admin degree program. They are NOT beginners. They understand basic networking terms and device configuration.
- The AI tutor's PRIMARY authority is the Cisco configuration guides for switches and routers — NOT third-party CCNA training books or websites, which often introduce misconceptions because the authors are not authorized to review the actual exam test bank.
- Questions must be presented to students EXACTLY as written in the exam guide — same wording, same answer format, same structure. No paraphrasing or rewording.

Project structure should be:
ccna-tutor/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── render.yaml               # Render.com deployment config
├── .gitignore
├── templates/                # Jinja2 HTML templates
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
│   ├── config_guides/        # Cisco configuration guide documents go here
│   │   ├── router/           # Router configuration guide sections
│   │   └── switch/           # Switch configuration guide sections
│   └── labs/                 # Lab definitions
├── utils/
│   ├── __init__.py
│   ├── question_parser.py    # Parses test bank files
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
- static/css/style.css: Custom styles — use a color scheme of dark blue (#1a365d) and teal (#2c7a7b) to match Cisco branding
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
- Method: load_all_guides() -> reads all .txt/.md/.pdf files from router/ and switch/ folders
- Method: search_guides(keywords) -> returns relevant sections from the config guides matching keywords
- Method: get_guide_section(device_type, topic) -> returns specific config guide content
  - device_type is "router" or "switch"
  - topic is like "ospf", "vlan", "acl", etc.
- Stores guide content in memory indexed by device type and topic keywords
- If no config guides are present yet, returns a placeholder message saying "Config guide not yet loaded for this topic"

PART B — AI Tutor (utils/ai_tutor.py):

Build a class CCNATutor that implements this SPECIFIC teaching methodology:

The system prompt must encode this teaching philosophy:
"""
You are an expert CCNA tutor. Your ONLY authoritative references are the Cisco configuration guides for routers and switches. You do NOT use third-party CCNA training books, websites, or study guides as sources — these often contain misconceptions because their authors cannot review the actual CCNA exam.

Your students have completed three courses in a network administrator degree program. They understand basic networking terms and device configuration. Do not explain things at a beginner level.

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

IMPORTANT: Many CCNA training resources teach information that contradicts or oversimplifies what Cisco's own documentation says. When you see a question where common training materials would lead to a wrong answer, explicitly call this out as a common misconception.
"""

Methods:
- __init__: Initialize Anthropic client, load config guide manager, set system prompt
- handle_wrong_answer(question_data, student_answer, config_context) -> returns hints combining broad concept + config guide details WITHOUT revealing correct answer
- handle_correct_answer(question_data, student_answer, config_context) -> returns explanation of why correct + why each wrong answer is incorrect, referencing config guides
- explain_concept(protocol_name, specific_topic, config_context) -> explains using config guide as authority
- get_config_context(question_data) -> searches config guides for relevant sections based on question content
- Uses claude-sonnet-4-20250514 model
- Max tokens 1500 for responses (needs room for detailed explanations)
- Has error handling for API failures

Add a test route in app.py at "/test-ai" that:
  - Sends a test question with a wrong answer to handle_wrong_answer
  - Displays the hint response
  - This route is for testing only

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
   - Section: "Common Misconceptions" — shows misconceptions from the JSON to warn students about bad info from non-Cisco sources
   - Section: "Configuration Guide References" — shows which config guide sections are relevant
   - Has an "Ask the Tutor" chat box at the bottom:
     - Text input where student types questions
     - Submit button
     - Response area that shows AI tutor response
     - The AI response should reference config guide content when answering
     - Uses JavaScript fetch() to call an API endpoint
   - Has a "Practice Exam Questions" button that links to the quiz page for this protocol

4. Add Flask routes:
   - GET /protocols -> list all protocols page
   - GET /protocol/<slug> -> individual protocol study page
   - POST /api/ask -> JSON endpoint that takes {protocol, question} and returns {response} from AI tutor, including config guide context automatically

5. Update the nav bar: Protocols link goes to /protocols
6. Update home page cards to link to /protocols

Test: Visit /protocols, click TCP/IP, read the content, then type "How does the router handle TCP keepalive configuration?" in the chat box and verify you get an AI response that references Cisco config guide details.
```

---

## Step 4 — Add All Core CCNA Protocols

```
Step 4: Add JSON data files for ALL core CCNA protocols. Create a JSON file in data/protocols/ for each.

IMPORTANT: Each protocol JSON must include:
- config_guide_refs pointing to relevant router and/or switch config guide topics
- common_misconceptions noting where third-party training materials often get it wrong versus what Cisco's own documentation says
- related_protocols linking to other protocols (many exam questions span multiple protocols)

Protocols to create:
1. tcp-ip.json (already exists from Step 3)
2. ospf.json - Open Shortest Path First
   - Config refs: router OSPF configuration, OSPF network types, OSPF authentication
   - Misconception example: training books often oversimplify OSPF neighbor states
3. eigrp.json - Enhanced Interior Gateway Routing Protocol
   - Config refs: router EIGRP configuration, EIGRP metrics
4. stp.json - Spanning Tree Protocol
   - Config refs: switch STP configuration, PortFast, BPDU guard
5. vlan.json - Virtual LANs
   - Config refs: switch VLAN configuration, inter-VLAN routing on router
6. dhcp.json - Dynamic Host Configuration Protocol
   - Config refs: router DHCP server config, DHCP relay
7. dns.json - Domain Name System
   - Config refs: router DNS configuration, ip name-server
8. nat-pat.json - Network Address Translation / Port Address Translation
   - Config refs: router NAT configuration, NAT overload
9. acl.json - Access Control Lists
   - Config refs: router and switch ACL configuration, standard vs extended
   - Misconception: many resources teach ACL wildcard masks incorrectly
10. ipsec-vpn.json - IPSec VPN
    - Config refs: router VPN and crypto configuration
11. ipv6.json - IPv6 Addressing and Routing
    - Config refs: router IPv6 configuration, dual-stack
12. wireless.json - Wireless Networking (802.11)
    - Config refs: wireless controller configuration basics
13. ethernet.json - Ethernet and Switching Fundamentals
    - Config refs: switch interface configuration, speed/duplex
14. bgp.json - Border Gateway Protocol basics
    - Config refs: router BGP configuration (CCNA level)
15. snmp-syslog.json - Network Management Protocols
    - Config refs: router/switch SNMP and logging configuration

Also update the protocols list page (templates/protocols_list.html):
- Group protocols by category (Routing, Switching/L2, Services, Security, Other)
- Show exam weight as colored badges (High=red, Medium=yellow, Low=green)
- Show "Multi-Protocol" indicator for protocols that commonly appear together in exam questions
- Each protocol links to its study page

Test: Visit /protocols and verify all 15 protocols display, grouped by category, with correct badges and working links.
```

---

## Step 5 — Test Bank Question Parser

```
Step 5: Build the test bank question parser.

CRITICAL REQUIREMENT: Questions must be stored and displayed to students EXACTLY as they appear in the exam guide. Do NOT paraphrase, reformat, reword, or simplify. The student needs to see the EXACT question and answer wording they will encounter on the exam.

I will place test bank files in data/test_bank/. The parser needs to handle these common formats:

Build utils/question_parser.py with:

1. Class QuestionParser that can parse questions from text files:

   Format A (Numbered with lettered answers):
   1. What protocol operates at Layer 3?
   a) Ethernet
   b) IP
   c) TCP
   d) HTTP
   Answer: b

   Format B (Question with asterisk marking correct answer):
   What is the default administrative distance of OSPF?
   A. 90
   B. 100
   *C. 110
   D. 120

2. Each parsed question becomes a dict:
   {
     "id": "q001",
     "question_text": "What protocol operates at Layer 3?",
     "question_text_original": "What protocol operates at Layer 3?",
     "choices": {"a": "Ethernet", "b": "IP", "c": "TCP", "d": "HTTP"},
     "choices_original": {"a": "Ethernet", "b": "IP", "c": "TCP", "d": "HTTP"},
     "correct_answer": "b",
     "protocol_tags": [],
     "multi_protocol": false
   }
   
   The _original fields preserve exact exam wording and must NEVER be modified.

3. Method: parse_file(filepath) -> list of question dicts
4. Method: tag_questions(questions, protocols_list) -> adds protocol_tags to each question
   - Uses keyword matching: check if protocol name or key_topics appear in question text or answer choices
   - A question CAN AND SHOULD be tagged with multiple protocols when applicable
   - Set multi_protocol=true when tagged with 2+ protocols
   - Questions involving configuration that spans router AND switch should be tagged with all relevant protocols
5. Method: get_questions_by_protocol(protocol_slug) -> filtered list of questions tagged with that protocol
   - This means a multi-protocol question appears in EVERY relevant protocol's question set
6. Method: get_multi_protocol_questions() -> questions tagged with 2+ protocols
7. Method: get_all_questions() -> all parsed questions

8. On app startup, parse all files in data/test_bank/ and tag them automatically

Add a test route GET /api/questions/<protocol_slug> that returns JSON list of questions for that protocol.
Add a test route GET /api/questions/multi-protocol that returns all multi-protocol questions.

Test: Place a sample test bank file in data/test_bank/, restart the app, and hit /api/questions/tcp-ip to see tagged questions. Verify multi-protocol questions appear under ALL their tagged protocols.
```

---

## Step 6 — Quiz Page (Exam-Style with Tutoring Flow)

```
Step 6: Build the interactive quiz page with the full tutoring methodology.

THE QUIZ FLOW MUST WORK EXACTLY LIKE THIS:

1. Student sees a question displayed EXACTLY as written in the exam guide (original wording, original answer format)
2. Student selects an answer and clicks Submit
3. IF WRONG:
   - The page shows "Incorrect" but does NOT show the correct answer
   - The AI tutor provides:
     a) The broad concept/protocol this question is testing
     b) A specific detail from the Cisco configuration guide that hints at the correct answer
     c) A note if this is a common misconception from non-Cisco training materials
   - Student gets a "Try Again" button to answer again
   - Student can try as many times as needed
   - Each wrong attempt gets a NEW, different hint from the AI (progressively more specific)
4. IF CORRECT (on any attempt):
   - The page shows "Correct!" with a green highlight
   - The AI tutor provides:
     a) WHY the correct answer is correct, referencing the Cisco config guide
     b) WHY each of the other answers is INCORRECT, one by one, referencing the config guide
     c) If applicable: notes about common misconceptions from training materials
   - Student clicks "Next Question" to continue
5. For multi-protocol questions, show badges indicating which protocols are involved

Requirements:
1. templates/quiz.html extending base.html:
   - Protocol selector dropdown (pre-selected if coming from ?protocol=tcp-ip)
   - Option to select "Multi-Protocol Questions" as a quiz category
   - "Start Quiz" button
   - Quiz interface:
     - Shows one question at a time in EXACT exam format
     - Multiple choice radio buttons matching exact exam answer wording
     - "Submit Answer" button
     - Wrong answer: shows AI hint area + "Try Again" button (Submit changes to Try Again)
     - Correct answer: shows full AI explanation area + "Next Question" button
     - Multi-protocol badges on applicable questions
   - Progress bar showing question X of Y
   - Score tracker: first-attempt correct / total questions
   - Attempt counter per question
   - End-of-quiz summary:
     - Overall score (first-attempt accuracy)
     - List of questions that needed multiple attempts
     - Protocols where student struggled most
     - "Review Weak Areas" links to relevant protocol study pages

2. Add Flask routes:
   - GET /quiz -> quiz page
   - POST /api/quiz/submit -> takes {question_id, student_answer, attempt_number}
     - If wrong: returns {correct: false, hint: "AI hint text", attempt: N}
       - hint comes from ai_tutor.handle_wrong_answer() with config guide context
       - Each attempt generates a progressively more specific hint
     - If correct: returns {correct: true, explanation: "full AI explanation", attempts_needed: N}
       - explanation comes from ai_tutor.handle_correct_answer() with config guide context

3. JavaScript in static/js/quiz.js:
   - Fetches questions from /api/questions/<protocol>
   - Presents questions in exact exam format (no reformatting!)
   - Manages the wrong/retry/correct flow
   - Tracks attempts per question
   - Tracks first-attempt score
   - Generates end-of-quiz summary with weak protocol areas

4. Update protocol.html: "Practice Exam Questions" button links to /quiz?protocol=<slug>
5. Update home page Quiz card to link to /quiz

Test: Go to /quiz, select TCP/IP. Answer a question WRONG — verify you get a hint without seeing the correct answer, and can try again. Answer correctly — verify you see why each wrong answer is wrong. Finish quiz — verify summary shows weak areas.
```

---

## Step 7 — Lab Launcher Page

```
Step 7: Build the Packet Tracer lab launcher page.

Context: Students use Cisco Packet Tracer (a network simulator). They have accounts on Cisco NetAcad (netacad.com). Labs are .pkt files that they open in Packet Tracer after downloading.

Requirements:
1. Create data/labs/labs.json:
   {
     "labs": [
       {
         "id": "lab001",
         "title": "Basic Router Configuration",
         "protocols": ["tcp-ip", "ospf"],
         "difficulty": "Beginner",
         "description": "Configure hostnames, passwords, and basic IP addressing on two routers",
         "objectives": [
           "Configure router hostnames",
           "Set console and VTY passwords",
           "Assign IP addresses to interfaces",
           "Verify connectivity with ping"
         ],
         "config_guide_sections": [
           "Router initial configuration",
           "Interface IP address assignment"
         ],
         "estimated_time": "30 minutes",
         "pkt_filename": "lab001_basic_router.pkt",
         "netacad_link": ""
       }
     ]
   }

   Add 8-10 labs covering different protocols and difficulties (Beginner, Intermediate, Advanced).
   Each lab must reference which Cisco config guide sections are relevant.

2. templates/labs.html extending base.html:
   - Filter bar: by protocol (dropdown), by difficulty (buttons)
   - Lab cards in a grid layout, each showing:
     - Title and difficulty badge (color coded)
     - Related protocols as small badges
     - Config guide references
     - Estimated time
     - Brief description
     - "View Details" expand to show full objectives list
     - "Launch in Packet Tracer" button with instructions:
       - Step 1: Login at netacad.com
       - Step 2: Open Cisco Packet Tracer
       - Step 3: Download the .pkt file or follow NetAcad link
     - "Ask Tutor About This Lab" button that opens a chat
       - AI is pre-prompted with the lab objectives, relevant protocols, AND the relevant config guide sections
       - So the AI can give configuration commands straight from the Cisco documentation

3. Add Flask routes:
   - GET /labs -> labs page
   - POST /api/lab-help -> takes {lab_id, question} and returns AI help
     (AI system prompt includes lab objectives + config guide sections for that lab)

4. JavaScript: filtering, expand/collapse details, lab chat functionality
5. Update home page Labs card to link to /labs
6. Update nav bar

Test: Visit /labs, filter by protocol and difficulty, expand a lab's details, click "Ask Tutor About This Lab" and ask "What IOS commands do I need for this lab?" — verify AI gives relevant commands referencing the Cisco config guide.
```

---

## Step 8 — Polish and Deploy

```
Step 8: Final polish and Render.com deployment prep.

1. Error handling:
   - Add a custom 404 page
   - Add a custom 500 page that says "The tutor is taking a break — try again!"
   - Handle Anthropic API rate limits gracefully with a user message
   - Add try/except around all API calls
   - If config guides are not loaded, show a clear message rather than crashing

2. Loading states:
   - Add spinner/loading animation when waiting for AI responses
   - On quiz: show "Your tutor is reviewing your answer..." while waiting
   - Disable submit buttons while waiting to prevent double-clicks

3. Config guide loading indicator:
   - On startup, log which config guide sections were loaded
   - On the admin/health page, show which guides are loaded and which are missing

4. render.yaml finalize:
   - Ensure ANTHROPIC_API_KEY is referenced as env variable
   - Set Python version to 3.11
   - Health check endpoint at /health that returns {"status": "ok", "config_guides_loaded": true/false, "questions_loaded": N, "protocols_loaded": N}

5. README.md:
   - Project description emphasizing Cisco config guide authority
   - Teaching methodology explanation
   - How to run locally (flask run with ANTHROPIC_API_KEY set)
   - How it deploys on Render.com
   - How to add test bank questions (drop files in data/test_bank/ — questions must be in exact exam format)
   - How to add Cisco config guides (place text files in data/config_guides/router/ or switch/)
   - How to add new protocols (create JSON in data/protocols/ with config_guide_refs)
   - How to add new labs (edit data/labs/labs.json with config_guide_sections)

6. .gitignore: Make sure __pycache__, .env, venv/, and any .pkt files are ignored

7. Security: Make sure no API keys are hardcoded anywhere — all from environment variables

Test: Run locally one final time. Full test checklist:
- Home page loads with config guide messaging
- All protocols display with misconception warnings
- Quiz flow: wrong answer → hint (no answer revealed) → retry → correct → full explanation with config guide refs
- Multi-protocol questions appear under all relevant protocols
- Labs page filters correctly, AI gives config-guide-based commands
- /health returns status with loaded resource counts
Then git push and deploy to Render.com.
```

---

## Prompt for Loading Config Guides

> **Use this prompt AFTER Step 2 when you have the Cisco configuration guide documents ready:**

```
I've placed Cisco configuration guide files in data/config_guides/:
- data/config_guides/router/ contains: [list your router guide files]
- data/config_guides/switch/ contains: [list your switch guide files]

Process these files:
1. Load and index all content by device type and topic
2. Show me a summary of what topics are covered for router and switch
3. Show me which protocol JSON files in data/protocols/ have config_guide_refs that match loaded content
4. Show me which protocols are MISSING config guide coverage so I know what documents I still need to add
```

---

## Prompt for Loading Test Bank

> **Use this prompt AFTER Step 5 when you have exam question files ready:**

```
I've placed my exam guide test bank file(s) in data/test_bank/:
- [list your files, e.g., data/test_bank/ccna_200-301_questions.txt]

Process these files:
1. Parse all questions preserving EXACT original wording — do not modify any question or answer text
2. Show me: total questions found, parsing errors (if any)
3. Tag all questions to protocols — show the breakdown of how many questions per protocol
4. Show me all multi-protocol questions (tagged to 2+ protocols) and which protocols each spans
5. Show me any questions that could NOT be tagged to any protocol so I can review them
6. Verify that the original question text and answer text are preserved character-for-character
```

---

## Tips for Working with Claude Code

1. **One prompt at a time** — Copy one step, let Claude Code finish, test it, then move to the next.

2. **If something breaks**, tell Claude Code exactly what the error is:
   ```
   When I run flask, I get this error: [paste error]. Fix this.
   ```

3. **To check the tutoring methodology works**, test this specific flow:
   ```
   I need to verify the quiz tutoring flow. Give me a test question, I'll answer wrong on purpose. Check that:
   1. The AI gives me a hint using config guide details WITHOUT revealing the answer
   2. I can try again
   3. When I answer correctly, the AI explains why EVERY wrong answer is wrong using config guide references
   Run this test and show me the full interaction.
   ```

4. **To fix AI tutor responses that aren't right**:
   ```
   The AI tutor responses need adjustment. Currently the problem is: [describe issue, e.g., "it's revealing the correct answer when the student gets it wrong" or "it's not referencing config guides" or "it's giving beginner-level explanations — students already have 3 courses"]. 
   
   Fix the system prompt and methods in utils/ai_tutor.py to correct this.
   ```

5. **To add more protocols later**:
   ```
   Add a new protocol: [protocol name]. Create the JSON file in data/protocols/ with:
   - CCNA-relevant key topics
   - Config guide references for router and/or switch
   - Common misconceptions from third-party training materials
   - Related protocols that share exam questions with this one
   ```

6. **To add more labs later**:
   ```
   Add a new lab to labs.json: [describe the lab scenario]. Include which config guide sections are relevant so the AI tutor can reference them when students ask for help.
   ```

7. **To handle a question that spans many protocols**:
   ```
   I have exam questions that involve both [protocol A] and [protocol B] together. Make sure these questions:
   1. Are tagged with BOTH protocols
   2. Appear in quiz sets for BOTH protocols
   3. Show multi-protocol badges in the quiz
   4. When the AI tutors on these, it references config guide sections for ALL involved protocols
   ```
