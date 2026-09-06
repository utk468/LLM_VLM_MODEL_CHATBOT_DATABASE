import { appendMessage, addTypingIndicator, addCopyButton, handleHITL } from './ui.js';
import { formatMessage } from './utils.js';

export async function sendMessage(text, currentThreadId, { onComplete }) {
    if (!text) return;

    appendMessage('user', text);
    const aiMessageDiv = appendMessage('assistant', '');
    const typingIndicator = addTypingIndicator(aiMessageDiv);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify({ message: text, thread_id: currentThreadId })
        });
        
        await consumeStream(response, aiMessageDiv, typingIndicator, currentThreadId, onComplete);
    } catch (error) {
        if (typingIndicator) typingIndicator.remove();
        aiMessageDiv.textContent = 'Sorry, I encountered an error connecting to the server.';
    }
}

export async function sendVisionMessage(text, imageData, currentThreadId, { onComplete }) {
    if (!text || !imageData) return;

    appendMessage('user', text, imageData);
    const aiMessageDiv = appendMessage('assistant', '');
    const typingIndicator = addTypingIndicator(aiMessageDiv);

    try {
        const response = await fetch('/api/vision', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify({ message: text, image: imageData, thread_id: currentThreadId })
        });
        
        const data = await response.json();
        
        if (typingIndicator) typingIndicator.remove();
        
        if (data.error) {
            aiMessageDiv.textContent = `Error: ${data.error}`;
        } else {
            aiMessageDiv.innerHTML = formatMessage(data.content);
            addCopyButton(aiMessageDiv, data.content);
        }
        
        if (onComplete) onComplete();
    } catch (error) {
        if (typingIndicator) typingIndicator.remove();
        aiMessageDiv.textContent = 'Sorry, I encountered an error connecting to the vision server.';
    }
}

export async function consumeStream(response, messageDiv, typingIndicator, currentThreadId, onComplete) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let content = '';
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.substring(6));
                    if (data.type === 'content') {
                        if (typingIndicator) {
                            typingIndicator.remove();
                            typingIndicator = null;
                        }
                        content += data.content;
                        messageDiv.innerHTML = formatMessage(content);
                        const chatMessages = document.getElementById('chat-messages');
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    } else if (data.type === 'hitl') {
                        if (typingIndicator) {
                            typingIndicator.remove();
                            typingIndicator = null;
                        }
                        if (!content) messageDiv.parentElement.remove();
                        handleHITL(data, (decision) => resumeChat(decision, currentThreadId, onComplete));
                    } else if (data.type === 'end') {
                        if (typingIndicator) {
                            typingIndicator.remove();
                            typingIndicator = null;
                        }
                        if (content) {
                            addCopyButton(messageDiv, content);
                        } else {
                            messageDiv.parentElement.remove();
                        }
                        if (onComplete) onComplete();
                    }
                } catch (e) {
                    console.error("Error parsing stream line:", e);
                }
            }
        }
    }
}

export async function resumeChat(decision, currentThreadId, onComplete) {
    
    const aiMessageDiv = appendMessage('assistant', '');
    
    const typingIndicator = addTypingIndicator(aiMessageDiv);
    
    try {
        
        const response = await fetch('/api/chat/resume', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify({ decision: decision, thread_id: currentThreadId })
        });
        
        await consumeStream(response, aiMessageDiv, typingIndicator, currentThreadId, onComplete);
    } 
    
    catch (error) {
        if (typingIndicator) typingIndicator.remove();
        aiMessageDiv.textContent = 'Error resuming chat.';
    }
}

export async function handleFileUpload(e) {
    
    const file = e.target.files[0];
    
    if (!file) return;
    
    const formData = new FormData();
    
    formData.append('file', file);
    
    const statusDiv = document.getElementById('upload-status');
    
    statusDiv.innerHTML = '<div class="loader-small"></div> Processing...';

    try {
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = `<span class="success-text"><i data-lucide="check-circle"></i> ${file.name} ready</span>`;
            if (window.lucide) lucide.createIcons();
        } else {
            statusDiv.innerHTML = `<span class="error-text">Error uploading</span>`;
        }
    }
    
    catch (error) {
        statusDiv.innerHTML = `<span class="error-text">Upload failed</span>`;
    }

}
