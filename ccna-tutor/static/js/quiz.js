// Quiz JavaScript - Manages concept-group-based quiz flow

let quizState = {
    sessionId: null,
    protocol: null,
    conceptGroups: [],
    currentIndex: 0,
    attemptNumber: 1,
    scores: {},
    totalConcepts: 0,
    dragDropWindow: null,
    dragDropQuestions: []
};

// DOM elements - will be initialized after DOM is loaded
let quizSetup, quizInterface, quizSummary, protocolSelect, startQuizBtn;
let conceptIndicator, scoreTracker, progressBar, questionText, answerChoices;
let feedbackSection, feedbackStatus, feedbackContent, multiProtocolBadges;
let submitBtn, tryAgainBtn, moreConceptBtn, nextTopicBtn, restartQuizBtn;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    quizSetup = document.getElementById('quiz-setup');
    quizInterface = document.getElementById('quiz-interface');
    quizSummary = document.getElementById('quiz-summary');
    protocolSelect = document.getElementById('protocol-select');
    startQuizBtn = document.getElementById('start-quiz-btn');
    conceptIndicator = document.getElementById('concept-indicator');
    scoreTracker = document.getElementById('score-tracker');
    progressBar = document.getElementById('progress-bar');
    questionText = document.getElementById('question-text');
    answerChoices = document.getElementById('answer-choices');
    feedbackSection = document.getElementById('feedback-section');
    feedbackStatus = document.getElementById('feedback-status');
    feedbackContent = document.getElementById('feedback-content');
    multiProtocolBadges = document.getElementById('multi-protocol-badges');
    submitBtn = document.getElementById('submit-btn');
    tryAgainBtn = document.getElementById('try-again-btn');
    moreConceptBtn = document.getElementById('more-concept-btn');
    nextTopicBtn = document.getElementById('next-topic-btn');
    restartQuizBtn = document.getElementById('restart-quiz-btn');

    // Only set up event listeners if we're on the quiz page
    if (startQuizBtn) {
        startQuizBtn.addEventListener('click', startQuiz);
    }
    if (submitBtn) {
        submitBtn.addEventListener('click', submitAnswer);
    }
    if (tryAgainBtn) {
        tryAgainBtn.addEventListener('click', tryAgain);
    }
    if (moreConceptBtn) {
        moreConceptBtn.addEventListener('click', loadMoreFromConcept);
    }
    if (nextTopicBtn) {
        nextTopicBtn.addEventListener('click', nextTopic);
    }
    if (restartQuizBtn) {
        restartQuizBtn.addEventListener('click', restartQuiz);
    }

    // Listen for messages from drag-drop popup
    window.addEventListener('message', handleDragDropMessage);

    // Load drag-drop questions
    loadDragDropQuestions();
});

function loadDragDropQuestions() {
    fetch('/api/drag-drop-questions')
        .then(response => response.json())
        .then(data => {
            if (data.questions) {
                quizState.dragDropQuestions = data.questions;
                console.log('Loaded ' + data.questions.length + ' drag-drop questions');
            }
        })
        .catch(error => {
            console.log('Drag-drop questions not available:', error);
        });
}

function startQuiz() {
    const protocol = protocolSelect.value;
    if (!protocol) {
        alert('Please select a protocol');
        return;
    }
    fetch('/api/quiz/start/' + protocol)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }
            quizState.sessionId = data.session_id;
            quizState.protocol = data.protocol;
            quizState.conceptGroups = data.concept_groups;
            quizState.currentIndex = 0;
            quizState.totalConcepts = data.total_concepts;
            quizState.attemptNumber = 1;
            quizState.scores = {};
            quizSetup.classList.add('d-none');
            quizInterface.classList.remove('d-none');
            displayCurrentQuestion();
            updateProgress();
        })
        .catch(error => {
            alert('Error starting quiz: ' + error);
        });
}

function displayCurrentQuestion() {
    const currentGroup = quizState.conceptGroups[quizState.currentIndex];
    if (!currentGroup) {
        showSummary();
        return;
    }
    const question = currentGroup.question;

    // Check if this is a drag-drop question
    if (question.type === 'drag_drop' || question.question_type === 'drag_drop') {
        displayDragDropQuestion(question, currentGroup);
        return;
    }

    conceptIndicator.textContent = 'Concept ' + (quizState.currentIndex + 1) + ' of ' + quizState.totalConcepts;

    // Detect multi-answer questions
    const isMultiAnswer = question.multi_answer || (question.correct_answer && question.correct_answer.includes(','));
    const numCorrect = isMultiAnswer ? question.correct_answer.split(',').length : 1;
    const inputType = isMultiAnswer ? 'checkbox' : 'radio';

    let displayText = question.question_text;
    if (isMultiAnswer && !displayText.toLowerCase().includes('choose')) {
        displayText += ' (Choose ' + numCorrect + ')';
    }
    questionText.textContent = displayText;

    if (question.multi_protocol && question.protocol_tags) {
        multiProtocolBadges.innerHTML = question.protocol_tags.map(tag =>
            '<span class="badge bg-info me-1">' + tag + '</span>'
        ).join('');
    } else {
        multiProtocolBadges.innerHTML = '';
    }
    if (isMultiAnswer) {
        multiProtocolBadges.innerHTML += '<span class="badge bg-warning text-dark me-1">Select ' + numCorrect + '</span>';
    }
    const choicesHtml = Object.entries(question.choices)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([letter, text]) =>
            '<div class="form-check mb-2">' +
            '<input class="form-check-input" type="' + inputType + '" name="answer" id="choice-' + letter + '" value="' + letter + '">' +
            '<label class="form-check-label" for="choice-' + letter + '">' +
            '<strong>' + letter.toUpperCase() + '.</strong> ' + text +
            '</label></div>'
        ).join('');
    answerChoices.innerHTML = choicesHtml;
    feedbackSection.classList.add('d-none');
    submitBtn.classList.remove('d-none');
    tryAgainBtn.classList.add('d-none');
    moreConceptBtn.classList.add('d-none');
    nextTopicBtn.classList.add('d-none');
    quizState.attemptNumber = 1;
}

function displayDragDropQuestion(question, currentGroup) {
    conceptIndicator.textContent = 'Concept ' + (quizState.currentIndex + 1) + ' of ' + quizState.totalConcepts + ' (Interactive)';

    // Show message about drag-drop
    questionText.innerHTML = '<div class="alert alert-info">' +
        '<h5><i class="bi bi-arrows-move"></i> Interactive Drag & Drop Question</h5>' +
        '<p>' + question.question + '</p>' +
        '<p class="mb-0"><strong>Topic:</strong> ' + question.topic + '</p>' +
        '</div>';

    multiProtocolBadges.innerHTML = '<span class="badge bg-warning text-dark">Drag & Drop</span>';

    // Show button to open drag-drop popup
    answerChoices.innerHTML = '<div class="text-center py-4">' +
        '<button class="btn btn-primary btn-lg" onclick="openDragDropPopup(' + question.id + ')">' +
        '<i class="bi bi-box-arrow-up-right"></i> Open Interactive Question' +
        '</button>' +
        '<p class="text-muted mt-3">A new window will open with the drag-and-drop interface.</p>' +
        '<p class="text-muted">The window will close automatically when you complete the question.</p>' +
        '</div>';

    feedbackSection.classList.add('d-none');
    submitBtn.classList.add('d-none');
    tryAgainBtn.classList.add('d-none');
    moreConceptBtn.classList.add('d-none');
    nextTopicBtn.classList.remove('d-none');
    nextTopicBtn.textContent = 'Skip to Next Topic';
}

function openDragDropPopup(questionId) {
    const width = 900;
    const height = 700;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;

    const origin = window.location.origin;
    const url = '/drag-drop?q=' + questionId + '&popup=true&origin=' + encodeURIComponent(origin);

    // Close existing popup if open
    if (quizState.dragDropWindow && !quizState.dragDropWindow.closed) {
        quizState.dragDropWindow.close();
    }

    quizState.dragDropWindow = window.open(
        url,
        'DragDropQuestion',
        'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top + ',scrollbars=yes,resizable=yes'
    );

    // Update UI to show waiting state
    answerChoices.innerHTML = '<div class="text-center py-4">' +
        '<div class="spinner-border text-primary mb-3" role="status">' +
        '<span class="visually-hidden">Loading...</span>' +
        '</div>' +
        '<p class="text-muted">Waiting for you to complete the interactive question...</p>' +
        '<button class="btn btn-outline-secondary mt-2" onclick="openDragDropPopup(' + questionId + ')">' +
        'Reopen Window' +
        '</button>' +
        '</div>';

    // Focus the popup
    if (quizState.dragDropWindow) {
        quizState.dragDropWindow.focus();
    }
}

function handleDragDropMessage(event) {
    // Verify origin if needed
    const data = event.data;

    if (data && data.type === 'dragDropComplete') {
        console.log('Drag-drop completed:', data);

        const currentGroup = quizState.conceptGroups[quizState.currentIndex];
        if (!currentGroup) return;

        if (data.correct) {
            // Mark as correct
            quizState.scores[currentGroup.group_id] = {
                firstAttemptCorrect: quizState.attemptNumber === 1,
                attempts: quizState.attemptNumber,
                concept: currentGroup.concept
            };

            // Show success feedback
            feedbackSection.classList.remove('d-none');
            feedbackStatus.className = 'alert alert-success mb-3';
            feedbackStatus.innerHTML = '<strong>Correct!</strong> You completed the drag-and-drop question successfully.';
            feedbackContent.innerHTML = '<div class="alert alert-info">Great job! Ready to move to the next topic?</div>';

            answerChoices.innerHTML = '<div class="alert alert-success text-center">' +
                '<i class="bi bi-check-circle-fill" style="font-size: 3rem;"></i>' +
                '<p class="mt-2 mb-0">Question completed successfully!</p>' +
                '</div>';

            submitBtn.classList.add('d-none');
            tryAgainBtn.classList.add('d-none');
            moreConceptBtn.classList.add('d-none');
            nextTopicBtn.classList.remove('d-none');
            nextTopicBtn.textContent = 'Next Topic';
        } else {
            // Show feedback for skipped/incorrect
            feedbackSection.classList.remove('d-none');
            feedbackStatus.className = 'alert alert-warning mb-3';
            feedbackStatus.innerHTML = '<strong>Question Closed</strong>';
            feedbackContent.innerHTML = '<div class="mb-3">You can try the question again or move to the next topic.</div>';

            answerChoices.innerHTML = '<div class="text-center py-4">' +
                '<button class="btn btn-primary btn-lg me-2" onclick="openDragDropPopup(' + data.questionId + ')">' +
                '<i class="bi bi-arrow-repeat"></i> Try Again' +
                '</button>' +
                '</div>';

            quizState.attemptNumber++;
            nextTopicBtn.classList.remove('d-none');
            nextTopicBtn.textContent = 'Skip to Next Topic';
        }

        updateProgress();
    }
}

function submitAnswer() {
    const selectedAnswers = document.querySelectorAll('input[name="answer"]:checked');
    if (selectedAnswers.length === 0) {
        alert('Please select an answer');
        return;
    }
    const currentGroup = quizState.conceptGroups[quizState.currentIndex];
    const question = currentGroup.question;
    const isMultiAnswer = question.multi_answer || (question.correct_answer && question.correct_answer.includes(','));
    const numCorrect = isMultiAnswer ? question.correct_answer.split(',').length : 1;

    if (isMultiAnswer && selectedAnswers.length !== numCorrect) {
        alert('Please select exactly ' + numCorrect + ' answers');
        return;
    }

    const answerValue = Array.from(selectedAnswers).map(el => el.value).sort().join(',');

    document.querySelectorAll('input[name="answer"]').forEach(input => {
        input.disabled = true;
    });
    fetch('/api/quiz/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: quizState.sessionId,
            question_id: question.id,
            student_answer: answerValue,
            attempt_number: quizState.attemptNumber,
            group_id: currentGroup.group_id
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }
            feedbackSection.classList.remove('d-none');
            if (data.correct) {
                feedbackStatus.className = 'alert alert-success mb-3';
                feedbackStatus.innerHTML = '<strong>Correct!</strong>';
                feedbackContent.innerHTML = '<div class="mb-3">' + data.explanation + '</div>';
                if (!quizState.scores[currentGroup.group_id]) {
                    quizState.scores[currentGroup.group_id] = {
                        firstAttemptCorrect: quizState.attemptNumber === 1,
                        attempts: quizState.attemptNumber,
                        concept: currentGroup.concept
                    };
                }
                submitBtn.classList.add('d-none');
                if (data.more_in_group > 0) {
                    feedbackContent.innerHTML += '<div class="alert alert-info">This concept has <strong>' +
                        data.more_in_group + '</strong> more exam question(s) with different wording. ' +
                        'Want to try another question on the same concept, or move to a different topic?</div>';
                    moreConceptBtn.classList.remove('d-none');
                } else {
                    feedbackContent.innerHTML += '<div class="alert alert-success">You have covered all variations of this concept!</div>';
                }
                nextTopicBtn.classList.remove('d-none');
                nextTopicBtn.textContent = 'Next Topic';
            } else {
                feedbackStatus.className = 'alert alert-danger mb-3';
                feedbackStatus.innerHTML = '<strong>Incorrect</strong>';
                feedbackContent.innerHTML = '<div class="mb-3">' + data.hint + '</div>';
                quizState.attemptNumber = data.attempt + 1;
                submitBtn.classList.add('d-none');
                tryAgainBtn.classList.remove('d-none');
            }
            updateProgress();
        })
        .catch(error => {
            alert('Error submitting answer: ' + error);
        });
}

function tryAgain() {
    document.querySelectorAll('input[name="answer"]').forEach(input => {
        input.disabled = false;
        input.checked = false;
    });
    feedbackSection.classList.add('d-none');
    tryAgainBtn.classList.add('d-none');
    submitBtn.classList.remove('d-none');
}

function loadMoreFromConcept() {
    const currentGroup = quizState.conceptGroups[quizState.currentIndex];
    const seenQuestions = currentGroup.seen_questions || [];
    fetch('/api/quiz/group-question/' + currentGroup.group_id + '?session_id=' + quizState.sessionId + '&exclude=' + seenQuestions.join(','))
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                if (data.all_covered) {
                    alert('You have answered all questions in this concept group!');
                    nextTopic();
                } else {
                    alert('Error: ' + data.error);
                }
                return;
            }
            currentGroup.question = data.question;
            currentGroup.seen_questions = seenQuestions;
            currentGroup.seen_questions.push(data.question.id);
            document.querySelectorAll('input[name="answer"]').forEach(input => {
                input.disabled = false;
            });
            displayCurrentQuestion();
        })
        .catch(error => {
            alert('Error loading question: ' + error);
        });
}

function nextTopic() {
    // Close drag-drop popup if open
    if (quizState.dragDropWindow && !quizState.dragDropWindow.closed) {
        quizState.dragDropWindow.close();
    }

    quizState.currentIndex++;
    document.querySelectorAll('input[name="answer"]').forEach(input => {
        input.disabled = false;
    });
    if (quizState.currentIndex >= quizState.conceptGroups.length) {
        showSummary();
    } else {
        displayCurrentQuestion();
        updateProgress();
    }
}

function updateProgress() {
    const progress = ((quizState.currentIndex + 1) / quizState.totalConcepts) * 100;
    progressBar.style.width = progress + '%';
    progressBar.textContent = Math.round(progress) + '%';
    progressBar.setAttribute('aria-valuenow', progress);
    const firstAttemptCorrect = Object.values(quizState.scores).filter(s => s.firstAttemptCorrect).length;
    const totalAnswered = Object.keys(quizState.scores).length;
    scoreTracker.textContent = 'First-Attempt Correct: ' + firstAttemptCorrect + ' / ' + totalAnswered;
}

function showSummary() {
    // Close drag-drop popup if open
    if (quizState.dragDropWindow && !quizState.dragDropWindow.closed) {
        quizState.dragDropWindow.close();
    }

    quizInterface.classList.add('d-none');
    quizSummary.classList.remove('d-none');
    const totalConcepts = Object.keys(quizState.scores).length;
    const firstAttemptCorrect = Object.values(quizState.scores).filter(s => s.firstAttemptCorrect).length;
    const percentage = totalConcepts > 0 ? Math.round((firstAttemptCorrect / totalConcepts) * 100) : 0;
    document.getElementById('final-score').textContent = percentage + '%';
    document.getElementById('concepts-covered').textContent = totalConcepts + ' / ' + quizState.totalConcepts;
    const strongAreas = [];
    const weakAreas = [];
    for (const [groupId, score] of Object.entries(quizState.scores)) {
        if (score.firstAttemptCorrect) {
            strongAreas.push(score.concept);
        } else {
            weakAreas.push({ concept: score.concept, attempts: score.attempts });
        }
    }
    const strongList = document.getElementById('strong-list');
    if (strongAreas.length > 0) {
        strongList.innerHTML = strongAreas.map(concept =>
            '<li class="list-group-item">' + concept + '</li>'
        ).join('');
    } else {
        strongList.innerHTML = '<li class="list-group-item">None</li>';
    }
    const weakList = document.getElementById('weak-list');
    if (weakAreas.length > 0) {
        weakList.innerHTML = weakAreas.map(item =>
            '<li class="list-group-item">' + item.concept + ' <span class="badge bg-warning">' + item.attempts + ' attempts</span></li>'
        ).join('');
    } else {
        weakList.innerHTML = '<li class="list-group-item text-success">None - Great job!</li>';
    }
}

function restartQuiz() {
    // Close drag-drop popup if open
    if (quizState.dragDropWindow && !quizState.dragDropWindow.closed) {
        quizState.dragDropWindow.close();
    }

    quizState = {
        sessionId: null,
        protocol: null,
        conceptGroups: [],
        currentIndex: 0,
        attemptNumber: 1,
        scores: {},
        totalConcepts: 0,
        dragDropWindow: null,
        dragDropQuestions: quizState.dragDropQuestions // Preserve loaded questions
    };
    quizSummary.classList.add('d-none');
    quizSetup.classList.remove('d-none');
}
