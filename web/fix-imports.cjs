const fs = require('fs');

const files = [
  'src/pages/admin/AdminConfigAuditTab.tsx',
  'src/pages/admin/AdminModelsTab.tsx',
  'src/pages/admin/AdminSystemAuditTab.tsx',
  'src/pages/admin/AdminTimelineTab.tsx',
  'src/pages/admin/AdminUsersTab.tsx',
  'src/pages/calibration/CalibrationHistoryTable.tsx',
  'src/pages/calibration/CalibrationStatusBanner.tsx',
  'src/pages/calibration/CalibrationValidateWidget.tsx',
  'src/pages/calibration/CalibrationWizard.tsx'
];

files.forEach(f => {
  let content = fs.readFileSync(f, 'utf8');
  content = content.replace(/\.\.\/\.\.\/\.\.\//g, '../../');
  fs.writeFileSync(f, content);
});
console.log('Fixed imports');
