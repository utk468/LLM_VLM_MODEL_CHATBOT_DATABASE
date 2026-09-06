export function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function parseMarkdownTables(text) {
    const lines = text.split('\n');
    let inTable = false;
    let resultLines = [];
    let tableRows = [];

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        
        // Pipe-delimited tables: | Col 1 | Col 2 |
        if (line.startsWith('|') && line.endsWith('|')) {
            if (!inTable) {
                inTable = true;
                tableRows = [];
            }
            if (/^\|[\s\-:|]+\|$/.test(line)) {
                continue;
            }
            tableRows.push(line);
        } 
        // Fallback for space-separated two-column metric lines (e.g., "Metric              Value")
        else if (!inTable && /^(Metric|Parameter|Currency|Item|Property|Feature)\s{2,}(Value|Current|Forecast|Rate|Amount|Details)/i.test(line)) {
            inTable = true;
            tableRows = [convertToPipeRow(line)];
        } else if (inTable && line.includes('  ') && !line.startsWith('#') && !line.startsWith('-') && !line.startsWith('•')) {
            tableRows.push(convertToPipeRow(line));
        } else {
            if (inTable) {
                resultLines.push(renderHtmlTable(tableRows));
                inTable = false;
                tableRows = [];
            }
            resultLines.push(line);
        }
    }
    if (inTable && tableRows.length > 0) {
        resultLines.push(renderHtmlTable(tableRows));
    }

    return resultLines.join('\n');
}

function convertToPipeRow(line) {
    const parts = line.split(/\s{2,}/).map(p => p.trim()).filter(Boolean);
    if (parts.length >= 2) {
        return `| ${parts[0]} | ${parts.slice(1).join(' ')} |`;
    }
    return line;
}

function renderHtmlTable(rows) {
    if (!rows || rows.length === 0) return '';
    let html = '<table>';
    
    // Header row
    const headerCols = rows[0].split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
    html += '<thead><tr>';
    headerCols.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead><tbody>';

    // Body rows
    for (let i = 1; i < rows.length; i++) {
        const cols = rows[i].split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
        html += '<tr>';
        cols.forEach(col => {
            html += `<td>${col}</td>`;
        });
        html += '</tr>';
    }

    html += '</tbody></table>';
    return html;
}

export function formatMessage(text) {
    if (!text) return '';

    // If marked is available, use it first
    if (typeof window !== 'undefined' && window.marked && typeof window.marked.parse === 'function') {
        try {
            // First run table conversion if model output plain space tables
            const preprocessed = parseMarkdownTables(text);
            return window.marked.parse(preprocessed);
        } catch (e) {
            console.error("Marked parser error:", e);
        }
    }

    // Custom fallback markdown parser for tables, headings, lists, bold, inline code, and linebreaks
    let formatted = parseMarkdownTables(text);

    formatted = formatted
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/^[\-•] (.*$)/gim, '<li>$1</li>')
        .replace(/\n/g, '<br>');

    return formatted;
}

export function showConfirmModal(message) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('confirm-modal-overlay');
        const modalMessage = document.getElementById('confirm-modal-message');
        const confirmBtn = document.getElementById('confirm-modal-delete');
        const cancelBtn = document.getElementById('confirm-modal-cancel');

        if (!overlay || !modalMessage || !confirmBtn || !cancelBtn) {
            console.error('Confirmation modal elements not found.');
            return resolve(confirm(message)); 
        }

        if (message) modalMessage.textContent = message;
        overlay.classList.remove('hidden');

        const cleanup = (result) => {
            overlay.classList.add('hidden');
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', onCancel);
            resolve(result);
        };

        const onConfirm = () => cleanup(true);
        const onCancel = () => cleanup(false);

        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', onCancel);
    });
}
