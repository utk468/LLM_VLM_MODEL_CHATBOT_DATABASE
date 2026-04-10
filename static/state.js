import { uuidv4, showConfirmModal } from './utils.js';
import { appendMessage, addCopyButton } from './ui.js';

export let activeModel = 'pro'; // 'pro' or 'vision'

export function setActiveModel(model) {
    activeModel = model;
}



/**
 * Initializes a new chat session.
 * @param {Function} onThreadChange - Callback when a new thread is started.
 * @returns {string} The new thread ID.
 */
export function startNewChat(onThreadChange) {
    // generating a new thread id using uuidv4() function
    const threadId = uuidv4();
    // storing the new thread id in local storage
    localStorage.setItem('currentThreadId', threadId);
    
    // taking the chat messages div and setting its inner html to a welcome message
    // this is done to clear the chat messages when a new thread is started
    // and also to display a welcome message to the user
    document.getElementById('chat-messages').innerHTML = `
        <div class="welcome-message">
            <h1>How can I help you today?</h1>
            <p>I can search the web, calculate math, analyze documents, or just chat with you.</p>
        </div>`;
    // taking the current thread title div and setting its inner html to "New Conversation"
    // this is done to display the new thread title to the user
    document.getElementById('current-thread-title').textContent = "New Conversation";
    
    // calling the onThreadChange callback function with the new thread id
    if (onThreadChange) onThreadChange(threadId);

    // returning the new thread id
    return threadId;
}



/**
 * Loads all available threads from the server.
 * @param {string} currentThreadId - The currently active thread ID.
 * @param {Object} callbacks - Functions to handle thread switching and deletion.
 */
// Fetches all threads from backend
// Renders them in UI
// Highlights current thread
// Handles switch and delete actions
export async function loadThreads(currentThreadId, { onSwitch, onDelete }) {


    try {
        // Fetch threads from backend from the chat.py file
        const response = await fetch('/api/threads', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        // creating to json format
        const threads = await response.json();
        // for example
        // [
        //     {
        //         "id": "t1",
        //         "title": "Explain RAG pipeline in deta..."
        //     },
        //     {
        //         "id": "t2",
        //         "title": "How to use FastAPI async?"
        //     },
        //     {
        //         "id": "t3",
        //         "title": "New Conversation"
        //     }
        // ]

        // taking the thread list div and setting its inner html to empty
        const threadList = document.getElementById('thread-list');
        threadList.innerHTML = '';
        
        // iterating through all the threads 
        threads.forEach(thread => {
            // creating a div for each thread
            const item = document.createElement('div');
            // adding the class name to the div if the thread id is equal to the current thread id
            item.className = `thread-item ${thread.id === currentThreadId ? 'active' : ''}`;
            // adding the inner html to the div here we are showing title of the thread
            item.innerHTML = `
                <div class="thread-info">
                    <i data-lucide="message-square"></i>
                    <span>${thread.title || 'Conversation'}</span>
                </div>
                <span class="btn-delete-wrapper" id="delete-${thread.id}">
                    <i data-lucide="trash-2" class="btn-delete-thread"></i>
                </span>
            `;
             // handle the user when it switches on next thread using onclick event 
            item.onclick = () => onSwitch(thread.id);
            // appending the item to the thread list
            threadList.appendChild(item);

        
            const deleteBtn = document.getElementById(`delete-${thread.id}`);
            // handle the user when it delete the thread using onclick event 
            // stopPropagation() prevents triggering onSwitch
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                onDelete(thread.id);
            };
        });

        // calling the lucide.createIcons() function to create the icons
        // this is done to display the icons to the user
        if (window.lucide) lucide.createIcons();

    // catching the error if any
    // this is done to display an error message to the user
    } catch (e) {
        console.error("Error loading threads:", e);
    }

    
}







/**
 * Loads chat history for a specific thread.
 * @param {string} id - The thread ID.
 */
// loading all chats using threads when evere we click on specfic 
// thread we getting all the chats related to that created thread    
export async function loadChatHistory(id) {
    // taking the chat messages div and setting its inner html to a loader
    // this is done to display a loader to the user while loading the chat history
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '<div class="loader"></div>';
    
    // taking the thread id and loading the chat history using fetch function
    // this is calling from the chat.py file
    try {
        const response = await fetch(`/api/history/${id}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
        });
        const data = await response.json();
        chatMessages.innerHTML = '';
        
        // checking if the data has messages and if the messages are more than 0
        // if the messages are more than 0 then we are appending the messages to the chat messages
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                // Pass msg.image so history can render uploaded images
                const div = appendMessage(
                    msg.role === 'human' ? 'user' : 'assistant', 
                    msg.content, 
                    msg.image
                );
                // adding copy button to the messages
                if (msg.role !== 'human') addCopyButton(div, msg.content);
            });

        // if the messages are 0 then we are displaying a welcome message
        // this is done to display a welcome message to the user
        } else {
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <i data-lucide="sparkles"></i>
                    <h1>How can I help you today?</h1>
                    <p>I can search the web, calculate math, analyze documents, or just chat with you.</p>
                </div>`;
        }
        // calling the lucide.createIcons() function to create the icons
        // this is done to display the icons to the user
        if (window.lucide) lucide.createIcons();

    // catching the error if any
    // this is done to display an error message to the user
    } catch (e) {
        chatMessages.innerHTML = 'Error loading history.';
    }

    // taking the thread id and loading the chat history using fetch function
    
}






/**
 * Deletes a thread from the server.
 * @param {string} id - The thread ID to delete.
 */
// deleteing the thread from the server
// used to delete the chat history
export async function deleteThread(id) {
    // taking the thread id and deleting it from the server using the custom modal
    // this is done to delete the chat history
    const confirmed = await showConfirmModal('Are you sure you want to delete this conversation? This cannot be undone.');
    if (!confirmed) return false;

    // calling api/thread/id to delete the thread using fetch function 
    // using method delete to delete the thread
    // this is calling from the chat.py file
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
