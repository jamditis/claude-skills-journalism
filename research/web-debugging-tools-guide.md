# Web Debugging Tools: Browser Extensions, Bookmarklets, and Console Access

A comprehensive guide to debugging web applications without desktop DevTools, especially useful for mobile development, remote debugging, and journalism/research workflows.

---

## Table of Contents

1. [In-Page JavaScript Consoles](#1-in-page-javascript-consoles)
2. [Mobile Browser Debugging](#2-mobile-browser-debugging)
3. [Bookmarklets for Debugging](#3-bookmarklets-for-debugging)
4. [Error Logging & Monitoring Services](#4-error-logging--monitoring-services)
5. [Browser Automation Tools](#5-browser-automation-tools)
6. [Comparison Table](#comparison-table)

---

## 1. In-Page JavaScript Consoles

These tools inject a developer console directly into the webpage, visible on mobile devices and any browser without DevTools access.

### Eruda

**Best for:** Full-featured mobile debugging with network monitoring

**Overview:**
Eruda is a comprehensive developer console for mobile browsers that runs as an in-browser overlay, providing a DevTools-like experience directly on the page.

**Key Features:**
- **Console**: Display JavaScript logs with color-coded levels
- **Elements**: Inspect and modify DOM state in real-time
- **Network**: Monitor HTTP requests, responses, and timing
- **Resources**: View localStorage, sessionStorage, cookies
- **Info**: Display URL, user agent, screen info
- **Snippets**: Store commonly used code snippets
- **Sources**: View HTML, CSS, JavaScript source code

**Setup Instructions:**

**Method 1: CDN Script Tag**
```html
<script src="https://cdn.jsdelivr.net/npm/eruda"></script>
<script>eruda.init();</script>
```

**Method 2: npm Installation**
```bash
npm install eruda --save-dev
```

```javascript
import eruda from 'eruda';
eruda.init();
```

**Method 3: Bookmarklet** (see Bookmarklets section)

**Important Notes:**
- File size: ~100kb gzipped
- Not recommended for production (use only for debugging)
- Works on all modern mobile and desktop browsers

**URLs:**
- Website: https://eruda.liriliri.io/
- GitHub: https://github.com/liriliri/eruda
- npm: https://www.npmjs.com/package/eruda

---

### vConsole

**Best for:** Lightweight console for WeChat Mini Programs and mobile web

**Overview:**
vConsole is Tencent's lightweight, extendable front-end developer tool, now the official debugging tool for WeChat Miniprograms. It's lighter than Eruda with a simpler UI.

**Key Features:**
- Log, Info, Warn, Error console output
- System information display
- Network request monitoring
- Element inspection
- Storage viewer (cookies, localStorage, sessionStorage)
- Custom plugin support
- Dark theme support (v3.4.0+)

**Setup Instructions:**

**Method 1: CDN**
```html
<script src="https://unpkg.com/vconsole@latest/dist/vconsole.min.js"></script>
<script>
  // VConsole will be exported to `window.VConsole` by default
  var vConsole = new window.VConsole();
</script>
```

Alternative CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/vconsole@latest/dist/vconsole.min.js"></script>
```

**Method 2: npm (Recommended)**
```bash
npm install vconsole
```

```javascript
import VConsole from 'vconsole';

const vConsole = new VConsole();
// or init with options
const vConsole = new VConsole({ theme: 'dark' });

// Use console methods as usual
console.log('Hello world');

// Remove when finished debugging
vConsole.destroy();
```

**Configuration Options:**
- `theme`: 'light' or 'dark' (default: 'light')
- `target`: Custom DOM element to mount vConsole
- `pluginOrder`: Adjust tab order
- `maxLogNumber`: Limit console log entries
- `maxNetworkNumber`: Limit network request entries

**URLs:**
- GitHub: https://github.com/Tencent/vConsole
- npm: https://www.npmjs.com/package/vconsole
- Live Demo: http://wechatfe.github.io/vconsole/demo.html

**Comparison: Eruda vs vConsole**

| Feature | Eruda | vConsole |
|---------|-------|----------|
| File Size | ~100kb gzipped | ~85kb gzipped |
| Features | Full-featured, more panels | Lightweight, essential features |
| Best For | Comprehensive debugging | Quick console access |
| Maintenance | Active | Active (Tencent official) |
| Mobile Screen | Can feel cramped | More optimized |

---

## 2. Mobile Browser Debugging

### Remote Debugging (Native Tools)

**Chrome on Android:**

1. Enable USB debugging on Android device:
   - Settings → About Phone → Tap "Build Number" 7 times
   - Settings → Developer Options → Enable "USB Debugging"

2. Connect device to computer via USB

3. On desktop Chrome, navigate to: `chrome://inspect`

4. Select your device and click "Inspect"

**Full DevTools access:** Console, Network, Elements, Performance, etc.

**Documentation:** https://www.browserstack.com/guide/debug-website-on-android-chrome

---

**Safari on iOS:**

1. On iPhone/iPad:
   - Settings → Safari → Advanced → Enable "Web Inspector"

2. On Mac:
   - Safari → Preferences → Advanced → "Show Develop menu in menu bar"

3. Connect device via USB/cable

4. On Mac: Develop menu → [Your Device] → Select page to inspect

**Limitations:** Requires macOS; Windows users need alternatives

---

### Browser Extensions for Debugging

**Firefox Developer Tools:**
- Built-in responsive design mode
- Remote debugging via USB and WiFi
- Console, Network, Inspector all available
- **Setup:** No extension needed, built into Firefox

**Web Developer Extension (Firefox & Chrome):**
- Toolbar with debugging features
- CSS inspection and validation
- Form manipulation
- Cookie management
- **Install:** https://chromewebstore.google.com/detail/web-developer (Chrome)
- **GitHub:** https://github.com/chrispederick/web-developer

**JSON Viewer Pro (Chrome):**
- Beautifies JSON responses with syntax highlighting
- Collapsible nodes and search
- Useful for API debugging
- **Install:** Chrome Web Store → Search "JSON Viewer Pro"

---

### Third-Party Testing Platforms

**BrowserStack:**
- Test on real mobile devices remotely
- Integrated Chrome DevTools on iOS & Android
- Network throttling, geolocation testing
- **URL:** https://www.browserstack.com/
- **Pricing:** Starts at $29/month

**LambdaTest:**
- Cross-browser testing platform
- Real device cloud with DevTools
- Screenshot and video recording
- **URL:** https://www.lambdatest.com/
- **Pricing:** Free tier available; paid starts at $15/month

---

## 3. Bookmarklets for Debugging

Bookmarklets are JavaScript snippets saved as browser bookmarks that execute on the current page. They work on most browsers including mobile Safari and Chrome.

### How to Create a Bookmarklet

1. Create a new bookmark in your browser
2. Name it descriptively (e.g., "Debug Console")
3. For the URL/location, use: `javascript:(function(){/* your code */})();`
4. Click the bookmark on any page to run it

**Best Practice Pattern:**
```javascript
javascript:(function(){
  // Your debugging code here
  console.log('Bookmarklet executed!');
})();
```

---

### Recommended Debugging Bookmarklets

#### 1. Eruda Injector Bookmarklet

```javascript
javascript:(function(){var script=document.createElement('script');script.src='https://cdn.jsdelivr.net/npm/eruda';document.body.append(script);script.onload=function(){eruda.init();}})();
```

**What it does:** Dynamically loads Eruda console on any webpage

**Use case:** Quick debugging on mobile devices without DevTools access

---

#### 2. vConsole Injector Bookmarklet

```javascript
javascript:(function(){var script=document.createElement('script');script.src='https://unpkg.com/vconsole@latest/dist/vconsole.min.js';document.body.append(script);script.onload=function(){new VConsole();}})();
```

**What it does:** Loads vConsole on the current page

---

#### 3. Mobile Console Bookmarklet

**Project:** mobile-console by David Calhoun

**Features:**
- Overrides `console.log()` to display on-screen
- Creates expandable console at bottom of page
- Optionally sends logs to remote server for viewing
- Perfect for devices where remote debugging isn't available

**Setup:**
```javascript
// Bookmarklet code available at:
// https://github.com/davidcalhoun/mobile-console
```

**GitHub:** https://github.com/davidcalhoun/mobile-console

---

#### 4. Firebug Lite Bookmarklet (Legacy)

**Note:** Firebug is discontinued (2017) but Firebug Lite still works as bookmarklet

```javascript
javascript:(function(F,i,r,e,b,u,g,L,I,T,E){if(F.getElementById(b))return;E=F[i+'NS']&&F.documentElement.namespaceURI;E=E?F[i+'NS'](E,'script'):F[i]('script');E[r]('id',b);E[r]('src',I+g+T);E[r](b,u);(F[e]('head')[0]||F[e]('body')[0]).appendChild(E);E=new%20Image;E[r]('src',I+L);})(document,'createElement','setAttribute','getElementsByTagName','FirebugLite','4','firebug-lite.js','releases/lite/latest/skin/xp/sprite.png','https://getfirebug.com/','#startOpened');
```

**Modern Alternatives:**
- Use Eruda or vConsole instead
- Firefox Developer Tools
- Chrome DevTools

**Reference:** http://marklets.com/Firebug%20Lite.aspx

---

#### 5. View All Links Bookmarklet

```javascript
javascript:(function(){console.log([...document.querySelectorAll('a')].map(a=>a.href));})();
```

**What it does:** Logs all URLs on the page to console (useful with Eruda/vConsole)

---

#### 6. Debugger Breakpoint Bookmarklet

```javascript
javascript:(function(){debugger;})();
```

**What it does:** Pauses JavaScript execution immediately (if DevTools open)

**Use case:** Freeze transient DOM states (hover menus, tooltips, etc.)

---

#### 7. Mobile Perf Bookmarklet

**Author:** Steve Souders

**Features:**
- Performance metrics for mobile
- Page load timing
- Resource analysis
- Network waterfall

**URL:** https://stevesouders.com/mobileperf/mobileperfbkm.php

---

### Bookmarklet Limitations on Mobile

**Important Notes:**
- iOS Safari: Bookmarklets work but require typing bookmark name in address bar
- Some mobile browsers block `javascript:` URLs in address bar for security
- Solution: Create actual browser bookmarks with the javascript: code
- Android Chrome: May require enabling "Desktop site" for some bookmarklets

---

## 4. Error Logging & Monitoring Services

These services capture JavaScript errors, console logs, and user sessions remotely, essential for production debugging.

---

### Sentry

**Best for:** Comprehensive error tracking with performance monitoring

**Overview:**
Sentry is the most popular open-source error tracking platform, offering detailed error context, stack traces, and performance monitoring.

**Key Features:**
- Real-time error tracking with full stack traces
- Source map support for minified code
- Release tracking and regression detection
- Breadcrumbs (events leading to error)
- Performance monitoring (transaction tracing)
- User feedback integration
- Machine learning for error grouping
- Custom tags and context
- 100+ integrations (Slack, Jira, GitHub, etc.)

**Supported Platforms:**
JavaScript, Python, Ruby, Node.js, Go, React, Angular, Vue, Swift, Java, PHP, Laravel, Rails, and 50+ more

**Pricing (2025):**
- **Developer (Free):** 5,000 errors/month, 1 user
- **Team ($26/month):** 50,000 errors/month, performance monitoring
- **Business ($80/month):** Advanced features, more quota
- **Enterprise:** Custom pricing

**Setup Instructions:**

**JavaScript (Browser):**
```bash
npm install @sentry/browser
```

```javascript
import * as Sentry from "@sentry/browser";

Sentry.init({
  dsn: "YOUR_DSN_HERE",
  integrations: [new Sentry.BrowserTracing()],
  tracesSampleRate: 1.0, // Adjust for production
});
```

**React:**
```bash
npm install @sentry/react
```

```javascript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "YOUR_DSN_HERE",
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay()
  ],
  tracesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

**URLs:**
- Website: https://sentry.io/
- Documentation: https://docs.sentry.io/
- GitHub: https://github.com/getsentry/sentry

**When to Choose Sentry:**
- Need balanced error + performance monitoring
- Want open-source option (self-hosted available)
- Excellent developer experience required
- Budget-conscious teams (best value)

---

### LogRocket

**Best for:** Session replay and understanding user behavior during errors

**Overview:**
LogRocket records everything users do—mouse movements, clicks, console logs, network requests—allowing you to replay sessions like a video.

**Key Features:**
- **Session Replay:** Watch exact user interactions leading to errors
- Console log recording (browser-side)
- Network monitoring with request/response bodies
- Redux/Vuex state inspection
- DOM mutations and state changes
- User identification and segmentation
- Performance monitoring
- Error tracking with full context
- Funnel analysis
- Integration with Sentry, Bugsnag, etc.

**Supported Platforms:**
JavaScript, React, Angular, Vue, Ember, Redux, Gatsby, Next.js, React Native

**Pricing (2025):**
- **Developer (Free):** 1,000 sessions/month
- **Team ($99/month):** 10,000 sessions/month
- **Professional ($249/month):** 25,000 sessions/month
- **Enterprise:** Custom pricing

**Setup Instructions:**

```bash
npm install logrocket
```

```javascript
import LogRocket from 'logrocket';

LogRocket.init('YOUR_APP_ID/your-project-name');

// Identify users
LogRocket.identify('USER_ID', {
  name: 'John Doe',
  email: 'john@example.com',
});

// Track custom events
LogRocket.track('Button Clicked', {
  buttonName: 'Subscribe',
});
```

**Integration with Sentry:**
```javascript
import LogRocket from 'logrocket';
import * as Sentry from '@sentry/browser';

LogRocket.getSessionURL(sessionURL => {
  Sentry.configureScope(scope => {
    scope.setExtra('sessionURL', sessionURL);
  });
});
```

**URLs:**
- Website: https://logrocket.com/
- Documentation: https://docs.logrocket.com/

**When to Choose LogRocket:**
- Need to see exact user behavior during bugs
- Debugging race conditions, UI glitches
- Understanding user workflows
- Frontend-focused teams
- Budget allows premium pricing

---

### Bugsnag

**Best for:** Mobile app error tracking and enterprise stability monitoring

**Overview:**
Bugsnag excels at mobile error tracking with specialized handling for iOS/Android crashes, ANR (Application Not Responding), and OOM (Out Of Memory) events.

**Key Features:**
- Automatic error grouping by root cause
- Stability scoring by release
- ANR and OOM detection (mobile)
- Breadcrumbs and custom metadata
- Release health monitoring
- User impact analysis
- Advanced enterprise permissions
- Compliance reporting (SOC2, GDPR)
- Source map support
- Real-time alerting

**Supported Platforms:**
JavaScript, React, React Native, Node.js, Ruby, Python, Java, Android, iOS, Unity, Unreal Engine, and more

**Pricing (2025):**
- **Free:** 7,500 events/month
- **Standard ($59/month):** 50,000 events/month
- **Pro ($249/month):** 250,000 events/month
- **Enterprise:** Custom (typically 40-50% higher than Sentry)

**Setup Instructions:**

**JavaScript (Browser):**
```bash
npm install @bugsnag/js
```

```javascript
import Bugsnag from '@bugsnag/js'

Bugsnag.start({
  apiKey: 'YOUR_API_KEY',
  enabledReleaseStages: ['production', 'staging'],
  releaseStage: 'production',
})

// Notify manually
try {
  riskyOperation()
} catch (error) {
  Bugsnag.notify(error)
}
```

**React:**
```bash
npm install @bugsnag/js @bugsnag/plugin-react
```

```javascript
import Bugsnag from '@bugsnag/js'
import BugsnagPluginReact from '@bugsnag/plugin-react'
import React from 'react'

Bugsnag.start({
  apiKey: 'YOUR_API_KEY',
  plugins: [new BugsnagPluginReact()],
})

const ErrorBoundary = Bugsnag.getPlugin('react')
  .createErrorBoundary(React)

// Wrap your app
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

**URLs:**
- Website: https://www.bugsnag.com/
- Documentation: https://docs.bugsnag.com/

**When to Choose Bugsnag:**
- Mobile-first applications (iOS/Android)
- Enterprise compliance requirements
- Need advanced user permissions
- Prefer stability scoring features

---

### TrackJS

**Best for:** Frontend-specific JavaScript error monitoring

**Overview:**
TrackJS is laser-focused on frontend JavaScript errors with deep browser insights and telemetry timelines.

**Key Features:**
- Telemetry timeline (events before error)
- Browser-specific error tracking
- Network request monitoring
- User session tracking
- Advanced filtering (no query language needed)
- Unlimited server-side ignore rules
- Visitor identification
- Custom context and metadata

**Supported Platforms:**
JavaScript, React, Angular, Vue, Ember, Backbone, jQuery, and any JS framework

**Pricing (2025):**
- **Trial:** 30 days free
- **Professional ($99/month):** Up to 1 million page views, unlimited errors
- **Enterprise:** Custom pricing

**Value Proposition:**
Priced by page views (not errors), so more bugs don't cost more. Significantly cheaper than competitors (75% less than LogRocket for similar features).

**Setup Instructions:**

```html
<!-- Include before other scripts -->
<script src="https://cdn.trackjs.com/releases/current/tracker.js"
        data-token="YOUR_TOKEN">
</script>
```

**Advanced Setup:**
```javascript
TrackJS.install({
  token: "YOUR_TOKEN",
  application: "my-app",

  // Capture context
  onError: function(payload) {
    payload.userId = getCurrentUserId();
    payload.version = APP_VERSION;
    return true; // return false to ignore error
  }
});
```

**URLs:**
- Website: https://trackjs.com/
- Documentation: https://docs.trackjs.com/

**When to Choose TrackJS:**
- Pure frontend focus (JavaScript only)
- Budget-conscious teams
- Want unlimited errors per plan
- Prefer page view pricing model

---

### Rollbar

**Best for:** Full-stack error tracking (frontend + backend)

**Overview:**
Rollbar provides centralized error management across frontend and backend with strong DevOps focus.

**Key Features:**
- Real-time AI-assisted error workflows
- Error prediction and prevention
- Full-stack coverage (frontend + backend)
- Deployment tracking
- Custom grouping rules
- Version tracking
- Integrations with CI/CD pipelines
- Team collaboration features
- Advanced dashboards

**Supported Platforms:**
JavaScript, Python, Ruby, PHP, Node.js, Java, .NET, Go, iOS, Android, and 50+ frameworks

**Pricing (2025):**
- **Free:** 5,000 events/month
- **Essentials ($25/month):** 25,000 events/month
- **Advanced ($99/month):** 100,000 events/month
- **Enterprise:** Custom

**Pricing Model:** Per-error event (more bugs = higher cost)

**Setup Instructions:**

**JavaScript:**
```bash
npm install rollbar
```

```javascript
import Rollbar from 'rollbar';

const rollbar = new Rollbar({
  accessToken: 'YOUR_ACCESS_TOKEN',
  captureUncaught: true,
  captureUnhandledRejections: true,
  environment: 'production',
});

// Log errors
rollbar.error('Something went wrong', error);

// Add context
rollbar.configure({
  payload: {
    person: {
      id: userId,
      username: userName,
      email: userEmail,
    }
  }
});
```

**URLs:**
- Website: https://rollbar.com/
- Documentation: https://docs.rollbar.com/

**When to Choose Rollbar:**
- Need full-stack error management
- DevOps-focused teams
- Want AI-assisted error workflows
- Managing complex multi-service architectures

---

### Comparison Table: Error Monitoring Services

| Service | Best For | Pricing (Entry) | Session Replay | Performance Monitoring | Mobile Focus | Open Source |
|---------|----------|-----------------|----------------|----------------------|--------------|-------------|
| **Sentry** | Balanced error + performance | $26/month | Limited | ✅ Yes | Good | ✅ Yes |
| **LogRocket** | Session replay & UX debugging | $99/month | ✅ Excellent | ✅ Yes | Limited | ❌ No |
| **Bugsnag** | Mobile apps & enterprise | $59/month | ❌ No | Limited | ✅ Excellent | ❌ No |
| **TrackJS** | Frontend JavaScript only | $99/month | ❌ No | ❌ No | Limited | ❌ No |
| **Rollbar** | Full-stack DevOps | $25/month | ❌ No | Limited | Good | ❌ No |

**Value Analysis (2025):**
- **Best Value:** Sentry ($26 for 50k errors + performance monitoring)
- **Most Expensive:** LogRocket ($99, but includes session replay)
- **Best for Startups:** Sentry (generous free tier, open source)
- **Best for Enterprise:** Bugsnag or Rollbar

---

### Using Multiple Services Together

**Common Combinations:**

1. **Sentry + LogRocket:**
   - Sentry for error alerting
   - LogRocket for session replay on critical errors
   - Integration: Attach LogRocket session URL to Sentry errors

2. **Bugsnag + Internal Logging:**
   - Bugsnag for production errors
   - Custom logging for business metrics

3. **TrackJS + Backend Monitor:**
   - TrackJS for frontend
   - Separate service for backend (e.g., Sentry, Rollbar)

---

## 5. Browser Automation Tools

These tools programmatically control browsers and can capture console output, useful for automated testing and monitoring.

---

### Playwright

**Best for:** Modern cross-browser automation with excellent developer experience

**Overview:**
Playwright is Microsoft's next-generation browser automation framework, built by the original Puppeteer team. It supports Chromium, Firefox, and WebKit (Safari) with a unified API.

**Key Features:**
- Multi-browser support (Chromium, Firefox, WebKit)
- Auto-waiting for elements (reduces flaky tests)
- Network interception and mocking
- Geolocation, permissions, and device emulation
- Screenshot and video recording
- Trace viewer with timeline
- Console log capture
- Mobile browser testing
- Headless and headed modes
- Parallel test execution

**Supported Languages:**
JavaScript/TypeScript, Python, .NET, Java

**Console Log Capture:**

**JavaScript/TypeScript:**
```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Capture console logs
  const logs = [];
  page.on('console', msg => {
    logs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });

  // Listen for errors only
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`Error: ${msg.text()}`);
    }
  });

  await page.goto('https://example.com');

  // View captured logs
  console.log(logs);

  await browser.close();
})();
```

**Python:**
```python
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()

    # Capture console logs
    logs = []
    page.on("console", lambda msg: logs.append({
        "type": msg.type,
        "text": msg.text
    }))

    # Or handle errors only
    page.on("console", lambda msg:
        print(f"Error: {msg.text}") if msg.type == "error" else None
    )

    page.goto("https://example.com")

    print(logs)
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
```

**Supported Console Types:**
log, debug, info, error, warning, dir, dirxml, table, trace, clear, startGroup, startGroupCollapsed, endGroup, assert, profile, profileEnd, count, timeEnd

**Installation:**

```bash
# Node.js
npm install -D @playwright/test
npx playwright install

# Python
pip install playwright
playwright install

# .NET
dotnet add package Microsoft.Playwright
pwsh bin/Debug/net6.0/playwright.ps1 install

# Java
mvn dependency:add -Dartifact=com.microsoft.playwright:playwright:VERSION
```

**URLs:**
- Website: https://playwright.dev/
- Documentation: https://playwright.dev/docs/intro
- GitHub: https://github.com/microsoft/playwright

**When to Choose Playwright:**
- Modern web apps with React, Vue, Angular
- Cross-browser testing required
- Need mobile browser testing (iOS Safari, Android Chrome)
- Want best-in-class developer experience
- Prefer auto-waiting over manual waits

---

### Puppeteer

**Best for:** Chrome/Chromium-specific automation with simple API

**Overview:**
Puppeteer is Google Chrome's official Node.js library for controlling headless Chrome via the DevTools Protocol.

**Key Features:**
- Chrome/Chromium only (fastest for Chrome)
- PDF generation from web pages
- Screenshot capture
- Performance profiling
- Network interception
- Console log capture
- Form automation
- Crawler and scraping
- Simpler API than Selenium

**Supported Languages:**
JavaScript/Node.js primarily (community ports for other languages)

**Console Log Capture:**

```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // Capture all console logs
  page.on('console', msg => {
    console.log(`${msg.type()}: ${msg.text()}`);
  });

  // Handle console errors specifically
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('Browser error:', msg.text());
    }
  });

  // Capture console arguments
  page.on('console', async msg => {
    const msgArgs = msg.args();
    for (let i = 0; i < msgArgs.length; i++) {
      console.log(await msgArgs[i].jsonValue());
    }
  });

  await page.goto('https://example.com');

  await browser.close();
})();
```

**Installation:**

```bash
npm install puppeteer
```

**URLs:**
- Website: https://pptr.dev/
- Documentation: https://pptr.dev/api/
- GitHub: https://github.com/puppeteer/puppeteer

**When to Choose Puppeteer:**
- Chrome-only automation is sufficient
- Need PDF generation from HTML
- Prefer simpler, more focused API
- Building web scrapers
- Google ecosystem preference

---

### Selenium

**Best for:** Legacy browser support and multi-language requirements

**Overview:**
Selenium is the oldest and most established browser automation framework (since 2004). It uses WebDriver protocol and supports the widest range of browsers.

**Key Features:**
- Broadest browser support (Chrome, Firefox, Edge, Safari, Opera, IE)
- Widest language support (Java, Python, C#, Ruby, JavaScript, Kotlin)
- Mature ecosystem with extensive documentation
- Grid support for distributed testing
- Mobile testing (Appium integration)
- Stable and battle-tested
- Active community

**Console Log Capture:**

**JavaScript (Node.js):**
```javascript
const { Builder, Browser } = require('selenium-webdriver');

(async function example() {
  const driver = await new Builder()
    .forBrowser(Browser.CHROME)
    .build();

  try {
    await driver.get('https://example.com');

    // Get browser console logs
    const logs = await driver.manage().logs().get('browser');
    logs.forEach(log => {
      console.log(`[${log.level.name}] ${log.message}`);
    });

  } finally {
    await driver.quit();
  }
})();
```

**Python:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://example.com")

# Get console logs
logs = driver.get_log('browser')
for log in logs:
    print(f"[{log['level']}] {log['message']}")

driver.quit()
```

**Java:**
```java
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.logging.LogEntries;
import org.openqa.selenium.logging.LogEntry;

WebDriver driver = new ChromeDriver();
driver.get("https://example.com");

LogEntries logs = driver.manage().logs().get("browser");
for (LogEntry log : logs) {
    System.out.println(log.getLevel() + " " + log.getMessage());
}

driver.quit();
```

**Installation:**

```bash
# Python
pip install selenium

# Node.js
npm install selenium-webdriver

# Java (Maven)
# Add to pom.xml:
# <dependency>
#   <groupId>org.seleniumhq.selenium</groupId>
#   <artifactId>selenium-java</artifactId>
#   <version>4.x.x</version>
# </dependency>
```

**Browser Drivers Required:**
- ChromeDriver for Chrome
- GeckoDriver for Firefox
- EdgeDriver for Edge
- SafariDriver (built-in macOS)

**URLs:**
- Website: https://www.selenium.dev/
- Documentation: https://www.selenium.dev/documentation/
- GitHub: https://github.com/SeleniumHQ/selenium

**When to Choose Selenium:**
- Need multi-language support (Java, C#, Ruby, etc.)
- Legacy browser testing (IE11, older Firefox)
- Team already experienced with Selenium
- Selenium Grid infrastructure in place
- Maximum browser compatibility required

---

### Comparison Table: Browser Automation Tools

| Feature | Playwright | Puppeteer | Selenium |
|---------|-----------|-----------|----------|
| **Browser Support** | Chromium, Firefox, WebKit | Chrome, Chromium only | Chrome, Firefox, Safari, Edge, Opera, IE |
| **Language Support** | JS, Python, .NET, Java | JavaScript/Node.js | Java, Python, C#, Ruby, JS, Kotlin |
| **Auto-Waiting** | ✅ Yes | ❌ No | ❌ No |
| **Performance** | Fast (WebSocket) | Fastest (DevTools Protocol) | Slower (WebDriver HTTP) |
| **Learning Curve** | Moderate | Easy | Moderate-Hard |
| **Mobile Testing** | ✅ Yes (iOS/Android) | ❌ No | ✅ Yes (via Appium) |
| **Trace/Debug Tools** | ✅ Excellent | Good | Basic |
| **Best For** | Modern cross-browser testing | Chrome-specific automation | Enterprise, multi-language |
| **Release Year** | 2020 | 2017 | 2004 |

**Recommendation:**
- **Choose Playwright** for modern web apps requiring cross-browser testing
- **Choose Puppeteer** for Chrome-specific tasks, PDF generation, or simpler API
- **Choose Selenium** for legacy browser support or non-JavaScript languages

---

## Comparison Table

### Quick Reference: All Tools at a Glance

| Category | Tool | Platform | Cost | Best Use Case |
|----------|------|----------|------|---------------|
| **In-Page Console** | Eruda | Browser | Free | Full-featured mobile debugging |
| **In-Page Console** | vConsole | Browser | Free | Lightweight console for mobile |
| **Bookmarklet** | Eruda Injector | Browser | Free | Quick debug injection |
| **Bookmarklet** | Mobile Console | Browser | Free | On-device console display |
| **Error Monitoring** | Sentry | Cloud | Free-$26+ | Best value, error + performance |
| **Error Monitoring** | LogRocket | Cloud | Free-$99+ | Session replay & UX debugging |
| **Error Monitoring** | Bugsnag | Cloud | Free-$59+ | Mobile apps & enterprise |
| **Error Monitoring** | TrackJS | Cloud | $99+ | Frontend JavaScript focus |
| **Error Monitoring** | Rollbar | Cloud | Free-$25+ | Full-stack DevOps |
| **Automation** | Playwright | Node/Python/.NET/Java | Free | Cross-browser, modern apps |
| **Automation** | Puppeteer | Node.js | Free | Chrome-specific automation |
| **Automation** | Selenium | Multi-language | Free | Legacy browsers, enterprise |

---

## Setup Workflow Examples

### Scenario 1: Debug Mobile Website on Phone

**Goal:** See console errors on a live mobile site without desktop

**Solution:**

1. Add Eruda bookmarklet to mobile browser:
   - Copy Eruda bookmarklet code (see Bookmarklets section)
   - Create new bookmark in mobile browser
   - Navigate to problem site
   - Tap bookmarklet to activate console

**Alternative:** Add vConsole script tag if you control the site

---

### Scenario 2: Monitor Production JavaScript Errors

**Goal:** Capture and alert on errors in production app

**Solution:**

1. Install Sentry (best value):
   ```bash
   npm install @sentry/react
   ```

2. Initialize in your app:
   ```javascript
   import * as Sentry from "@sentry/react";

   Sentry.init({
     dsn: "YOUR_DSN",
     environment: "production",
     tracesSampleRate: 0.1, // 10% performance monitoring
   });
   ```

3. Configure alerts in Sentry dashboard

---

### Scenario 3: Automated Testing with Console Capture

**Goal:** Run automated tests and capture browser console errors

**Solution using Playwright:**

```javascript
const { test, expect } = require('@playwright/test');

test('Check for console errors', async ({ page }) => {
  const errors = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  await page.goto('https://yoursite.com');

  // Assert no console errors
  expect(errors).toHaveLength(0);
});
```

---

### Scenario 4: Debug Customer-Reported Issue

**Goal:** See exactly what customer experienced during bug

**Solution:**

1. Use LogRocket for session replay:
   ```bash
   npm install logrocket
   ```

2. Initialize with user identification:
   ```javascript
   import LogRocket from 'logrocket';

   LogRocket.init('app-id');
   LogRocket.identify(userId, {
     name: userName,
     email: userEmail
   });
   ```

3. When customer reports bug, search for their session in LogRocket dashboard
4. Watch replay to see exact interactions and console errors

---

## Best Practices

### For Mobile Debugging:

1. **Start with bookmarklets** (Eruda/vConsole) for quick debugging
2. **Use remote debugging** (Chrome DevTools, Safari Web Inspector) for deeper inspection
3. **Keep production clean** - Remove debug tools before deploying
4. **Test on real devices** when possible (emulators miss device-specific bugs)

### For Error Monitoring:

1. **Implement early** - Add error tracking before launch
2. **Set up alerts** - Get notified of new errors immediately
3. **Add context** - Include user ID, release version, environment
4. **Filter noise** - Ignore third-party script errors
5. **Track releases** - Correlate errors with deployments
6. **Respect privacy** - Sanitize PII from error reports

### For Automation:

1. **Choose tool based on needs** - Don't use Selenium if Playwright works
2. **Capture screenshots** on test failures
3. **Save console logs** to artifacts for debugging
4. **Run headless in CI/CD** for faster execution
5. **Use headed mode** when developing tests locally

---

## Additional Resources

### Browser DevTools Documentation:
- Chrome DevTools: https://developer.chrome.com/docs/devtools/
- Firefox Developer Tools: https://firefox-source-docs.mozilla.org/devtools-user/
- Safari Web Inspector: https://webkit.org/web-inspector/

### Testing Platforms:
- BrowserStack: https://www.browserstack.com/
- LambdaTest: https://www.lambdatest.com/
- Sauce Labs: https://saucelabs.com/

### Remote Debugging:
- Weinre (Web Inspector Remote): https://people.apache.org/~pmuellr/weinre/
- Chii (Remote debugging tool): https://github.com/liriliri/chii

### Learning Resources:
- MDN Web Docs - Debugging: https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Cross_browser_testing
- Playwright University: https://playwright.dev/docs/intro
- Selenium Documentation: https://www.selenium.dev/documentation/

---

## Summary & Recommendations

### Quick Decision Guide:

**I need to debug a mobile website right now:**
→ Use **Eruda bookmarklet** (30 seconds to set up)

**I need to monitor production errors:**
→ Use **Sentry** (best value, comprehensive features)

**I need to see what users experienced during bugs:**
→ Use **LogRocket** (session replay is invaluable)

**I need to automate browser testing:**
→ Use **Playwright** (modern, cross-browser, excellent DX)

**I'm building a mobile app:**
→ Use **Bugsnag** (best mobile error tracking)

**I only care about Chrome automation:**
→ Use **Puppeteer** (simpler API, faster)

**I have a legacy enterprise app:**
→ Use **Selenium** (widest browser support)

---

## Sources

This guide was compiled from the following sources:

### Mobile Debugging & Extensions:
- [Debug with Native Browser Tools | LambdaTest](https://www.lambdatest.com/developer-tools)
- [Top Browser Extensions Every Developer Should Install in 2025 | Medium](https://medium.com/@somendradev23/top-browser-extensions-every-developer-should-install-in-2025-0e4155b73226)
- [How to Remotely Debug Websites on Android Chrome | BrowserStack](https://www.browserstack.com/guide/debug-website-on-android-chrome)
- [Top 15 Debugging Tools in 2025 | BrowserStack](https://www.browserstack.com/guide/debugging-tools)
- [How to Perform Mobile Browser Debugging | BrowserStack](https://www.browserstack.com/guide/mobile-browser-debugging)

### Eruda & vConsole:
- [GitHub - liriliri/eruda: Console for mobile browsers](https://github.com/liriliri/eruda)
- [Eruda - Console for Mobile Browsers](https://eruda.liriliri.io/)
- [eruda - npm](https://www.npmjs.com/package/eruda/v/3.0.1)
- [Console in Android Mobile Browser Using Eruda - DEV Community](https://dev.to/cwrcode/console-in-android-mobile-browser-using-eruda-how-to-use-eruda-3n3b)
- [GitHub - Tencent/vConsole](https://github.com/Tencent/vConsole)
- [vconsole - npm](https://www.npmjs.com/package/vconsole)
- [Getting Started | vConsole | DeepWiki](https://deepwiki.com/Tencent/vConsole/2-getting-started)

### Bookmarklets:
- [The Magic of Bookmarklets | Medium](https://medium.com/@pkrystkiewicz/the-magic-of-bookmarklets-40c815823217)
- [GitHub - davidcalhoun/mobile-console](https://github.com/davidcalhoun/mobile-console)
- [Quick Console bookmarklet for Desktop and Mobile](https://paul.kinlan.me/quick-console-bookmarklet-for-desktop-and-mobile/)
- [Introduction to Bookmarklets | DEV Community](https://dev.to/ahandsel/introduction-to-bookmarklets-javascript-everywhere-280m)
- [Ben Alman » Bookmarklets](https://benalman.com/projects/bookmarklets/)
- [Browser debugging with bookmarklets](https://palmo.xyz/post/20200907-browser-debugging-with-bookmarklets/)
- [Mobile Perf bookmarklet](https://stevesouders.com/mobileperf/mobileperfbkm.php)
- [10 Best Firebug Alternatives](https://alternative.me/firebug)
- [Firebug Lite Bookmarklet](http://marklets.com/Firebug%20Lite.aspx)

### Error Monitoring Services:
- [LogRocket vs Sentry - Compare Pricing & Features | TrackJS](https://trackjs.com/compare/logrocket-vs-sentry/)
- [Sentry vs LogRocket - Compare Pricing & Features | TrackJS](https://trackjs.com/compare/sentry-vs-logrocket/)
- [Sentry vs BugSnag - Compare Pricing & Features | TrackJS](https://trackjs.com/compare/sentry-vs-bugsnag/)
- [Top 8 Sentry Alternatives for Error Tracking in 2026 | SigNoz](https://signoz.io/comparisons/sentry-alternatives/)
- [12 Best Bugsnag Alternatives | Better Stack](https://betterstack.com/community/comparisons/bugsnag-alternatives/)
- [Sentry vs Bugsnag: Ultimate Comparison 2025 | Medium](https://medium.com/@squadcast/sentry-vs-bugsnag-the-ultimate-comparison-of-error-monitoring-tools-in-2025-5ce02838d1ca)
- [LogRocket vs Sentry | StackShare](https://stackshare.io/stackups/logrocket-vs-sentry)
- [Rollbar Alternative - Compare Pricing & Features | TrackJS](https://trackjs.com/compare/rollbar-alternative/)
- [5 Best Frontend Error Monitoring Tools in 2026 | TrackJS](https://trackjs.com/blog/best-error-monitoring-tools/)

### Browser Automation:
- [Choosing between Playwright, Puppeteer, or Selenium | Browserbase](https://www.browserbase.com/blog/recommending-playwright)
- [Browser Automation Showdown | Evomi Blog](https://evomi.com/blog/puppeteer-playwright-selenium-showdown)
- [Puppeteer vs Selenium | BrowserStack](https://www.browserstack.com/guide/puppeteer-vs-selenium)
- [Selenium vs Puppeteer vs Playwright | DEV Community](https://dev.to/mechcloud_academy/selenium-vs-puppeteer-vs-playwright-choosing-the-right-tool-for-web-automation-5el)
- [Puppeteer vs Playwright vs Selenium: Ultimate Comparison 2025](https://iproyal.com/blog/puppeteer-vs-playwright-vs-selenium/)
- [How to Debug Playwright & Puppeteer With Effective Logging](https://www.browserless.io/blog/logs-and-debugging-for-playwright-and-puppeteer)
- [ConsoleMessage | Playwright](https://playwright.dev/docs/api/class-consolemessage)
- [How to Monitor JavaScript Logs with Playwright | Checkly](https://www.checklyhq.com/blog/how-to-monitor-javascript-logs-and-exceptions-with-playwright/)
- [Playwright: Capture Console Logs | Medium](https://medium.com/@prateek291992/playwright-with-typescript-how-to-capture-and-validate-browser-console-logs-a7c1f3622eb4)
- [How to capture console logs using Playwright | WebScraping.AI](https://webscraping.ai/faq/playwright/how-to-capture-console-logs-using-playwright)

---

*Last Updated: January 2026*
*Guide compiled for journalism, research, and web development workflows*
