import { sendMessage, sendVisionMessage, handleFileUpload } from './api.js';
import { activeModel, setActiveModel, startNewChat, loadThreads, loadChatHistory, deleteThread } from './state.js';
import { updateMCPStatus, fetchStaticTools, connectMCPServer, disconnectMCPServer } from './mcp.js';




document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    const token = localStorage.getItem('auth_token');
    const username = localStorage.getItem('username');
    
    // Robust auth check
    const isAuthenticated = token && token !== 'undefined' && token !== 'null';
    
    // Redirect logic moved to interaction handlers

    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('upload-area');
    const logoutBtn = document.getElementById('logout-btn');
    const userDisplayName = document.getElementById('user-display-name');
    
    // Set user display name and Logout button visibility
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

    // Logout logic
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('username');
            localStorage.removeItem('currentThreadId');
            window.location.href = '/login';
        });
    }
    
    // MCP sidebar elements
    //taking the connect button from the ui
    const connectMcpBtn = document.getElementById('connect-mcp-btn');
    //taking the disconnect button from the ui
    const disconnectMcpBtn = document.getElementById('disconnect-mcp-btn');
    //taking the tool count from the ui
    const mcpToolCount = document.getElementById('mcp-tool-count');
    //taking the tool list from the ui
    const mcpToolList = document.getElementById('mcp-tool-list');
    

    //taking the current thread id from the local storage
    let currentThreadId = localStorage.getItem('currentThreadId') || null;

    // Initialization
    //calling the updateMCPStatus function to update the status of the MCP server
    updateMCPStatus();
    //calling the fetchStaticTools function to fetch the static tools
    fetchStaticTools();
    
    //here we are using current thread id to load the chat history
    if (isAuthenticated) {
        if (!currentThreadId) {
            //if not current thread then creating new chat using startNewChat function
            currentThreadId = startNewChat();
        } else {
            //if current thread is present then loading the chat history
            refreshThreads();
            loadChatHistory(currentThreadId);
        }
    } else {
        // Guest mode - provide a clear way to login
        console.log("Running in Guest mode");
        // Optionally redirect automatically if you prefer a strict landing page
        // window.location.href = '/login'; 
    }

    // Restore pending message if any
    const pendingMessage = localStorage.getItem('pending_message');
    if (pendingMessage && isAuthenticated) {
        userInput.value = pendingMessage;
        userInput.style.height = 'auto';
        userInput.style.height = (userInput.scrollHeight) + 'px';
        localStorage.removeItem('pending_message');
    }

    // --- Core Functions ---
    function refreshThreads() {
        //loading the threads using loadThreads function
        loadThreads(currentThreadId, {
            //switching the thread
            onSwitch: (id) => {
                currentThreadId = id;
                localStorage.setItem('currentThreadId', id);
                refreshThreads();
                loadChatHistory(id);
            },
            //deleting the thread
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

    // Event Listeners
    // Redirect function
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

    // Adjust input height and check Auth
    userInput.addEventListener('input', function() {
        if (redirectToLogin()) return;

        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Also redirect on focus/click for better UX
    userInput.addEventListener('focus', redirectToLogin);
    userInput.addEventListener('click', redirectToLogin);

    // Send message on enter
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Send button click
    sendBtn.addEventListener('click', handleSend);

    // New chat button click
    newChatBtn.addEventListener('click', () => {
        currentThreadId = startNewChat(refreshThreads);
    });

    // File upload area click
    uploadArea.addEventListener('click', () => fileInput.click());
    // File upload area change
    fileInput.addEventListener('change', handleFileUpload);




    // MCP Event Listeners
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


    // Track if current image has been uploaded for the current thread
    let isNewImageForThread = true;

    // Send message function
    async function handleSend() {
        const text = userInput.value.trim();
        if (!text) return;

        // AUTH CHECK: Redirect to login if not authenticated
        if (!localStorage.getItem('auth_token')) {
            localStorage.setItem('pending_message', text);
            window.location.href = '/login';
            return;
        }
        
        userInput.value = '';
        userInput.style.height = 'auto';
         
        // If vision mode is active and we have an image, send to vision endpoint
        if (activeModel === 'vision' && currentImageData) {
            // Speed Optimization: Only send image if it's the first time for this thread
            const imageToSend = isNewImageForThread ? currentImageData : null;
            
            await sendVisionMessage(text, imageToSend, currentThreadId, {
                onComplete: () => {
                    isNewImageForThread = false; // Mark as uploaded
                    refreshThreads();
                }
            });
        } else {
            // Processing as standard chat (handles Pro mode OR Vision mode without image)
            await sendMessage(text, currentThreadId, {
                onComplete: () => refreshThreads()
            });
        }
    }

    // Model Selection Listeners
    // updating the and selection the pro model and vision model from ui
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
                imageInput.value = ''; // Reset file input
                imageUploadBtn.classList.add('hidden');
                imagePreviewContainer.classList.add('hidden');
                currentImageData = null;
                isNewImageForThread = true; // Reset flag
            }
        });

        modelVision.addEventListener('click', () => {
            setActiveModel('vision');
            modelVision.classList.add('active');
            modelPro.classList.remove('active');
            if (imageUploadBtn) imageUploadBtn.classList.remove('hidden');
        });
    }

    // Handle image upload and preview
    if (imageUploadBtn && imageInput) {
        imageUploadBtn.addEventListener('click', () => imageInput.click());
        
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    currentImageData = event.target.result; // Base64 string
                    isNewImageForThread = true; // Mark as NEW image
                    // Show preview
                    if (imagePreviewContainer && imagePreviewImg) {
                        imagePreviewImg.src = currentImageData;
                        imagePreviewContainer.classList.remove('hidden');
                        imageUploadBtn.style.color = '#9b72cb';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Remove preview logic
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
            // Start a new chat when the image is removed to give a fresh context
            currentThreadId = startNewChat();
            refreshThreads();
        });
    }

    // New chat button click logic updated
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            currentThreadId = startNewChat(refreshThreads);
            currentImageData = null;
            isNewImageForThread = true;
            if (imagePreviewContainer) imagePreviewContainer.classList.add('hidden');
        });
    }
});
