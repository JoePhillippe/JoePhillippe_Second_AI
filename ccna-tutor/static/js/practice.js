/**
 * Practice Mode - Questions-First Study Flow
 * Handles both the practice page and summary page
 */

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('question-card')) {
        initPracticePage();
    } else if (document.getElementById('total-answered')) {
        initSummaryPage();
    }
});

// ==================== Practice Page ====================

let practiceState = {
    protocolSlug: null,
    totalQuestions: 0,
    currentQuestion: null,
    questionNumber: 0,
    correctCount: 0,
    incorrectCount: 0,
    skippedCount: 0,
    attemptNumber: 0,
    disabledChoices: [],
    canReveal: false
};

function initPracticePage() {
    var config = window.practiceConfig;
    practiceState.protocolSlug = config.protocolSlug;
    practiceState.totalQuestions = config.totalQuestions;

    // Wire up button listeners
    document.getElementById('submit-btn').addEventListener('click', submitAnswer);
    document.getElementById('try-again-btn').addEventListener('click', tryAgain);
    document.getElementById('reveal-btn').addEventListener('click', revealAnswer);
    document.getElementById('next-btn').addEventListener('click', nextQuestion);
    document.getElementById('skip-btn').addEventListener('click', skipQuestion);

    startSession();
}

function startSession() {
    fetch('/practice/start-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ protocol_slug: practiceState.protocolSlug })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            document.getElementById('question-text').textContent = 'Error: ' + data.error;
            return;
        }
        practiceState.totalQuestions = data.total_questions;
        displayQuestion(data.first_question);
    })
    .catch(function(err) {
        document.getElementById('question-text').textContent = 'Failed to start session: ' + err;
    });
}

function displayQuestion(questionData) {
    practiceState.currentQuestion = questionData;
    practiceState.questionNumber = questionData.question_number;
    practiceState.attemptNumber = 0;
    practiceState.disabledChoices = [];
    practiceState.canReveal = false;

    // Update counter
    updateProgress();

    // Set question text
    document.getElementById('question-text').textContent = questionData.question_text;

    // Multi-answer badge
    var multiBadge = document.getElementById('multi-answer-badge');
    var isMultiAnswer = questionData.multi_answer;
    if (isMultiAnswer) {
        // Count correct answers from the question (we don't know exact count, show generic)
        multiBadge.classList.remove('d-none');
    } else {
        multiBadge.classList.add('d-none');
    }

    // Render answer choices
    var inputType = isMultiAnswer ? 'checkbox' : 'radio';
    var choicesHtml = Object.entries(questionData.choices)
        .sort(function(a, b) { return a[0].localeCompare(b[0]); })
        .map(function(entry) {
            var letter = entry[0];
            var text = entry[1];
            return '<div class="form-check mb-2 p-2 rounded" id="choice-wrapper-' + letter + '">' +
                '<input class="form-check-input" type="' + inputType + '" ' +
                'name="answer" id="choice-' + letter + '" value="' + letter + '">' +
                '<label class="form-check-label" for="choice-' + letter + '">' +
                '<strong>' + letter.toUpperCase() + '.</strong> ' + escapeHtml(text) +
                '</label></div>';
        }).join('');

    document.getElementById('answer-choices').innerHTML = choicesHtml;

    // Add change listeners to enable submit button
    var inputs = document.querySelectorAll('input[name="answer"]');
    inputs.forEach(function(input) {
        input.addEventListener('change', function() {
            document.getElementById('submit-btn').disabled = false;
        });
    });

    // Reset UI state
    document.getElementById('feedback-section').classList.add('d-none');
    document.getElementById('ai-loading').classList.add('d-none');
    document.getElementById('submit-btn').classList.remove('d-none');
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('skip-btn').classList.remove('d-none');
    document.getElementById('try-again-btn').classList.add('d-none');
    document.getElementById('reveal-btn').classList.add('d-none');
    document.getElementById('next-btn').classList.add('d-none');

    // Enable all choices
    inputs.forEach(function(input) {
        input.disabled = false;
        var wrapper = document.getElementById('choice-wrapper-' + input.value);
        if (wrapper) {
            wrapper.style.opacity = '1';
            wrapper.style.textDecoration = 'none';
        }
    });
}

function submitAnswer() {
    var question = practiceState.currentQuestion;
    var isMultiAnswer = question.multi_answer;

    // Collect selected answers
    var selected;
    if (isMultiAnswer) {
        selected = Array.from(document.querySelectorAll('input[name="answer"]:checked'))
            .map(function(el) { return el.value; })
            .sort()
            .join(',');
    } else {
        var checked = document.querySelector('input[name="answer"]:checked');
        selected = checked ? checked.value : null;
    }

    if (!selected) return;

    // Show loading, hide buttons
    document.getElementById('ai-loading').classList.remove('d-none');
    document.getElementById('submit-btn').classList.add('d-none');
    document.getElementById('skip-btn').classList.add('d-none');
    document.getElementById('try-again-btn').classList.add('d-none');
    document.getElementById('reveal-btn').classList.add('d-none');

    // Disable all inputs during submission
    document.querySelectorAll('input[name="answer"]').forEach(function(input) {
        input.disabled = true;
    });

    fetch('/practice/check-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_id: question.id,
            selected_answer: selected
        })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        document.getElementById('ai-loading').classList.add('d-none');

        if (data.error) {
            showFeedback('danger', 'Error', data.error);
            document.getElementById('skip-btn').classList.remove('d-none');
            return;
        }

        if (data.correct) {
            practiceState.correctCount++;
            showFeedback('success', 'Correct!', data.feedback);

            // Highlight the correct answer
            highlightCorrectAnswer(data.correct_answer);

            // Show next button
            document.getElementById('next-btn').classList.remove('d-none');
        } else {
            practiceState.attemptNumber = data.attempt;
            practiceState.canReveal = data.can_reveal;
            practiceState.disabledChoices = data.disabled_choices || [];

            showFeedback('warning', 'Not quite. Here\'s a hint...', data.feedback);

            // Grey out wrong choices
            applyDisabledChoices(practiceState.disabledChoices);

            // Show try again button
            document.getElementById('try-again-btn').classList.remove('d-none');

            // Show reveal button after 2 wrong attempts
            if (data.can_reveal) {
                document.getElementById('reveal-btn').classList.remove('d-none');
            }
        }

        updateProgress();
    })
    .catch(function(err) {
        document.getElementById('ai-loading').classList.add('d-none');
        showFeedback('danger', 'Error', 'Failed to submit answer: ' + err);
        document.getElementById('skip-btn').classList.remove('d-none');
    });
}

function tryAgain() {
    // Hide feedback
    document.getElementById('feedback-section').classList.add('d-none');
    document.getElementById('try-again-btn').classList.add('d-none');
    document.getElementById('reveal-btn').classList.add('d-none');

    // Show submit and skip
    document.getElementById('submit-btn').classList.remove('d-none');
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('skip-btn').classList.remove('d-none');

    // Re-enable non-disabled choices
    document.querySelectorAll('input[name="answer"]').forEach(function(input) {
        if (practiceState.disabledChoices.indexOf(input.value) === -1) {
            input.disabled = false;
        }
        input.checked = false;
    });
}

function revealAnswer() {
    document.getElementById('ai-loading').classList.remove('d-none');
    document.getElementById('try-again-btn').classList.add('d-none');
    document.getElementById('reveal-btn').classList.add('d-none');

    fetch('/practice/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_id: practiceState.currentQuestion.id
        })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        document.getElementById('ai-loading').classList.add('d-none');

        if (data.error) {
            showFeedback('danger', 'Error', data.error);
            return;
        }

        practiceState.incorrectCount++;

        // Highlight correct answer
        highlightCorrectAnswer(data.correct_answer);

        var content = '<p class="fw-bold mb-2">The correct answer is: ' +
            escapeHtml(data.correct_answer_text) + '</p>' + formatAIResponse(data.feedback);
        showFeedback('info', 'Answer Revealed', content);

        document.getElementById('next-btn').classList.remove('d-none');
        updateProgress();
    })
    .catch(function(err) {
        document.getElementById('ai-loading').classList.add('d-none');
        showFeedback('danger', 'Error', 'Failed to reveal answer: ' + err);
    });
}

function skipQuestion() {
    fetch('/practice/skip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question_id: practiceState.currentQuestion.id
        })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            showFeedback('danger', 'Error', data.error);
            return;
        }

        practiceState.skippedCount++;

        if (data.done || !data.next_question) {
            navigateToSummary();
        } else {
            practiceState.totalQuestions = data.total_questions;
            displayQuestion(data.next_question);
        }
    })
    .catch(function(err) {
        showFeedback('danger', 'Error', 'Failed to skip: ' + err);
    });
}

function nextQuestion() {
    fetch('/practice/next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            showFeedback('danger', 'Error', data.error);
            return;
        }

        if (data.done || !data.question) {
            navigateToSummary();
        } else {
            displayQuestion(data.question);
        }
    })
    .catch(function(err) {
        showFeedback('danger', 'Error', 'Failed to get next question: ' + err);
    });
}

// ==================== UI Helpers ====================

function updateProgress() {
    var qNum = practiceState.questionNumber;
    var total = practiceState.totalQuestions;
    var pct = total > 0 ? Math.round((qNum / total) * 100) : 0;

    document.getElementById('question-counter').textContent =
        'Question ' + qNum + ' of ' + total;
    document.getElementById('progress-bar').style.width = pct + '%';
    document.getElementById('correct-count').textContent =
        'Correct: ' + practiceState.correctCount;
    document.getElementById('incorrect-count').textContent =
        'Incorrect: ' + practiceState.incorrectCount;
}

function showFeedback(type, title, content) {
    var section = document.getElementById('feedback-section');
    var status = document.getElementById('feedback-status');
    var contentDiv = document.getElementById('feedback-content');

    section.classList.remove('d-none');

    status.className = 'alert alert-' + type + ' mb-3';
    status.innerHTML = '<strong>' + title + '</strong>';

    contentDiv.innerHTML = formatAIResponse(content);

    // Scroll feedback into view
    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function applyDisabledChoices(disabledLetters) {
    disabledLetters.forEach(function(letter) {
        var input = document.getElementById('choice-' + letter);
        if (input) {
            input.disabled = true;
            input.checked = false;
            var wrapper = document.getElementById('choice-wrapper-' + letter);
            if (wrapper) {
                wrapper.style.opacity = '0.4';
                wrapper.style.textDecoration = 'line-through';
            }
        }
    });
}

function highlightCorrectAnswer(correctAnswer) {
    var letters = correctAnswer.split(',');
    letters.forEach(function(letter) {
        letter = letter.trim().toLowerCase();
        var wrapper = document.getElementById('choice-wrapper-' + letter);
        if (wrapper) {
            wrapper.style.backgroundColor = 'rgba(40, 167, 69, 0.15)';
            wrapper.style.borderLeft = '3px solid #28a745';
            wrapper.style.opacity = '1';
            wrapper.style.textDecoration = 'none';
        }
    });
}

function navigateToSummary() {
    window.location.href = '/practice/' + practiceState.protocolSlug + '/summary';
}

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatAIResponse(text) {
    if (!text) return '';
    // Escape HTML first
    var escaped = escapeHtml(text);
    // Convert **bold** to <strong>
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Convert newlines to <br>
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
}

// ==================== Summary Page ====================

function initSummaryPage() {
    fetch('/practice/summary')
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            document.getElementById('total-answered').textContent = 'Error';
            return;
        }
        populateSummary(data);
    })
    .catch(function(err) {
        document.getElementById('total-answered').textContent = 'Error';
    });
}

function populateSummary(data) {
    document.getElementById('total-answered').textContent = data.answered;
    document.getElementById('correct-pct').textContent = data.percentage + '%';
    document.getElementById('total-correct').textContent = data.correct;
    document.getElementById('total-incorrect').textContent = data.incorrect;

    // Skipped section
    if (data.skipped > 0) {
        document.getElementById('skipped-section').classList.remove('d-none');
        document.getElementById('skipped-count').textContent = data.skipped;
    }

    // Missed questions
    if (data.missed_questions && data.missed_questions.length > 0) {
        var missedSection = document.getElementById('missed-section');
        missedSection.classList.remove('d-none');

        var missedList = document.getElementById('missed-list');
        missedList.innerHTML = data.missed_questions.map(function(q) {
            return '<div class="list-group-item d-flex justify-content-between align-items-start">' +
                '<div class="me-auto">' +
                '<span class="text-muted small">' + escapeHtml(q.question_id) + '</span><br>' +
                escapeHtml(q.question_text) +
                '</div>' +
                '<span class="badge bg-danger rounded-pill">' + q.attempts + ' attempts</span>' +
                '</div>';
        }).join('');
    }
}
