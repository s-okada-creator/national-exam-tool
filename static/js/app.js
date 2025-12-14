/**
 * 国家試験対策ツール - メインアプリケーションロジック
 */

// セッション管理
let currentSession = null;
let currentQuestions = [];
let currentQuestionIndex = 0;
let answers = [];
let mode = 'test';
let questionStartTime = null;

/**
 * セッションを初期化
 */
async function initSession(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        const data = await response.json();
        
        currentSession = sessionId;
        currentQuestions = data.questions || [];
        answers = data.answers || [];
        mode = data.mode || 'test';
        
        // URLパラメータから開始位置を取得
        const urlParams = new URLSearchParams(window.location.search);
        const startIndex = parseInt(urlParams.get('index')) || 0;
        currentQuestionIndex = Math.max(0, Math.min(startIndex, currentQuestions.length - 1));
        
        return true;
    } catch (error) {
        console.error('Error initializing session:', error);
        return false;
    }
}

/**
 * 現在の問題を取得
 */
function getCurrentQuestion() {
    if (currentQuestions.length === 0 || currentQuestionIndex >= currentQuestions.length) {
        return null;
    }
    return currentQuestions[currentQuestionIndex];
}

/**
 * 問題を表示
 */
function displayQuestion(question) {
    if (!question) return;
    
    questionStartTime = Date.now();
    
    const questionContainer = document.querySelector('.question-container');
    if (!questionContainer) return;
    
    // 問題文を取得（問題文が空の場合はテーマを使用）
    // 複数行の問題文にも対応（改行を保持）
    let questionText = (question.question_text && question.question_text.trim()) 
        ? question.question_text 
        : (question.theme || `問題 ${question.question_number}`);
    
    // 改行を<br>に変換して表示
    questionText = questionText.replace(/\n/g, '<br>');
    
    questionContainer.innerHTML = `
        <div class="question-header">
            <div>
                <span class="question-number">第${question.exam_number}回 問${question.question_number}</span>
                <span class="question-category" style="margin-left: 10px;">${question.category}</span>
            </div>
            <div>
                <span class="timer" id="timer">00:00</span>
            </div>
        </div>
        
        <div class="question-text">${questionText}</div>
        ${question.theme && question.theme !== question.question_text ? `<div class="question-theme" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-left: 3px solid #667eea; border-radius: 4px; font-size: 0.95rem; color: #666;">
            <strong>テーマ・キーワード:</strong> ${escapeHtml(question.theme)}
        </div>` : ''}
        
        <div class="choices" id="choices-container">
            ${renderChoices(question)}
        </div>
        
        ${mode === 'practice' ? renderPracticeModeButtons(question) : ''}
    `;
    
    // タイマー開始
    if (mode === 'test') {
        startTimer();
    }
    
    // 選択肢のイベントリスナーを追加
    attachChoiceListeners(question);
    
    // 既に解答済みの場合は選択状態を復元
    const existingAnswer = answers.find(a => a.question_id === question.id);
    if (existingAnswer && existingAnswer.answer !== null) {
        restoreAnswer(existingAnswer.answer);
    }
}

/**
 * 選択肢をレンダリング
 */
function renderChoices(question) {
    const choices = question.choices || {};
    const choiceKeys = ['1', '2', '3', '4'];
    
    // 選択肢のテキストがすべて空の場合は、テーマ・キーワードを問題文として扱う
    const hasChoices = choiceKeys.some(key => choices[key] && choices[key].trim() !== '');
    
    if (!hasChoices) {
        return `
            <div style="padding: 20px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 6px;">
                <p><strong>注意:</strong> 選択肢のデータが現在ありません。</p>
                <p>正答番号: ${(question.correct_answer || []).join(', ')}</p>
                <p>テーマ: ${escapeHtml(question.theme || '')}</p>
            </div>
        `;
    }
    
    return choiceKeys.map(key => {
        const choiceText = choices[key] || `選択肢${key}（データなし）`;
        return `
            <div class="choice-item" data-choice="${key}">
                <span class="choice-label">${key}.</span>
                <span class="choice-text">${escapeHtml(choiceText)}</span>
            </div>
        `;
    }).join('');
}

/**
 * 学習モード用のボタンをレンダリング
 */
function renderPracticeModeButtons(question) {
    const existingAnswer = answers.find(a => a.question_id === question.id);
    const hasAnswered = existingAnswer && existingAnswer.answer !== null;
    
    if (!hasAnswered) {
        return '';
    }
    
    const correctAnswer = question.correct_answer || [];
    const userAnswer = existingAnswer.answer;
    const isCorrect = Array.isArray(userAnswer) 
        ? JSON.stringify(userAnswer.sort()) === JSON.stringify(correctAnswer.sort())
        : correctAnswer.includes(userAnswer);
    
    let explanationHtml = '';
    if (question.explanation) {
        explanationHtml = `
            <div class="explanation">
                <h3>解説</h3>
                <p>${escapeHtml(question.explanation)}</p>
            </div>
        `;
    }
    
    if (question.hint) {
        explanationHtml += `
            <div class="hint">
                <strong>ヒント:</strong> ${escapeHtml(question.hint)}
            </div>
        `;
    }
    
    return `
        <div style="margin-top: 20px;">
            <div style="padding: 15px; background: ${isCorrect ? '#d4edda' : '#f8d7da'}; border-radius: 8px; margin-bottom: 15px;">
                <strong>${isCorrect ? '✅ 正解です！' : '❌ 不正解です'}</strong>
                <div style="margin-top: 10px;">
                    正解: ${correctAnswer.join(', ')}
                </div>
            </div>
            ${explanationHtml}
        </div>
    `;
}

/**
 * 選択肢のイベントリスナーを追加
 */
function attachChoiceListeners(question) {
    const choiceItems = document.querySelectorAll('.choice-item');
    const existingAnswer = answers.find(a => a.question_id === question.id);
    
    if (existingAnswer && existingAnswer.answer !== null && mode === 'practice') {
        // 学習モードで既に解答済みの場合は、正誤表示
        const correctAnswer = question.correct_answer || [];
        const userAnswer = existingAnswer.answer;
        const userAnswers = Array.isArray(userAnswer) ? userAnswer : [userAnswer];
        
        choiceItems.forEach(item => {
            const choice = parseInt(item.dataset.choice);
            if (correctAnswer.includes(choice)) {
                item.classList.add('correct');
            }
            if (userAnswers.includes(choice) && !correctAnswer.includes(choice)) {
                item.classList.add('incorrect');
            }
            if (userAnswers.includes(choice)) {
                item.classList.add('selected');
            }
        });
        return;
    }
    
    choiceItems.forEach(item => {
        item.addEventListener('click', function() {
            // 既に解答済みの場合は無視
            if (existingAnswer && existingAnswer.answer !== null && mode === 'test') {
                return;
            }
            
            // 選択状態を切り替え（複数選択対応）
            if (mode === 'practice' || !existingAnswer || existingAnswer.answer === null) {
                this.classList.toggle('selected');
            }
            
            // 解答を送信
            const selectedChoices = Array.from(document.querySelectorAll('.choice-item.selected'))
                .map(el => parseInt(el.dataset.choice));
            
            submitAnswer(question.id, selectedChoices.length > 0 ? selectedChoices : null);
        });
    });
}

/**
 * 解答を復元
 */
function restoreAnswer(answer) {
    const answerArray = Array.isArray(answer) ? answer : [answer];
    answerArray.forEach(ans => {
        const item = document.querySelector(`.choice-item[data-choice="${ans}"]`);
        if (item) {
            item.classList.add('selected');
        }
    });
}

/**
 * 解答を送信
 */
async function submitAnswer(questionId, answer) {
    const timeSpent = questionStartTime ? (Date.now() - questionStartTime) / 1000 : 0;
    
    try {
        await fetch(`/api/sessions/${currentSession}/answers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question_id: questionId,
                answer: answer,
                time_spent: timeSpent
            })
        });
        
        // ローカルのanswers配列も更新
        const existingIndex = answers.findIndex(a => a.question_id === questionId);
        const answerData = {
            question_id: questionId,
            answer: answer,
            time_spent: timeSpent
        };
        
        if (existingIndex >= 0) {
            answers[existingIndex] = answerData;
        } else {
            answers.push(answerData);
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
    }
}

/**
 * 次の問題へ
 */
function nextQuestion() {
    if (currentQuestionIndex < currentQuestions.length - 1) {
        currentQuestionIndex++;
        const question = getCurrentQuestion();
        if (question) {
            displayQuestion(question);
            updateNavigation();
        }
    }
}

/**
 * 前の問題へ
 */
function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        const question = getCurrentQuestion();
        if (question) {
            displayQuestion(question);
            updateNavigation();
        }
    }
}

/**
 * ナビゲーションを更新
 */
function updateNavigation() {
    const currentQuestion = getCurrentQuestion();
    if (!currentQuestion) return;
    
    // プログレスバー
    const progress = ((currentQuestionIndex + 1) / currentQuestions.length) * 100;
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
    }
    
    // 問題番号表示
    const questionNumberEl = document.querySelector('.question-counter');
    if (questionNumberEl) {
        questionNumberEl.textContent = `${currentQuestionIndex + 1} / ${currentQuestions.length}`;
    }
    
    // ボタンの有効/無効
    const prevBtn = document.querySelector('#prev-btn');
    const nextBtn = document.querySelector('#next-btn');
    const finishBtn = document.querySelector('#finish-btn');
    
    if (prevBtn) {
        prevBtn.disabled = currentQuestionIndex === 0;
    }
    
    if (nextBtn) {
        nextBtn.disabled = currentQuestionIndex >= currentQuestions.length - 1;
    }
    
    // 問題リストの更新
    updateQuestionList();
}

/**
 * 問題リストを更新（現在は使用していないが、将来の拡張のために残す）
 */
function updateQuestionList() {
    const listContainer = document.querySelector('.question-list');
    if (!listContainer) return;  // 問題リストが存在しない場合は何もしない
    
    // 問題リストのHTMLを削除したため、この関数は何もしない
    // 将来的に問題リストが必要になった場合に備えて関数は残しておく
}

/**
 * タイマーを開始
 */
function startTimer() {
    let startTime = Date.now();
    
    function updateTimer() {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const timerEl = document.getElementById('timer');
        if (timerEl) {
            timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }
    }
    
    setInterval(updateTimer, 1000);
    updateTimer();
}

/**
 * HTMLエスケープ
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

