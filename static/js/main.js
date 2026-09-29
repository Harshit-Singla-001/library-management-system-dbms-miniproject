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

/**
 * SQL Live Console Drawer Controls (Split View alongside active table)
 */
function toggleSqlDrawer(forceState) {
  const drawer = document.getElementById('sqlConsoleDrawer');
  if (!drawer) return;

  const isOpen = drawer.classList.contains('drawer-open');
  const targetState = typeof forceState === 'boolean' ? forceState : !isOpen;

  if (targetState) {
    drawer.classList.add('drawer-open');
    highlightAllSqlCode();
  } else {
    drawer.classList.remove('drawer-open');
  }
}

function toggleExpandDrawer() {
  const drawer = document.getElementById('sqlConsoleDrawer');
  const btn = document.getElementById('btnExpandDrawer');
  if (!drawer || !btn) return;

  drawer.classList.toggle('drawer-expanded');
  const isExp = drawer.classList.contains('drawer-expanded');
  btn.innerHTML = isExp ? '⤡ Compact' : '⤢ Expand';
}

function toggleSyllabusGuide() {
  const box = document.getElementById('syllabusGuideBox');
  if (!box) return;
  box.style.display = box.style.display === 'none' ? 'block' : 'none';
}

function toggleQueryInfo(btn) {
  const card = btn.closest('.sql-card');
  if (!card) return;
  const infoBox = card.querySelector('.query-info-box');
  if (!infoBox) return;

  const isVisible = infoBox.style.display !== 'none';
  infoBox.style.display = isVisible ? 'none' : 'flex';
  btn.style.background = isVisible ? '#0f172a' : '#38bdf8';
  btn.style.color = isVisible ? '#38bdf8' : '#0f172a';
}

// Global ESC key listener to hide drawer
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    toggleSqlDrawer(false);
  }
});

/**
 * 1-Click Copy SQL to Clipboard
 */
function copySqlFromElement(btn) {
  const card = btn.closest('.sql-card');
  if (!card) return;
  const codeEl = card.querySelector('.sql-code code');
  if (!codeEl) return;

  const rawSql = codeEl.innerText || codeEl.textContent;
  navigator.clipboard.writeText(rawSql.trim()).then(() => {
    const originalText = btn.innerHTML;
    btn.innerHTML = '✅ Copied!';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.classList.remove('copied');
    }, 1800);
  }).catch(err => {
    console.error('Clipboard copy failed:', err);
  });
}

/**
 * Rich Syntax Highlighting for viva display (adhering to DBMS Syllabus tasks)
 */
let sqlHighlighted = false;
function highlightAllSqlCode() {
  if (sqlHighlighted) return;
  const codeBlocks = document.querySelectorAll('.sql-code code');
  codeBlocks.forEach(code => {
    let text = code.textContent;
    // Escape HTML first
    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Highlight strings in quotes (emerald green)
    escaped = escaped.replace(/('(?:''|[^'])*')/g, '<span style="color:#4ade80; font-weight:600;">$1</span>');

    // Highlight comments (-- or /* */)
    escaped = escaped.replace(/(--.*?$)/gm, '<span style="color:#94a3b8; font-style:italic;">$1</span>');

    // Highlight syllabus keywords (Task 2, 3, 4, 5) in vivid cyan
    const keywords = [
      'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'ON',
      'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'AS', 'AND', 'OR', 'IN', 'NOT', 'IS',
      'NULL', 'LIKE', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
      'INSERT INTO', 'INSERT', 'VALUES', 'UPDATE', 'SET', 'DELETE',
      'START TRANSACTION', 'COMMIT', 'ROLLBACK', 'FOR UPDATE', 'DESC', 'ASC',
      'GRANT', 'REVOKE', 'CURDATE', 'DATEDIFF', 'NOW', 'INTERVAL', 'DAY'
    ];

    keywords.forEach(kw => {
      const regex = new RegExp('\\b(' + kw + ')\\b', 'gi');
      escaped = escaped.replace(regex, '<span style="color:#38bdf8; font-weight:700;">$1</span>');
    });

    code.innerHTML = escaped;
  });
  sqlHighlighted = true;
}

/**
 * Direct block-to-query inspection: Jump directly to a specific query in the console drawer
 */
function inspectQueryNumber(queryIndex) {
  const drawer = document.getElementById('sqlConsoleDrawer');
  if (!drawer) return;

  // Open drawer if closed
  if (!drawer.classList.contains('drawer-open')) {
    toggleSqlDrawer(true);
  }

  // Find target card
  let card = document.getElementById(`sql-card-${queryIndex}`);
  if (!card) {
    const cards = drawer.querySelectorAll('.sql-cards-list .sql-card');
    if (cards && cards[queryIndex - 1]) {
      card = cards[queryIndex - 1];
    }
  }

  if (card) {
    revealAndHighlightCard(card);
  }
}

function revealAndHighlightCard(card) {
  // Ensure syntax highlighting is active
  highlightAllSqlCode();

  // Reveal info box and color the button
  const infoBox = card.querySelector('.query-info-box');
  const infoBtn = card.querySelector('.btn-info-query');
  if (infoBox) {
    infoBox.style.display = 'flex';
    if (infoBtn) {
      infoBtn.style.background = '#38bdf8';
      infoBtn.style.color = '#0f172a';
    }
  }

  // Scroll smoothly into view inside drawer body
  setTimeout(() => {
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, 100);

  // Pulse animation highlight
  card.classList.remove('card-highlight-pulse');
  void card.offsetWidth; // Force CSS reflow
  card.classList.add('card-highlight-pulse');
}

