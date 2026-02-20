from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for
from functools import wraps
import os
import uuid
import random
import json
from dotenv import load_dotenv
from utils.ai_tutor import CCNATutor
from utils.protocol_manager import ProtocolManager
from utils.question_parser import QuestionParser
from utils.concept_grouper import ConceptGrouper
from routes.practice_routes import practice_bp, init_app as init_practice_routes

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Hardcoded credentials (single-user auth)
APP_USERNAME = 'Student12345'
APP_PASSWORD = '12345FTCC!@#$%'


def login_required(f):
    """Decorator to protect routes behind login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize managers
protocol_manager = ProtocolManager()
question_parser = QuestionParser()
concept_grouper = ConceptGrouper()

# Load questions on startup
# Build list of protocol names and slugs for tagging
protocols_list = []
for slug, protocol_data in protocol_manager.protocols.items():
    protocols_list.append(slug)
    protocols_list.append(protocol_data.get('name', ''))
question_parser.load_all_questions(protocols_list=protocols_list)

# Load cached concept groups on startup
print("\nLoading cached concept groups...")
for protocol_slug in protocol_manager.protocols.keys():
    cached_groups = concept_grouper.load_groups(protocol_slug)
    if cached_groups:
        print(f"  Loaded {len(cached_groups)} groups for {protocol_slug}")

# In-memory quiz sessions storage (session_id -> session_data)
quiz_sessions = {}

# Register practice Blueprint
init_practice_routes(protocol_manager, question_parser)
app.register_blueprint(practice_bp)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication handler."""
    if session.get('logged_in'):
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == APP_USERNAME and password == APP_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid credentials. Please try again.'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Render the landing page"""
    return render_template('index.html')

@app.route('/test-ai')
@login_required
def test_ai():
    """Test route to verify AI tutor functionality"""
    try:
        # Check if API key is set
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'ANTHROPIC_API_KEY environment variable not set. Please set it to test the AI tutor.'
            }), 500

        # Initialize the tutor
        tutor = CCNATutor()

        # Sample question for testing
        sample_question = {
            'question': 'Which routing protocol uses the Diffusing Update Algorithm (DUAL)?',
            'options': [
                'OSPF',
                'EIGRP',
                'RIP',
                'BGP'
            ],
            'correct_answer': 'EIGRP',
            'topic': 'EIGRP',
            'keywords': ['EIGRP', 'DUAL', 'routing protocol']
        }

        # Get config context
        config_context = tutor.get_config_context(sample_question)

        # Test wrong answer handling
        wrong_answer_hint = tutor.handle_wrong_answer(
            question_data=sample_question,
            student_answer='OSPF',
            config_context=config_context,
            attempt_number=1
        )

        # Test correct answer handling
        correct_answer_explanation = tutor.handle_correct_answer(
            question_data=sample_question,
            student_answer='EIGRP',
            config_context=config_context
        )

        return jsonify({
            'status': 'success',
            'message': 'AI Tutor is working!',
            'sample_question': sample_question['question'],
            'config_context_preview': config_context[:500] + '...' if len(config_context) > 500 else config_context,
            'wrong_answer_hint': wrong_answer_hint,
            'correct_answer_explanation': correct_answer_explanation
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error testing AI tutor: {str(e)}'
        }), 500

@app.route('/protocols')
@login_required
def protocols():
    """Display all protocols grouped by category"""
    protocols_by_category = protocol_manager.get_protocols_by_category()
    return render_template('protocols.html', protocols_by_category=protocols_by_category)

@app.route('/protocol/<slug>')
@login_required
def protocol(slug):
    """Display individual protocol study page"""
    protocol_data = protocol_manager.get_protocol(slug)

    if not protocol_data:
        return render_template('404.html', message=f"Protocol '{slug}' not found"), 404

    related_protocols = protocol_manager.get_related_protocols(slug)

    return render_template('protocol.html', protocol=protocol_data, related_protocols=related_protocols)

@app.route('/api/ask', methods=['POST'])
@login_required
def api_ask():
    """API endpoint for AI tutor chat on protocol pages"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        protocol_slug = data.get('protocol_slug')
        question = data.get('question')

        if not protocol_slug or not question:
            return jsonify({'error': 'Missing protocol_slug or question'}), 400

        # Get protocol data
        protocol_data = protocol_manager.get_protocol(protocol_slug)
        if not protocol_data:
            return jsonify({'error': f'Protocol {protocol_slug} not found'}), 404

        # Check if API key is set
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'ANTHROPIC_API_KEY environment variable not set'
            }), 500

        # Initialize the tutor
        tutor = CCNATutor()

        # Get configuration guide context based on protocol
        config_context = tutor.config_manager.get_guide_section('router', protocol_slug)
        if not config_context:
            # Try to search for relevant sections
            keywords = [protocol_data.get('name', '')]
            keywords.extend(protocol_data.get('key_topics', [])[:3])  # Add first 3 key topics
            results = tutor.config_manager.search_guides(keywords)
            if results:
                config_context = '\n\n'.join([r['content'] for r in results[:2]])
            else:
                config_context = "No specific configuration guide content found for this protocol yet."

        # Use the explain_concept method to answer the question
        response = tutor.explain_concept(
            protocol_name=protocol_data.get('name'),
            specific_topic=question,
            config_context=config_context
        )

        return jsonify({
            'answer': response,
            'protocol': protocol_data.get('name')
        })

    except Exception as e:
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500

@app.route('/api/questions/<protocol_slug>', methods=['GET'])
@login_required
def api_questions_by_protocol(protocol_slug):
    """API endpoint to get questions for a specific protocol"""
    try:
        questions = question_parser.get_questions_by_protocol(protocol_slug)
        return jsonify({
            'protocol': protocol_slug,
            'count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving questions: {str(e)}'
        }), 500

@app.route('/api/questions/multi-protocol', methods=['GET'])
@login_required
def api_multi_protocol_questions():
    """API endpoint to get all multi-protocol questions"""
    try:
        questions = question_parser.get_multi_protocol_questions()
        return jsonify({
            'count': len(questions),
            'questions': questions
        })
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving multi-protocol questions: {str(e)}'
        }), 500

@app.route('/api/drag-drop-questions', methods=['GET'])
@login_required
def api_drag_drop_questions():
    """API endpoint to get drag-and-drop questions"""
    try:
        # Load drag-drop questions from JSON file
        drag_drop_path = os.path.join(app.root_path, 'data', 'test_bank', '200-301_7-1_drag_drop.json')
        if os.path.exists(drag_drop_path):
            with open(drag_drop_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'error': 'Drag-drop questions file not found'}), 404
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving drag-drop questions: {str(e)}'
        }), 500

@app.route('/api/drag-drop-questions/<int:question_id>', methods=['GET'])
@login_required
def api_drag_drop_question(question_id):
    """API endpoint to get a specific drag-and-drop question"""
    try:
        drag_drop_path = os.path.join(app.root_path, 'data', 'test_bank', '200-301_7-1_drag_drop.json')
        if os.path.exists(drag_drop_path):
            with open(drag_drop_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Find the specific question
            question = next((q for q in data.get('questions', []) if q.get('id') == question_id), None)
            if question:
                return jsonify(question)
            else:
                return jsonify({'error': f'Question {question_id} not found'}), 404
        else:
            return jsonify({'error': 'Drag-drop questions file not found'}), 404
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving drag-drop question: {str(e)}'
        }), 500

@app.route('/drag-drop')
@login_required
def drag_drop_viewer():
    """Serve the drag-and-drop question viewer"""
    return send_from_directory(os.path.join(app.root_path, 'data', 'test_bank'), 'drag_drop_viewer.html')

@app.route('/api/concept-groups/<protocol_slug>', methods=['GET'])
@login_required
def api_concept_groups(protocol_slug):
    """API endpoint to get concept groups for a protocol"""
    try:
        groups = concept_grouper.get_groups_by_protocol(protocol_slug)

        if not groups:
            return jsonify({
                'protocol': protocol_slug,
                'message': 'No concept groups found. Run /admin/regroup to generate them.',
                'groups': []
            })

        return jsonify({
            'protocol': protocol_slug,
            'count': len(groups),
            'groups': groups
        })
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving concept groups: {str(e)}'
        }), 500

@app.route('/admin/regroup', methods=['POST'])
@login_required
def admin_regroup_all():
    """Admin endpoint to regenerate all concept groups using AI"""
    try:
        # Check if API key is set
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'ANTHROPIC_API_KEY environment variable not set'
            }), 500

        # Build questions by protocol
        questions_by_protocol = {}
        for protocol_slug in protocol_manager.protocols.keys():
            questions = question_parser.get_questions_by_protocol(protocol_slug)
            if questions:
                questions_by_protocol[protocol_slug] = questions

        # Analyze and group
        all_groups = concept_grouper.analyze_and_group(questions_by_protocol)

        # Summary
        total_groups = sum(len(groups) for groups in all_groups.values())

        return jsonify({
            'status': 'success',
            'message': f'Regrouped {len(all_groups)} protocols',
            'total_groups': total_groups,
            'protocols': list(all_groups.keys())
        })

    except Exception as e:
        return jsonify({
            'error': f'Error regrouping questions: {str(e)}'
        }), 500

@app.route('/admin/regroup/<protocol_slug>', methods=['POST'])
@login_required
def admin_regroup_protocol(protocol_slug):
    """Admin endpoint to regenerate concept groups for one protocol"""
    try:
        # Check if API key is set
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'ANTHROPIC_API_KEY environment variable not set'
            }), 500

        # Get questions for this protocol
        questions = question_parser.get_questions_by_protocol(protocol_slug)

        if not questions:
            return jsonify({
                'error': f'No questions found for protocol: {protocol_slug}'
            }), 404

        # Analyze and group
        questions_by_protocol = {protocol_slug: questions}
        all_groups = concept_grouper.analyze_and_group(questions_by_protocol)

        groups = all_groups.get(protocol_slug, [])

        return jsonify({
            'status': 'success',
            'message': f'Regrouped {protocol_slug}',
            'protocol': protocol_slug,
            'total_groups': len(groups),
            'groups': groups
        })

    except Exception as e:
        return jsonify({
            'error': f'Error regrouping protocol: {str(e)}'
        }), 500

@app.route('/quiz')
@login_required
def quiz():
    """Render the quiz page"""
    protocol_slug = request.args.get('protocol', '')
    protocols_by_category = protocol_manager.get_protocols_by_category()
    return render_template('quiz.html',
                         protocols_by_category=protocols_by_category,
                         selected_protocol=protocol_slug)

@app.route('/api/quiz/start/<protocol_slug>', methods=['GET'])
@login_required
def api_quiz_start(protocol_slug):
    """Start a new quiz session for a protocol"""
    try:
        # Get concept groups for this protocol
        groups = concept_grouper.get_groups_by_protocol(protocol_slug)

        if not groups:
            return jsonify({
                'error': f'No concept groups found for {protocol_slug}. Run /admin/regroup first.'
            }), 404

        # Get questions for this protocol
        all_questions = question_parser.get_questions_by_protocol(protocol_slug)

        # Build quiz session: one random question per concept group
        session_id = str(uuid.uuid4())
        concept_groups_with_questions = []

        for group in groups:
            group_id = group['group_id']
            question_ids = group.get('question_ids', [])

            if not question_ids:
                continue

            # Pick random question from this group
            random_qid = random.choice(question_ids)
            question = question_parser.get_question_by_id(random_qid)

            if question:
                concept_groups_with_questions.append({
                    'group_id': group_id,
                    'concept': group.get('concept', ''),
                    'question': question,
                    'group_size': group.get('group_size', 1),
                    'seen_questions': [random_qid]  # Track which questions student has seen
                })

        # Store session
        quiz_sessions[session_id] = {
            'protocol': protocol_slug,
            'concept_groups': concept_groups_with_questions,
            'current_index': 0,
            'scores': {}  # group_id -> {first_attempt_correct: bool, attempts: int}
        }

        return jsonify({
            'session_id': session_id,
            'protocol': protocol_slug,
            'total_concepts': len(concept_groups_with_questions),
            'concept_groups': concept_groups_with_questions
        })

    except Exception as e:
        return jsonify({
            'error': f'Error starting quiz: {str(e)}'
        }), 500

@app.route('/api/quiz/submit', methods=['POST'])
@login_required
def api_quiz_submit():
    """Submit an answer and get AI feedback"""
    try:
        data = request.get_json()

        session_id = data.get('session_id')
        question_id = data.get('question_id')
        student_answer = data.get('student_answer')
        attempt_number = data.get('attempt_number', 1)
        group_id = data.get('group_id')

        if not all([session_id, question_id, student_answer, group_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Get session
        session = quiz_sessions.get(session_id)
        if not session:
            return jsonify({'error': 'Invalid session'}), 404

        # Get question
        question = question_parser.get_question_by_id(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # Check answer (supports multi-answer questions with comma-separated values)
        correct_answer = question['correct_answer']
        if ',' in correct_answer:
            correct_set = set(correct_answer.lower().split(','))
            student_set = set(student_answer.lower().split(','))
            is_correct = student_set == correct_set
        else:
            is_correct = student_answer.lower() == correct_answer.lower()

        # Update session scores
        if group_id not in session['scores']:
            session['scores'][group_id] = {
                'first_attempt_correct': is_correct and attempt_number == 1,
                'attempts': attempt_number
            }
        else:
            session['scores'][group_id]['attempts'] = attempt_number

        # Get AI feedback
        tutor = CCNATutor()
        config_context = tutor.get_config_context(question)

        if is_correct:
            # Get explanation of why answer is correct and others are wrong
            explanation = tutor.handle_correct_answer(
                question_data=question,
                student_answer=student_answer,
                config_context=config_context
            )

            # Find how many more questions in this group
            current_group = next((g for g in session['concept_groups'] if g['group_id'] == group_id), None)
            more_in_group = 0
            if current_group:
                seen = current_group.get('seen_questions', [])
                total_in_group = current_group['group_size']
                more_in_group = total_in_group - len(seen)

            return jsonify({
                'correct': True,
                'explanation': explanation,
                'attempts_needed': attempt_number,
                'more_in_group': more_in_group,
                'correct_answer': correct_answer
            })
        else:
            # Get hint without revealing answer
            hint = tutor.handle_wrong_answer(
                question_data=question,
                student_answer=student_answer,
                config_context=config_context,
                attempt_number=attempt_number
            )

            return jsonify({
                'correct': False,
                'hint': hint,
                'attempt': attempt_number
            })

    except Exception as e:
        return jsonify({
            'error': f'Error submitting answer: {str(e)}'
        }), 500

@app.route('/api/quiz/group-question/<group_id>', methods=['GET'])
@login_required
def api_quiz_group_question(group_id):
    """Get another random question from the same concept group"""
    try:
        session_id = request.args.get('session_id')
        exclude = request.args.get('exclude', '').split(',')

        if not session_id:
            return jsonify({'error': 'Missing session_id'}), 400

        # Get session
        session = quiz_sessions.get(session_id)
        if not session:
            return jsonify({'error': 'Invalid session'}), 404

        protocol_slug = session['protocol']

        # Get the concept group
        groups = concept_grouper.get_groups_by_protocol(protocol_slug)
        group = next((g for g in groups if g.get('group_id') == group_id), None)

        if not group:
            return jsonify({'error': 'Group not found'}), 404

        # Get question IDs in this group, excluding already seen
        question_ids = group.get('question_ids', [])
        available_ids = [qid for qid in question_ids if qid not in exclude]

        if not available_ids:
            return jsonify({
                'error': 'No more questions in this group',
                'all_covered': True
            }), 404

        # Pick random question
        random_qid = random.choice(available_ids)
        question = question_parser.get_question_by_id(random_qid)

        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # Update session to track this question as seen
        current_group = next((g for g in session['concept_groups'] if g['group_id'] == group_id), None)
        if current_group:
            if 'seen_questions' not in current_group:
                current_group['seen_questions'] = []
            current_group['seen_questions'].append(random_qid)

        return jsonify({
            'question': question,
            'group_id': group_id,
            'remaining_in_group': len(available_ids) - 1
        })

    except Exception as e:
        return jsonify({
            'error': f'Error getting group question: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
