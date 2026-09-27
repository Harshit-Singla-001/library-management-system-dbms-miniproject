/**
 * Library Management System - Client Interactive Helper
 */

document.addEventListener('DOMContentLoaded', () => {
  // Alert dismiss handlers
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) alert.remove();
    });
  });

  // Auto-dismiss notifications after 4.5 seconds with smooth animation
  const alerts = document.querySelectorAll('.alert');
  if (alerts.length > 0) {
    setTimeout(() => {
      alerts.forEach(alert => {
        alert.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-8px)';
        setTimeout(() => alert.remove(), 600);
      });
    }, 4500);
  }

  // Client-side table search filter utility
  const tableSearchInput = document.getElementById('clientTableSearch');
  if (tableSearchInput) {
    tableSearchInput.addEventListener('keyup', (e) => {
      const query = e.target.value.toLowerCase();
      const rows = document.querySelectorAll('.data-table tbody tr');
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  }
});

/**
 * Quick fill helper on the login page for effortless oral demonstration
 */
function fillLogin(username, password) {
  const userField = document.getElementById('username');
  const passField = document.getElementById('password');
  if (userField && passField) {
    userField.value = username;
    passField.value = password;
  }
}

/**
 * Safe confirmation prompt for destructive operations
 */
function confirmAction(message) {
  return window.confirm(message || 'Are you sure you want to perform this action?');
}
