/**
 * Redesign Roadmap Spreadsheet — AMION NEXT
 *
 * Run this script from Extensions > Apps Script in the Google Sheet.
 * It applies four changes:
 *   1. Removes the "Category" column (Column E)
 *   2. Removes colored backgrounds from the "Jira Epic" column
 *   3. Styles the "Est. Delivery" column (green for Shipped, spelled-out months, bold current month)
 *   4. Replaces "What users gain" with succinct descriptions
 *
 * Target sheet GID: 598121109
 */

function redesignRoadmap() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = getSheetByGid(ss, 598121109);

  if (!sheet) {
    SpreadsheetApp.getUi().alert('Could not find the sheet with GID 598121109. Please run this from the correct spreadsheet.');
    return;
  }

  // Step 1: Update "What users gain" BEFORE deleting columns (currently Column G)
  updateWhatUsersGain(sheet, 7); // Column G = 7

  // Step 2: Style "Est. Delivery" column (currently Column D)
  styleEstDelivery(sheet, 4); // Column D = 4

  // Step 3: Remove colored backgrounds from "Jira Epic" (currently Column F)
  clearJiraEpicStyling(sheet, 6); // Column F = 6

  // Step 4: Delete "Category" column (Column E) — do this last since it shifts columns
  sheet.deleteColumn(5); // Column E = 5

  SpreadsheetApp.getUi().alert('Roadmap redesign complete!');
}

function getSheetByGid(ss, gid) {
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getSheetId() === gid) {
      return sheets[i];
    }
  }
  return null;
}

function clearJiraEpicStyling(sheet, col) {
  var lastRow = sheet.getLastRow();
  if (lastRow < 3) return;

  var range = sheet.getRange(3, col, lastRow - 2, 1); // Start from row 3 (skip header rows)
  range.setBackground(null); // Remove all background colors
}

function styleEstDelivery(sheet, col) {
  var lastRow = sheet.getLastRow();
  if (lastRow < 3) return;

  var range = sheet.getRange(3, col, lastRow - 2, 1);
  var values = range.getValues();

  var shippedGreenBg = '#e6f4ea';   // Subtle green background
  var shippedGreenText = '#1e7e34'; // Bold green text
  var currentMonthBg = '#e8f0fe';   // Subtle blue background for current quarter

  for (var i = 0; i < values.length; i++) {
    var cell = range.getCell(i + 1, 1);
    var val = String(values[i][0]).trim();

    if (val.toLowerCase() === 'shipped') {
      cell.setValue('Shipped');
      cell.setFontWeight('bold');
      cell.setFontColor(shippedGreenText);
      cell.setBackground(shippedGreenBg);
    } else if (val) {
      // Spell out abbreviated months
      var spelled = spellOutMonth(val);
      if (spelled !== val) {
        cell.setValue(spelled);
      }

      // Bold and tint items landing this month (March 2026)
      if (isCurrentMonth(val)) {
        cell.setFontWeight('bold');
        cell.setBackground(currentMonthBg);
      }
    }
  }
}

function spellOutMonth(val) {
  var abbrevMap = {
    'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
    'Apr': 'April', 'May': 'May', 'Jun': 'June',
    'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
    'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
  };
  for (var abbr in abbrevMap) {
    if (val.indexOf(abbr) === 0) {
      return val.replace(abbr, abbrevMap[abbr]);
    }
  }
  return val;
}

function isCurrentMonth(val) {
  var now = new Date();
  var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var currentAbbr = monthNames[now.getMonth()];
  var currentYear = now.getFullYear();
  return val.indexOf(currentAbbr) !== -1 && val.indexOf(String(currentYear)) !== -1;
}

function updateWhatUsersGain(sheet, col) {
  // Map of row numbers to new succinct descriptions
  var rewrites = {
    6:  'Block count changes no longer wipe existing assignments.',
    7:  'Services and time-off categories migrate with correct default colors matching AmionC conventions.',
    8:  'Residents auto-archive from the schedule at the end of their final training year.',
    9:  'Split block assignments migrate correctly with independent dates per split, separate from time-off.',
    10: 'Duplicate year-specific staff types are consolidated into standardized training levels before migration.',
    11: 'Only residents active in the selected academic year appear, with correct training levels across all views.',
    12: 'Schedulers can build next year\'s schedule privately, then release it to residents with a single toggle.',
    13: 'Academic year visibility auto-switches on the cutover date, matching Amion Classic behavior.',
    15: 'Add an entire incoming class to the schedule in one action instead of per-resident entry.',
    16: 'Coordinators review and correct Classic-to-Next staff type mappings before migration.'
  };

  for (var row in rewrites) {
    sheet.getRange(parseInt(row), col).setValue(rewrites[row]);
  }
}
