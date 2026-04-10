import { appendMessage, addTypingIndicator, addCopyButton, handleHITL } from './ui.js';
import { formatMessage } from './utils.js';




// sneding the message to the backend 
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

// Sending vision message to the vision endpoint
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





// streaming the response from the backend 
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






//resume the chat after hitl loop
//taking the decision from the user
export async function resumeChat(decision, currentThreadId, onComplete) {
    //taking the ai message div from the ui
    const aiMessageDiv = appendMessage('assistant', '');
    //adding the typing indicator
    const typingIndicator = addTypingIndicator(aiMessageDiv);
    
    try {
        //sending the decision to the backend using fetch api
        const response = await fetch('/api/chat/resume', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify({ decision: decision, thread_id: currentThreadId })
        });
        //consuming the stream
        await consumeStream(response, aiMessageDiv, typingIndicator, currentThreadId, onComplete);
    } 
    //if error then showing the error message
    catch (error) {
        if (typingIndicator) typingIndicator.remove();
        aiMessageDiv.textContent = 'Error resuming chat.';
    }
}






/**
 * Handles file upload to the backend.
 * @param {Event} e - The file upload event.
 */ 
//taking the file upload event
export async function handleFileUpload(e) {
    //taking the file from the event its like <input type="file">
    const file = e.target.files[0];
    //if not file then return
    if (!file) return;
    
    //preparing data for backend
    const formData = new FormData();
    //appending the file to the form data
    formData.append('file', file);
    

    //taking the upload status div from the ui
    const statusDiv = document.getElementById('upload-status');
    //showing the processing message
    statusDiv.innerHTML = '<div class="loader-small"></div> Processing...';

    try {
        //sending the file to the backend using fetch api
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: formData
        });
        //taking the response from the backend
        const data = await response.json();
        //if response is success then showing the success message
        if (data.success) {
            statusDiv.innerHTML = `<span class="success-text"><i data-lucide="check-circle"></i> ${file.name} ready</span>`;
            if (window.lucide) lucide.createIcons();
        } else {
            statusDiv.innerHTML = `<span class="error-text">Error uploading</span>`;
        }
    }
    //if error then showing the error message
    catch (error) {
        statusDiv.innerHTML = `<span class="error-text">Upload failed</span>`;
    }


}
