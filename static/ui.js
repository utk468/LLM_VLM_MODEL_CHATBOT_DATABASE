import { formatMessage } from './utils.js';

/**
 * Appends a message to the chat and scrolls to the bottom.
 * @param {string} role - The role of the message (user/assistant).
 * @param {string} text - The message content.
 * @param {string} imageData - Optional base64 image data.
 * @returns {HTMLElement} The created message element.
 */
//here we are appending the message to the chat
export function appendMessage(role, text, imageData = null) {
    const chatMessages = document.getElementById('chat-messages');

    // Remove welcome message if present because we are 
    // appending the message to the chat thats why removal of 
    // welcome message is important
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    //creating a wrapper for the message
    const msgWrapper = document.createElement('div');
    //adding class to the wrapper this is dynamic 
    //based on the role of the message
    msgWrapper.className = `message-wrapper ${role}`;


    //creating a div for the message
    const msgDiv = document.createElement('div');
    //adding class to the div this is dynamic 
    //based on the role of the message
    msgDiv.className = `message ${role}`;
    
    // If imageData exists, append the image first
    if (imageData) {
        const img = document.createElement('img');
        img.src = imageData.startsWith('data:') ? imageData : `data:image/png;base64,${imageData}`;
        img.className = 'message-image';
        msgDiv.appendChild(img);
    }

    //creating text container
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMessage(text);
    msgDiv.appendChild(textDiv);



    //appending the message to the wrapper
    msgWrapper.appendChild(msgDiv);
    //appending the wrapper to the chat messages
    chatMessages.appendChild(msgWrapper);


    //scrolling to the bottom of the chat messages
    chatMessages.scrollTop = chatMessages.scrollHeight;
    //returning the message element
    return msgDiv;

}




/**
 * Adds a typing indicator to a parent element.
 * @param {HTMLElement} parent - The parent element to add the indicator to.
 * @returns {HTMLElement} The created indicator element.
 */
export function addTypingIndicator(parent) {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    parent.appendChild(indicator);
    return indicator;
}





/**
 * Adds a copy button to a message.
 * @param {HTMLElement} parent - The message element.
 * @param {string} text - The text to be copied.
 */
//copying the message to the clipboard
export function addCopyButton(parent, text) {
    const btn = document.createElement('button');
    btn.className = 'btn-copy';
    btn.innerHTML = '<i data-lucide="copy"></i>';
    btn.onclick = () => {
        navigator.clipboard.writeText(text);
        btn.innerHTML = '<i data-lucide="check"></i>';
        if (window.lucide) lucide.createIcons();
        setTimeout(() => {
            btn.innerHTML = '<i data-lucide="copy"></i>';
            if (window.lucide) lucide.createIcons();
        }, 2000);
    };
    parent.parentElement.appendChild(btn);
}







/**
 * Handles the Human-in-the-Loop interaction.
 * @param {Object} data - The HITL data from the server.
 * @param {Function} resumeCallback - Function to call when allowed or denied.
 */
//handling the human in the loop interaction comming from the server
//this is the main function that will be called when the server sends a HITL event
export function handleHITL(data, resumeCallback) {
    const hitlOverlay = document.getElementById('hitl-overlay');
    const hitlMessage = document.getElementById('hitl-message');
    const allowBtn = document.getElementById('allow-btn');
    const denyBtn = document.getElementById('deny-btn');
     

        //     example of hitl data from server
        // {
        //   "type": "hitl",
        //   "action": "book_appointment",
        //   "args": {
        //     "date": "2026-04-01",
        //     "doctor": "Dr. Sharma"
        //   }
        
    console.log("Handling HITL Event:", data);
    const action = data.action || 'Unknown Tool';
    const argsStr = data.args ? JSON.stringify(data.args, null, 2) : '{}';

    //setting the innerHTML of the hitlMessage
    //this will show the message to the user
    hitlMessage.innerHTML = `
        <div style="margin-bottom: 10px;">The Assistant wants to use: <strong style="color: var(--accent-primary);">${action}</strong></div>
        <div style="text-align: left; background: #f3f4f6; padding: 10px; border-radius: 8px; font-size: 0.85rem; max-height: 150px; overflow-y: auto;">
            <code>${argsStr}</code>
        </div>
    `;
    
    //removing the hidden class from the hitlOverlay
    //this will show the hitlOverlay to the user
    hitlOverlay.classList.remove('hidden');
    
    //adding event listener to the allow button
    //this will call the resumeCallback function with 'allow' as the argument
    allowBtn.onclick = () => {
        hitlOverlay.classList.add('hidden');
        resumeCallback('allow');
    };
    //adding event listener to the deny button
    //this will call the resumeCallback function with 'deny' as the argument
    denyBtn.onclick = () => {
        hitlOverlay.classList.add('hidden');
        resumeCallback('deny');
    };


}

