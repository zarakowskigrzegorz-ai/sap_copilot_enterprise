// =========================================================================
// MODUŁ 1: AUTH, LOCK SCREEN (PIN / FACE ID), AUDIO FX, ONBOARDING & THEME
// =========================================================================

let currentPin = "";
const VALID_PINS = ["1234", "2026"];
let isLocked = true;
let audioCtx = null;

function getAudioContext() {
    if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
            audioCtx = new AudioContextClass();
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

// Subtelny klik klawiatury numerycznej (styl iOS Taptic Tap)
function playKeyTapSound(digit = 5) {
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        const baseFreq = 520 + (parseInt(digit, 10) || 0) * 18;
        osc.type = 'sine';
        osc.frequency.setValueAtTime(baseFreq, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(160, ctx.currentTime + 0.045);

        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.045);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 0.05);
    } catch (e) {}
}

// Przyjemny akord odblokowania (styl Apple Pay / Face ID Success Chime)
function playUnlockChime() {
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;

        const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        notes.forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            const startTime = now + idx * 0.055;

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, startTime);

            gain.gain.setValueAtTime(0.001, startTime);
            gain.gain.linearRampToValueAtTime(0.11, startTime + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0008, startTime + 0.38);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(startTime);
            osc.stop(startTime + 0.4);
        });
    } catch (e) {}
}

// Dźwięk błędu autoryzacji (podwójny niski puls iOS Error)
function playErrorBuzz() {
    try {
        const ctx = getAudioContext();
        if (!ctx) return;
        const now = ctx.currentTime;

        [0, 0.12].forEach(offset => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            const start = now + offset;

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(155, start);
            osc.frequency.linearRampToValueAtTime(120, start + 0.09);

            gain.gain.setValueAtTime(0.09, start);
            gain.gain.exponentialRampToValueAtTime(0.001, start + 0.095);

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.start(start);
            osc.stop(start + 0.1);
        });
    } catch (e) {}
}

function initLockScreen() {
    const unlockedSession = sessionStorage.getItem('sap_copilot_unlocked');
    const lockEl = document.getElementById('ios-lock-screen');
    if (unlockedSession === 'true' && lockEl) {
        isLocked = false;
        lockEl.style.display = 'none';
        checkFirstTimeOnboarding();
    } else {
        isLocked = true;
    }

    document.addEventListener('keydown', (e) => {
        if (!isLocked) return;
        if (e.key >= '0' && e.key <= '9') {
            enterPin(e.key);
        } else if (e.key === 'Backspace' || e.key === 'Escape') {
            clearPin();
        } else if (e.key === 'Enter') {
            triggerFaceID();
        }
    });
}

function enterPin(digit) {
    if (!isLocked || currentPin.length >= 4) return;
    playKeyTapSound(digit);
    currentPin += String(digit);
    updatePinDots();

    if (currentPin.length === 4) {
        setTimeout(verifyPin, 120);
    }
}

function clearPin() {
    playKeyTapSound(0);
    currentPin = currentPin.length > 0 ? currentPin.slice(0, -1) : "";
    updatePinDots();
}

function updatePinDots(state = 'normal') {
    const dots = document.querySelectorAll('#pin-dots-container .ios-pin-dot');
    dots.forEach((dot, idx) => {
        dot.classList.remove('filled', 'error', 'success');
        if (state === 'error') {
            dot.classList.add('error');
        } else if (state === 'success') {
            dot.classList.add('success');
        } else if (idx < currentPin.length) {
            dot.classList.add('filled');
        }
    });
}

function verifyPin() {
    const dotsContainer = document.getElementById('pin-dots-container');
    if (VALID_PINS.includes(currentPin)) {
        updatePinDots('success');
        playUnlockChime();
        setTimeout(unlockApp, 220);
    } else {
        updatePinDots('error');
        playErrorBuzz();
        if (dotsContainer) {
            dotsContainer.classList.remove('apple-shake');
            void dotsContainer.offsetWidth;
            dotsContainer.classList.add('apple-shake');
        }
        setTimeout(() => {
            currentPin = "";
            updatePinDots('normal');
        }, 550);
    }
}

function triggerFaceID() {
    if (!isLocked) return;
    playKeyTapSound(8);
    const hud = document.getElementById('face-id-hud');
    const icon = document.getElementById('face-id-icon');
    const text = document.getElementById('face-id-status') || document.getElementById('face-id-text');

    if (hud) {
        hud.classList.add('show');
        if (text) text.textContent = "Weryfikacja Face ID...";
        if (icon) icon.style.color = "#60a5fa";

        setTimeout(() => {
            updatePinDots('success');
            playUnlockChime();
            if (icon) icon.style.color = "#34c759";
            if (text) text.textContent = "Autoryzowano: Senior SAP SD Consultant";
        }, 550);

        setTimeout(() => {
            hud.classList.remove('show');
            unlockApp();
        }, 1050);
    } else {
        playUnlockChime();
        unlockApp();
    }
}

function unlockApp() {
    isLocked = false;
    sessionStorage.setItem('sap_copilot_unlocked', 'true');
    const lockEl = document.getElementById('ios-lock-screen');
    if (lockEl) {
        lockEl.classList.add('unlocked');
        setTimeout(() => {
            lockEl.style.display = 'none';
            checkFirstTimeOnboarding();
        }, 380);
    }
    showToast("🔓 Odblokowano sesję SAP SD Enterprise Copilot");
}

function checkFirstTimeOnboarding() {
    const welcomeDismissed = sessionStorage.getItem('sap_copilot_welcome_seen');
    if (!welcomeDismissed) {
        setTimeout(() => {
            openWelcomeOnboardingModal();
        }, 250);
    }
}

function openWelcomeOnboardingModal() {
    const modal = document.getElementById('modal-welcome-onboarding');
    if (modal) modal.classList.remove('hidden');
}

function handleWelcomeAcknowledge() {
    sessionStorage.setItem('sap_copilot_welcome_seen', 'true');
    const modal = document.getElementById('modal-welcome-onboarding');
    if (modal) modal.classList.add('hidden');

    const editBtn = document.getElementById('btn-edit-profile');
    if (editBtn) {
        editBtn.classList.add('btn-profile-glow');
        showToast("👉 Kliknij podświetlony przycisk u góry, aby uzupełnić lub zaimportować dane firmy");
    }
}

function lockApp() {
    isLocked = true;
    currentPin = "";
    sessionStorage.removeItem('sap_copilot_unlocked');
    updatePinDots('normal');
    const lockEl = document.getElementById('ios-lock-screen');
    if (lockEl) {
        lockEl.style.display = 'flex';
        requestAnimationFrame(() => {
            lockEl.classList.remove('unlocked');
        });
    }
}

async function handleLockCompanySelect(companyId) {
    if (!companyId) return;
    await handleCompanyChange(companyId);
}

// --- DARK / LIGHT MODE (iOS Appearance) ---
function initTheme() {
    const savedTheme = localStorage.getItem('sap_copilot_theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        const btn = document.getElementById('btn-theme-toggle');
        if (btn) btn.textContent = '☀️';
    }
}

function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('sap_copilot_theme', isDark ? 'dark' : 'light');
    const btn = document.getElementById('btn-theme-toggle');
    if (btn) {
        btn.textContent = isDark ? '☀️' : '🌙';
    }
    showToast(isDark ? '🌙 Włączono tryb ciemny (iOS Dark)' : '☀️ Włączono tryb jasny (iOS Light)');
}

// Aliasy dla atrybutów HTML w index.html
const handleKeypadPress = enterPin;
const handleKeypadDelete = clearPin;
const triggerFaceIdAuth = triggerFaceID;
const playUnlockSuccess = playUnlockChime;

// Eksport globalny dla atrybutów inline HTML
window.enterPin = enterPin;
window.clearPin = clearPin;
window.triggerFaceID = triggerFaceID;
window.handleKeypadPress = handleKeypadPress;
window.handleKeypadDelete = handleKeypadDelete;
window.triggerFaceIdAuth = triggerFaceIdAuth;
window.playUnlockSuccess = playUnlockSuccess;
window.lockApp = lockApp;
window.handleLockCompanySelect = handleLockCompanySelect;
window.openWelcomeOnboardingModal = openWelcomeOnboardingModal;
window.handleWelcomeAcknowledge = handleWelcomeAcknowledge;
window.toggleDarkMode = toggleDarkMode;
window.initTheme = initTheme;
window.initLockScreen = initLockScreen;
