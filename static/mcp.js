// handle mcp server connection and tool fetching

/**
 * Gets a Lucide icon name based on the tool name.
 * @param {string} name - The name of the tool.
 * @returns {string} The icon name.
 */
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
/*
| Tool Name         | Output Icon   |
| ----------------- | ------------- |
| "search_document" | "search"      |
| "pdf_reader"      | "file-text"   |
| "add_expense"     | "credit-card" |
| "register_user"   | "user-plus"   |
| "random_tool"     | "box"         |
*/




// fetching static tools from the backend and updating the UI
export async function fetchStaticTools() {
    const staticToolList = document.getElementById('static-tool-list');
    if (!staticToolList) return;

    try {

        // calling this function @tools_router.get("/api/tools/static"
        const response = await fetch('/api/tools/static');
        //converting the response to json here we will get all static tools in data.tools
        const data = await response.json();

        //checking if the data.tools is not empty 
        if (data.tools && data.tools.length > 0) {
            //mapping the tools to the UI using map function
            //and joining them using join function
            //this will create a list of tools
            staticToolList.innerHTML = data.tools.map(tool =>
                `<div class="mcp-tool-item">
                    <i data-lucide="${getToolIcon(tool)}"></i>
                    <span class="tool-name">${tool.replace(/_/g, ' ')}</span>
                </div>`
            ).join('');
            //calling lucide.createIcons() to render the icons
            if (window.lucide) lucide.createIcons();
        }

        //catch block is used to handle the error
    } catch (e) {
        console.error("Failed to fetch static tools", e);
    }
}

//updating mcp conncetion to ui
export async function updateMCPStatus() {

    const mcpStatusText = document.getElementById('mcp-status-text');
    const mcpServerName = document.getElementById('mcp-server-name');
    const mcpToolCount = document.getElementById('mcp-tool-count');
    const mcpToolList = document.getElementById('mcp-tool-list');
    const connectMcpBtn = document.getElementById('connect-mcp-btn');
    const disconnectMcpBtn = document.getElementById('disconnect-mcp-btn');

    //checking if the elements are not empty
    if (!mcpStatusText || !mcpToolCount || !connectMcpBtn || !mcpToolList) return;

    try {
        //taking the status from the backend @tools_router.get("/api/mcp/status")
        const response = await fetch('/api/mcp/status');
        //converting the response to json here we will get all mcp tools
        const data = await response.json();

        //checking if the data.connected is true
        if (data.connected) {
            //updating the status text 
            mcpStatusText.textContent = 'Server is running';
            mcpStatusText.className = 'status-badge connected';

            //when connection is done show the server name and tool count
            if (mcpServerName) {
                //removing the hidden class from the server name
                mcpServerName.classList.remove('hidden');
                //server url and icon
                mcpServerName.innerHTML = `<i data-lucide="link"></i> ${data.url}`;
            }



            //reomving the hidden class from the tool count
            mcpToolCount.classList.remove('hidden');
            //tool count and icon
            mcpToolCount.innerHTML = `<span>${data.tool_count} Active Tools</span> <i data-lucide="chevron-down"></i>`;



            //disconnect button and connect button
            disconnectMcpBtn.classList.remove('hidden');
            connectMcpBtn.classList.add('hidden');

            //fetching tool list and also givng the tools icon
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
        //else block is used to handle the case when the connection is not established
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

        //handle error
    } catch (e) {
        console.error("Failed to fetch MCP status", e);
    }

}





//connection of mcp server
export async function connectMCPServer() {
    //taking the connect button from the ui
    const connectMcpBtn = document.getElementById('connect-mcp-btn');
    //if not connect button then return 
    if (!connectMcpBtn) return;

    connectMcpBtn.innerHTML = '<div class="loader-small"></div> Connecting...';
    connectMcpBtn.disabled = true;

    try {

        //fetcheing the mcp server url from the backend @tools_router.post("/api/mcp/connect")
        //here we are sending the mcp server url to the backend
        //the url is https://render-expense-tracker-mlxb.onrender.com/sse
        //this is the url of the mcp server
        const response = await fetch('/api/mcp/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: 'https://render-expense-tracker-mlxb.onrender.com/sse' })
        });
        //converting the response to json here we will get the success status
        const data = await response.json();
        //checking if the data.success is true
        if (data.success) {
            updateMCPStatus();
        }
        //else block is used to handle the case when the connection is not established
        else {
            alert('Connection Failed: ' + data.message);
            updateMCPStatus();
        }


    }
    //catch block is used to handle the error
    catch (error) {
        alert('Error connecting to MCP backend.');
        updateMCPStatus();
    }
    //Without finally
    //If error happens:
    // Button may stay disabled forever 
    // User can’t click again it runs 
    finally {
        connectMcpBtn.disabled = false;
    }


}






//disconnect mcp server
export async function disconnectMCPServer() {

    if (!confirm('Are you sure you want to disconnect from the MCP server?')) return;
    
    try {
        //here we are taking api mcp disconnect @tools_router.post("/api/mcp/disconnect")
        const response = await fetch('/api/mcp/disconnect', {
            method: 'POST'
        });
        //converting the response to json here we will get the success status
        const data = await response.json();
        //checking if the data.success is true
        if (data.success) {
            updateMCPStatus();
        }
        //else block is used to handle the case when the connection is not established
        else {
            alert('Disconnection Failed: ' + data.message);
            updateMCPStatus();
        }

    }
    //catch block is used to handle the error
    catch (error) {
        alert('Error disconnecting from MCP server.');
    }
}
