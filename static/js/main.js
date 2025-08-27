// main.js - Custom JS for FinTrack

// ===============================
// DARK MODE TOGGLE FUNCTIONALITY (using [data-theme="dark"])
// ===============================

/**
 * Toggles dark mode by setting the data-theme attribute on <body>.
 * Persists user preference in localStorage and updates toggle button.
 */
function toggleDarkMode() {
    const isDark = document.body.getAttribute('data-theme') === 'dark';
    if (isDark) {
        document.body.removeAttribute('data-theme'); // Switch to light
        localStorage.setItem('theme', 'light');
    } else {
        document.body.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
    // Update toggle button UI if present
    const btn = document.getElementById('darkModeToggle');
    if (btn) {
        btn.innerHTML = isDark ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
    }
}

/**
 * On page load, set theme based on localStorage or system preference.
 * Also updates the toggle button UI if present.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check localStorage for theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.setAttribute('data-theme', 'dark');
    } else {
        document.body.removeAttribute('data-theme');
    }
    // Set toggle button text/icon
    const btn = document.getElementById('darkModeToggle');
    if (btn) {
        btn.innerHTML = document.body.getAttribute('data-theme') === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
});

function getCSRF() {
    const m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.getAttribute('content') : '';
}
// ===============================
// FORM VALIDATION HELPERS
// ===============================

/**
 * Validates that an input (by id) is a positive number.
 * Adds/removes Bootstrap 'is-invalid' class for feedback.
 * @param {string} inputId - The id of the input element
 * @returns {boolean} - True if valid, false otherwise
 */
function validateAmount(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        const value = parseFloat(input.value);
        if (isNaN(value) || value <= 0) {
            input.classList.add('is-invalid');
            return false;
        } else {
            input.classList.remove('is-invalid');
            return true;
        }
    }
    return false;
}

// ===============================
// ALERT/NOTIFICATION SYSTEM
// ===============================

/**
 * Shows a Bootstrap alert message in a placeholder div.
 * @param {string} message - The alert message
 * @param {string} [type='success'] - Bootstrap alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'success') {
    const alertPlaceholder = document.getElementById('alert-placeholder');
    if (alertPlaceholder) {
        alertPlaceholder.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`;
    }
}

// ===============================
// CHART.JS DYNAMIC UPDATE
// ===============================

/**
 * Updates a Chart.js chart with new labels and data.
 * @param {object} chart - Chart.js chart instance
 * @param {Array} labels - Array of labels
 * @param {Array} data - Array of data values
 */
function updateSpendingChart(chart, labels, data) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
}

// ===============================
// UI/UX IMPROVEMENTS
// ===============================

/**
 * Smoothly scrolls to a given element by id.
 * @param {string} elementId - The id of the element to scroll to
 */
function scrollToSection(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Focuses the first invalid input in a form for better accessibility.
 * @param {string} formId - The id of the form
 */
function focusFirstInvalid(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const invalid = form.querySelector('.is-invalid');
        if (invalid) {
            invalid.focus();
        }
    }
}

// ===============================
// AJAX for Add/Delete Transaction (Transactions Page)
// ===============================

// ...existing code (REPLACE the entire AJAX + hideable sections from "document.addEventListener('DOMContentLoaded'" down to the end with below)...
document.addEventListener('DOMContentLoaded', function() {
    // Theme init already above (keep)
    const addForm = document.getElementById('add-transaction-form');
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(addForm);
            fetch(addForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': getCSRF()
                }
            }).then(async res => {
                let data;
                try { data = await res.json(); } catch { data = { success:false, message:'Server error' }; }
                if (data.success) {
                    location.reload();
                } else {
                    showAlert(data.message || 'Failed to add transaction.', 'danger');
                }
            }).catch(() => showAlert('Failed to add transaction.', 'danger'));
        });
    }

    document.querySelectorAll('.delete-transaction-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!confirm('Delete this transaction?')) return;
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': getCSRF()
                }
            }).then(async res => {
                let data;
                try { data = await res.json(); } catch { data = { success:false, message:'Server error' }; }
                if (data.success) {
                    form.closest('tr').remove();
                    showAlert('Transaction deleted successfully', 'success');
                } else {
                    showAlert(data.message || 'Failed to delete transaction.', 'danger');
                }
            }).catch(() => showAlert('Failed to delete transaction.', 'danger'));
        });
    });

    initHideables();
    renderRestoreBar();
});

// ---- Hideable widgets ----
const HIDE_KEY = 'fintrack.hiddenWidgets';
function getHiddenSet() {
    return new Set(JSON.parse(localStorage.getItem(HIDE_KEY) || '[]'));
}
function saveHidden(set) {
    localStorage.setItem(HIDE_KEY, JSON.stringify(Array.from(set)));
}
function initHideables() {
    const hidden = getHiddenSet();
    document.querySelectorAll('[data-hideable="true"][data-id]').forEach(el => {
        const id = el.getAttribute('data-id');
        if (hidden.has(id)) {
            el.style.display = 'none';
            return;
        }
        if (el.querySelector('.hide-widget-btn')) return;
        el.style.position = 'relative';
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-secondary hide-widget-btn';
        btn.style.cssText = 'position:absolute;top:.5rem;right:.5rem;';
        btn.textContent = 'Hide';
        btn.onclick = () => {
            const h = getHiddenSet();
            h.add(id);
            saveHidden(h);
            el.style.display = 'none';
            renderRestoreBar();
        };
        el.appendChild(btn);
    });
}
function renderRestoreBar() {
    const hidden = getHiddenSet();
    let bar = document.getElementById('restore-hidden-bar');
    if (!hidden.size) {
        if (bar) bar.remove();
        return;
    }
    if (!bar) {
        bar = document.createElement('div');
        bar.id = 'restore-hidden-bar';
        bar.className = 'mb-3 d-flex flex-wrap gap-2';
        const container = document.querySelector('.container, .container-fluid');
        if (container) container.prepend(bar);
    }
    bar.innerHTML = '';
    hidden.forEach(id => {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'btn btn-sm btn-outline-secondary';
        b.textContent = 'Show ' + id;
        b.onclick = () => {
            const h = getHiddenSet();
            h.delete(id);
            saveHidden(h);
            const el = document.querySelector('[data-id="'+id+'"]');
            if (el) el.style.display = '';
            renderRestoreBar();
            initHideables();
        };
        bar.appendChild(b);
    });
}
// ...end of file...