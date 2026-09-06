
function getToolIcon(name) {
    const n = name.toLowerCase();
    if (n.includes('calculator')) return 'calculator';
    if (n.includes('search')) return 'search';
    if (n.includes('wiki')) return 'globe';
    if (n.includes('document') || n.includes('pdf')) return 'file-text';
    if (n.includes('expense') || n.includes('spent') || n.includes('budget')) return 'credit-card';
    if (n.includes('user') || n.includes('register')) return 'user-plus';
    return 'box';
}

export async function fetchStaticTools() {
    const staticToolList = document.getElementById('static-tool-list');
    if (!staticToolList) return;

    try {

        const response = await fetch('/api/tools/static');
        
        const data = await response.json();

        if (data.tools && data.tools.length > 0) {
            
            staticToolList.innerHTML = data.tools.map(tool =>
                `<div class="mcp-tool-item">
                    <i data-lucide="${getToolIcon(tool)}"></i>
                    <span class="tool-name">${tool.replace(/_/g, ' ')}</span>
                </div>`
            ).join('');
            
            if (window.lucide) lucide.createIcons();
        }

    } catch (e) {
        console.error("Failed to fetch static tools", e);
    }
}

export async function updateMCPStatus() {

    const mcpStatusText = document.getElementById('mcp-status-text');
    const mcpServerName = document.getElementById('mcp-server-name');
    const mcpToolCount = document.getElementById('mcp-tool-count');
    const mcpToolList = document.getElementById('mcp-tool-list');
    const connectMcpBtn = document.getElementById('connect-mcp-btn');
    const disconnectMcpBtn = document.getElementById('disconnect-mcp-btn');

    if (!mcpStatusText || !mcpToolCount || !connectMcpBtn || !mcpToolList) return;

    try {
        
        const response = await fetch('/api/mcp/status');
        
        const data = await response.json();

        if (data.connected) {
            
            mcpStatusText.textContent = 'Server is running';
            mcpStatusText.className = 'status-badge connected';

            if (mcpServerName) {
                
                mcpServerName.classList.remove('hidden');
                
                mcpServerName.innerHTML = `<i data-lucide="link"></i> ${data.url}`;
            }

            mcpToolCount.classList.remove('hidden');
            
            mcpToolCount.innerHTML = `<span>${data.tool_count} Active Tools</span> <i data-lucide="chevron-down"></i>`;

            disconnectMcpBtn.classList.remove('hidden');
            connectMcpBtn.classList.add('hidden');

            if (data.tools && data.tools.length > 0) {
                mcpToolList.innerHTML = data.tools.map(tool =>
                    `<div class="mcp-tool-item">
                        <i data-lucide="${getToolIcon(tool)}"></i>
                        <span class="tool-name">${tool.replace(/_/g, ' ')}</span>
                    </div>`
                ).join('');
            }
            if (window.lucide) lucide.createIcons();

        }
        
        else {
            mcpStatusText.textContent = 'Disconnected';
            mcpStatusText.className = 'status-badge disconnected';
            if (mcpServerName) mcpServerName.classList.add('hidden');
            mcpToolCount.classList.add('hidden');
            mcpToolList.classList.add('hidden');

            disconnectMcpBtn.classList.add('hidden');
            connectMcpBtn.classList.remove('hidden');
            connectMcpBtn.innerHTML = '<i data-lucide="unplug"></i> Connect Expense Tracker';
            if (window.lucide) lucide.createIcons();
        }

    } catch (e) {
        console.error("Failed to fetch MCP status", e);
    }

}

export async function connectMCPServer() {
    
    const connectMcpBtn = document.getElementById('connect-mcp-btn');
    
    if (!connectMcpBtn) return;

    connectMcpBtn.innerHTML = '<div class="loader-small"></div> Connecting...';
    connectMcpBtn.disabled = true;

    try {

        const response = await fetch('/api/mcp/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: 'https://render-expense-tracker-mlxb.onrender.com/sse' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateMCPStatus();
        }
        
        else {
            alert('Connection Failed: ' + data.message);
            updateMCPStatus();
        }

    }
    
    catch (error) {
        alert('Error connecting to MCP backend.');
        updateMCPStatus();
    }
    
    finally {
        connectMcpBtn.disabled = false;
    }

}

export async function disconnectMCPServer() {

    if (!confirm('Are you sure you want to disconnect from the MCP server?')) return;
    
    try {
        
        const response = await fetch('/api/mcp/disconnect', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateMCPStatus();
        }
        
        else {
            alert('Disconnection Failed: ' + data.message);
            updateMCPStatus();
        }

    }
    
    catch (error) {
        alert('Error disconnecting from MCP server.');
    }
}
