import { sendMessage, sendVisionMessage, handleFileUpload } from './api.js';
import { activeModel, setActiveModel, startNewChat, loadThreads, loadChatHistory, deleteThread } from './state.js';
import { updateMCPStatus, fetchStaticTools, connectMCPServer, disconnectMCPServer } from './mcp.js';

document.addEventListener('DOMContentLoaded', () => {
    
    const token = localStorage.getItem('auth_token');
    const username = localStorage.getItem('username');
    
    const isAuthenticated = token && token !== 'undefined' && token !== 'null';
    
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');
    const logoutBtn = document.getElementById('logout-btn');
    const userDisplayName = document.getElementById('user-display-name');
    
    if (isAuthenticated) {
        if (userDisplayName && username) {
            userDisplayName.textContent = `Hello, ${username}`;
            userDisplayName.style.display = 'block';
        }
        if (logoutBtn) logoutBtn.style.display = 'flex';
    } else {
        if (userDisplayName) {
            userDisplayName.innerHTML = '<a href="/login" style="color: var(--accent-primary); text-decoration: none; font-weight: 600;">Sign In</a>';
            userDisplayName.style.display = 'block';
        }
        if (logoutBtn) logoutBtn.style.display = 'none';
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('username');
            localStorage.removeItem('currentThreadId');
            window.location.href = '/login';
        });
    }
    
    const connectMcpBtn = document.getElementById('connect-mcp-btn');
    
    const disconnectMcpBtn = document.getElementById('disconnect-mcp-btn');
    
    const mcpToolCount = document.getElementById('mcp-tool-count');
    
    const mcpToolList = document.getElementById('mcp-tool-list');
    
    let currentThreadId = localStorage.getItem('currentThreadId') || null;

    updateMCPStatus();
    
    fetchStaticTools();
    
    if (isAuthenticated) {
        if (!currentThreadId) {
            
            currentThreadId = startNewChat();
        } else {
            
            refreshThreads();
            loadChatHistory(currentThreadId);
        }
    } else {
        
        console.log("Running in Guest mode");
        
    }

    const pendingMessage = localStorage.getItem('pending_message');
    if (pendingMessage && isAuthenticated) {
        userInput.value = pendingMessage;
        userInput.style.height = 'auto';
        userInput.style.height = (userInput.scrollHeight) + 'px';
        localStorage.removeItem('pending_message');
    }

    function refreshThreads() {
        
        loadThreads(currentThreadId, {
            
            onSwitch: (id) => {
                currentThreadId = id;
                localStorage.setItem('currentThreadId', id);
                refreshThreads();
                loadChatHistory(id);
            },
            
            onDelete: async (id) => {
                if (await deleteThread(id)) {
                    if (currentThreadId === id) {
                        currentThreadId = startNewChat(refreshThreads);
                    } else {
                        refreshThreads();
                    }
                }
            }
        });
    }

    function redirectToLogin() {
        const token = localStorage.getItem('auth_token');
        const isNotAuthenticated = !token || token === 'null' || token === 'undefined' || token === '';
        
        console.log("Auth Check - Token:", token, "Authenticated:", !isNotAuthenticated);
        
        if (isNotAuthenticated) {
            console.log("Redirecting to login...");
            const text = userInput.value.trim();
            if (text) localStorage.setItem('pending_message', text);
            window.location.href = '/login';
            return true;
        }
        return false;
    }

    userInput.addEventListener('input', function() {
        if (redirectToLogin()) return;

        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    userInput.addEventListener('focus', redirectToLogin);
    userInput.addEventListener('click', redirectToLogin);

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    sendBtn.addEventListener('click', handleSend);

    newChatBtn.addEventListener('click', () => {
        currentThreadId = startNewChat(refreshThreads);
    });

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFileUpload);
    }

    if (connectMcpBtn) {
        connectMcpBtn.addEventListener('click', connectMCPServer);
    }
    if (disconnectMcpBtn) {
        disconnectMcpBtn.addEventListener('click', disconnectMCPServer);
    }
    if (mcpToolCount) {
        mcpToolCount.addEventListener('click', () => {
            mcpToolList.classList.toggle('hidden');
        });
    }

    let isNewImageForThread = true;

    async function handleSend() {
        const text = userInput.value.trim();
        if (!text) return;

        if (!localStorage.getItem('auth_token')) {
            localStorage.setItem('pending_message', text);
            window.location.href = '/login';
            return;
        }
        
        userInput.value = '';
        userInput.style.height = 'auto';
         
        if (activeModel === 'vision' && currentImageData) {
            
            const imageToSend = isNewImageForThread ? currentImageData : null;
            
            await sendVisionMessage(text, imageToSend, currentThreadId, {
                onComplete: () => {
                    isNewImageForThread = false; 
                    refreshThreads();
                }
            });
        } else {
            
            await sendMessage(text, currentThreadId, {
                onComplete: () => refreshThreads()
            });
        }
    }

    const modelPro = document.getElementById('model-pro');
    const modelVision = document.getElementById('model-vision');
    const imageUploadBtn = document.getElementById('image-upload-btn');
    const imageInput = document.getElementById('image-input');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreviewImg = document.getElementById('image-preview-img');
    const removePreviewBtn = document.getElementById('remove-image-preview');
    let currentImageData = null;

    if (modelPro && modelVision) {
        modelPro.addEventListener('click', () => {
            setActiveModel('pro');
            modelPro.classList.add('active');
            modelVision.classList.remove('active');
            if (imageUploadBtn) {
                imageInput.value = ''; 
                imageUploadBtn.classList.add('hidden');
                imagePreviewContainer.classList.add('hidden');
                currentImageData = null;
                isNewImageForThread = true; 
            }
        });

        modelVision.addEventListener('click', () => {
            setActiveModel('vision');
            modelVision.classList.add('active');
            modelPro.classList.remove('active');
            if (imageUploadBtn) imageUploadBtn.classList.remove('hidden');
        });
    }

    if (imageUploadBtn && imageInput) {
        imageUploadBtn.addEventListener('click', () => imageInput.click());
        
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    currentImageData = event.target.result; 
                    isNewImageForThread = true; 
                    
                    if (imagePreviewContainer && imagePreviewImg) {
                        imagePreviewImg.src = currentImageData;
                        imagePreviewContainer.classList.remove('hidden');
                        imageUploadBtn.style.color = '#7c3aed';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (removePreviewBtn) {
        removePreviewBtn.addEventListener('click', () => {
            currentImageData = null;
            isNewImageForThread = true;
            imageInput.value = '';
            if (imagePreviewContainer) imagePreviewContainer.classList.add('hidden');
            if (imageUploadBtn) {
                imageUploadBtn.style.color = '';
                imageUploadBtn.classList.remove('active');
            }
            
            currentThreadId = startNewChat();
            refreshThreads();
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            currentThreadId = startNewChat(refreshThreads);
            currentImageData = null;
            isNewImageForThread = true;
            if (imagePreviewContainer) imagePreviewContainer.classList.add('hidden');
        });
    }
});
