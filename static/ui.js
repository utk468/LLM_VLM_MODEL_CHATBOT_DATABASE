import { formatMessage } from './utils.js';

export function appendMessage(role, text, imageData = null) {
    const chatMessages = document.getElementById('chat-messages');

    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const msgWrapper = document.createElement('div');
    
    msgWrapper.className = `message-wrapper ${role}`;

    const msgDiv = document.createElement('div');
    
    msgDiv.className = `message ${role}`;
    
    if (imageData) {
        const img = document.createElement('img');
        img.src = imageData.startsWith('data:') ? imageData : `data:image/png;base64,${imageData}`;
        img.className = 'message-image';
        msgDiv.appendChild(img);
    }

    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.innerHTML = formatMessage(text);
    msgDiv.appendChild(textDiv);

    msgWrapper.appendChild(msgDiv);
    
    chatMessages.appendChild(msgWrapper);

    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return msgDiv;

}

export function addTypingIndicator(parent) {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    parent.appendChild(indicator);
    return indicator;
}

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

export function handleHITL(data, resumeCallback) {
    const hitlOverlay = document.getElementById('hitl-overlay');
    const hitlMessage = document.getElementById('hitl-message');
    const allowBtn = document.getElementById('allow-btn');
    const denyBtn = document.getElementById('deny-btn');
     
    console.log("Handling HITL Event:", data);
    const action = data.action || 'Unknown Tool';
    const argsStr = data.args ? JSON.stringify(data.args, null, 2) : '{}';

    hitlMessage.innerHTML = `
        <div style="margin-bottom: 10px;">The Assistant wants to use: <strong style="color: var(--accent-primary);">${action}</strong></div>
        <div style="text-align: left; background: #f3f4f6; padding: 10px; border-radius: 8px; font-size: 0.85rem; max-height: 150px; overflow-y: auto;">
            <code>${argsStr}</code>
        </div>
    `;
    
    hitlOverlay.classList.remove('hidden');
    
    allowBtn.onclick = () => {
        hitlOverlay.classList.add('hidden');
        resumeCallback('allow');
    };
    
    denyBtn.onclick = () => {
        hitlOverlay.classList.add('hidden');
        resumeCallback('deny');
    };

}

