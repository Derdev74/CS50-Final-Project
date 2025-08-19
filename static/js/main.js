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
        btn.innerHTML = isDark ? '🌙 Dark Mode' : '☀️ Light Mode';
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
        btn.innerHTML = document.body.getAttribute('data-theme') === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
    }
});

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
// END OF main.js
// ===============================
