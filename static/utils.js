/**
 * Generates a UUID v4 string.
 * @returns {string} A randomly generated UUID.
 */
export function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}



/**
 * Formats plain text into HTML with bold, code, and line breaks.
 * @param {string} text - The text to format.
 * @returns {string} The formatted HTML string.
 */
export function formatMessage(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

/**
 * Displays a custom confirmation modal and returns a Promise resolving to true or false.
 * @param {string} message - The message to display.
 * @returns {Promise<boolean>} Resolves to true if confirmed, false otherwise.
 */
export function showConfirmModal(message) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('confirm-modal-overlay');
        const modalMessage = document.getElementById('confirm-modal-message');
        const confirmBtn = document.getElementById('confirm-modal-delete');
        const cancelBtn = document.getElementById('confirm-modal-cancel');

        if (!overlay || !modalMessage || !confirmBtn || !cancelBtn) {
            console.error('Confirmation modal elements not found.');
            return resolve(confirm(message)); // Fallback to native confirm if elements missing
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
