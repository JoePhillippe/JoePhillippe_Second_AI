"""
Practice Routes Blueprint
Questions-first study flow with AI-powered feedback
"""

import random
import uuid
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for

from utils.ai_tutor import CCNATutor
from utils.protocol_manager import ProtocolManager
from utils.question_parser import QuestionParser

practice_bp = Blueprint('practice', __name__, url_prefix='/practice')


@practice_bp.before_request
def require_login():
    """Redirect to login if not authenticated."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

# Shared instances (set during blueprint registration via init_app)
_protocol_manager = None
_question_parser = None

# Server-side practice session storage (keyed by session ID stored in Flask session)
_practice_sessions = {}


def init_app(protocol_manager, question_parser):
    """Initialize the blueprint with shared app instances."""
    global _protocol_manager, _question_parser
    _protocol_manager = protocol_manager
    _question_parser = question_parser


def _get_practice_session():
    """Get the current practice session from Flask session."""
    sid = session.get('practice_session_id')
    if sid and sid in _practice_sessions:
        return _practice_sessions[sid]
    return None


def _sanitize_question(question, question_number):
    """Return question data safe for the client (no correct_answer)."""
    return {
        'id': question['id'],
        'question_text': question['question_text'],
        'choices': question['choices'],
        'multi_answer': question.get('multi_answer', False),
        'question_number': question_number,
        'protocol_tags': question.get('protocol_tags', [])
    }


def _build_tutor_question_data(question):
    """Convert QuestionParser question dict to CCNATutor format."""
    options = [question['choices'][k] for k in sorted(question['choices'].keys())]
    if ',' in question['correct_answer']:
        correct_texts = [question['choices'].get(letter.strip(), letter)
                         for letter in question['correct_answer'].split(',')]
        correct_answer_text = ', '.join(correct_texts)
    else:
        correct_answer_text = question['choices'].get(question['correct_answer'],
                                                       question['correct_answer'])
    return {
        'question': question['question_text'],
        'options': options,
        'correct_answer': correct_answer_text,
        'topic': question.get('protocol_tags', [''])[0] if question.get('protocol_tags') else '',
        'keywords': question.get('protocol_tags', [])
    }


# ==================== Page Routes ====================

@practice_bp.route('/')
def study_home():
    """Render the study landing page with all protocol cards."""
    protocols_by_category = _protocol_manager.get_protocols_by_category()
    question_counts = {}
    for slug in _protocol_manager.protocols:
        questions = _question_parser.get_questions_by_protocol(slug)
        question_counts[slug] = len(questions)
    total_questions = len(_question_parser.get_all_questions())
    return render_template('study_home.html',
                           protocols_by_category=protocols_by_category,
                           question_counts=question_counts,
                           total_questions=total_questions)


@practice_bp.route('/<slug>')
def practice(slug):
    """Render the practice page for a specific protocol or all protocols."""
    if slug == 'all':
        all_questions = _question_parser.get_all_questions()
        return render_template('practice.html',
                               protocol_name='All Protocols',
                               protocol_slug='all',
                               total_questions=len(all_questions))
    else:
        protocol_data = _protocol_manager.get_protocol(slug)
        if not protocol_data:
            return render_template('404.html', message=f"Protocol '{slug}' not found"), 404
        questions = _question_parser.get_questions_by_protocol(slug)
        return render_template('practice.html',
                               protocol_name=protocol_data.get('name', slug),
                               protocol_slug=slug,
                               total_questions=len(questions))


@practice_bp.route('/<slug>/summary')
def practice_summary_page(slug):
    """Render the practice summary page."""
    if slug == 'all':
        protocol_name = 'All Protocols'
    else:
        protocol_data = _protocol_manager.get_protocol(slug)
        protocol_name = protocol_data.get('name', slug) if protocol_data else slug
    return render_template('practice_summary.html',
                           protocol_name=protocol_name,
                           protocol_slug=slug)


# ==================== API Endpoints ====================

@practice_bp.route('/start-session', methods=['POST'])
def start_session():
    """Start a new practice session. Stores session ID in Flask session."""
    try:
        data = request.get_json()
        protocol_slug = data.get('protocol_slug')

        if not protocol_slug:
            return jsonify({'error': 'Missing protocol_slug'}), 400

        if protocol_slug == 'all':
            questions = _question_parser.get_all_questions()
            protocol_name = 'All Protocols'
        else:
            protocol_data = _protocol_manager.get_protocol(protocol_slug)
            if not protocol_data:
                return jsonify({'error': f'Protocol {protocol_slug} not found'}), 404
            questions = _question_parser.get_questions_by_protocol(protocol_slug)
            protocol_name = protocol_data.get('name', protocol_slug)

        if not questions:
            return jsonify({'error': f'No questions found for {protocol_slug}'}), 404

        shuffled = list(questions)
        random.shuffle(shuffled)

        sid = str(uuid.uuid4())
        _practice_sessions[sid] = {
            'protocol_slug': protocol_slug,
            'protocol_name': protocol_name,
            'question_ids': [q['id'] for q in shuffled],
            'current_index': 0,
            'results': [],
            'wrong_attempts': {},
            'skipped': [],
            'disabled_choices': {},
        }

        # Store session ID in Flask session cookie
        session['practice_session_id'] = sid

        first_q = shuffled[0]
        return jsonify({
            'protocol_slug': protocol_slug,
            'protocol_name': protocol_name,
            'total_questions': len(shuffled),
            'first_question': _sanitize_question(first_q, 1)
        })

    except Exception as e:
        return jsonify({'error': f'Error starting practice: {str(e)}'}), 500


@practice_bp.route('/check-answer', methods=['POST'])
def check_answer():
    """Check a practice answer and return AI feedback."""
    try:
        ps = _get_practice_session()
        if not ps:
            return jsonify({'error': 'No active practice session'}), 404

        data = request.get_json()
        question_id = data.get('question_id')
        selected_answer = data.get('selected_answer')
        attempt_number = data.get('attempt_number', 1)

        if not question_id or not selected_answer:
            return jsonify({'error': 'Missing question_id or selected_answer'}), 400

        question = _question_parser.get_question_by_id(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # Grade: simple string comparison against test bank data
        correct_answer = question['correct_answer']
        if ',' in correct_answer:
            correct_set = set(correct_answer.lower().split(','))
            student_set = set(selected_answer.lower().split(','))
            is_correct = student_set == correct_set
        else:
            is_correct = selected_answer.lower() == correct_answer.lower()

        # Track attempts
        if question_id not in ps['wrong_attempts']:
            ps['wrong_attempts'][question_id] = 0

        if is_correct:
            attempts_used = ps['wrong_attempts'][question_id] + 1
            ps['results'].append({
                'question_id': question_id,
                'correct': True,
                'attempts': attempts_used,
                'question_text': question['question_text'][:100]
            })

            # AI explains why correct + why each wrong answer is wrong
            try:
                question_data = _build_tutor_question_data(question)
                tutor = CCNATutor()
                config_context = tutor.get_config_context(question_data)
                wrong_answers = [opt for opt in question_data['options']
                                 if opt != question_data['correct_answer']]
                feedback = tutor.explain_correct_answer(
                    question_data=question_data,
                    correct_answer=question_data['correct_answer'],
                    wrong_answers=wrong_answers,
                    config_guide_context=config_context
                )
            except Exception:
                feedback = 'AI explanations unavailable — but you got it right!'

            return jsonify({
                'correct': True,
                'feedback': feedback,
                'attempt': attempts_used,
                'correct_answer': correct_answer
            })
        else:
            ps['wrong_attempts'][question_id] += 1
            attempt_num = ps['wrong_attempts'][question_id]

            # Track disabled choices for single-answer questions
            if question_id not in ps['disabled_choices']:
                ps['disabled_choices'][question_id] = []
            if ',' not in selected_answer:
                if selected_answer.lower() not in ps['disabled_choices'][question_id]:
                    ps['disabled_choices'][question_id].append(selected_answer.lower())

            # AI generates hint (does NOT reveal answer)
            try:
                question_data = _build_tutor_question_data(question)
                tutor = CCNATutor()
                config_context = tutor.get_config_context(question_data)
                feedback = tutor.generate_hint(
                    question_data=question_data,
                    wrong_answer=selected_answer,
                    attempt_number=attempt_num,
                    config_guide_context=config_context
                )
            except Exception:
                feedback = 'AI hints unavailable — try again or reveal the answer.'

            return jsonify({
                'correct': False,
                'feedback': feedback,
                'attempt': attempt_num,
                'correct_answer': None,
                'can_reveal': attempt_num >= 2,
                'disabled_choices': ps['disabled_choices'].get(question_id, [])
            })

    except Exception as e:
        return jsonify({'error': f'Error checking answer: {str(e)}'}), 500


@practice_bp.route('/explain', methods=['POST'])
def explain():
    """Reveal correct answer with full AI explanation after max wrong attempts."""
    try:
        ps = _get_practice_session()
        if not ps:
            return jsonify({'error': 'No active practice session'}), 404

        data = request.get_json()
        question_id = data.get('question_id')

        if not question_id:
            return jsonify({'error': 'Missing question_id'}), 400

        question = _question_parser.get_question_by_id(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # Record as incorrect
        attempts = ps['wrong_attempts'].get(question_id, 0)
        ps['results'].append({
            'question_id': question_id,
            'correct': False,
            'attempts': attempts,
            'question_text': question['question_text'][:100]
        })

        # Full AI explanation after failed attempts
        try:
            question_data = _build_tutor_question_data(question)
            tutor = CCNATutor()
            config_context = tutor.get_config_context(question_data)
            student_attempts = ps['disabled_choices'].get(question_id, [])
            feedback = tutor.explain_after_failed_attempts(
                question_data=question_data,
                student_attempts=student_attempts,
                config_guide_context=config_context
            )
        except Exception:
            feedback = 'AI explanations unavailable.'

        correct_answer = question['correct_answer']
        if ',' in correct_answer:
            correct_text = ', '.join(
                f"{l.upper()}. {question['choices'].get(l.strip(), l)}"
                for l in correct_answer.split(',')
            )
        else:
            correct_text = f"{correct_answer.upper()}. {question['choices'].get(correct_answer, correct_answer)}"

        return jsonify({
            'correct_answer': correct_answer,
            'correct_answer_text': correct_text,
            'feedback': feedback
        })

    except Exception as e:
        return jsonify({'error': f'Error revealing answer: {str(e)}'}), 500


@practice_bp.route('/skip', methods=['POST'])
def skip_question():
    """Skip the current question and get the next one."""
    try:
        ps = _get_practice_session()
        if not ps:
            return jsonify({'error': 'No active practice session'}), 404

        data = request.get_json()
        question_id = data.get('question_id')

        if question_id:
            ps['skipped'].append(question_id)

        ps['current_index'] += 1

        if ps['current_index'] < len(ps['question_ids']):
            next_qid = ps['question_ids'][ps['current_index']]
            next_q = _question_parser.get_question_by_id(next_qid)
            if next_q:
                return jsonify({
                    'skipped': True,
                    'next_question': _sanitize_question(next_q, ps['current_index'] + 1),
                    'total_questions': len(ps['question_ids']),
                    'done': False
                })

        return jsonify({'skipped': True, 'next_question': None, 'done': True})

    except Exception as e:
        return jsonify({'error': f'Error skipping question: {str(e)}'}), 500


@practice_bp.route('/next', methods=['POST'])
def next_question():
    """Get the next question in the practice session."""
    try:
        ps = _get_practice_session()
        if not ps:
            return jsonify({'error': 'No active practice session'}), 404

        ps['current_index'] += 1

        if ps['current_index'] < len(ps['question_ids']):
            next_qid = ps['question_ids'][ps['current_index']]
            next_q = _question_parser.get_question_by_id(next_qid)
            if next_q:
                return jsonify({
                    'question': _sanitize_question(next_q, ps['current_index'] + 1),
                    'question_number': ps['current_index'] + 1,
                    'total_questions': len(ps['question_ids']),
                    'done': False
                })

        return jsonify({'question': None, 'done': True})

    except Exception as e:
        return jsonify({'error': f'Error getting next question: {str(e)}'}), 500


@practice_bp.route('/summary', methods=['GET'])
def practice_summary_data():
    """Get practice session results as JSON for the summary page."""
    try:
        ps = _get_practice_session()
        if not ps:
            return jsonify({'error': 'No active practice session'}), 404

        results = ps['results']
        correct = sum(1 for r in results if r['correct'])
        incorrect = sum(1 for r in results if not r['correct'])
        answered = len(results)
        percentage = round((correct / answered) * 100) if answered > 0 else 0

        missed = [r for r in results if not r['correct']]

        return jsonify({
            'protocol_slug': ps['protocol_slug'],
            'protocol_name': ps['protocol_name'],
            'total_questions': len(ps['question_ids']),
            'answered': answered,
            'correct': correct,
            'incorrect': incorrect,
            'skipped': len(ps['skipped']),
            'percentage': percentage,
            'missed_questions': missed
        })

    except Exception as e:
        return jsonify({'error': f'Error getting summary: {str(e)}'}), 500
