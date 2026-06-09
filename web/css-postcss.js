import fs from 'fs';
import path from 'path';
import postcss from 'postcss';

const inputPath = path.join(process.cwd(), 'src', 'styles.css');
const stylesDir = path.join(process.cwd(), 'src', 'styles');

const content = fs.readFileSync(inputPath, 'utf8');

const mapping = {
  'variables.css': (node) => node.type === 'decl' || (node.type === 'rule' && (node.selector.includes(':root') || node.selector === '*')),
  'layout.css': (node) => node.type === 'rule' && (node.selector.includes('body') || node.selector.includes('.app') || node.selector.includes('.header') || node.selector.includes('.footer') || node.selector.includes('.main-content')),
  'sidebar.css': (node) => node.type === 'rule' && node.selector.includes('.sidebar'),
  'forms.css': (node) => node.type === 'rule' && (node.selector.includes('button') || node.selector.includes('input') || node.selector.includes('select') || node.selector.includes('textarea') || node.selector.includes('.field') || node.selector.includes('.form')),
  'tables.css': (node) => node.type === 'rule' && (node.selector.includes('.table') || node.selector.includes('th') || node.selector.includes('td') || node.selector.includes('tr')),
  'kpi.css': (node) => node.type === 'rule' && (node.selector.includes('.kpi') || node.selector.includes('.oee-badge') || node.selector.includes('.metric')),
  'utilities.css': (node) => node.type === 'rule' && (node.selector.includes('.alert') || node.selector.includes('.badge') || node.selector.includes('.status-')),
  'calibration.css': (node) => node.type === 'rule' && node.selector.includes('.cal-'),
  'settings.css': (node) => node.type === 'rule' && node.selector.includes('.settings-'),
  'history.css': (node) => node.type === 'rule' && node.selector.includes('.history-'),
  'production.css': (node) => node.type === 'rule' && (node.selector.includes('.production') || node.selector.includes('.grid-')),
  'system-health.css': (node) => node.type === 'rule' && (node.selector.includes('.sys-') || node.selector.includes('.system-')),
  'dashboard.css': (node) => node.type === 'rule' && node.selector.includes('.dashboard'),
};

const extracted = {};
for (const file of Object.keys(mapping)) extracted[file] = [];

const ast = postcss.parse(content);
const unhandled = [];

ast.nodes.forEach(node => {
  if (node.type === 'atrule' && node.name === 'import') {
    return; // Ignore imports
  }
  if (node.type === 'comment') {
    return;
  }
  
  let matched = false;
  for (const [file, predicate] of Object.entries(mapping)) {
    if (predicate(node)) {
      extracted[file].push(node.toString());
      matched = true;
      break;
    }
  }
  if (!matched) {
    unhandled.push(node.toString());
  }
});

for (const [file, rules] of Object.entries(extracted)) {
  if (rules.length > 0) {
    fs.writeFileSync(path.join(stylesDir, file), rules.join('\n\n'));
  }
}

// Any leftover rules go back into styles.css, plus the imports.
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
  "@import './styles/cleanup-manager.css';"
].join('\n');

fs.writeFileSync(inputPath, imports + '\n\n' + unhandled.join('\n\n'));

console.log('CSS extracted based on selectors.');
