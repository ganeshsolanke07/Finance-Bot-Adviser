/* ========================================================
   Personal Finance Advisor Bot - Interactive JavaScript
   ======================================================== */

// Global Chart instances
let categoryChartInstance = null;
let comparisonChartInstance = null;

/**
 * Initialize Dashboard Chart.js Visualizations
 */
function initDashboardCharts(data) {
    if (!data) return;

    // Palette of attractive modern colors for categories
    const categoryPalette = [
        '#f97316', // Food - Orange
        '#6366f1', // Rent - Indigo
        '#3b82f6', // Transport - Blue
        '#a855f7', // Education - Purple
        '#10b981', // Healthcare - Emerald
        '#ec4899', // Shopping - Pink
        '#8b5cf6', // Entertainment - Violet
        '#14b8a6', // Bills - Teal
        '#64748b'  // Other - Slate
    ];

    // 1. Category Breakdown Doughnut Chart
    const catCanvas = document.getElementById('categoryChart');
    if (catCanvas && data.categories) {
        const ctxCat = catCanvas.getContext('2d');
        if (categoryChartInstance) {
            categoryChartInstance.destroy();
        }

        categoryChartInstance = new Chart(ctxCat, {
            type: 'doughnut',
            data: {
                labels: data.categories.labels,
                datasets: [{
                    data: data.categories.values,
                    backgroundColor: categoryPalette.slice(0, data.categories.labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            font: { family: 'Plus Jakarta Sans', size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const val = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: $${val.toLocaleString()} (${pct}%)`;
                            }
                        }
                    }
                },
                cutout: '68%'
            }
        });
    }

    // 2. Income vs Expenses Bar Chart
    const compCanvas = document.getElementById('comparisonChart');
    if (compCanvas) {
        const ctxComp = compCanvas.getContext('2d');
        if (comparisonChartInstance) {
            comparisonChartInstance.destroy();
        }

        comparisonChartInstance = new Chart(ctxComp, {
            type: 'bar',
            data: {
                labels: ['Income', 'Expenses', 'Savings'],
                datasets: [{
                    label: 'Amount ($)',
                    data: [data.income, data.expenses, data.savings],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.85)', // Income - Green
                        'rgba(239, 68, 68, 0.85)',   // Expenses - Red
                        'rgba(59, 130, 246, 0.85)'   // Savings - Blue
                    ],
                    borderColor: ['#10b981', '#ef4444', '#3b82f6'],
                    borderWidth: 1.5,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return ` $${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: {
                            callback: function (val) {
                                return '$' + val.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }
}

/**
 * Initialize AI Financial Advisor Chat Engine
 */
function initAdvisorChat(defaultMonth) {
    const chatForm = document.getElementById('advisorChatForm');
    const userInput = document.getElementById('userInput');
    const chatContainer = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const analysisBtn = document.getElementById('generateAnalysisBtn');
    const promptChips = document.querySelectorAll('.prompt-chip');

    // Scroll helper
    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    // Append User Message Bubble
    function appendUserMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message user mb-3';
        msgDiv.innerHTML = `
            <div class="message-bubble p-3 shadow-sm">
                <p class="mb-0">${escapeHtml(text)}</p>
            </div>
        `;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    // Append Typing Indicator
    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.id = id;
        typingDiv.className = 'chat-message bot mb-3';
        typingDiv.innerHTML = `
            <div class="d-flex gap-2">
                <div class="avatar-small bg-warning text-dark rounded-circle d-flex align-items-center justify-content-center flex-shrink-0">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-bubble bg-light text-dark p-3 rounded-4 shadow-sm border typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatContainer.appendChild(typingDiv);
        scrollToBottom();
        return id;
    }

    // Append Bot Message Bubble (with basic Markdown formatting)
    function appendBotMessage(markdownText) {
        const formatted = parseMarkdown(markdownText);
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message bot mb-3';
        msgDiv.innerHTML = `
            <div class="d-flex gap-2">
                <div class="avatar-small bg-warning text-dark rounded-circle d-flex align-items-center justify-content-center flex-shrink-0">
                    <i class="bi bi-robot"></i>
                </div>
                <div class="message-bubble bg-light text-dark p-3 rounded-4 shadow-sm border">
                    ${formatted}
                </div>
            </div>
        `;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    // Send Message to Server
    function sendMessage(message) {
        if (!message.trim()) return;

        appendUserMessage(message);
        userInput.value = '';
        const typingId = showTypingIndicator();

        fetch('/api/advisor/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                month: defaultMonth
            })
        })
        .then(res => {
            if (!res.ok) throw new Error('Network error');
            return res.json();
        })
        .then(data => {
            const typingElem = document.getElementById(typingId);
            if (typingElem) typingElem.remove();
            appendBotMessage(data.reply);
        })
        .catch(err => {
            const typingElem = document.getElementById(typingId);
            if (typingElem) typingElem.remove();
            appendBotMessage("⚠️ Sorry, I encountered an issue connecting to the financial advisor service. Please check your connection or `.env` configuration.");
            console.error(err);
        });
    }

    // Form submit
    if (chatForm) {
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            sendMessage(userInput.value);
        });
    }

    // Quick Prompt Chips
    promptChips.forEach(chip => {
        chip.addEventListener('click', function () {
            const prompt = this.getAttribute('data-prompt');
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    // Auto Full Analysis Button
    if (analysisBtn) {
        analysisBtn.addEventListener('click', function () {
            appendUserMessage("Generate full monthly spending analysis and saving recommendations.");
            const typingId = showTypingIndicator();

            fetch('/api/advisor/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ month: defaultMonth })
            })
            .then(res => res.json())
            .then(data => {
                const typingElem = document.getElementById(typingId);
                if (typingElem) typingElem.remove();
                appendBotMessage(data.analysis);
            })
            .catch(err => {
                const typingElem = document.getElementById(typingId);
                if (typingElem) typingElem.remove();
                appendBotMessage("Failed to generate comprehensive analysis. Please try again.");
                console.error(err);
            });
        });
    }

    // Reset Chat Button
    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', function () {
            while (chatContainer.children.length > 1) {
                chatContainer.removeChild(chatContainer.lastChild);
            }
        });
    }
}

/**
 * Simple client-side Markdown to HTML converter
 */
function parseMarkdown(md) {
    if (!md) return '';
    let html = md
        // Headers
        .replace(/^### (.*$)/gim, '<h6 class="fw-bold mt-2 mb-1 text-primary">$1</h6>')
        .replace(/^## (.*$)/gim, '<h5 class="fw-bold mt-2 mb-1">$1</h5>')
        .replace(/^# (.*$)/gim, '<h4 class="fw-bold mt-2 mb-1">$1</h4>')
        // Bold & Italic
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Blockquotes
        .replace(/^\> (.*$)/gim, '<blockquote class="border-start border-3 border-primary ps-2 text-muted my-2">$1</blockquote>')
        // Unordered lists
        .replace(/^\s*-\s+(.*$)/gim, '<li class="mb-1">$1</li>')
        // Paragraph line breaks
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');

    // Wrap loose <li> in <ul>
    if (html.includes('<li>')) {
        html = html.replace(/(<li.*<\/li>)/s, '<ul class="ps-3 mb-2">$1</ul>');
    }

    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
