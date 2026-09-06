import { uuidv4, showConfirmModal } from './utils.js';
import { appendMessage, addCopyButton } from './ui.js';

export let activeModel = 'pro'; 

export function setActiveModel(model) {
    activeModel = model;
}

export function startNewChat(onThreadChange) {
    
    const threadId = uuidv4();
    
    localStorage.setItem('currentThreadId', threadId);
    
    document.getElementById('chat-messages').innerHTML = `
        <div class="welcome-message">
            <h1>How can I help you today?</h1>
            <p>I can search the web, calculate math, or just chat with you.</p>
        </div>`;
    
    document.getElementById('current-thread-title').textContent = "New Conversation";
    
    if (onThreadChange) onThreadChange(threadId);

    return threadId;
}

export async function loadThreads(currentThreadId, { onSwitch, onDelete }) {

    try {
        
        const response = await fetch('/api/threads', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        
        const threads = await response.json();
        
        const threadList = document.getElementById('thread-list');
        threadList.innerHTML = '';
        
        threads.forEach(thread => {
            
            const item = document.createElement('div');
            
            item.className = `thread-item ${thread.id === currentThreadId ? 'active' : ''}`;
            
            item.innerHTML = `
                <div class="thread-info">
                    <i data-lucide="message-square"></i>
                    <span>${thread.title || 'Conversation'}</span>
                </div>
                <span class="btn-delete-wrapper" id="delete-${thread.id}">
                    <i data-lucide="trash-2" class="btn-delete-thread"></i>
                </span>
            `;
             
            item.onclick = () => onSwitch(thread.id);
            
            threadList.appendChild(item);

            const deleteBtn = document.getElementById(`delete-${thread.id}`);
            
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                onDelete(thread.id);
            };
        });

        if (window.lucide) lucide.createIcons();

    } catch (e) {
        console.error("Error loading threads:", e);
    }

}

export async function loadChatHistory(id) {
    
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '<div class="loader"></div>';
    
    try {
        const response = await fetch(`/api/history/${id}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        const data = await response.json();
        chatMessages.innerHTML = '';
        
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                
                const div = appendMessage(
                    msg.role === 'human' ? 'user' : 'assistant', 
                    msg.content, 
                    msg.image
                );
                
                if (msg.role !== 'human') addCopyButton(div, msg.content);
            });

        } else {
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <i data-lucide="sparkles"></i>
                    <h1>How can I help you today?</h1>
                    <p>I can search the web, calculate math, or just chat with you.</p>
                </div>`;
        }
        
        if (window.lucide) lucide.createIcons();

    } catch (e) {
        chatMessages.innerHTML = 'Error loading history.';
    }

}

export async function deleteThread(id) {
    
    const confirmed = await showConfirmModal('Are you sure you want to delete this conversation? This cannot be undone.');
    if (!confirmed) return false;

    try {
        await fetch(`/api/threads/${id}`, { 
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        return true;
    } catch (e) {
        console.error("Error deleting thread:", e);
        return false;
    }
}
