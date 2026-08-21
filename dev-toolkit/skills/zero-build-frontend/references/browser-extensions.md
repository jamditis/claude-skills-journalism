## Browser extension (Manifest V3)

### manifest.json

```json
{
  "manifest_version": 3,
  "name": "PocketLink",
  "version": "1.0.0",
  "description": "Create shortlinks from right-click context menu",

  "permissions": [
    "contextMenus",
    "storage",
    "activeTab",
    "scripting",
    "notifications",
    "offscreen"
  ],

  "background": {
    "service_worker": "background.js",
    "type": "module"
  },

  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },

  "options_page": "options.html",

  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### Service worker (background.js)

```javascript
// background.js - Service Worker

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'create-shortlink',
    title: 'Create Shortlink',
    contexts: ['page', 'link']
  });
});

// Handle context menu click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== 'create-shortlink') return;

  const url = info.linkUrl || info.pageUrl;

  try {
    const shortUrl = await createShortlink(url);
    await copyToClipboard(shortUrl);
    showNotification('Shortlink Created', shortUrl);
  } catch (error) {
    showNotification('Error', error.message);
  }
});

async function createShortlink(longUrl) {
  const { apiToken } = await chrome.storage.sync.get('apiToken');
  if (!apiToken) throw new Error('API token not configured');

  const response = await fetch('https://api-ssl.bitly.com/v4/shorten', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ long_url: longUrl })
  });

  if (!response.ok) throw new Error('API request failed');

  const data = await response.json();
  return data.link;
}

// Clipboard methods (three fallback strategies)

// Method 1: Offscreen API (preferred)
async function copyToClipboard(text) {
  try {
    await copyViaOffscreen(text);
  } catch {
    try {
      await copyViaContentScript(text);
    } catch {
      await copyViaPopup(text);
    }
  }
}

async function copyViaOffscreen(text) {
  await chrome.offscreen.createDocument({
    url: 'offscreen.html',
    reasons: ['CLIPBOARD'],
    justification: 'Copy shortlink to clipboard'
  });

  await chrome.runtime.sendMessage({ type: 'copy', text });
  await chrome.offscreen.closeDocument();
}

async function copyViaContentScript(text) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: (text) => navigator.clipboard.writeText(text),
    args: [text]
  });
}

function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title,
    message
  });
}
```

### Options page

```html
<!-- options.html -->
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Inline CSS for extension compliance (no remote code) */
    body {
      font-family: system-ui, sans-serif;
      padding: 20px;
      max-width: 400px;
      margin: 0 auto;
    }
    h1 { font-size: 1.5rem; margin-bottom: 1rem; }
    label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
    input {
      width: 100%;
      padding: 8px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-size: 14px;
    }
    button {
      margin-top: 1rem;
      padding: 10px 20px;
      background: #2dc8d2;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    button:hover { background: #25a8b0; }
    .status { margin-top: 1rem; padding: 10px; border-radius: 4px; }
    .success { background: #d4edda; color: #155724; }
    .error { background: #f8d7da; color: #721c24; }
  </style>
</head>
<body>
  <h1>PocketLink Settings</h1>

  <label for="apiToken">Bit.ly API Token</label>
  <input type="password" id="apiToken" placeholder="Enter your API token">

  <button id="save">Save Settings</button>

  <div id="status" class="status" style="display: none;"></div>

  <script src="options.js"></script>
</body>
</html>
```

```javascript
// options.js
document.addEventListener('DOMContentLoaded', async () => {
  const tokenInput = document.getElementById('apiToken');
  const saveButton = document.getElementById('save');
  const status = document.getElementById('status');

  // Load saved token
  const { apiToken } = await chrome.storage.sync.get('apiToken');
  if (apiToken) tokenInput.value = apiToken;

  saveButton.addEventListener('click', async () => {
    const token = tokenInput.value.trim();

    if (!token) {
      showStatus('Please enter an API token', 'error');
      return;
    }

    // Validate token by making test request
    try {
      const response = await fetch('https://api-ssl.bitly.com/v4/user', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Invalid token');

      await chrome.storage.sync.set({ apiToken: token });
      showStatus('Settings saved successfully!', 'success');
    } catch {
      showStatus('Invalid API token', 'error');
    }
  });

  function showStatus(message, type) {
    status.textContent = message;
    status.className = `status ${type}`;
    status.style.display = 'block';
    setTimeout(() => { status.style.display = 'none'; }, 3000);
  }
});
```
