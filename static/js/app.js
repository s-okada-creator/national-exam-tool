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
// 制限時間関連の変数（テストモードのみ）
let timeLimit = null; // 制限時間（秒）
let timeLimitTimer = null; // 制限時間タイマー
let testStartTime = null; // テスト開始時刻
let timerStarted = false; // タイマーが開始されたかどうかのフラグ
// タイマー更新用のキャッシュ変数（グローバルスコープ）
let timerLastRemaining = -1;
let timerLastColor = '';

/**
 * セッションを初期化（最適化版：段階的な処理）
 */
async function initSession(sessionId) {
    try {
        console.log('initSession開始:', sessionId);
        
        // ローディング表示を即座に表示（既に表示されている場合はそのまま）
        const loadingEl = document.getElementById('loading');
        if (loadingEl) {
            loadingEl.style.display = 'block';
        }
        
        // セッションデータを取得
        console.log('セッションデータ取得開始:', `/api/sessions/${sessionId}`);
        const response = await fetch(`/api/sessions/${sessionId}`);
        console.log('レスポンスステータス:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('HTTPエラー:', response.status, errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('セッションデータ取得完了:', {
            questions: data.questions ? data.questions.length : 0,
            mode: data.mode,
            answers: data.answers ? data.answers.length : 0
        });
        
        // データを一度に処理（パフォーマンス向上）
        currentSession = sessionId;
        currentQuestions = data.questions || [];
        answers = data.answers || [];
        mode = data.mode || 'test';
        
        if (!currentQuestions || currentQuestions.length === 0) {
            console.error('問題データが空です');
            throw new Error('問題データが空です');
        }
        
        // テストモードの場合、制限時間を計算（1問あたり70秒）
        if (mode === 'test' && currentQuestions.length > 0) {
            timeLimit = currentQuestions.length * 70; // 総問題数 × 70秒
            testStartTime = Date.now();
            timerStarted = false; // タイマーフラグをリセット
            // タイマーキャッシュをリセット
            timerLastRemaining = -1;
            timerLastColor = '';
            console.log('タイマー設定:', { timeLimit, testStartTime });
        }
        
        // URLパラメータから開始位置を取得（最適化：一度だけ取得）
        const urlParams = new URLSearchParams(window.location.search);
        const startIndex = parseInt(urlParams.get('index')) || 0;
        currentQuestionIndex = Math.max(0, Math.min(startIndex, currentQuestions.length - 1));
        
        console.log('initSession完了:', {
            currentQuestionIndex,
            totalQuestions: currentQuestions.length
        });
        
        return true;
    } catch (error) {
        console.error('Error initializing session:', error);
        console.error('Error stack:', error.stack);
        return false;
    }
}

/**
 * 現在の問題を取得
 */
function getCurrentQuestion() {
    console.log('getCurrentQuestion呼び出し:', {
        currentQuestionsLength: currentQuestions.length,
        currentQuestionIndex: currentQuestionIndex
    });
    
    if (currentQuestions.length === 0) {
        console.error('問題リストが空です');
        return null;
    }
    
    if (currentQuestionIndex >= currentQuestions.length) {
        console.error('問題インデックスが範囲外です:', currentQuestionIndex, '>=', currentQuestions.length);
        return null;
    }
    
    const question = currentQuestions[currentQuestionIndex];
    console.log('現在の問題:', question ? question.id : 'null');
    return question;
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
    
    // テーマ・キーワードの表示（学習モードのみ）
    let themeHtml = '';
    if (mode === 'practice' && (question.theme || question.hint) && question.theme !== question.question_text) {
        // 学習モードのみテーマ・キーワードを表示
        // ヒントがあればヒントを表示、なければテーマから括弧内の答えを除去
        let displayText = '';
        if (question.hint && question.hint.trim()) {
            displayText = question.hint;
        } else if (question.theme) {
            // テーマから括弧内の答えを除去（学習モードでは答えを表示しない）
            // 全角括弧と半角括弧の両方に対応
            displayText = question.theme
                .replace(/[（(][^）)]*[）)]/g, '')  // 全角括弧と半角括弧の両方を除去
                .trim();
            // 末尾の空白や不要な文字を削除
            displayText = displayText.replace(/\s+$/, '');
        }
        if (displayText) {
            themeHtml = `<div class="question-theme" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-left: 3px solid #667eea; border-radius: 4px; font-size: 0.95rem; color: #666;">
                <strong>テーマ・キーワード:</strong> ${escapeHtml(displayText)}
            </div>`;
        }
    }
    
    // 学習モードのボタン
    let practiceButtonsHtml = '';
    if (mode === 'practice') {
        practiceButtonsHtml = renderPracticeModeButtons(question);
    }
    
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
        ${themeHtml}
        
        <div class="choices" id="choices-container">
            ${renderChoices(question)}
        </div>
        
        ${practiceButtonsHtml}
    `;
    
    // タイマー開始（テストモードの場合、まだ開始されていない場合のみ）
    // タイマーは既にsetIntervalで自動更新されているため、問題切り替え時に手動更新は不要
    if (mode === 'test') {
        if (!timerStarted && timeLimit && testStartTime) {
            // タイマーがまだ開始されていない場合、開始する
            startTimer();
            timerStarted = true; // タイマー開始フラグを設定
        } else if (timerStarted && timeLimitTimer) {
            // タイマーが既に開始されている場合、表示を即座に更新
            // タイマー要素が再作成された場合でも、正しい値を表示する
            const timerEl = document.getElementById('timer');
            if (timerEl && testStartTime && timeLimit) {
                const elapsed = Math.floor((Date.now() - testStartTime) / 1000);
                const remaining = Math.max(0, timeLimit - elapsed);
                const minutes = Math.floor(remaining / 60);
                const seconds = remaining % 60;
                timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                
                // 警告色も設定
                if (remaining <= 60) {
                    timerEl.style.color = '#dc3545';
                    timerEl.style.fontWeight = 'bold';
                } else if (remaining <= 180) {
                    timerEl.style.color = '#ffc107';
                    timerEl.style.fontWeight = 'normal';
                } else {
                    timerEl.style.color = '';
                    timerEl.style.fontWeight = 'normal';
                }
            }
        } else {
            // タイマーが開始されていない場合、強制的に開始を試みる
            console.log('タイマー開始を試みます:', { mode, timerStarted, timeLimit, testStartTime });
            if (timeLimit && testStartTime) {
                startTimer();
                timerStarted = true;
            }
        }
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
    
    // 学習モードで既に解答済みの場合は、正誤表示を追加
    if (existingAnswer && existingAnswer.answer !== null && mode === 'practice') {
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
        // 学習モードで既に解答済みの場合は、イベントリスナーを追加しない（自動移動しない）
        return;
    }
    
    // 未解答またはテストモードの場合、イベントリスナーを追加
    choiceItems.forEach(item => {
        item.addEventListener('click', function() {
            // テストモードで既に解答済みの場合は無視
            if (existingAnswer && existingAnswer.answer !== null && mode === 'test') {
                return;
            }
            
            // 選択状態を切り替え（複数選択対応）
            if (mode === 'practice' || !existingAnswer || existingAnswer.answer === null) {
                this.classList.toggle('selected');
            }
            
            // 解答を送信（選択肢が選択されている場合のみ）
            // 少し遅延させて、選択状態が更新された後に実行
            setTimeout(() => {
                const selectedChoices = Array.from(document.querySelectorAll('.choice-item.selected'))
                    .map(el => parseInt(el.dataset.choice));
                
                // 選択肢が選択されている場合のみ解答を送信
                // テストモードと学習モードの両方で自動移動を有効にする
                if (selectedChoices.length > 0) {
                    const currentAnswer = answers.find(a => a.question_id === question.id);
                    // まだ解答していない場合のみ送信（重複送信を防ぐ）
                    if (!currentAnswer || currentAnswer.answer === null) {
                        // 即座に解答を送信（自動移動を有効にする）
                        submitAnswer(question.id, selectedChoices);
                    }
                }
            }, 10);
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
    
    // 解答送信前に、既に解答済みかどうかをチェック
    const existingAnswerBefore = answers.find(a => a.question_id === questionId);
    const wasAlreadyAnswered = existingAnswerBefore && existingAnswerBefore.answer !== null;
    
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
        
        // 自動的に次の問題に移動（既に解答済みでない場合、かつ最後の問題でない場合、かつ解答がnullでない場合）
        if (!wasAlreadyAnswered && answer !== null && currentQuestionIndex < currentQuestions.length - 1) {
            // 即座に次の問題に移動
            nextQuestion();
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
 * 制限時間タイマーを開始（テストモードのみ、1回だけ開始）
 */
function startTimeLimitTimer() {
    if (mode !== 'test' || !timeLimit || !testStartTime) {
        return;
    }
    
    // 既にタイマーが動作している場合は再起動しない
    if (timeLimitTimer) {
        return;
    }
    
    function updateTimeLimit() {
        if (!testStartTime || !timeLimit) {
            return;
        }
        
        const elapsed = Math.floor((Date.now() - testStartTime) / 1000);
        const remaining = Math.max(0, timeLimit - elapsed);
        
        // 制限時間が経過したら強制終了
        if (remaining <= 0) {
            if (timeLimitTimer) {
                clearInterval(timeLimitTimer);
                timeLimitTimer = null;
            }
            timerStarted = false; // フラグをリセット
            timerLastRemaining = -1;
            timerLastColor = '';
            alert('制限時間が経過しました。テストを終了します。');
            // レポートページにリダイレクト
            if (currentSession) {
                window.location.href = `/report/${currentSession}`;
            }
            return;
        }
        
        // タイマー要素を取得（要素が再作成されても取得できる）
        const timerEl = document.getElementById('timer');
        if (!timerEl) {
            // タイマー要素が存在しない場合はスキップ（問題切り替え中など）
            return;
        }
        
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        const timeText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        // 残り時間が変わった場合のみDOM操作を実行（パフォーマンス最適化）
        if (remaining !== timerLastRemaining) {
            // テキストを更新
            timerEl.textContent = timeText;
            timerLastRemaining = remaining;
        }
        
        // 警告色の判定と更新（必要な場合のみ）
        let newColor = '';
        let newFontWeight = 'normal';
        
        if (remaining <= 60) {
            newColor = '#dc3545'; // 赤色
            newFontWeight = 'bold';
        } else if (remaining <= 180) {
            newColor = '#ffc107'; // 黄色
            newFontWeight = 'normal';
        }
        
        // 色が変わった場合のみ更新
        if (newColor !== timerLastColor) {
            timerEl.style.color = newColor;
            timerEl.style.fontWeight = newFontWeight;
            timerLastColor = newColor;
        }
    }
    
    // 1秒ごとに更新
    timeLimitTimer = setInterval(updateTimeLimit, 1000);
    updateTimeLimit(); // 即座に実行
}

/**
 * タイマーを開始
 */
function startTimer() {
    // テストモードの場合は制限時間タイマーを開始
    if (mode === 'test' && timeLimit) {
        startTimeLimitTimer();
        return;
    }
    
    // 学習モードの場合は通常のタイマー（経過時間を表示）
    let startTime = Date.now();
    
    function updateTimer() {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const timerEl = document.getElementById('timer');
        if (timerEl) {
            timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            timerEl.style.color = ''; // デフォルト
            timerEl.style.fontWeight = 'normal';
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

