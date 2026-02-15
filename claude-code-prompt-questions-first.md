# Claude Code Prompt — Restructure CCNA Tutor to Questions-First Study Flow

## Context for Claude Code

> **Paste this context block first so Claude Code understands the change:**

```
I need to restructure my CCNA Tutor Flask app's study flow. Here is the current state and what needs to change:

CURRENT STATE:
- Flask web app with 628 exam questions parsed into 19 protocol groups
- Current flow: Students read concept material FIRST, then answer exam questions
- Files exist in: templates/, utils/, data/, static/, app.py
- Hosted on Render.com, repo on GitHub
- Uses Anthropic API for AI tutoring
- Cisco configuration guides in data/config_guides/ are the PRIMARY authoritative source, supplemented by Cisco websites and third-party CCNA books for depth

WHAT NEEDS TO CHANGE:
- NEW flow: Students answer exam questions FIRST, then the AI explains the answer using a 3-tier source hierarchy: Cisco configuration guides (primary), Cisco websites (secondary), third-party CCNA books (tertiary for depth)
- Do NOT modify or delete any existing files
- Create ALL changes as NEW files alongside the existing ones
- The old concept-review pages can remain accessible but should no longer be the primary entry point

IMPORTANT CONSTRAINTS:
- Students have completed 3 courses in a network admin degree. They are NOT beginners.
- Questions must be presented EXACTLY as written in the test bank — same wording, same answer choices, same format. No paraphrasing.
- The 628 questions are grouped into 19 protocol groups. Some questions involve multiple protocols and appear in more than one group.
- The AI tutor's PRIMARY authority is the Cisco configuration guides — supplemented by official Cisco websites as secondary source and third-party CCNA books as tertiary source for added depth. If sources conflict, the configuration guide wins.
- All students share one login — no individual tracking.
```

---

## Step 1 — New Questions-First Templates

```
Step 1: Create new templates for the questions-first study flow. Do NOT modify existing templates — create new ones.

Create these NEW files:

templates/study_home.html — New primary study landing page
- Extends base.html
- Displays all 19 protocol groups as clickable cards
- Each card shows: protocol name, number of questions in that group, brief description
- Cards link to the question practice page for that protocol group
- Simple, clean layout — no concept material here, just jump straight into practice
- Include a "Study All" option that pulls questions from all groups randomly

templates/practice.html — The core questions-first practice page
- Extends base.html
- Shows the protocol group name at the top
- Displays ONE question at a time, exactly as written in the test bank
- Answer choices shown as clickable buttons or radio buttons
- Student selects their answer and clicks "Submit"
- After submit, the page shows one of two responses:

  IF WRONG:
  - Message: "Not quite. Here's a hint..."
  - AI generates a hint grounded in the Cisco configuration guide, supplemented by Cisco docs and CCNA references for depth
  - The hint must NOT reveal the correct answer
  - Student can try again (same question, their wrong answer is greyed out)
  - After 2 wrong attempts, offer to reveal the answer with full explanation

  IF CORRECT:
  - Message: "Correct!"
  - AI explains WHY it is correct, starting with the Cisco configuration guide and adding depth from Cisco websites and CCNA books
  - AI also explains why EACH wrong answer is incorrect — this is critical because third-party study materials sometimes teach the wrong reasoning
  - Show a "Next Question" button

- Track progress within the session: questions answered, correct/incorrect counts
- Show a "Skip" button to move to next question without answering
- Show question number: "Question 3 of 47" for the current protocol group

templates/practice_summary.html — End of practice session summary
- Shows how many questions answered, correct percentage
- Lists which questions were missed with links to retry them
- Button to continue with remaining questions or pick a new protocol group

Use Bootstrap 5, match the existing dark blue (#1a365d) and teal (#2c7a7b) color scheme from style.css.
All AI interactions should be AJAX calls so the page doesn't reload between attempts.
```

---

## Step 2 — New Routes and Practice Logic

```
Step 2: Create new route handlers for the questions-first flow. Do NOT modify app.py — create a new Blueprint.

Create NEW file: routes/practice_routes.py — Flask Blueprint for practice flow

Routes needed:

GET /practice/
- Renders study_home.html
- Loads all 19 protocol groups with question counts from the existing question parser

GET /practice/<protocol_group>
- Renders practice.html
- Loads questions for the selected protocol group
- Randomizes question order for each session
- Tracks which questions have been shown (session-based, using Flask session)

POST /practice/check-answer
- AJAX endpoint
- Receives: question_id, selected_answer, attempt_number
- GRADING: Compare the student's selected_answer directly against the correct answer stored in the test bank data. This is a simple string comparison — do NOT call the AI to grade.
- AFTER grading:
  - If WRONG: Call the AI tutor to generate a hint (this is the only part that uses the API)
  - If CORRECT: Call the AI tutor to explain why it's correct and why each wrong answer is wrong
- Returns JSON:
  {
    "correct": true/false,
    "feedback": "AI generated explanation or hint",
    "attempt": 1,
    "correct_answer": null (only revealed after max attempts or correct)
  }

GET /practice/<protocol_group>/summary
- Renders practice_summary.html with session results

POST /practice/explain
- AJAX endpoint for when student requests full explanation after max wrong attempts
- Returns the complete AI explanation with config guide references

Then create NEW file: routes/__init__.py
- Register the practice Blueprint

Then modify app.py MINIMALLY:
- Import and register the practice Blueprint
- Update the home page cards so "Practice Exam Questions" links to /practice/ instead of the old quiz route
- Keep ALL existing routes working — do not remove anything
```

---

## Step 3 — Updated AI Tutor Methods

```
Step 3: Add new methods to the AI tutor for the questions-first flow. Do NOT replace existing methods — add new ones.

IMPORTANT SEPARATION OF CONCERNS:
- GRADING is done by simple comparison against the correct answer already stored in the test bank. No AI needed.
- The AI is ONLY called for two purposes:
  1. Generating hints when the student answers wrong (without revealing the correct answer)
  2. Explaining the reasoning after a correct answer or after max failed attempts, using a 3-tier source hierarchy: Cisco configuration guides (primary), Cisco websites (secondary), and third-party CCNA books (tertiary for added depth)
- This saves API calls — the AI is never used just to check if an answer is right or wrong.

Add these methods to utils/ai_tutor.py (or create utils/practice_tutor.py if you prefer not to touch the existing file):

Method: generate_hint(question, wrong_answer, attempt_number, config_guide_context)
- Takes the full question object, the student's wrong answer, which attempt this is, and relevant config guide text
- System prompt:
  """
  You are a CCNA tutor helping a student who answered incorrectly.

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
  - Never say "the answer is" or directly identify the correct option
  """

Method: explain_correct_answer(question, correct_answer, wrong_answers, config_guide_context)
- Takes the full question, correct answer, all wrong answers, and relevant config guide text
- System prompt:
  """
  You are a CCNA tutor explaining why an answer is correct.

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
  - Total explanation should be 4-8 sentences
  """

Method: explain_after_failed_attempts(question, student_attempts, config_guide_context)
- Called when student exhausts attempts and asks for the full answer
- Reveals the correct answer AND gives the complete explanation
- Same quality and source hierarchy as explain_correct_answer but acknowledges the student struggled
- Use the same 3-tier source approach: config guide first, Cisco websites second, third-party books for depth

For config guide context: use the existing ConfigGuideManager.search_guides() to find relevant sections based on keywords from the question. Pass that text into the AI prompts.
```

---

## Step 4 — Practice JavaScript

```
Step 4: Create the client-side JavaScript for the practice flow.

Create NEW file: static/js/practice.js

This handles:
1. Answer submission via AJAX (no page reloads)
2. Displaying AI feedback inline on the page
3. Greying out wrong answers after failed attempts
4. Showing/hiding the "Try Again" and "Next Question" buttons
5. Updating the progress counter
6. Loading the next question without page reload
7. Tracking session progress (questions seen, correct, incorrect) in a JS object
8. "Skip" functionality
9. End-of-session detection — when all questions are done, redirect to summary page

AJAX flow:
- Student clicks answer -> POST to /practice/check-answer
- Show a loading spinner while waiting for AI response
- Display the response in a styled feedback div below the question
- If wrong: grey out that answer choice, show "Try Again"
- If wrong on attempt 2: show "Try Again" and "Show Answer" button
- If correct: show explanation, enable "Next Question"

Keep it clean — no frameworks needed, vanilla JS with fetch() is fine.
Use the existing Bootstrap classes for styling feedback messages.
```

---

## Step 5 — Update Navigation and Home Page

```
Step 5: Update the navigation to feature the questions-first flow as the primary path.

Modify templates/base.html MINIMALLY:
- Add "Practice" as a primary nav link pointing to /practice/
- Keep all existing nav links working

Modify templates/index.html MINIMALLY:
- Update the "Practice Exam Questions" card to link to /practice/
- Change the card description to emphasize: "Jump straight into exam questions — get AI-powered explanations grounded in Cisco configuration guides with added depth from Cisco docs and CCNA references"
- Keep the other cards (Study Protocols, Packet Tracer Labs) as they are

Do NOT remove or rename any existing pages or routes.
```

---

## Step 6 — Test and Verify

```
Step 6: Test the complete questions-first flow.

Verify:
1. /practice/ loads and shows all 19 protocol groups with correct question counts
2. Clicking a protocol group loads the first randomized question
3. Selecting a wrong answer returns an AI hint that does NOT reveal the answer (grading is instant via test bank comparison, AI only generates the hint)
4. The wrong answer gets greyed out
5. Selecting wrong a second time returns a more specific hint
6. After 2 wrong attempts, "Show Answer" button appears and works
7. Selecting the correct answer returns the full explanation grounded in config guide with depth from Cisco docs/books (grading is instant, AI generates explanation)
8. If the Anthropic API key isn't set or the API is down, grading still works — just show "Correct!" or "Incorrect" without AI-generated hints/explanations
8. "Next Question" loads the next question without page reload
9. "Skip" works correctly
10. Progress counter updates accurately
11. Summary page shows correct stats at end of session
12. All OLD routes still work — /quiz, /protocol, etc.
13. The home page links to /practice/ for the question practice flow

Run the app locally with: flask run
Test with a few questions from at least 2 different protocol groups.
Grading should always work since it's just comparing against the test bank answer key — no API needed.
If the Anthropic API key isn't set, grading still works but hints and explanations should return a helpful fallback message like "AI explanations unavailable — the correct answer is [X]" instead of crashing.
```
