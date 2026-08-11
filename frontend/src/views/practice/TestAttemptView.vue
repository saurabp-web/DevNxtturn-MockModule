<template>
  <div ref="pageRoot" class="test-page" :class="{ 'test-page--exam': state === 'active' && isCustomTestModeUI }">

    <!-- Loading -->
    <div v-if="state === 'loading'" class="center-box">
      <div class="spinner"></div>
      <p>Loading questions…</p>
    </div>

    <!-- Error -->
    <div v-else-if="state === 'error'" class="center-box error-box">
      <p>{{ errorMsg }}</p>
      <button class="btn-primary" @click="goBack">Go Back</button>
    </div>

    <!-- Test in progress — Custom Test, Test Mode: exam-style UI -->
    <div v-else-if="state === 'active' && isCustomTestModeUI" class="ct-shell">

      <!-- Top bar -->
      <div class="ct-topbar">
        <div class="ct-brand">
          <span class="ct-logo">N</span>
          <span class="ct-brand-name">NxtTurn</span>
          <span class="ct-test-title">{{ ctTestName }}</span>
        </div>
        <div class="ct-topbar-actions">
          <button class="ct-pause-btn" @click="togglePause">
            <span class="ct-icon">&#10073;&#10073;</span> {{ isPaused ? 'Resume' : 'Pause' }}
          </button>
          <div class="ct-info-box">
            <span class="ct-info-icon">&#8986;</span>
            <div class="ct-info-text">
              <span class="ct-info-label">Time Left</span>
              <span class="ct-info-value" :class="{ warning: timeLeft < 120 }">{{ formattedTime }}</span>
            </div>
          </div>
          <div class="ct-info-box">
            <span class="ct-info-icon">&#128203;</span>
            <div class="ct-info-text">
              <span class="ct-info-label">Questions</span>
              <span class="ct-info-value">{{ currentIndex + 1 }} / {{ questions.length }}</span>
            </div>
          </div>
          <button class="ct-end-btn" @click="confirmSubmit">End Test</button>
        </div>
      </div>

      <!-- Subject bar -->
      <div class="ct-subjectbar">
        <div class="ct-subject-tabs">
          <button
            v-for="grp in subjectGroups"
            :key="grp.name"
            class="ct-subject-tab"
            :class="{ active: activeSubjectName === grp.name }"
            @click="selectSubjectTab(grp.name)"
          >
            {{ grp.name }}
          </button>
        </div>
        <button class="ct-download-btn" @click="showQuestionPaper = true">
          <span class="ct-icon">&#8681;</span> Download
        </button>
      </div>

      <div class="ct-body">

        <!-- Left: progress + status + subject overview -->
        <aside class="ct-panel ct-left">
          <div class="ct-progress-head">
            <span class="ct-panel-title"><span class="ct-title-icon">&#128202;</span> Progress</span>
            <span class="ct-overall-badge">&#10003; Overall</span>
          </div>

          <div class="ct-ring-wrap">
            <svg viewBox="0 0 120 120" class="ct-ring">
              <circle cx="60" cy="60" r="52" class="ct-ring-bg" />
              <circle
                cx="60" cy="60" r="52" class="ct-ring-fg"
                :style="{ strokeDasharray: 327, strokeDashoffset: 327 - (327 * overallPercent / 100) }"
              />
            </svg>
            <div class="ct-ring-center">
              <span class="ct-ring-pct">{{ overallPercent }}%</span>
              <span class="ct-ring-label">Completed</span>
            </div>
          </div>
          <p class="ct-solved-line">{{ answeredCount }} / {{ questions.length }} Solved</p>

          <div class="ct-status-title">Question Status</div>
          <div class="ct-status-grid">
            <div class="ct-status-cell">
              <span class="ct-status-num">{{ notVisitedCount }}</span>
              <span class="ct-status-label">Not Visited</span>
            </div>
            <div class="ct-status-cell">
              <span class="ct-status-num ct-status-orange">{{ skippedCount }}</span>
              <span class="ct-status-label">Skipped</span>
            </div>
            <div class="ct-status-cell">
              <span class="ct-status-num ct-status-green">{{ answeredCount }}</span>
              <span class="ct-status-label">Answered</span>
            </div>
            <div class="ct-status-cell">
              <span class="ct-status-num ct-status-purple">{{ markedOnlyCount }}</span>
              <span class="ct-status-label">Marked for R...</span>
            </div>
            <div class="ct-status-cell">
              <span class="ct-status-num ct-status-red">{{ answeredMarkedCount }}</span>
              <span class="ct-status-label">Answered &amp; ...</span>
            </div>
          </div>

          <div class="ct-subject-overview-title">Subject Overview</div>
          <div class="ct-subject-overview">
            <div v-for="grp in subjectGroups" :key="grp.name" class="ct-so-row">
              <span>{{ grp.name }}</span>
              <span>{{ subjectPercent(grp.name) }}%</span>
            </div>
          </div>

          <hr class="ov-divider" />
          <div class="ov-row"><span>Total Questions</span><strong>{{ questions.length }}</strong></div>
        </aside>

        <!-- Center: question card -->
        <section class="ct-panel ct-question">
          <div class="ct-question-scroll">
            <div class="q-top">
              <span class="q-count">Question {{ indexWithinSubject }} of {{ subjectQuestions.length }}</span>
            </div>

            <div class="q-meta" v-if="currentQ?.difficulty_level">
              <span class="diff-badge" :class="currentQ.difficulty_level">
                {{ currentQ.difficulty_level }}
              </span>
            </div>

            <p class="q-text">{{ currentQ?.question_text }}</p>

            <div v-if="currentQ?.image_url" class="q-diagram">
              <img
                :src="mediaUrl(currentQ.image_url)"
                alt="Question diagram"
                class="q-diagram-img"
                @error="onImgError($event)"
              />
            </div>

            <div v-if="currentOptions" class="ct-options">
              <button
                v-for="opt in currentOptions"
                :key="opt.key"
                class="ct-option-btn"
                :class="{ 'ct-option-selected': currentQ && answers[currentQ.question_id] === opt.key }"
                @click="selectAnswer(opt.key)"
              >
                <span class="ct-opt-avatar">{{ opt.key }}</span>
                <span class="ct-opt-text">{{ opt.text }}</span>
                <span class="ct-opt-radio" :class="{ on: currentQ && answers[currentQ.question_id] === opt.key }"></span>
              </button>
            </div>
          </div>

          <div class="ct-footer">
            <button class="btn-secondary" :disabled="currentIndex === 0" @click="prevQ">&larr; Previous</button>
            <button class="btn-secondary" :disabled="!isAnswered" @click="clearSelection">Clear Selection</button>
            <button class="ct-btn-mark" @click="markAndNext">
              <span class="bm-icon">&#128278;</span> Mark for Review &amp; Next
            </button>
            <button
              v-if="currentIndex < questions.length - 1"
              class="ct-btn-skip-next"
              @click="skipAndNext"
            >
              Skip &amp; Next &rarr;
            </button>
            <button v-else class="btn-submit-footer" @click="confirmSubmit">Submit Test ✓</button>
          </div>
        </section>

        <!-- Right: Question overview -->
        <aside class="ct-panel ct-right">
          <div class="ct-ov-head">
            <span class="ct-panel-title">Question Overview</span>
            <button class="ct-collapse-btn" @click="rightPanelCollapsed = !rightPanelCollapsed">
              {{ rightPanelCollapsed ? '▾' : '▴' }}
            </button>
          </div>

          <template v-if="!rightPanelCollapsed">
            <div class="ct-ov-tabs">
              <button class="ct-ov-tab" :class="{ active: rightPanelTab === 'all' }" @click="rightPanelTab = 'all'">All Questions</button>
              <button class="ct-ov-tab" :class="{ active: rightPanelTab === 'review' }" @click="rightPanelTab = 'review'">Review</button>
              <button class="ct-ov-tab" :class="{ active: rightPanelTab === 'skipped' }" @click="rightPanelTab = 'skipped'">Skipped</button>
            </div>

            <div class="ct-subj-filter">
              <button
                class="ct-subj-filter-btn"
                :class="{ active: rightPanelSubjectFilter === 'all' }"
                @click="rightPanelSubjectFilter = 'all'"
              >All</button>
              <button
                v-for="grp in subjectGroups"
                :key="grp.name"
                class="ct-subj-filter-btn"
                :class="{ active: rightPanelSubjectFilter === grp.name }"
                @click="rightPanelSubjectFilter = grp.name"
              >{{ grp.name }}</button>
            </div>

            <div class="ct-qn-title">Quick Navigation</div>
            <div class="ct-qn-grid">
              <button
                v-for="item in quickNavList"
                :key="item.q.question_id"
                class="ct-qn-cell"
                :class="cellClass(item.index)"
                @click="jumpTo(item.index)"
              >{{ item.index + 1 }}</button>
              <p v-if="quickNavList.length === 0" class="q-list-empty">No questions match this filter.</p>
            </div>

            <div class="legend-title">Legend</div>
            <div class="legend-grid">
              <span class="legend-item"><i class="dot dot-answered"></i> Answered</span>
              <span class="legend-item"><i class="dot dot-not-answered"></i> Skipped</span>
              <span class="legend-item"><i class="dot dot-marked"></i> Marked for Review</span>
              <span class="legend-item legend-item-wide"><i class="dot dot-marked-answered"></i> Answered &amp; Marked</span>
              <span class="legend-item"><i class="dot dot-not-visited"></i> Not Visited</span>
            </div>
          </template>
        </aside>

        <!-- Pause overlay -->
        <div v-if="isPaused" class="pause-overlay">
          <div class="pause-card">
            <span class="pause-icon">&#9208;</span>
            <h3>Test Paused</h3>
            <p>Your timer is on hold. Press Resume when you're ready to continue.</p>
            <button class="btn-primary" @click="togglePause">Resume Test</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Test in progress (chapter practice / full-syllabus / custom-test Practice Mode) -->
    <div v-else-if="state === 'active' && !isCustomTestModeUI" class="test-shell">

      <!-- Top bar -->
      <div class="topbar">
        <button class="exit-link" @click="confirmExit">
          <span class="chev">&lsaquo;</span> Exit Test
        </button>
        <div class="topbar-right">
          <button class="report-link" @click="showReport = true">
            <span class="report-icon">&#128203;</span> Report
          </button>
          <div class="avatar">{{ initials }}</div>
        </div>
      </div>

      <!-- Header -->
      <div class="test-header">
        <div class="test-meta">
          <h2 class="subject-name">
            {{ store.customConfig ? (store.customConfig.subjectLabel ?? 'Custom Test') : (currentQ?.subject_name ?? store.subject?.label) }}
          </h2>
          <p v-if="!store.customConfig && store.scope !== 'full'" class="chapter-name">{{ currentQ?.chapter_name ?? store.chapter?.label }}</p>
        </div>
        <div class="test-right">
          <span class="mode-tag" :class="store.mode === 'test' ? 'mode-test' : 'mode-practice'">
            {{ store.mode === 'test' ? 'Test Mode' : 'Practice Mode' }}
          </span>
          <!-- Timer: only shown for Custom Tests (both Test & Practice Mode).
               Practice Test (chapter/full-syllabus) never shows a timer. -->
          <div v-if="showTimer" class="timer-block">
            <span class="timer-icon">&#128337;</span>
            <div class="timer-text">
              <span class="timer-label">Time Left</span>
              <span class="timer-value" :class="{ warning: timeLeft < 120 }">{{ formattedTime }}</span>
            </div>
          </div>
       <!-- <button class="btn-submit-top" @click="confirmSubmit">Submit Test</button> -->
        </div>
      </div>

      <!-- 3-column body -->
      <div class="test-body">

        <!-- Left: Question list, filterable by status -->
        <aside class="panel palette-panel">
          <div class="tabs-row">
            <button
              class="tab-btn"
              :class="{ active: activeFilter === 'answered' }"
              @click="toggleFilter('answered')"
            >
              Answered <span class="tab-count">({{ answeredCount }})</span>
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeFilter === 'unanswered' }"
              @click="toggleFilter('unanswered')"
            >
              Unanswered <span class="tab-count">({{ unansweredCount }})</span>
            </button>
            <button
              class="tab-btn"
              :class="{ active: activeFilter === 'marked' }"
              @click="toggleFilter('marked')"
            >
              Marked <span class="tab-count">({{ markedCount }})</span>
            </button>
          </div>

          <div class="q-list">
            <button
              v-for="item in filteredQuestionList"
              :key="item.q.question_id"
              class="q-list-card"
              :class="{ 'q-list-current': item.index === currentIndex }"
              @click="jumpTo(item.index)"
            >
              <span class="q-list-num" :class="cellClass(item.index)">{{ item.index + 1 }}</span>
              <span class="q-list-body">
                <span class="q-list-title">{{ item.q.question_text }}</span>
                <span v-if="item.q.hint" class="q-list-sub">{{ item.q.hint }}</span>
              </span>
              <span class="q-list-status">
                <span v-if="marked[item.q.question_id]" class="status-icon status-marked">&#128278;</span>
                <span v-else-if="answers[item.q.question_id]" class="status-icon status-answered">&#10003;</span>
                <span v-else class="status-icon status-unanswered"></span>
              </span>
            </button>
            <p v-if="filteredQuestionList.length === 0" class="q-list-empty">No questions match this filter.</p>
          </div>

          <button class="clear-filters-btn" :disabled="!activeFilter" @click="clearFilters">
            Clear Filters
            <svg class="filter-icon" viewBox="0 0 16 16" width="13" height="13" fill="none">
              <path d="M2 3h12l-4.5 5.5V13l-3 1.5V8.5L2 3z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
            </svg>
          </button>
        </aside>

        <!-- Center: Question card -->
        <section class="panel question-panel">
          <div class="q-top">
            <span class="q-count">Question {{ currentIndex + 1 }} of {{ questions.length }}</span>
            <button class="mark-link" @click="toggleMark()">
              <span class="bm-icon">&#128278;</span>
              {{ isMarked(currentQ?.question_id) ? 'Marked for Review' : 'Mark for Review' }}
            </button>
          </div>

          <div class="q-meta" v-if="currentQ?.difficulty_level">
            <span class="diff-badge" :class="currentQ.difficulty_level">
              {{ currentQ.difficulty_level }}
            </span>
          </div>

          <p class="q-text">{{ currentQ?.question_text }}</p>

          <!-- Diagram image (only shown if question has an image) -->
          <div v-if="currentQ?.image_url" class="q-diagram">
            <img
              :src="mediaUrl(currentQ.image_url)"
              alt="Question diagram"
              class="q-diagram-img"
              @error="onImgError($event)"
            />
          </div>

          <div v-if="currentOptions" class="options">
            <button
              v-for="opt in currentOptions"
              :key="opt.key"
              class="option-btn"
              :class="optionClass(opt.key)"
              :disabled="isChapterPracticeMode && isChecked"
              @click="selectAnswer(opt.key)"
            >
              <span class="opt-radio" :class="{ on: currentQ && answers[currentQ.question_id] === opt.key }"></span>
              <span class="opt-key">{{ opt.key }}.</span>
              <span class="opt-text">{{ opt.text }}</span>
            </button>
          </div>

          <!-- Hint + Check Answer / Skip on the same row. Check Answer / Skip Question
               are chapter-flow Practice Mode only — custom tests in Practice Mode use
               plain Next / Submit navigation instead (see q-footer below). -->
          <div class="hint-check-row">
            <button
              v-if="!(isChapterPracticeMode && isChecked)"
              class="hint-btn"
              @click="currentQ && (hintOpen[currentQ.question_id] = !hintOpen[currentQ.question_id])"
            >
              <span class="hint-icon">&#128161;</span> Hint
            </button>
            <div class="hint-check-actions">
              <button
                v-if="isChapterPracticeMode && !isChecked"
                class="btn-skip"
                @click="skipQuestion"
              >
                Skip Question
              </button>
              <button
                v-if="isChapterPracticeMode && !isChecked"
                class="btn-check"
                :disabled="!isAnswered"
                @click="checkAnswer"
              >
                Check Answer
              </button>
            </div>
          </div>
          <div v-if="!(isChapterPracticeMode && isChecked) && currentQ && hintOpen[currentQ.question_id]" class="hint-box">
            {{ currentQ?.hint || 'No hint available for this question.' }}
          </div>

          <!-- Chapter-flow Practice Mode: show verdict + explanation only after Check Answer is pressed -->
          <div v-if="isChapterPracticeMode && isChecked" class="explanation-box">
            <div class="verdict-label" :class="isCurrentCorrect ? 'verdict-correct' : 'verdict-wrong'">
              {{ isCurrentCorrect ? '✓ Correct!' : '✗ Incorrect' }}
              <span v-if="!isCurrentCorrect && practiceCorrectAnswer">
                &nbsp;— Correct Answer: <strong>{{ practiceCorrectAnswer }}</strong>
              </span>
            </div>
            <div v-if="practiceExplanation" class="explanation">
              <strong>Explanation:</strong> {{ practiceExplanation }}
            </div>
          </div>

          <div class="q-footer">
            <button class="btn-secondary" :disabled="currentIndex === 0" @click="prevQ">&larr; Previous</button>
            <!-- Custom-test Practice Mode falls into this branch too (isChapterPracticeMode
                 is false for it), so it always gets Next / Submit rather than waiting on
                 Check Answer. -->
            <template v-if="!isChapterPracticeMode || isChecked">
              <button
                v-if="currentIndex < questions.length - 1"
                class="btn-primary"
                @click="nextQ"
              >
                Next &rarr;
              </button>
              <button v-else class="btn-submit-footer" @click="confirmSubmit">
                Submit Test ✓
              </button>
            </template>
          </div>
        </section>

        <!-- Right: Question overview + quick actions -->
        <aside class="panel overview-panel">
          <h3 class="panel-title">Question Overview</h3>

          <div class="qgrid" :style="{ gridTemplateColumns: `repeat(auto-fill, minmax(${qgridMinCell}, 1fr))`, fontSize: qgridFontSize }">
            <button
              v-for="(q, i) in questions"
              :key="q.question_id"
              class="qcell"
              :class="cellClass(i)"
              @click="jumpTo(i)"
            >
              {{ i + 1 }}
            </button>
          </div>

          <div class="legend-title">Legend</div>
          <div class="legend-grid">
            <span class="legend-item"><i class="dot dot-answered"></i> Answered</span>
            <span class="legend-item"><i class="dot dot-not-answered"></i> Not Answered</span>
            <span class="legend-item"><i class="dot dot-not-visited"></i> Not Visited</span>
            <span class="legend-item"><i class="dot dot-marked"></i> Marked</span>
            <span class="legend-item legend-item-wide">
              <i class="dot dot-marked-answered"></i> Answered &amp; Marked For Review
            </span>
          </div>

          <div class="ov-actions">
            <button class="ov-action-btn ov-action-paper" @click="showQuestionPaper = true">
              Question Paper <span class="ov-action-icon">&#128203;</span>
            </button>
            <button class="ov-action-btn ov-action-pause" @click="togglePause">
              {{ isPaused ? 'Resume' : 'Pause' }} <span class="ov-action-icon">{{ isPaused ? '▶' : '⏸' }}</span>
            </button>
            <button class="ov-action-btn ov-action-submit" @click="confirmSubmit">
              Submit <span class="ov-action-icon">&#10003;</span>
            </button>
          </div>

          <hr class="ov-divider" />
          <div class="ov-row"><span>Questions</span><strong>{{ questions.length }}</strong></div>
          <div class="ov-row"><span>Answered</span><strong class="c-green">{{ answeredCount }}</strong></div>
          <div class="ov-row"><span>Marked</span><strong class="c-orange">{{ markedCount }}</strong></div>
          <div class="ov-row"><span>Unanswered</span><strong class="c-gray">{{ unansweredCount }}</strong></div>
          <hr class="ov-divider" />
          <div class="ov-row"><span>Total Marks</span><strong class="c-green">+{{ totalMarksDisplay }}</strong></div>
          <div v-if="store.mode === 'test'" class="ov-row"><span>Negative Marks</span><strong class="c-red">-{{ negativeMarkDisplay }}</strong></div>
        </aside>

        <!-- Pause overlay — blocks the question area until Resume is pressed -->
        <div v-if="isPaused" class="pause-overlay">
          <div class="pause-card">
            <span class="pause-icon">&#9208;</span>
            <h3>Test Paused</h3>
            <p>Your timer is on hold. Press Resume when you're ready to continue.</p>
            <button class="btn-primary" @click="togglePause">Resume Test</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Results (chapter / practice flow only — custom tests navigate to
         the dedicated 'practice-custom-result' route instead) -->
    <div v-else-if="state === 'results' && result" class="results-wrap">
      <div class="score-circle" :class="scoreClass">
        <span class="score-num">{{ result.score }}/{{ result.total }}</span>
        <span class="score-pct">{{ result.percentage }}%</span>
      </div>

      <h2 class="result-title">
        {{ (result.percentage ?? 0) >= 70 ? '🎉 Great job!'
         : (result.percentage ?? 0) >= 40 ? '👍 Good effort!'
         : '📚 Keep practising!' }}
      </h2>

      <div class="result-list">
        <div
          v-for="(r, i) in result.results"
          :key="r.question_id"
          class="result-item"
          :class="r.is_correct ? 'correct' : 'wrong'"
        >
          <div class="ri-top">
            <span class="ri-num">Q{{ i + 1 }}</span>
            <span class="ri-verdict">{{ r.is_correct ? '✓ Correct' : '✗ Wrong' }}</span>
          </div>
          <p class="ri-q">{{ r.question_text }}</p>
          <p class="ri-ans">
            Your answer: <strong>{{ r.your_answer || '—' }}</strong>
            &nbsp;|&nbsp;
            Correct: <strong>{{ r.correct_answer }}</strong>
          </p>
          <p v-if="r.explanation" class="ri-exp">{{ r.explanation }}</p>
          <p v-if="r.hints" class="ri-hint">💡 {{ r.hints }}</p>
        </div>
      </div>

      <div class="result-footer">
        <button class="btn-secondary" @click="retake">Retake</button>
        <button class="btn-primary"   @click="backToExams">Back to Exams</button>
      </div>
    </div>

    <!-- Report modal (placeholder — not yet wired to a backend endpoint) -->
    <div v-if="showReport" class="modal-backdrop" @click.self="showReport = false">
      <div class="modal-box">
        <h3>Report an issue</h3>
        <p class="modal-sub">Question {{ currentIndex + 1 }} · {{ currentQ?.subject_name }}</p>
        <textarea v-model="reportText" placeholder="Describe the issue with this question…" rows="4"></textarea>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showReport = false">Cancel</button>
          <button class="btn-primary" @click="submitReport">Submit</button>
        </div>
      </div>
    </div>

    <!-- Confirm submit modal -->
    <div v-if="showSubmitConfirm" class="modal-backdrop" @click.self="showSubmitConfirm = false">
      <div class="modal-box">
        <h3>Submit test?</h3>
        <p class="modal-sub">
          {{ answeredCount }} answered · {{ markedCount }} marked · {{ unansweredCount }} unanswered
        </p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showSubmitConfirm = false">Keep Reviewing</button>
          <button class="btn-primary" @click="submitTest">Submit Now</button>
        </div>
      </div>
    </div>

    <!-- Time's up modal — Practice Mode only, first expiry, with questions still
         pending: offers a one-time extension or an immediate submit. -->
    <div v-if="showTimeUpModal" class="modal-backdrop">
      <div class="modal-box">
        <h3>&#9203; Time's up!</h3>
        <p class="modal-sub">
          You still have {{ unansweredCount }} question{{ unansweredCount === 1 ? '' : 's' }} left to solve.
          Since you're in Practice Mode, you can take a bit more time or submit what you have.
        </p>
        <div class="modal-actions">
          <button class="btn-secondary" @click="submitNow">Submit Now</button>
          <button class="btn-primary" @click="extendTime(5)">+5 Minutes</button>
        </div>
      </div>
    </div>

    <!-- Forced-submit modal — Test Mode (always), or Practice Mode once the
         one-time extension has already been used up. No extension offered
         here; the test is never auto-submitted straight to the report —
         the student must acknowledge and press Submit first. -->
    <div v-if="showForcedSubmitModal" class="modal-backdrop">
      <div class="modal-box">
        <h3>&#9203; Time's up!</h3>
        <p class="modal-sub">Your time has ended. Please submit the exam to see your results.</p>
        <div class="modal-actions">
          <button class="btn-primary" @click="forceSubmit">Submit Exam</button>
        </div>
      </div>
    </div>

    <!-- Question Paper — subject-tabbed, read-only view of every question,
         for reference / printing / PDF download -->
    <div v-if="showQuestionPaper" class="paper-fullscreen">
      <div class="paper-box">
        <div class="paper-header">
          <div class="paper-header-title">
            <span class="paper-tab-icon">&#128218;</span>
            <h3>{{ paperSubjects.length === 1 ? paperSubjects[0] : 'Question Paper' }}</h3>
          </div>
          <div class="paper-header-actions">
            <button class="btn-secondary" @click="printQuestionPaper">
              <span class="pdf-icon">&#128424;</span> Print
            </button>
            <button class="btn-primary btn-pdf" :disabled="isGeneratingPdf" @click="downloadQuestionPaperPdf">
              <span v-if="isGeneratingPdf" class="pdf-spinner"></span>
              {{ isGeneratingPdf ? 'Generating…' : 'Download PDF' }}
              <span v-if="!isGeneratingPdf" class="pdf-icon">&#8681;</span>
            </button>
            <button class="modal-close" @click="showQuestionPaper = false">&times;</button>
          </div>
        </div>

        <!-- Subject tabs -->
        <div class="paper-tabs">
          <button
            v-for="subj in paperSubjects"
            :key="subj"
            class="paper-tab-btn"
            :class="{ active: paperActiveSubject === subj }"
            @click="paperActiveSubject = subj"
          >
            <span class="paper-tab-icon">&#128218;</span> {{ subj }}
          </button>
        </div>

        <div class="paper-list">
          <div v-for="(q, i) in paperQuestionsForActiveSubject" :key="q.question_id" class="paper-item">
            <span class="paper-q-num">{{ i + 1 }}</span>
            <div class="paper-item-body">
              <p class="paper-q">{{ q.question_text }}</p>

              <div v-if="q.image_url" class="paper-q-diagram">
                <img
                  :src="mediaUrl(q.image_url)"
                  alt="Question diagram"
                  class="paper-q-diagram-img"
                  @error="onImgError($event)"
                />
              </div>

              <ul v-if="q.options?.[0]" class="paper-opts">
                <li>(A) {{ q.options[0].option_A }}</li>
                <li>(B) {{ q.options[0].option_B }}</li>
                <li>(C) {{ q.options[0].option_C }}</li>
                <li>(D) {{ q.options[0].option_D }}</li>
              </ul>
            </div>
          </div>
          <p v-if="paperQuestionsForActiveSubject.length === 0" class="q-list-empty">
            No questions in this subject.
          </p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/axiosInstance'
import { usePracticeTestStore } from '@/stores/practiceTest'
import type { CustomTestResult } from '@/stores/practiceTest'

const router = useRouter()
const store  = usePracticeTestStore()

// ── Types ──────────────────────────────────────────────────────────
interface QuestionOption {
  option_id: number
  option_A: string
  option_B: string
  option_C: string
  option_D: string
}

interface Solution {
  explaination_text: string
  hints: string
}

interface CorrectAnswer {
  answer_value: string
  answer_type: string
}

interface Question {
  question_id:     number
  question_text:   string
  difficulty_level: string
  subject_name:    string
  chapter_name:    string
  options:         QuestionOption[]
  solution:        Solution[]        // empty in test mode
  correct_answer:  CorrectAnswer[]   // empty in test mode
  hint:            string            // always available, both modes
  image_url?:      string | null     // optional diagram, not every question has one
}

interface SubmitResult {
  score:      number
  total:      number
  percentage: number
  results: {
    question_id:    number
    question_text:  string
    your_answer:    string
    correct_answer: string
    is_correct:     boolean
    explanation:    string
    hints:          string
  }[]
}

// ── State ──────────────────────────────────────────────────────────
type AppState = 'loading' | 'active' | 'results' | 'error'

const state        = ref<AppState>('loading')
const errorMsg     = ref('')
const questions    = ref<Question[]>([])
const currentIndex = ref(0)
const answers      = reactive<Record<number, string>>({})
const marked       = reactive<Record<number, boolean>>({})
const visited      = reactive<Record<number, boolean>>({}) // has this question ever been opened? (distinguishes "Not Visited" from "Not Answered")
const hintOpen      = reactive<Record<number, boolean>>({})
const checked      = reactive<Record<number, boolean>>({})  // practice mode: has "Check Answer" been pressed?
const result       = ref<SubmitResult | null>(null)

// Question palette auto-sizes cells to fit the container width (never
// overflows it) while shrinking as question count grows, so a 5-question
// chapter test and a 130-question full-syllabus test both stay compact.
const qgridMinCell = computed(() => {
  const n = questions.value.length
  if (n > 100) return '22px'
  if (n > 60)  return '26px'
  if (n > 30)  return '30px'
  return '38px'
})
const qgridFontSize = computed(() => {
  const n = questions.value.length
  if (n > 100) return '9px'
  if (n > 60)  return '10px'
  if (n > 30)  return '11px'
  return '13px'
})

const showReport         = ref(false)
const reportText         = ref('')
const showSubmitConfirm  = ref(false)
const showTimeUpModal    = ref(false) // Practice Mode: shown when time runs out with questions still pending
const showForcedSubmitModal = ref(false) // Test Mode always, or Practice Mode after its one extension is used up
const hasExtended        = ref(false) // Practice Mode: has the student already used their one-time extension?
const showQuestionPaper  = ref(false)
const paperActiveSubject = ref('')   // which subject tab is open inside the Question Paper modal
const isGeneratingPdf    = ref(false)

// Distinct subjects present in this test, in first-appearance order (Physics, Chemistry, Mathematics…)
const paperSubjects = computed<string[]>(() => {
  const seen = new Set<string>()
  const list: string[] = []
  for (const q of questions.value) {
    const subj = q.subject_name || 'General'
    if (!seen.has(subj)) { seen.add(subj); list.push(subj) }
  }
  return list
})

// Keep the active tab valid — default to the first subject whenever the modal opens
// or the subject list changes (e.g. questions finish loading after the modal was opened).
watch([showQuestionPaper, paperSubjects], () => {
  if (showQuestionPaper.value && !paperSubjects.value.includes(paperActiveSubject.value)) {
    paperActiveSubject.value = paperSubjects.value[0] ?? ''
  }
})

const paperQuestionsForActiveSubject = computed<Question[]>(() =>
  questions.value.filter(q => (q.subject_name || 'General') === paperActiveSubject.value)
)

// Left panel: Answered / Unanswered / Marked tab filter for the question list.
// null = no filter, show every question. Clicking the active tab again clears it.
const activeFilter = ref<'answered' | 'unanswered' | 'marked' | null>(null)
function toggleFilter(tab: 'answered' | 'unanswered' | 'marked'): void {
  activeFilter.value = activeFilter.value === tab ? null : tab
}
function clearFilters(): void {
  activeFilter.value = null
}

const timeLeft    = ref(0)
let   timerHandle: ReturnType<typeof setInterval> | null = null
let   totalAllottedSeconds = 0
const timeTakenSeconds = ref(0)

// ── Computed ───────────────────────────────────────────────────────
const currentQ = computed<Question | undefined>(() => questions.value[currentIndex.value])

const currentOptions = computed(() => {
  const opts = currentQ.value?.options[0]
  if (!opts) return null
  return [
    { key: 'A', text: opts.option_A },
    { key: 'B', text: opts.option_B },
    { key: 'C', text: opts.option_C },
    { key: 'D', text: opts.option_D },
  ]
})

const isAnswered = computed(() =>
  currentQ.value ? !!answers[currentQ.value.question_id] : false
)

const practiceCorrectAnswer = computed(() =>
  currentQ.value?.correct_answer[0]?.answer_value ?? null
)
const practiceExplanation = computed(() =>
  currentQ.value?.solution[0]?.explaination_text ?? null
)

const isChecked = computed(() =>
  currentQ.value ? !!checked[currentQ.value.question_id] : false
)

// True only for the chapter/full-syllabus Practice Mode flow (the one with
// Check Answer / Skip Question / locked-after-checking options). Custom
// tests in Practice Mode intentionally do NOT use this — they navigate with
// plain Next / Submit like Test Mode, just without the timer's hard cutoff.
const isChapterPracticeMode = computed(() => store.mode === 'practice' && !store.customConfig)

// Timer is shown ONLY for Custom Tests (both Test Mode and Practice Mode),
// because the user explicitly chose a duration on the Create Custom Test page.
// Practice Tests (chapter-wise or full-syllabus) never show a timer.
const showTimer = computed(() => !!store.customConfig)

const isCurrentCorrect = computed(() => {
  const qId = currentQ.value?.question_id
  if (!qId) return false
  const correct = practiceCorrectAnswer.value?.toUpperCase()
  return answers[qId] === correct
})

const answeredCount = computed(() =>
  questions.value.filter(q => !!answers[q.question_id]).length
)
const markedCount = computed(() =>
  questions.value.filter(q => marked[q.question_id]).length
)
const unansweredCount = computed(() =>
  questions.value.length - answeredCount.value
)

// ── Custom Test / Test Mode: exam-style UI (own block, separate from the
//    chapter-practice palette/overview panels above) ──────────────────
const isCustomTestModeUI = computed(() => !!store.customConfig && store.mode === 'test')

const ctTestName = computed(() => store.customConfig?.subjectLabel ?? 'Custom Test')

interface SubjectGroup { name: string; list: Question[] }
const subjectGroups = computed<SubjectGroup[]>(() => {
  const map = new Map<string, Question[]>()
  for (const q of questions.value) {
    const name = q.subject_name || 'General'
    if (!map.has(name)) map.set(name, [])
    map.get(name)!.push(q)
  }
  return Array.from(map.entries()).map(([name, list]) => ({ name, list }))
})

// Which subject tab is currently open in the center question card.
const activeSubjectName = ref('')
watch(subjectGroups, (groups) => {
  if (groups.length && !groups.some(g => g.name === activeSubjectName.value)) {
    activeSubjectName.value = groups[0].name
  }
}, { immediate: true })

// Keep the subject tab in sync with whichever question is open (e.g. jumped to
// via Quick Navigation) so "Question X of Y" always reflects the right subject.
watch(currentQ, (q) => {
  if (q?.subject_name && q.subject_name !== activeSubjectName.value) {
    activeSubjectName.value = q.subject_name
  }
})

const subjectQuestions = computed(() =>
  questions.value.filter(q => (q.subject_name || 'General') === activeSubjectName.value)
)

const indexWithinSubject = computed(() => {
  if (!currentQ.value) return 0
  const pos = subjectQuestions.value.findIndex(q => q.question_id === currentQ.value!.question_id)
  return pos === -1 ? 1 : pos + 1
})

function selectSubjectTab(name: string): void {
  activeSubjectName.value = name
  const firstIdx = questions.value.findIndex(q => (q.subject_name || 'General') === name)
  if (firstIdx !== -1) jumpTo(firstIdx)
}

function subjectPercent(name: string): number {
  const list = subjectGroups.value.find(g => g.name === name)?.list ?? []
  if (!list.length) return 0
  const done = list.filter(q => !!answers[q.question_id]).length
  return Math.round((done / list.length) * 100)
}

const overallPercent = computed(() =>
  questions.value.length ? Math.round((answeredCount.value / questions.value.length) * 100) : 0
)

// Status buckets shown in the left "Question Status" grid.
const notVisitedCount = computed(() =>
  questions.value.filter(q => !visited[q.question_id]).length
)
const skippedCount = computed(() =>
  questions.value.filter(q => visited[q.question_id] && !answers[q.question_id] && !marked[q.question_id]).length
)
const markedOnlyCount = computed(() =>
  questions.value.filter(q => marked[q.question_id] && !answers[q.question_id]).length
)
const answeredMarkedCount = computed(() =>
  questions.value.filter(q => marked[q.question_id] && !!answers[q.question_id]).length
)

function clearSelection(): void {
  const qId = currentQ.value?.question_id
  if (qId != null) delete answers[qId]
}

function markAndNext(): void {
  const qId = currentQ.value?.question_id
  if (qId != null) marked[qId] = true
  if (currentIndex.value < questions.value.length - 1) nextQ()
  else confirmSubmit()
}

function skipAndNext(): void {
  nextQ()
}

// Right "Question Overview" panel: All Questions / Review / Skipped tabs,
// crossed with an optional per-subject filter.
const rightPanelCollapsed = ref(false)
const rightPanelTab = ref<'all' | 'review' | 'skipped'>('all')
const rightPanelSubjectFilter = ref('all')

const quickNavList = computed(() => {
  return questions.value
    .map((q, index) => ({ q, index }))
    .filter(({ q }) => {
      if (rightPanelSubjectFilter.value !== 'all' && (q.subject_name || 'General') !== rightPanelSubjectFilter.value) return false
      if (rightPanelTab.value === 'review')  return !!marked[q.question_id]
      if (rightPanelTab.value === 'skipped') return visited[q.question_id] && !answers[q.question_id]
      return true
    })
})

// Left panel list, filtered by the active Answered/Unanswered/Marked tab.
// Keeps original index (for numbering + jumpTo) even though items may be filtered out.
const filteredQuestionList = computed(() => {
  return questions.value
    .map((q, index) => ({ q, index }))
    .filter(({ q }) => {
      if (activeFilter.value === 'answered')   return !!answers[q.question_id]
      if (activeFilter.value === 'unanswered') return !answers[q.question_id]
      if (activeFilter.value === 'marked')     return !!marked[q.question_id]
      return true
    })
})

const formattedTime = computed(() => {
  const m = Math.floor(timeLeft.value / 60).toString().padStart(2, '0')
  const s = (timeLeft.value % 60).toString().padStart(2, '0')
  return `${m}:${s}`
})

const scoreClass = computed(() => {
  const pct = result.value?.percentage ?? 0
  return pct >= 70 ? 'score-high' : pct >= 40 ? 'score-mid' : 'score-low'
})

const initials = computed(() => 'T') // placeholder — wire to auth store if available

// ── Media helpers ──────────────────────────────────────────────────────────
const MEDIA_BASE = import.meta.env.VITE_MEDIA_URL ?? (import.meta.env.VITE_API_BASE ?? '').replace('/api', '')

function mediaUrl(path: string | null | undefined): string {
  if (!path) return ''
  // Already an absolute URL
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  // Strip leading slash if present, then join with base
  return `${MEDIA_BASE.replace(/\/+$/, '')}/media/${path.replace(/^\/+/, '')}`
}

function onImgError(event: Event): void {
  // Hide broken image gracefully
  const img = event.target as HTMLImageElement
  if (img) img.style.display = 'none'
}

const totalMarksDisplay = computed(() => {
  const config = store.customConfig
  if (config) return config.numQuestions * config.marksPerQuestion
  return questions.value.length
})

const negativeMarkDisplay = computed(() => {
  const config = store.customConfig
  const perQuestion = config?.marksPerQuestion ?? 1
  return (0.25 * perQuestion).toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1')
})

// ── Methods ────────────────────────────────────────────────────────
function cellClass(i: number): string {
  const q = questions.value[i]
  if (!q) return ''
  if (i === currentIndex.value) return 'cell-current'
  const qId = q.question_id
  const isAnswered = !!answers[qId]
  const isMarkedQ  = !!marked[qId]
  const isVisited  = !!visited[qId]
  if (isMarkedQ && isAnswered) return 'cell-marked-answered'
  if (isMarkedQ)   return 'cell-marked'
  if (isAnswered)  return 'cell-answered'
  if (isVisited)   return 'cell-not-answered'  // opened but left blank
  return 'cell-not-visited'                    // never opened
}

function isMarked(qId: number | undefined): boolean {
  return qId ? !!marked[qId] : false
}

function toggleMark(): void {
  const qId = currentQ.value?.question_id
  if (!qId) return
  marked[qId] = !marked[qId]
}

// ── ANSWER HIGHLIGHTING: practice/chapter flow (own logic, do not merge with custom) ──
function optionClassPractice(key: string): string {
  const qId = currentQ.value?.question_id
  if (!qId) return ''
  const selected = answers[qId]
  if (!selected) return ''

  if (store.mode === 'practice') {
    if (!checked[qId]) {
      // Not checked yet — just highlight the current selection, no right/wrong reveal.
      return key === selected ? 'opt-selected' : ''
    }
    const correct = practiceCorrectAnswer.value?.toUpperCase()
    if (key === correct)  return 'opt-correct'
    if (key === selected) return 'opt-wrong'
  } else {
    if (key === selected) return 'opt-selected'
  }
  return ''
}

// ── ANSWER HIGHLIGHTING: custom test (own logic, do not merge with practice) ──
function optionClassCustom(key: string): string {
  const qId = currentQ.value?.question_id
  if (!qId) return ''
  const selected = answers[qId]
  if (!selected) return ''
  // Custom tests (both Test and Practice Mode) navigate with plain Next/Submit —
  // no right/wrong reveal mid-test, even in Practice Mode.
  return key === selected ? 'opt-selected' : ''
}

function optionClass(key: string): string {
  return store.customConfig ? optionClassCustom(key) : optionClassPractice(key)
}

// ── SELECT ANSWER: practice/chapter flow ──
function selectAnswerPractice(key: string): void {
  const qId = currentQ.value?.question_id
  if (!qId) return
  if (store.mode === 'practice' && checked[qId]) return // lock once checked
  answers[qId] = key
}

// ── SELECT ANSWER: custom test ──
function selectAnswerCustom(key: string): void {
  const qId = currentQ.value?.question_id
  if (!qId) return
  answers[qId] = key
}

function selectAnswer(key: string): void {
  if (store.customConfig) selectAnswerCustom(key)
  else selectAnswerPractice(key)
}

// "Check Answer" only ever appears in the practice-flow UI (custom tests are always
// mode === 'test', so the template's v-if hides this button for them). Guarded here too.
function checkAnswerPractice(): void {
  const qId = currentQ.value?.question_id
  if (!qId || !answers[qId]) return
  checked[qId] = true
}

function checkAnswer(): void {
  if (store.customConfig) return // no-op: custom tests don't use the check-answer flow
  checkAnswerPractice()
}

function markVisited(i: number): void {
  const qId = questions.value[i]?.question_id
  if (qId != null) visited[qId] = true
}
function jumpTo(i: number): void { currentIndex.value = i; markVisited(i) }
function nextQ(): void { if (currentIndex.value < questions.value.length - 1) { currentIndex.value++; markVisited(currentIndex.value) } }
function prevQ(): void { if (currentIndex.value > 0) { currentIndex.value--; markVisited(currentIndex.value) } }

// Skip the current question (practice mode) without checking/answering it,
// and move on to the next one — or wrap up if it's the last question.
function skipQuestion(): void {
  if (currentIndex.value < questions.value.length - 1) {
    nextQ()
  } else {
    confirmSubmit()
  }
}

function confirmSubmit(): void { showSubmitConfirm.value = true }

function confirmExit(): void {
  if (confirm('Exit the test? Your progress will be lost.')) {
    stopTimer()
    goBack()
  }
}

function goBack(): void {
  if (store.customConfig) {
    router.push({ name: 'practice-custom' })
  } else {
    router.push({ name: 'practice-test-type' })
  }
}

function submitReport(): void {
  // Placeholder: no backend endpoint provided for reporting yet.
  showReport.value = false
  reportText.value = ''
  alert('Thanks — your report was noted locally. (Backend reporting endpoint not yet wired up.)')
}

// ── SUBMIT: practice/chapter flow (own logic, do not merge with custom) ──
async function submitChapterTest(): Promise<void> {
  showSubmitConfirm.value = false
  stopTimer()
  // timeTakenSeconds is already being counted up by startChapterTimer's
  // setInterval — no recalculation needed here.
  state.value = 'loading'
  try {
    const payload: Record<string, string> = {}
    for (const q of questions.value) {
      payload[q.question_id] = answers[q.question_id] ?? ''
    }
    const res = await api.post<SubmitResult>('/questions/submit/', { answers: payload })
    result.value = res.data
    state.value  = 'results'
  } catch {
    errorMsg.value = 'Failed to submit. Please try again.'
    state.value    = 'error'
  }
}

// ── SUBMIT: custom test (own logic, do not merge with practice) ──
// NOTE: points at the same '/questions/submit/' endpoint for now — swap this to a
// dedicated route (and pass marksPerQuestion/difficulty) once the backend has one.
async function submitCustomTest(): Promise<void> {
  showSubmitConfirm.value = false
  stopTimer()
  timeTakenSeconds.value = Math.max(0, totalAllottedSeconds - timeLeft.value)
  state.value = 'loading'
  try {
    const payload: Record<string, string> = {}
    for (const q of questions.value) {
      payload[q.question_id] = answers[q.question_id] ?? ''
    }
    const config = store.customConfig
    const res = await api.post<SubmitResult>('/questions/submit/', {
      answers: payload,
      marks_per_question: config?.marksPerQuestion,
      difficulty: config?.difficulty,
    })
    const data = res.data

    const correct   = data.results.filter(r => r.is_correct).length
    const attempted = data.results.filter(r => !!r.your_answer).length
    const wrong     = data.results.filter(r => !r.is_correct && !!r.your_answer).length
    const skipped   = data.results.filter(r => !r.your_answer).length

    const customResult: CustomTestResult = {
      testName:         config ? `${config.subjectLabel} — Custom Test` : 'Custom Test',
      subjectName:       config?.subjectLabel ?? 'Custom Test',
      score:             data.score,
      total:             data.total,
      percentage:        data.percentage,
      correct,
      wrong,
      skipped,
      attempted,
      timeTakenSeconds:  timeTakenSeconds.value,
      totalTimeSeconds:  totalAllottedSeconds,
      submittedAt:       new Date().toISOString(),
    }
    store.setCustomTestResult(customResult)
    router.push({ name: 'practice-custom-result' })
  } catch {
    errorMsg.value = 'Failed to submit. Please try again.'
    state.value    = 'error'
  }
}

async function submitTest(): Promise<void> {
  if (store.customConfig) await submitCustomTest()
  else await submitChapterTest()
}

function backToExams(): void {
  store.reset()
  router.push({ name: 'exams' })
}

function retake(): void {
  resetProgressState()
  currentIndex.value = 0
  result.value = null
  hasExtended.value = false
  showTimeUpModal.value = false
  showForcedSubmitModal.value = false
  isPaused.value = false
  loadQuestions()
}

function stopTimer(): void {
  if (timerHandle) { clearInterval(timerHandle); timerHandle = null }
}

// Shared 1-second countdown tick, used by both timer starters, extendTime(),
// and Resume-from-Pause — kept in one place instead of four copies of setInterval.
function resumeCountdown(): void {
  timerHandle = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) handleTimeUp()
  }, 1000)
}

// ── PAUSE ──────────────────────────────────────────────────────────
// Stops the countdown and blocks the question area behind an overlay until
// Resume is pressed. Available in both modes via the right panel's Pause
// button. NOTE: the Create Custom Test page's "Important Notes" currently
// tell students the test can't be paused — update that copy to match.
const isPaused = ref(false)
function togglePause(): void {
  if (isPaused.value) {
    isPaused.value = false
    // Custom tests count down; practice tests count up.
    if (store.customConfig) {
      resumeCountdown()
    } else {
      timerHandle = setInterval(() => { timeTakenSeconds.value++ }, 1000)
    }
  } else {
    isPaused.value = true
    stopTimer()
  }
}

function printQuestionPaper(): void {
  window.print()
}

// ── QUESTION PAPER → PDF ──────────────────────────────────────────────
// Generates a real, downloadable .pdf (not just a print dialog), grouped by
// subject, with question text, diagrams (if any), and options A–D.
// Requires the `jspdf` package: npm install jspdf
async function downloadQuestionPaperPdf(): Promise<void> {
  if (isGeneratingPdf.value) return
  isGeneratingPdf.value = true
  try {
    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF({ unit: 'pt', format: 'a4' })

    const pageWidth    = doc.internal.pageSize.getWidth()
    const pageHeight   = doc.internal.pageSize.getHeight()
    const margin       = 48
    const contentWidth = pageWidth - margin * 2
    let y = margin

    const paperTitle =
      store.customConfig?.subjectLabel ??
      (paperSubjects.value.length === 1 ? paperSubjects.value[0] : 'Question Paper')

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(16)
    doc.text(paperTitle, margin, y)
    y += 12
    doc.setDrawColor(124, 58, 237)
    doc.setLineWidth(1.2)
    doc.line(margin, y, pageWidth - margin, y)
    y += 26

    const ensureSpace = (needed: number): void => {
      if (y + needed > pageHeight - margin) {
        doc.addPage()
        y = margin
      }
    }

    for (const subject of paperSubjects.value) {
      const subjQuestions = questions.value.filter(q => (q.subject_name || 'General') === subject)
      if (subjQuestions.length === 0) continue

      ensureSpace(34)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(13)
      doc.setTextColor(124, 58, 237)
      doc.text(subject, margin, y)
      doc.setTextColor(20, 20, 20)
      y += 20

      for (let i = 0; i < subjQuestions.length; i++) {
        const q = subjQuestions[i]

        doc.setFont('helvetica', 'bold')
        doc.setFontSize(11)
        const qLines = doc.splitTextToSize(`${i + 1}. ${q.question_text}`, contentWidth)
        ensureSpace(qLines.length * 14 + 6)
        doc.text(qLines, margin, y)
        y += qLines.length * 14 + 4

        // Diagram, if the question has one
        if (q.image_url) {
          try {
            const dataUrl = await imageUrlToDataUrl(mediaUrl(q.image_url))
            const dims = await getImageDimensions(dataUrl)
            const maxImgWidth = contentWidth * 0.6
            const scale = Math.min(1, maxImgWidth / dims.width)
            const imgW = dims.width * scale
            const imgH = dims.height * scale
            ensureSpace(imgH + 12)
            doc.addImage(dataUrl, dataUrlFormat(dataUrl), margin + 14, y, imgW, imgH)
            y += imgH + 12
          } catch {
            // Skip silently if the diagram can't be loaded — text still renders fine
          }
        }

        doc.setFont('helvetica', 'normal')
        doc.setFontSize(10.5)
        doc.setTextColor(50, 50, 50)
        if (q.options?.[0]) {
          const opts = [
            `(A) ${q.options[0].option_A}`,
            `(B) ${q.options[0].option_B}`,
            `(C) ${q.options[0].option_C}`,
            `(D) ${q.options[0].option_D}`,
          ]
          for (const opt of opts) {
            const optLines = doc.splitTextToSize(opt, contentWidth - 14)
            ensureSpace(optLines.length * 13)
            doc.text(optLines, margin + 14, y)
            y += optLines.length * 13
          }
        }
        doc.setTextColor(20, 20, 20)
        y += 14
      }
    }

    const fileName = `${paperTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')}.pdf`
    doc.save(fileName || 'question-paper.pdf')
  } catch (err) {
    console.error('Failed to generate question paper PDF', err)
    alert('Could not generate the PDF. Please try again.')
  } finally {
    isGeneratingPdf.value = false
  }
}

// Fetches an image URL and converts it to a base64 data URL, which jsPDF requires for addImage.
function imageUrlToDataUrl(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    fetch(url)
      .then(res => res.blob())
      .then(blob => {
        const reader = new FileReader()
        reader.onloadend = () => resolve(reader.result as string)
        reader.onerror = () => reject(new Error('Could not read image blob'))
        reader.readAsDataURL(blob)
      })
      .catch(reject)
  })
}

function getImageDimensions(dataUrl: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload  = () => resolve({ width: img.naturalWidth, height: img.naturalHeight })
    img.onerror = () => reject(new Error('Could not load image'))
    img.src = dataUrl
  })
}

// jsPDF's addImage needs the format ('PNG' | 'JPEG' | ...) to match the actual image type.
function dataUrlFormat(dataUrl: string): string {
  const match = dataUrl.match(/^data:image\/(\w+);base64,/)
  const ext = (match?.[1] ?? 'png').toUpperCase()
  return ext === 'JPG' ? 'JPEG' : ext
}

// ── TIME'S UP ──────────────────────────────────────────────────────
// Neither mode ever auto-submits straight to the report screen — the
// student always has to acknowledge a modal and press Submit first.
//   Test Mode: always the forced-submit modal, no extension offered.
//   Practice Mode: the FIRST time it runs out with questions still pending,
//     offer a one-time extension or an immediate submit. Once that
//     extension has been used (or there's nothing left unanswered), any
//     further expiry goes straight to the same forced-submit modal too.
function handleTimeUp(): void {
  stopTimer()
  if (store.mode === 'test') {
    showForcedSubmitModal.value = true
    return
  }
  if (!hasExtended.value && unansweredCount.value > 0) {
    showTimeUpModal.value = true
  } else {
    showForcedSubmitModal.value = true
  }
}

// Practice Mode only: adds more time, resumes the countdown, and uses up
// the one-time extension — if this extended time also runs out, handleTimeUp
// will go straight to the forced-submit modal instead of offering another one.
function extendTime(minutes: number): void {
  showTimeUpModal.value = false
  hasExtended.value = true
  const extraSeconds = minutes * 60
  timeLeft.value += extraSeconds
  totalAllottedSeconds += extraSeconds
  resumeCountdown()
}

// Practice Mode only: student chooses to submit instead of taking more time.
function submitNow(): void {
  showTimeUpModal.value = false
  submitTest()
}

// Test Mode, or Practice Mode with no extension left: the only way past
// the forced-submit modal — takes the student to the report screen.
function forceSubmit(): void {
  showForcedSubmitModal.value = false
  submitTest()
}

// ── TIMER: practice/chapter flow ──
// Practice Tests (chapter-wise or full-syllabus) have NO visible timer and
// no time limit — the student can take as long as they need. We still track
// elapsed time internally (for the results screen's "time taken" stat) using
// a simple count-up, but we never start a countdown and never trigger handleTimeUp.
function startChapterTimer(): void {
  // No countdown, no time limit for practice tests.
  // Start a silent count-up so timeTakenSeconds is accurate on submit.
  totalAllottedSeconds = 0  // no allotted limit
  timeLeft.value       = 0  // not displayed (showTimer is false)
  timerHandle = setInterval(() => {
    timeTakenSeconds.value++
  }, 1000)
}

// ── TIMER: custom test (uses durationMinutes from the custom config, own logic) ──
function startCustomTimer(): void {
  const minutes = store.customConfig?.durationMinutes ?? 0
  timeLeft.value = minutes * 60
  totalAllottedSeconds = timeLeft.value
  resumeCountdown()
}

function resetProgressState(): void {
  Object.keys(answers).forEach(k => delete answers[+k])
  Object.keys(marked).forEach(k => delete marked[+k])
  Object.keys(hintOpen).forEach(k => delete hintOpen[+k])
  Object.keys(checked).forEach(k => delete checked[+k])
  Object.keys(visited).forEach(k => delete visited[+k])
}

// Same fallback logic used in Createcustomtestview.vue's subjectQueryParams,
// kept in sync here so the custom-test question fetch resolves the same exam.
function customExamParams(): Record<string, string> | null {
  const examTypeId = store.examType?.id
  if (examTypeId && /^\d+$/.test(examTypeId)) return { exam_id: examTypeId }
  const examId = store.exam?.id
  if (examId && /^\d+$/.test(examId)) return { exam_id: examId }
  if (store.exam?.label) return { exam_category: store.exam.label }
  return null
}

async function loadCustomQuestions(): Promise<void> {
  const config = store.customConfig
  if (!config) { errorMsg.value = 'Custom test configuration missing.'; state.value = 'error'; return }

  const examParams = customExamParams()
  if (!examParams) {
    errorMsg.value = 'No exam selected — please go back and start again.'
    state.value    = 'error'
    return
  }

  try {
    const res = await api.get('/questions/custom/', {
      params: {
        ...examParams,
        subject_ids: config.subjectIds === 'all' ? 'all' : config.subjectIds.join(','),
        difficulty:  config.difficulty,
        count: config.numQuestions,
      }
    })
    // Safety net: the backend is expected to honor `count`, but if it doesn't
    // (returns every matching question instead of just `config.numQuestions`),
    // slice here so the UI never shows more questions than the user configured.
    // TODO: fix server-side — /questions/custom/ should apply `count` itself
    // (e.g. via a LIMIT/slice + shuffle before returning results).
    const fetched = res.data.questions as typeof questions.value
    questions.value    = fetched.slice(0, config.numQuestions)

    if (questions.value.length === 0) {
      errorMsg.value = 'No questions found for the selected subjects/difficulty. Please adjust your filters and try again.'
      state.value    = 'error'
      return
    }

    currentIndex.value = 0
    resetProgressState()
    state.value = 'active'
    markVisited(0)
    startCustomTimer()
  } catch {
    errorMsg.value = 'Failed to load questions. Please try again.'
    state.value    = 'error'
  }
}

async function loadChapterQuestions(): Promise<void> {
  // Store is primary source; URL query is a fallback (e.g. after a page refresh).
  const routeQuery  = router.currentRoute.value.query
  const chapterId   = store.chapter?.id ?? (routeQuery.chapter as string | undefined)
  const subjectId   = store.subject?.id ?? (routeQuery.subject as string | undefined)
  const scope       = store.scope ?? (routeQuery.scope as string | undefined)
  const mode        = store.mode ?? (routeQuery.mode as string | undefined) ?? 'test'

  // 'full' scope = Complete Syllabus Test — there's no chapter, only a subject.
  const isFullSyllabus = scope === 'full'

  if (!isFullSyllabus && !chapterId) {
    errorMsg.value = 'Chapter not selected. Please go back.'
    state.value    = 'error'
    return
  }
  if (isFullSyllabus && !subjectId) {
    errorMsg.value = 'Subject not selected. Please go back.'
    state.value    = 'error'
    return
  }

  try {
    // TODO: confirm with backend — assuming /questions/ accepts subject_id for
    // a full-syllabus pull the same way it accepts chapter_id for one chapter.
    const params = isFullSyllabus
      ? { subject_id: subjectId, scope: 'full', mode }
      : { chapter_id: chapterId, mode }
    const res = await api.get('/questions/', { params })
    questions.value    = res.data.questions
    currentIndex.value = 0
    resetProgressState()
    state.value = 'active'
    markVisited(0)
    startChapterTimer()  // both modes: 1 min per question; Test Mode ends on zero, Practice Mode offers an extension
  } catch {
    errorMsg.value = 'Failed to load questions. Please try again.'
    state.value    = 'error'
  }
}

async function loadQuestions(): Promise<void> {
  state.value = 'loading'

  if (store.customConfig) {
    await loadCustomQuestions()
  } else {
    await loadChapterQuestions()
  }
}

onMounted(loadQuestions)
onUnmounted(() => {
  stopTimer()
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  window.removeEventListener('resize', fitExamHeight)
})

const pageRoot = ref<HTMLElement | null>(null)

function fitExamHeight(): void {
  if (!pageRoot.value) return
  if (window.innerWidth <= 980) {
    pageRoot.value.style.height = ''
    return
  }
  const top = pageRoot.value.getBoundingClientRect().top
  pageRoot.value.style.height = `calc(100dvh - ${top}px)`
}

watch(
  () => state.value === 'active' && isCustomTestModeUI.value,
  (isExamActive) => {
    document.documentElement.style.overflow = isExamActive ? 'hidden' : ''
    document.body.style.overflow = isExamActive ? 'hidden' : ''
    if (isExamActive) {
      window.addEventListener('resize', fitExamHeight)
      nextTick(fitExamHeight)
    } else {
      window.removeEventListener('resize', fitExamHeight)
      if (pageRoot.value) pageRoot.value.style.height = ''
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.test-page { max-width: 1400px; margin: 0 auto; padding: 0 20px 40px; }

.test-page--exam {
  height: 100vh;
  height: 100dvh;
  padding-bottom: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.center-box {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 300px; gap: 14px; color: #6b7280;
}
.error-box { color: #ef4444; }
.spinner {
  width: 40px; height: 40px; border: 4px solid #e5e7eb;
  border-top-color: #7c3aed; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Top bar */
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 0;
}
.exit-link {
  background: none; border: none; cursor: pointer;
  user-select: none;
  font-weight: 700; font-size: 14px; color: #1e2536;
  display: flex; align-items: center; gap: 4px;
}
.chev { font-size: 18px; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.report-link {
  background: none; border: none; cursor: pointer;
  user-select: none;
  font-weight: 600; font-size: 13px; color: #1e2536;
  display: flex; align-items: center; gap: 6px;
}
.avatar {
  width: 32px; height: 32px; border-radius: 50%; background: #1e2536;
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 13px;
}

/* Header */
.test-header {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; border-radius: 12px; padding: 16px 20px;
  margin-bottom: 14px; border: 1px solid #f0f0f0;
}
.subject-name { font-size: 18px; font-weight: 800; color: #1e2536; margin: 0; }
.chapter-name { font-size: 13px; color: #6b7280; margin: 2px 0 0; }
.test-right { display: flex; align-items: center; gap: 16px; }
.mode-tag { font-size: 12px; font-weight: 700; padding: 6px 14px; border-radius: 20px; }
.mode-test     { background: #ede9fe; color: #6d28d9; }
.mode-practice { background: #d1fae5; color: #065f46; }

.timer-block { display: flex; align-items: center; gap: 8px; }
.timer-icon { font-size: 18px; color: #7c3aed; }
.timer-text { display: flex; flex-direction: column; line-height: 1.2; }
.timer-label { font-size: 11px; color: #9ca3af; }
.timer-value { font-size: 16px; font-weight: 800; color: #1e2536; font-variant-numeric: tabular-nums; }
.timer-value.warning { color: #ef4444; }

.btn-submit-top {
  background: #7c3aed; color: #fff; border: none; font-weight: 700;
  font-size: 13px; padding: 10px 20px; border-radius: 9px; cursor: pointer;
  user-select: none;
}

/* 3-column body */
.test-body {
  display: grid;
  grid-template-columns: 260px 1fr 260px;
  gap: 16px;
  align-items: start;
  position: relative;
}
@media (max-width: 980px) {
  .test-body { grid-template-columns: 1fr; }
}

.panel {
  background: #fff; border: 1px solid #f0f0f0; border-radius: 14px; padding: 18px;
}
.panel-title { font-size: 14px; font-weight: 800; color: #1e2536; margin: 0 0 12px; }

.palette-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* Answered / Unanswered / Marked filter tabs */
.tabs-row {
  display: flex; gap: 4px; border-bottom: 1px solid #f0f0f0; margin-bottom: 12px;
}
.tab-btn {
  background: none; border: none; cursor: pointer;
  user-select: none;
  padding: 8px 4px 10px; font-size: 12.5px; font-weight: 700; color: #9ca3af;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  white-space: nowrap;
}
.tab-btn .tab-count { font-weight: 600; }
.tab-btn.active { color: #10b981; border-bottom-color: #10b981; }

/* Question list */
.q-list {
  display: flex; flex-direction: column; gap: 8px;
  max-height: 520px; overflow-y: auto; padding-right: 2px;
}
.q-list-card {
  display: flex; align-items: flex-start; gap: 10px;
  border: 1.5px solid #f0f0f0; border-radius: 10px; background: #fff;
  padding: 10px 12px; text-align: left; cursor: pointer;
  user-select: none; width: 100%;
  transition: border-color 0.12s, background 0.12s;
}
.q-list-card:hover { border-color: #d1d5db; background: #fafafa; }
.q-list-current { border-color: #7c3aed; background: #f5f3ff; }

.q-list-num {
  flex-shrink: 0; width: 24px; height: 24px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11.5px; font-weight: 700; border: 1.5px solid #e5e7eb; color: #374151; background: #fff;
}

.q-list-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.q-list-title {
  font-size: 13px; font-weight: 600; color: #1e2536; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.q-list-sub {
  font-size: 11.5px; color: #9ca3af; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

.q-list-status { flex-shrink: 0; padding-top: 2px; }
.status-icon { display: inline-flex; align-items: center; justify-content: center; font-size: 13px; }
.status-answered { color: #10b981; font-weight: 800; }
.status-marked { color: #f59e0b; }
.status-unanswered {
  width: 14px; height: 14px; border-radius: 50%; border: 1.5px solid #d1d5db; display: inline-block;
}
.q-list-empty { font-size: 12.5px; color: #9ca3af; text-align: center; padding: 24px 0; }

.clear-filters-btn {
  margin-top: 12px; width: 100%;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  background: #fff; border: 1.5px solid #e5e7eb; border-radius: 9px;
  padding: 9px; font-size: 12.5px; font-weight: 700; color: #374151; cursor: pointer;
  user-select: none;
}
.clear-filters-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.clear-filters-btn:not(:disabled):hover { border-color: #d1d5db; background: #fafafa; }
.filter-icon { color: #6b7280; }

/* Right panel: quick-jump grid + legend + action buttons */
.qgrid {
  display: grid; gap: 6px; margin-bottom: 16px;
  width: 100%; box-sizing: border-box;
}
.qcell {
  aspect-ratio: 1; border-radius: 8px; border: 1.5px solid #e5e7eb; background: #fff;
  font-weight: 700; font-size: inherit; color: #374151; cursor: pointer;
  user-select: none;
}
/* Current question: outline only, doesn't override the underlying answered/marked color */
.cell-current        { background: #fff; border: 2px solid #7c3aed; color: #7c3aed; }
.cell-answered        { background: #10b981; border-color: #10b981; color: #fff; }
.cell-not-answered    { background: #f59e0b; border-color: #f59e0b; color: #fff; }
.cell-not-visited     { background: #fff; color: #374151; }
.cell-marked          { background: #7c3aed; border-color: #7c3aed; color: #fff; }
.cell-marked-answered { background: #7c3aed; border: 2px solid #10b981; color: #fff; }

.legend-title { font-size: 12.5px; font-weight: 700; color: #374151; margin-bottom: 8px; }
.legend-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px 10px;
  margin-bottom: 16px; font-size: 12px; color: #6b7280;
}
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-item-wide { grid-column: 1 / -1; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.dot-answered        { background: #10b981; }
.dot-not-answered    { background: #f59e0b; }
.dot-not-visited     { background: #fff; border: 1.5px solid #d1d5db; }
.dot-marked          { background: #7c3aed; }
.dot-marked-answered { background: #7c3aed; border: 2px solid #10b981; }

/* Quick action buttons: Question Paper / Pause / Submit */
.ov-actions { display: flex; flex-direction: column; gap: 8px; margin-bottom: 4px; }
.ov-action-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  border: none; border-radius: 9px; padding: 11px; cursor: pointer;
  user-select: none;
  font-weight: 700; font-size: 13px; color: #fff;
}
.ov-action-icon { font-size: 13px; }
.ov-action-paper  { background: #10b981; }
.ov-action-paper:hover  { background: #0ea472; }
.ov-action-pause  { background: #ef4444; }
.ov-action-pause:hover  { background: #dc2626; }
.ov-action-submit { background: #7c3aed; }
.ov-action-submit:hover { background: #6d28d9; }

/* Pause overlay */
.pause-overlay {
  position: absolute; inset: 0; z-index: 20;
  background: rgba(30, 37, 54, 0.55); border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  grid-column: 1 / -1;
}
.pause-card {
  background: #fff; border-radius: 14px; padding: 32px 36px; text-align: center;
  max-width: 320px; box-shadow: 0 20px 50px rgba(17, 17, 27, 0.3);
}
.pause-icon { font-size: 30px; display: block; margin-bottom: 8px; }
.pause-card h3 { margin: 0 0 8px; font-size: 16px; color: #1e2536; }
.pause-card p { margin: 0 0 18px; font-size: 12.5px; color: #6b7280; line-height: 1.5; }

/* Question Paper — full-screen view */
.paper-fullscreen {
  position: fixed; inset: 0; z-index: 100;
  background: #fff;
  display: flex; flex-direction: column;
}
.paper-box {
  width: 100%; height: 100%; max-width: none; max-height: none;
  display: flex; flex-direction: column;
  padding: 0;
}

.paper-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 32px; border-bottom: 1.5px solid #e5e7eb;
  flex-shrink: 0; background: #fff;
}
.paper-header-title { display: flex; align-items: center; gap: 10px; }
.paper-header-title .paper-tab-icon { font-size: 20px; }
.paper-header h3 { margin: 0; font-size: 19px; color: #1e2536; }
.paper-header-actions { display: flex; align-items: center; gap: 12px; }
.paper-header-actions .btn-secondary,
.paper-header-actions .btn-pdf {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 18px; border-radius: 9px; font-weight: 700; font-size: 13.5px;
}
.modal-close {
  border: none; background: #f3f4f6; color: #6b7280;
  width: 32px; height: 32px; border-radius: 50%;
  font-size: 17px; line-height: 1; cursor: pointer;
  user-select: none;
  display: flex; align-items: center; justify-content: center;
  margin-left: 4px;
}
.modal-close:hover { background: #e5e7eb; color: #1e2536; }

/* Subject tabs (Physics / Chemistry / Mathematics…) */
.paper-tabs {
  display: flex; gap: 10px; flex-wrap: wrap;
  padding: 16px 32px 0; flex-shrink: 0;
}
.paper-tab-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 24px; border: none; cursor: pointer;
  user-select: none;
  background: #f3f4f6; color: #374151; font-weight: 700; font-size: 14px;
  transition: background 0.15s, color 0.15s;
}
.paper-tab-btn:hover { background: #ede9fe; color: #6d28d9; }
.paper-tab-btn.active { background: #7c3aed; color: #fff; }
.paper-tab-icon { font-size: 14px; }

.paper-list {
  overflow-y: auto; flex: 1;
  padding: 20px 32px 40px;
  max-width: 900px; width: 100%; margin: 0 auto;
}
.paper-item {
  display: flex; gap: 14px;
  padding: 18px 0; border-bottom: 1px solid #f0f0f0;
}
.paper-item:last-child { border-bottom: none; }
.paper-q-num {
  flex-shrink: 0; width: 26px; height: 26px; border-radius: 6px;
  background: #ef4444; color: #fff; font-weight: 800; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
}
.paper-item-body { flex: 1; min-width: 0; }
.paper-q { margin: 0 0 10px; font-size: 14.5px; color: #1e2536; line-height: 1.55; }
.paper-opts { margin: 0; padding-left: 0; list-style: none; font-size: 13.5px; color: #374151; line-height: 2; }
.paper-q-diagram {
  margin: 0 0 12px; text-align: center; background: #f9fafb;
  border: 1.5px solid #e5e7eb; border-radius: 10px; padding: 10px;
}
.paper-q-diagram-img { max-width: 100%; max-height: 220px; object-fit: contain; border-radius: 6px; }

.btn-pdf { display: inline-flex; align-items: center; gap: 8px; background: #10b981; color: #fff; border: none; cursor: pointer;
  user-select: none; }
.btn-pdf:hover:not(:disabled) { background: #0ea472; }
.btn-pdf:disabled { background: #d1d5db; cursor: not-allowed; }
.pdf-icon { font-size: 13px; }
.pdf-spinner {
  width: 13px; height: 13px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.5); border-top-color: #fff;
  animation: pdf-spin 0.7s linear infinite;
}
@keyframes pdf-spin { to { transform: rotate(360deg); } }

@media print {
  .paper-fullscreen { position: static; background: none; }
  .paper-header-actions, .paper-tabs { display: none; }
  .paper-list { max-width: none; padding: 0; }
}

/* Question panel */
.q-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.q-count { font-size: 14px; font-weight: 700; color: #1e2536; }
.mark-link {
  background: none; border: none; cursor: pointer;
  user-select: none; color: #7c3aed;
  font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 5px;
}
.bm-icon { font-size: 14px; }

.q-meta { margin-bottom: 8px; }
.diff-badge { font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 20px; text-transform: capitalize; }
.easy   { background: #d1fae5; color: #065f46; }
.medium { background: #fef3c7; color: #92400e; }
.hard   { background: #fce7f3; color: #9d174d; }

.q-text { font-size: 16px; font-weight: 600; color: #1e2536; margin: 0 0 20px; line-height: 1.55; }

/* Question diagram */
.q-diagram {
  margin: 0 0 20px;
  text-align: center;
  background: #f9fafb;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
}
.q-diagram-img {
  max-width: 100%;
  max-height: 320px;
  object-fit: contain;
  border-radius: 6px;
}

/* Diagram inside result card */
.ri-diagram { margin: 6px 0; text-align: center; }
.ri-diagram-img { max-width: 100%; max-height: 160px; object-fit: contain; border-radius: 6px; border: 1px solid #e5e7eb; }

.options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.option-btn {
  display: flex; align-items: center; gap: 12px;
  background: #fafafa; border: 1.5px solid #e5e7eb; border-radius: 10px;
  padding: 12px 16px; cursor: pointer;
  user-select: none; text-align: left;
  font-size: 14px; color: #1e2536; transition: border-color 0.15s, background 0.15s;
}
.option-btn:hover:not(:disabled) { border-color: #c4b5fd; background: #f5f3ff; }
.opt-radio {
  width: 18px; height: 18px; border-radius: 50%; border: 2px solid #d1d5db; flex-shrink: 0;
}
.opt-radio.on { border-color: #7c3aed; background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%); }
.opt-key { font-weight: 700; }
.opt-text { flex: 1; }
.opt-selected { border-color: #7c3aed; background: #f5f3ff; }
.opt-correct  { border-color: #10b981; background: #ecfdf5; }
.opt-wrong    { border-color: #ef4444; background: #fef2f2; }

.hint-check-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px; gap: 12px;
}
.hint-check-actions { display: flex; align-items: center; gap: 10px; margin-left: auto; }
.hint-btn {
  background: #ede9fe; border: none; color: #6d28d9; font-weight: 700;
  font-size: 13px; padding: 9px 16px; border-radius: 9px; cursor: pointer;
  user-select: none;
  display: inline-flex; align-items: center; gap: 6px;
}
.btn-skip {
  background: #fff; color: #6b7280; border: 1.5px solid #e5e7eb; font-weight: 700;
  font-size: 13px; padding: 9px 16px; border-radius: 9px; cursor: pointer;
  user-select: none;
}
.btn-skip:hover { border-color: #c4b5fd; color: #6d28d9; }
.hint-box {
  margin-top: 0; margin-bottom: 16px; padding: 10px 14px; background: #ede9fe;
  border-left: 3px solid #7c3aed; border-radius: 8px;
  font-size: 13px; color: #374151;
}

.btn-check {
  background: #7c3aed; color: #fff; border: none; font-weight: 700;
  font-size: 13px; padding: 10px 20px; border-radius: 9px; cursor: pointer;
  user-select: none;
}
.btn-check:disabled { background: #d1d5db; color: #9ca3af; cursor: not-allowed; }

.explanation-box { margin-top: 6px; margin-bottom: 16px; display: flex; flex-direction: column; gap: 8px; }
.correct-label { font-size: 13px; font-weight: 600; color: #065f46; }
.verdict-label { font-size: 14px; font-weight: 700; }
.verdict-correct { color: #10b981; }
.verdict-wrong { color: #ef4444; }
.explanation {
  padding: 12px 14px; background: #fef9c3;
  border-left: 3px solid #f59e0b; border-radius: 8px;
  font-size: 13px; color: #374151; line-height: 1.5;
}

.q-footer { display: flex; justify-content: space-between; padding-top: 8px; border-top: 1px solid #f0f0f0; }
.btn-primary, .btn-secondary {
  padding: 10px 22px; border-radius: 9px; font-weight: 700; font-size: 13px; cursor: pointer;
  user-select: none; border: none;
}
.btn-primary        { background: #7c3aed; color: #fff; }
.btn-secondary      { background: #fff; color: #1e2536; border: 1.5px solid #e5e7eb; }
.btn-submit-footer  { background: #10b981; color: #fff; border: none; padding: 10px 22px; border-radius: 9px; font-weight: 700; font-size: 13px; cursor: pointer;
  user-select: none; }
.btn-primary:disabled, .btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }

/* Overview panel */
.ov-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 13px; color: #374151; }
.ov-divider { border: none; border-top: 1px solid #f0f0f0; margin: 8px 0; }
.c-green { color: #10b981; }
.c-orange { color: #f59e0b; }
.c-gray { color: #6b7280; }
.c-red { color: #ef4444; }

/* Modals */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 50;
}
.modal-box {
  background: #fff; border-radius: 14px; padding: 22px; width: 380px; max-width: 90vw;
}
.modal-box h3 { margin: 0 0 6px; font-size: 16px; color: #1e2536; }
.modal-sub { font-size: 13px; color: #6b7280; margin: 0 0 14px; }
.modal-box textarea {
  width: 100%; border: 1.5px solid #e5e7eb; border-radius: 8px; padding: 10px;
  font-size: 13px; resize: vertical; margin-bottom: 14px; font-family: inherit;
}
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }

/* Results (chapter/practice flow) */
.results-wrap { padding: 20px 0; max-width: 780px; margin: 0 auto; }
.score-circle {
  width: 110px; height: 110px; border-radius: 50%; border: 5px solid;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  margin: 0 auto 18px;
}
.score-high { border-color: #10b981; background: #ecfdf5; color: #065f46; }
.score-mid  { border-color: #f59e0b; background: #fef3c7; color: #92400e; }
.score-low  { border-color: #ef4444; background: #fef2f2; color: #991b1b; }
.score-num  { font-size: 22px; font-weight: 800; }
.score-pct  { font-size: 13px; font-weight: 600; }
.result-title { text-align: center; font-size: 18px; font-weight: 700; margin: 0 0 24px; }

.result-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.result-item { background: #fff; border-radius: 12px; padding: 16px; border: 1.5px solid; }
.result-item.correct { border-color: #10b981; }
.result-item.wrong   { border-color: #ef4444; }
.ri-top { display: flex; justify-content: space-between; margin-bottom: 6px; }
.ri-num { font-size: 12px; color: #6b7280; font-weight: 700; }
.ri-verdict { font-size: 12px; font-weight: 700; }
.result-item.correct .ri-verdict { color: #10b981; }
.result-item.wrong   .ri-verdict { color: #ef4444; }
.ri-q   { font-size: 14px; color: #1e2536; font-weight: 600; margin: 0 0 6px; }
.ri-ans { font-size: 12px; color: #6b7280; margin: 0 0 4px; }
.ri-exp { font-size: 12px; color: #374151; background: #fef9c3; padding: 8px; border-radius: 6px; margin: 6px 0 0; }
.ri-hint { font-size: 12px; color: #374151; background: #ede9fe; padding: 8px; border-radius: 6px; margin: 4px 0 0; }
.result-footer { display: flex; justify-content: center; gap: 14px; }
.btn-secondary { background: #fff; border: 1.5px solid #e5e7eb; color: #1e2536; font-weight: 700; font-size: 13px; padding: 10px 22px; border-radius: 9px; cursor: pointer;
  user-select: none; }
.btn-primary { background: #7c3aed; border: none; color: #fff; font-weight: 700; font-size: 13px; padding: 10px 22px; border-radius: 9px; cursor: pointer;
  user-select: none; }

/* ══════════════════════════════════════════════════════════════════
   Custom Test — Test Mode exam-style UI (ct-*)
   Kept fully separate from the chapter-practice styles above so
   nothing there is affected by these changes.
   ══════════════════════════════════════════════════════════════════ */
.ct-shell {
  position: relative;
  padding-top: 6px;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* Top bar */
.ct-topbar {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; border: 1px solid #f0f0f0; border-radius: 12px;
  padding: 12px 20px; margin-bottom: 12px;
  flex-shrink: 0;
}
.ct-brand { display: flex; align-items: center; gap: 10px; }
.ct-logo {
  width: 30px; height: 30px; border-radius: 9px; background: #7c3aed;
  color: #fff; font-weight: 800; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ct-brand-name { font-weight: 800; color: #1e2536; font-size: 15px; }
.ct-test-title { font-size: 14px; color: #6b7280; padding-left: 10px; border-left: 1px solid #e5e7eb; }

.ct-topbar-actions { display: flex; align-items: center; gap: 12px; }
.ct-pause-btn {
  display: flex; align-items: center; gap: 6px;
  background: #fff; border: 1.5px solid #e5e7eb; color: #1e2536;
  font-weight: 700; font-size: 13px; padding: 9px 16px; border-radius: 9px; cursor: pointer;
  user-select: none;
}
.ct-icon { font-size: 13px; }
.ct-info-box {
  display: flex; align-items: center; gap: 8px;
  background: #f9fafb; border: 1px solid #f0f0f0; border-radius: 9px;
  padding: 6px 14px;
}
.ct-info-icon { font-size: 16px; color: #7c3aed; }
.ct-info-text { display: flex; flex-direction: column; line-height: 1.2; }
.ct-info-label { font-size: 10.5px; color: #9ca3af; font-weight: 600; }
.ct-info-value { font-size: 14px; font-weight: 800; color: #1e2536; font-variant-numeric: tabular-nums; }
.ct-info-value.warning { color: #ef4444; }
.ct-end-btn {
  background: #fff; border: 1.5px solid #ef4444; color: #ef4444;
  font-weight: 700; font-size: 13px; padding: 9px 18px; border-radius: 9px; cursor: pointer;
  user-select: none;
}
.ct-end-btn:hover { background: #fef2f2; }

/* Subject bar */
.ct-subjectbar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px; gap: 12px; flex-wrap: wrap;
  flex-shrink: 0;
}
.ct-subject-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.ct-subject-tab {
  background: #fff; border: 1.5px solid #e5e7eb; color: #374151;
  font-weight: 700; font-size: 13.5px; padding: 10px 18px; border-radius: 10px;
  cursor: pointer; user-select: none;
}
.ct-subject-tab.active { background: #7c3aed; border-color: #7c3aed; color: #fff; }
.ct-download-btn {
  display: flex; align-items: center; gap: 6px;
  background: #fff; border: 1.5px solid #e5e7eb; color: #1e2536;
  font-weight: 700; font-size: 13px; padding: 9px 16px; border-radius: 9px; cursor: pointer;
  user-select: none;
}

/* 3-column body */
.ct-body {
  display: grid; grid-template-columns: 260px 1fr 300px; gap: 16px;
  align-items: stretch; position: relative;
  flex: 1;
  min-height: 0;
}
@media (max-width: 980px) {
  .ct-body { grid-template-columns: 1fr; flex: none; }
  .test-page--exam { overflow-y: auto; height: auto; min-height: 100vh; min-height: 100dvh; }
  .ct-panel { height: auto; overflow-y: visible; }
  .ct-question { overflow: visible; }
  .ct-question-scroll { overflow-y: visible; flex: none; }
}

.ct-panel {
  background: #fff; border: 1px solid #f0f0f0; border-radius: 14px; padding: 18px;
  height: 100%;
  overflow: hidden;
}
.ct-panel-title { font-size: 14.5px; font-weight: 800; color: #1e2536; display: flex; align-items: center; gap: 6px; }
.ct-title-icon { font-size: 15px; }

/* Left: progress */
.ct-progress-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.ct-overall-badge {
  font-size: 11.5px; font-weight: 700; color: #065f46; background: #d1fae5;
  padding: 4px 10px; border-radius: 20px;
}
.ct-ring-wrap { position: relative; width: 130px; height: 130px; margin: 0 auto 4px; }
.ct-ring { width: 100%; height: 100%; transform: rotate(-90deg); }
.ct-ring-bg { fill: none; stroke: #f0f0f0; stroke-width: 10; }
.ct-ring-fg { fill: none; stroke: #10b981; stroke-width: 10; stroke-linecap: round; transition: stroke-dashoffset 0.3s; }
.ct-ring-center {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.ct-ring-pct { font-size: 20px; font-weight: 800; color: #1e2536; }
.ct-ring-label { font-size: 11px; color: #9ca3af; }
.ct-solved-line { text-align: center; font-size: 13px; color: #6b7280; margin: 4px 0 18px; }

.ct-status-title, .ct-subject-overview-title {
  font-size: 11.5px; font-weight: 800; color: #9ca3af; text-transform: uppercase;
  letter-spacing: 0.02em; margin-bottom: 10px;
}
.ct-status-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 20px;
}
.ct-status-cell {
  background: #f9fafb; border-radius: 10px; padding: 10px; text-align: center;
}
.ct-status-num { display: block; font-size: 18px; font-weight: 800; color: #1e2536; }
.ct-status-label { font-size: 11px; color: #6b7280; }
.ct-status-orange { color: #f59e0b; }
.ct-status-green  { color: #10b981; }
.ct-status-purple { color: #7c3aed; }
.ct-status-red    { color: #ef4444; }

.ct-subject-overview { margin-bottom: 4px; }
.ct-so-row {
  display: flex; justify-content: space-between; padding: 8px 0;
  font-size: 13.5px; font-weight: 700; color: #1e2536;
  border-bottom: 1px solid #f5f5f5;
}
.ct-so-row:last-child { border-bottom: none; }

/* Center: question card */
.ct-question {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.ct-question-scroll {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding-right: 2px;
}
.ct-question .q-top { margin-bottom: 14px; }
.ct-options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px; }
.ct-option-btn {
  display: flex; align-items: center; gap: 14px;
  background: #fafafa; border: 1.5px solid #e5e7eb; border-radius: 10px;
  padding: 12px 16px; cursor: pointer; user-select: none; text-align: left;
  font-size: 14px; color: #1e2536; transition: border-color 0.15s, background 0.15s;
}
.ct-option-btn:hover { border-color: #c4b5fd; background: #f5f3ff; }
.ct-option-selected { border-color: #7c3aed; background: #f5f3ff; }
.ct-opt-avatar {
  width: 30px; height: 30px; border-radius: 50%; background: #f0f0f0; color: #374151;
  font-weight: 700; font-size: 13px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ct-option-selected .ct-opt-avatar { background: #7c3aed; color: #fff; }
.ct-opt-text { flex: 1; }
.ct-opt-radio { width: 18px; height: 18px; border-radius: 50%; border: 2px solid #d1d5db; flex-shrink: 0; }
.ct-opt-radio.on { border-color: #7c3aed; background: radial-gradient(circle, #7c3aed 0 40%, transparent 41%); }

.ct-footer {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  padding-top: 12px; margin-top: 12px; border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.ct-footer .btn-secondary,
.ct-footer .ct-btn-mark,
.ct-footer .ct-btn-skip-next,
.ct-footer .btn-submit-footer {
  flex: 0 0 auto;
  min-width: 0;
  white-space: nowrap;
  padding: 8px 14px;
  font-size: 12.5px;
  overflow: visible;
  text-overflow: unset;
  justify-content: center;
}
.ct-btn-mark {
  display: flex; align-items: center; gap: 5px;
  background: #ede9fe; color: #6d28d9; border: none; font-weight: 700;
  font-size: 12.5px; padding: 8px 14px; border-radius: 8px; cursor: pointer;
  user-select: none;
  margin-left: auto;
}
.ct-btn-skip-next {
  background: #1e2536; color: #fff; border: none; font-weight: 700;
  font-size: 12.5px; padding: 8px 16px; border-radius: 8px; cursor: pointer;
  user-select: none;
}
@media (max-width: 640px) {
  .ct-footer { gap: 6px; justify-content: flex-end; }
  .ct-footer .btn-secondary,
  .ct-footer .ct-btn-mark,
  .ct-footer .ct-btn-skip-next,
  .ct-footer .btn-submit-footer {
    font-size: 11px;
    padding: 7px 10px;
  }
  .ct-btn-mark { margin-left: 0; }
  .ct-footer .btn-secondary:nth-child(2) { margin-right: auto; }
}

/* Right: question overview */
.ct-ov-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.ct-collapse-btn { background: none; border: none; cursor: pointer; font-size: 14px; color: #6b7280; }
.ct-ov-tabs {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;
  background: #f5f3ff; border-radius: 10px; padding: 4px; margin-bottom: 12px;
}
.ct-ov-tab {
  background: none; border: none; cursor: pointer; user-select: none;
  font-size: 12px; font-weight: 700; color: #6b7280; padding: 8px 4px; border-radius: 8px;
}
.ct-ov-tab.active { background: #fff; color: #6d28d9; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }

.ct-subj-filter { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 16px; }
.ct-subj-filter-btn {
  background: #f9fafb; border: 1px solid #e5e7eb; color: #374151;
  font-size: 11.5px; font-weight: 700; padding: 5px 12px; border-radius: 20px;
  cursor: pointer; user-select: none;
}
.ct-subj-filter-btn.active { background: #1e2536; border-color: #1e2536; color: #fff; }

.ct-qn-title { font-size: 12.5px; font-weight: 700; color: #374151; margin-bottom: 10px; }
.ct-qn-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(38px, 1fr));
  gap: 8px; margin-bottom: 18px;
}
.ct-qn-cell {
  aspect-ratio: 1; border-radius: 8px; border: 1.5px solid #e5e7eb;
  background: #fff; font-size: 13px; font-weight: 700; cursor: pointer; user-select: none;
}
</style>