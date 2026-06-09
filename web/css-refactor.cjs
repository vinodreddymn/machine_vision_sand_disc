const fs = require('fs');
const path = require('path');

const inputPath = path.join(__dirname, 'src', 'styles.css');
const stylesDir = path.join(__dirname, 'src', 'styles');

let content = fs.readFileSync(inputPath, 'utf8');

// Function to extract blocks between headers or to the end of file
function extractBlock(startRegex, endRegex) {
  const matchStart = content.match(startRegex);
  if (!matchStart) return '';
  const startIndex = matchStart.index;
  let endIndex = content.length;
  if (endRegex) {
    const matchEnd = content.substring(startIndex + matchStart[0].length).match(endRegex);
    if (matchEnd) {
      endIndex = startIndex + matchStart[0].length + matchEnd.index;
    }
  }
  const extracted = content.substring(startIndex, endIndex);
  content = content.substring(0, startIndex) + content.substring(endIndex);
  return extracted.trim();
}

const css = {
  'variables.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   GLOBAL VARIABLES & RESET/, /\/\* ═══════════════════════════════════════════════════/),
  'layout.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   LAYOUT & APP SHELL/, /\/\* ═══════════════════════════════════════════════════/),
  'sidebar.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   SIDEBAR NAVIGATION/, /\/\* ═══════════════════════════════════════════════════/),
  'kpi.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   KPI & STATUS WIDGETS/, /\/\* ═══════════════════════════════════════════════════/),
  'tables.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   TABLES & LISTS/, /\/\* ═══════════════════════════════════════════════════/),
  'settings.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   SETTINGS PAGE/, /\/\* ═══════════════════════════════════════════════════/),
  'calibration.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   CALIBRATION PAGE/, /\/\* ═══════════════════════════════════════════════════/),
  'history.css': extractBlock(/\/\* ═══════════════════════════════════════════════════\r?\n   HISTORY PAGE/, /\/\* ═══════════════════════════════════════════════════/),
};

// Catch-alls and manual edits
// ... The rest of styles.css

// Create imports string
const imports = [
  "@import './styles/variables.css';",
  "@import './styles/layout.css';",
  "@import './styles/sidebar.css';",
  "@import './styles/forms.css';",
  "@import './styles/tables.css';",
  "@import './styles/kpi.css';",
  "@import './styles/utilities.css';",
  "@import './styles/dashboard.css';",
  "@import './styles/production.css';",
  "@import './styles/history.css';",
  "@import './styles/settings.css';",
  "@import './styles/calibration.css';",
  "@import './styles/system-health.css';",
  "@import './styles/json-editor.css';",
  "@import './styles/config-manager.css';",
  "@import './styles/admin-enhancements.css';",
  "@import './styles/event-log.css';",
  "@import './styles/production-dashboard.css';",
  "@import './styles/cleanup-manager.css';",
].join('\n');

for (const [name, data] of Object.entries(css)) {
  if (data) {
    fs.writeFileSync(path.join(stylesDir, name), data + '\n');
  }
}

fs.writeFileSync(inputPath, imports + '\n\n' + content.trim() + '\n');
console.log('Done mapping blocks.');
