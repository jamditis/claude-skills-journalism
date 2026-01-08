# Developer Guide: Web Access APIs & Console Capture Tools

## Table of Contents
1. [Headless Browser APIs](#1-headless-browser-apis)
2. [Web Scraping APIs](#2-web-scraping-apis)
3. [Console Log Capture](#3-console-log-capture)
4. [Proxy APIs for Blocked Sites](#4-proxy-apis-for-blocked-sites)
5. [CORS Bypass Tools](#5-cors-bypass-tools)

---

## 1. Headless Browser APIs

### Overview

| Tool | Created | By | Best For | Browser Support |
|------|---------|-----|----------|-----------------|
| **Selenium** | 2004 | Open Source | Legacy support, widest compatibility | Chrome, Firefox, WebKit, Opera, IE |
| **Puppeteer** | 2017 | Google | Chrome-specific tasks, speed | Chrome/Chromium |
| **Playwright** | 2020 | Microsoft | Modern cross-browser automation | Chromium, Firefox, WebKit |

### Key Comparisons

**Architecture:**
- **Selenium**: Uses Selenium WebDriver to control the browser
- **Puppeteer**: Uses Chrome DevTools Protocol (CDP) for direct browser control
- **Playwright**: Communicates directly with browsers using native DevTools protocols

**Language Support:**
- **Selenium**: C#, Ruby, Java, Python, JavaScript (broadest support)
- **Puppeteer**: JavaScript/Node.js only (unofficial Python port: pyppeteer)
- **Playwright**: Python, Java, JavaScript, TypeScript, C#

**Speed & Performance:**
- **Fastest**: Puppeteer (Chrome-specific optimization)
- **Fast**: Playwright
- **Slower**: Selenium (due to WebDriver overhead)

**Anti-Bot Detection:**
- **Most Detectable**: Selenium (navigator.webdriver = true)
- **Moderately Detectable**: Puppeteer (detectable but can use stealth plugins)
- **Least Detectable**: Playwright (built-in stealth capabilities)

---

### Installation & Setup

#### Playwright

**Quick Setup:**
```bash
# Create new project with initialization wizard
npm init playwright@latest

# Or for existing project
npm init -y
npm install -D playwright
npx playwright install
```

**Manual Installation:**
```bash
# Install Playwright test framework
npm i -D @playwright/test

# Install browser binaries (Chromium, Firefox, WebKit)
npx playwright install
```

**Basic Example:**
```javascript
import { test } from '@playwright/test';

test('Page Screenshot', async ({ page }) => {
  await page.goto('https://playwright.dev/');
  await page.screenshot({ path: `example.png` });
});
```

**Advanced Example with Stealth:**
```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    viewport: { width: 1920, height: 1080 },
    locale: 'en-US',
    timezoneId: 'America/New_York',
  });

  const page = await context.newPage();
  await page.goto('https://example.com');

  // Automatic waiting for elements
  await page.click('button#submit');

  await browser.close();
})();
```

---

#### Puppeteer

**Installation:**
```bash
# Full installation (includes Chrome)
npm i puppeteer

# Core only (no Chrome download)
npm i puppeteer-core
```

**Basic Example:**
```javascript
import puppeteer from 'puppeteer';

const browser = await puppeteer.launch();
const page = await browser.newPage();

await page.goto('https://developer.chrome.com/');
await page.setViewport({width: 1080, height: 1024});

// Take screenshot
await page.screenshot({ path: 'screenshot.png' });

// Generate PDF
await page.pdf({ path: 'page.pdf', format: 'A4' });

await browser.close();
```

**Advanced Example with Stealth Plugin:**
```javascript
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled'
    ]
  });

  const page = await browser.newPage();

  // Set realistic viewport
  await page.setViewport({ width: 1366, height: 768 });

  // Navigate and scrape
  await page.goto('https://example.com', {
    waitUntil: 'networkidle2'
  });

  // Extract data
  const data = await page.evaluate(() => {
    return {
      title: document.title,
      content: document.body.innerText
    };
  });

  console.log(data);
  await browser.close();
})();
```

---

#### Selenium

**Installation (Python):**
```bash
pip install selenium
```

**Installation (Node.js):**
```bash
npm install selenium-webdriver
```

**Basic Example (Python):**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Configure headless mode
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

# Launch browser
driver = webdriver.Chrome(options=options)

try:
    driver.get('https://example.com')

    # Find element and interact
    element = driver.find_element(By.ID, 'my-element')
    element.click()

    # Take screenshot
    driver.save_screenshot('screenshot.png')

finally:
    driver.quit()
```

**Basic Example (JavaScript):**
```javascript
const { Builder, By, Key, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

(async function example() {
  let options = new chrome.Options();
  options.addArguments('--headless');

  let driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();

  try {
    await driver.get('http://www.google.com');
    await driver.findElement(By.name('q')).sendKeys('webdriver', Key.RETURN);
    await driver.wait(until.titleIs('webdriver - Google Search'), 1000);
  } finally {
    await driver.quit();
  }
})();
```

---

### Recommendations

- **Choose Playwright** for modern apps requiring cross-browser coverage with built-in anti-detection
- **Choose Puppeteer** for Chrome-based automation, speed, and lightweight testing
- **Choose Selenium** for legacy support, enterprise-scale testing, and widest browser compatibility
- **Avoid Selenium** if speed is critical or you need advanced anti-bot features

---

## 2. Web Scraping APIs

### ScrapingBee

**Overview:**
ScrapingBee is a lightweight web scraping API focused on simplicity and reliability. It handles proxy rotation, JavaScript rendering, and CAPTCHA challenges behind a single HTTP endpoint.

**Pricing (2026):**
- **Free Tier**: 1,000 API credits
- **Freelance**: $49/month - 150,000 credits
- **Startup**: $99/month
- **Business**: $249/month - 8,000,000+ credits (includes JS rendering & geotargeting)
- **Enterprise**: $599+/month

**Key Limitations:**
- JavaScript rendering and geotargeting NOT available on $49 or $99 plans
- Requires $249 Business tier for these features (5x price jump)

**Setup & Usage:**
```bash
npm install scrapingbee
```

```javascript
const scrapingbee = require('scrapingbee');

const client = new scrapingbee.ScrapingBeeClient('YOUR_API_KEY');

// Simple request
client.get({
  url: 'https://example.com',
  params: {
    'render_js': 'true',
    'premium_proxy': 'true',
    'country_code': 'us'
  }
})
.then((response) => {
  console.log(response.data);
})
.catch((error) => {
  console.error(error);
});
```

**cURL Example:**
```bash
curl "https://app.scrapingbee.com/api/v1/?api_key=YOUR_API_KEY&url=https://example.com&render_js=true"
```

---

### Browserless

**Overview:**
Browserless is a headless browser automation platform for web scraping, PDF generation, screenshotting, and QA testing. Provides managed browser infrastructure with Puppeteer and Playwright support.

**Pricing (2026):**
- **Free Plan**: Limited features
- **Starter**: $50/month
- **Scale**: $200/month
- **Enterprise**: Custom pricing

**Unit-Based Billing:**
- 1 Unit = 30 seconds of browser runtime
- Proxy usage: 6 units per MB
- CAPTCHA solving: 10 units each
- Overages charged per unit on paid plans
- Free plans reject requests after threshold

**Self-Hosting Option Available** (Private/Open-Source Docker versions)

**Setup & Usage:**
```javascript
const puppeteer = require('puppeteer-core');

const browser = await puppeteer.connect({
  browserWSEndpoint: `wss://chrome.browserless.io?token=YOUR_API_TOKEN`,
});

const page = await browser.newPage();
await page.goto('https://example.com');

const screenshot = await page.screenshot();
await browser.close();
```

**REST API Example:**
```bash
# Take screenshot via REST API
curl -X POST \
  https://chrome.browserless.io/screenshot?token=YOUR_TOKEN \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com",
    "options": {
      "fullPage": true,
      "type": "png"
    }
  }'
```

**PDF Generation:**
```bash
curl -X POST \
  https://chrome.browserless.io/pdf?token=YOUR_TOKEN \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com",
    "options": {
      "format": "A4",
      "printBackground": true
    }
  }' > output.pdf
```

---

### Apify

**Overview:**
Apify is a full-stack cloud platform for web scraping, browser automation, and data extraction. Developers can build, deploy, and publish "Actors" (serverless programs) or use 4,000+ pre-built scrapers from the marketplace.

**Pricing (2026):**
- **Free Tier**: Small monthly credit allowance, full access to Actor Store
- **Personal**: $49/month
- **Scale**: Higher tier
- **Business**: Higher tier
- **Enterprise**: Custom pricing

**Note**: Can become expensive for large datasets or complex scraping tasks

**Key Differentiator:**
Unlike ScrapingBee's simple API approach, Apify is a complete cloud platform where you can:
- Use ready-made Actors from marketplace
- Build custom scrapers
- Combine both approaches

**Setup & Usage:**

```bash
# Install Apify SDK
npm install apify
```

**Basic Actor Example:**
```javascript
const Apify = require('apify');

Apify.main(async () => {
    const input = await Apify.getInput();
    const { url } = input;

    const browser = await Apify.launchPuppeteer();
    const page = await browser.newPage();

    await page.goto(url);

    const data = await page.evaluate(() => {
        return {
            title: document.title,
            text: document.body.innerText
        };
    });

    await Apify.pushData(data);
    await browser.close();
});
```

**Using Pre-built Actor (API):**
```bash
curl "https://api.apify.com/v2/acts/apify~web-scraper/runs" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "startUrls": [{"url": "https://example.com"}],
    "pageFunction": "async function pageFunction(context) { return context.jQuery(\"title\").text(); }"
  }'
```

---

### Comparison Summary

| Feature | ScrapingBee | Browserless | Apify |
|---------|------------|-------------|-------|
| **Starting Price** | $49/mo | $50/mo | $49/mo |
| **Free Tier** | 1,000 credits | Limited | Small credits |
| **JS Rendering** | $249+ tier | Included | Included |
| **CAPTCHA Solving** | Automatic | 10 units each | Via Actors |
| **Best For** | Simple API integration | Managed browsers | Complex workflows |
| **Marketplace** | No | No | 4,000+ Actors |
| **Self-Hosting** | No | Yes | No |

---

## 3. Console Log Capture

### Capturing Browser Console Logs in Headless Mode

Since browser code runs in a separate JavaScript context, `console.*` calls in the browser won't automatically appear in your Node.js output. You need to listen for console events.

---

### Puppeteer Console Capture

**Basic Console Listening:**
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // Listen to console events
  page.on('console', msg => {
    console.log('PAGE LOG:', msg.text());
  });

  await page.goto('https://example.com');

  // This will trigger the console event listener
  await page.evaluate(() => {
    console.log(`URL is ${location.href}`);
    console.warn('This is a warning');
    console.error('This is an error');
  });

  await browser.close();
})();
```

**Advanced Console Capture with Types:**
```javascript
page.on('console', async (msg) => {
  const msgArgs = msg.args();

  for (let i = 0; i < msgArgs.length; ++i) {
    console.log(`[${msg.type()}] arg ${i}: ${await msgArgs[i].jsonValue()}`);
  }
});

page.on('pageerror', error => {
  console.log('PAGE ERROR:', error.message);
});

page.on('requestfailed', request => {
  console.log('REQUEST FAILED:', request.url(), request.failure().errorText);
});
```

**Enable Browser Process Logs:**
```javascript
const browser = await puppeteer.launch({
  dumpio: true,  // Forward browser process stdout/stderr to Node.js
  headless: true
});
```

**Verbose Debugging:**
```bash
# Run with debug logging
DEBUG="puppeteer:*" node script.js
```

---

### Playwright Console Capture

**Basic Console Listening:**
```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Listen to console messages
  page.on('console', msg => {
    console.log(`[${msg.type()}] ${msg.text()}`);
  });

  // Listen to page errors
  page.on('pageerror', exception => {
    console.log('Uncaught exception:', exception);
  });

  await page.goto('https://example.com');

  await browser.close();
})();
```

**Comprehensive Logging Setup:**
```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    devtools: true  // Opens DevTools (automatically disables headless)
  });

  const page = await browser.newPage();

  // Console messages
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    const location = msg.location();

    console.log(`[CONSOLE ${type.toUpperCase()}] ${text}`);
    console.log(`  Location: ${location.url}:${location.lineNumber}`);
  });

  // Page errors
  page.on('pageerror', error => {
    console.log('[PAGE ERROR]', error.message);
    console.log(error.stack);
  });

  // Request failures
  page.on('requestfailed', request => {
    console.log('[REQUEST FAILED]', request.url());
    console.log('  Failure:', request.failure().errorText);
  });

  // Request interception
  page.on('request', request => {
    console.log('[REQUEST]', request.method(), request.url());
  });

  // Response logging
  page.on('response', response => {
    console.log('[RESPONSE]', response.status(), response.url());
  });

  await page.goto('https://example.com');

  await browser.close();
})();
```

**Verbose Debugging:**
```bash
# API-level debugging
DEBUG=pw:api node script.js

# Browser debugging mode
PWDEBUG=console node script.js
```

---

### Network Logging Example

**Puppeteer Network Capture:**
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  // Enable request interception
  await page.setRequestInterception(true);

  page.on('request', request => {
    console.log('REQUEST:', request.method(), request.url());
    request.continue();
  });

  page.on('response', response => {
    console.log('RESPONSE:', response.status(), response.url());
  });

  await page.goto('https://example.com');
  await browser.close();
})();
```

**Playwright Network Capture:**
```javascript
page.on('request', request => {
  console.log('>>', request.method(), request.url());
});

page.on('response', response => {
  console.log('<<', response.status(), response.url());
});

await page.goto('https://example.com');
```

---

### Why Logging Matters

Since headless browsers run without rendering UI, troubleshooting is difficult without proper logging. Key strategies:

1. **Console event listeners** - Capture all browser console output
2. **Screenshots** - Visual debugging at key points
3. **Network logging** - Track requests/responses
4. **Error handlers** - Catch uncaught exceptions
5. **Verbose debugging** - Enable framework-level logging

---

## 4. Proxy APIs for Blocked Sites

### Market Overview (2026)

The proxy service industry is projected to reach **$12.3 billion by 2026**. Bright Data and Oxylabs lead with 35% and 28% market share respectively.

---

### Bright Data

**Overview:**
Market leader with 72M+ IPs and 99.99% success rates. Dominates the proxy market with premium pricing and extensive features.

**Pricing:**
- **Datacenter Proxies**: $6.70/month (3 IPs) to $3,600/month (3,000 IPs)
- **Residential Proxies**: Premium pricing (custom quotes)
- **Free Trial**: Available for most products (except Datasets)
- **Pay-as-you-go**: Available

**Customer Base**: 20,000+ customers

**Key Features:**
- 72M+ IP pool across 195+ countries
- 99.99% uptime/success rate
- Extensive customization options
- Focus on data delivery (scraping + data packages)
- Advanced targeting and rotation

**Setup Example:**
```javascript
const axios = require('axios');

const proxy = {
  host: 'brd.superproxy.io',
  port: 22225,
  auth: {
    username: 'brd-customer-YOUR_CUSTOMER_ID-zone-YOUR_ZONE',
    password: 'YOUR_PASSWORD'
  }
};

axios.get('https://example.com', { proxy })
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

**cURL Example:**
```bash
curl --proxy brd.superproxy.io:22225 \
  --proxy-user brd-customer-CUSTOMER_ID-zone-ZONE:PASSWORD \
  https://example.com
```

**Best For:**
- Large-scale operations
- Teams needing low barrier to entry
- High throughput requirements
- Data-focused workflows

---

### Oxylabs

**Overview:**
Second-largest provider with 102M+ IPs and 99.95% uptime. Better performance metrics at lower costs than Bright Data.

**Pricing:**
- **Residential Proxies**: From $8/GB
- **Datacenter Proxies**: From $50/month (shared)
- **Enterprise Plans**: Custom quotes
- **Free Trial**: 7-day trial for qualifying businesses

**Note**: No pay-as-you-go plan available

**IP Pool:**
- 102M+ residential IPs
- 2M+ datacenter proxies
- 100K+ rotating datacenter options
- Coverage: 78+ countries

**Key Features:**
- Faster response rates (especially mobile proxies)
- 97%+ success rate on Cloudflare-protected sites
- AI-powered unblocker
- Dedicated account managers
- Focus on scraping tools and infrastructure

**Setup Example:**
```python
import requests

proxies = {
    'http': 'http://user-USERNAME:PASSWORD@pr.oxylabs.io:7777',
    'https': 'https://user-USERNAME:PASSWORD@pr.oxylabs.io:7777'
}

response = requests.get('https://example.com', proxies=proxies)
print(response.text)
```

**JavaScript Example:**
```javascript
const axios = require('axios');

const config = {
  proxy: {
    host: 'pr.oxylabs.io',
    port: 7777,
    auth: {
      username: 'user-USERNAME',
      password: 'PASSWORD'
    }
  }
};

axios.get('https://example.com', config)
  .then(response => console.log(response.data));
```

**Best For:**
- Maximum scale and enterprise support
- Performance-critical applications
- Mobile proxy needs
- Large operations with dedicated support requirements

---

### SmartProxy (Now Decodo)

**Overview:**
Recently rebranded to Decodo, maintains the same value proposition: excellent performance without premium pricing. 115M IP pool across 195 countries.

**Pricing:**
- **Significantly cheaper** than Bright Data and Oxylabs
- Competitive pricing for mid-scale projects
- Fast response times

**Key Features:**
- 115M+ IPs across 195 countries
- Features most customers need without complexity
- Convenient package structure
- Good balance of price and performance

**Setup Example:**
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    args: [
      '--proxy-server=gate.smartproxy.com:7000'
    ]
  });

  const page = await browser.newPage();

  await page.authenticate({
    username: 'YOUR_USERNAME',
    password: 'YOUR_PASSWORD'
  });

  await page.goto('https://example.com');

  await browser.close();
})();
```

**Best For:**
- Mid-scale projects
- Budget-conscious teams
- Projects needing good performance without premium pricing
- Standard scraping workflows

---

### Comparison Table

| Provider | Pool Size | Pricing | Success Rate | Best For |
|----------|-----------|---------|--------------|----------|
| **Bright Data** | 72M+ IPs | Premium ($6.70+) | 99.99% | Enterprise, high throughput |
| **Oxylabs** | 102M+ IPs | $8/GB, $50+ | 99.95% | Maximum scale, performance |
| **SmartProxy/Decodo** | 115M+ IPs | Competitive | High | Mid-scale, budget-conscious |

---

### Performance Comparison

**Response Times:**
- **Oxylabs**: Fastest (especially mobile proxies)
- **Bright Data**: Fast
- **SmartProxy/Decodo**: Fast, competitive

**Cloudflare Success Rate:**
- **Oxylabs**: 97%+
- **Bright Data**: 97%+
- **SmartProxy/Decodo**: High

**Market Position:**
- **Bright Data**: 35% market share, 20,000+ customers
- **Oxylabs**: 28% market share, 2,000+ customers
- **SmartProxy/Decodo**: Growing alternative

---

## 5. CORS Bypass Tools

### Understanding CORS

CORS (Cross-Origin Resource Sharing) is a security feature that restricts web pages from making requests to a different domain. During development, this can block legitimate API calls.

**Security Warning**: CORS proxies should ONLY be used for development. Never use them in production as they can expose sensitive data and create security vulnerabilities.

---

### CORS-Anywhere

**Overview:**
The most popular NodeJS reverse proxy that adds CORS headers to proxied requests. Self-hostable for unlimited use.

**GitHub**: [Rob--W/cors-anywhere](https://github.com/Rob--W/cors-anywhere)

**Public Demo** (Limited): `https://cors-anywhere.herokuapp.com` (requires opt-in as of Feb 2021)

**Installation:**
```bash
npm install cors-anywhere
```

**Self-Hosted Setup:**
```javascript
const cors_proxy = require('cors-anywhere');

const host = 'localhost';
const port = 8080;

cors_proxy.createServer({
  originWhitelist: [], // Allow all origins
  requireHeader: ['origin', 'x-requested-with'],
  removeHeaders: ['cookie', 'cookie2']
}).listen(port, host, () => {
  console.log(`CORS Anywhere server running on ${host}:${port}`);
});
```

**Usage from Client:**
```javascript
fetch('http://localhost:8080/https://api.example.com/data')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

**Heroku Deployment:**
```bash
# Clone the repo
git clone https://github.com/Rob--W/cors-anywhere.git
cd cors-anywhere

# Deploy to Heroku
heroku create
git push heroku master
```

---

### Local-CORS-Proxy

**Overview:**
Simple proxy specifically designed for local development to bypass CORS during prototyping.

**GitHub**: [garmeeh/local-cors-proxy](https://github.com/garmeeh/local-cors-proxy)

**Installation:**
```bash
npm install -g local-cors-proxy
```

**Usage:**
```bash
# Start proxy
lcp --proxyUrl https://api.example.com --port 8010

# Your app can now access:
# http://localhost:8010/endpoint
```

**Programmatic Usage:**
```javascript
const proxy = require('local-cors-proxy');

proxy.startProxy({
  proxyUrl: 'https://api.example.com',
  port: 8010,
  proxyPartial: ''
});
```

---

### CorsProxy.io

**Overview:**
Managed CORS proxy service with free tier for development.

**Website**: https://corsproxy.io/

**Usage:**
```javascript
// Simply prepend their URL to your API endpoint
fetch('https://corsproxy.io/?https://api.example.com/data')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Pricing:**
- **Free**: Development use without account
- **Paid**: Required for production sites (requires subscription)

---

### Bypass-CORS (Go-based)

**Overview:**
Middleware proxy server that modifies response headers to bypass CORS restrictions.

**GitHub**: [Shivam010/bypass-cors](https://github.com/Shivam010/bypass-cors)

**How It Works:**
Acts as middleware, makes requests to the destination server, obtains the response, and adds/modifies relevant headers to trick the browser.

**Setup:**
```bash
# Clone and run
git clone https://github.com/Shivam010/bypass-cors.git
cd bypass-cors
go run main.go
```

**Docker Usage:**
```bash
docker pull shivam010/bypass-cors
docker run -p 8080:8080 shivam010/bypass-cors
```

---

### DevPulsion CorsProxy (Docker)

**Overview:**
Dockerized version of cors-anywhere for easy deployment.

**GitHub**: [devpulsion/corsproxy](https://github.com/devpulsion/corsproxy)

**Docker Setup:**
```bash
# Run with Docker
docker run -p 8080:8080 devpulsion/corsproxy
```

**Docker Compose:**
```yaml
version: '3'
services:
  cors-proxy:
    image: devpulsion/corsproxy
    ports:
      - "8080:8080"
    environment:
      - ORIGIN=*
```

---

### Browser Extensions (Development Only)

**Chrome Extensions:**
- **CORS Unblock**: Simple toggle for CORS
- **Allow CORS**: Access-Control-Allow-Origin toggle
- **Moesif Origin & CORS Changer**: Advanced CORS control

**Firefox Extensions:**
- **CORS Everywhere**: Enable CORS for all sites

**Warning**: These bypass browser security. Only use during development and disable when not needed.

---

### Development Best Practices

**1. Backend Solution (Recommended):**
```javascript
// Express.js backend
const express = require('express');
const cors = require('cors');
const app = express();

// Enable CORS for specific origin
app.use(cors({
  origin: 'http://localhost:3000'
}));

// Or enable for all origins (dev only)
app.use(cors());
```

**2. Proxy in Package.json (React):**
```json
{
  "proxy": "https://api.example.com"
}
```

Then fetch from relative paths:
```javascript
fetch('/api/data')  // Proxied to https://api.example.com/api/data
  .then(res => res.json());
```

**3. Webpack Dev Server Proxy:**
```javascript
// webpack.config.js
module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'https://api.example.com',
        changeOrigin: true,
        pathRewrite: { '^/api': '' }
      }
    }
  }
};
```

**4. Vite Proxy:**
```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'https://api.example.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
};
```

---

### Security Considerations

**Risks of CORS Proxies:**
1. **Man-in-the-middle vulnerabilities**: Proxies intercept all traffic
2. **Data logging**: Some proxies log requests and IPs
3. **Trust requirements**: You're trusting the proxy operator
4. **Production risks**: Never use in production

**Public Proxy Limitations:**
- Rate limiting
- Unreliable uptime
- Potential logging of sensitive data
- Service interruptions

**Best Practices:**
- ✅ Use CORS proxies ONLY for development
- ✅ Self-host your own proxy for more control
- ✅ Whitelist specific origins in production
- ✅ Configure your backend properly for CORS
- ❌ Never use public proxies for sensitive data
- ❌ Never deploy CORS proxies to production
- ❌ Don't rely on browser extensions in production

---

### Comparison Table

| Tool | Type | Best For | Self-Host | Complexity |
|------|------|----------|-----------|------------|
| **CORS-Anywhere** | Node.js proxy | General use | Yes | Low |
| **Local-CORS-Proxy** | CLI tool | Quick prototyping | Yes | Very Low |
| **CorsProxy.io** | Managed service | No setup needed | No | None |
| **Bypass-CORS** | Go proxy | Go developers | Yes | Medium |
| **Browser Extensions** | Extension | Quick testing | N/A | None |
| **Backend Config** | Proper solution | Production | N/A | Low-Medium |

---

## Summary & Recommendations

### For Web Scraping Projects:

**Small Scale (< 1M requests/month):**
- Headless Browser: **Puppeteer** (speed + simplicity)
- Scraping API: **ScrapingBee Free/Freelance** ($49/mo)
- Proxy: **SmartProxy/Decodo** (budget-friendly)

**Medium Scale (1M - 10M requests/month):**
- Headless Browser: **Playwright** (cross-browser + stealth)
- Scraping API: **Browserless Scale** ($200/mo) or **Apify**
- Proxy: **SmartProxy/Decodo** or **Oxylabs**

**Large Scale (10M+ requests/month):**
- Headless Browser: **Playwright** (enterprise features)
- Scraping API: **Apify Enterprise** or custom infrastructure
- Proxy: **Oxylabs** or **Bright Data** (dedicated support)

### For Testing & Automation:

- **Cross-browser testing**: Playwright
- **Chrome-only testing**: Puppeteer
- **Legacy browser support**: Selenium
- **CI/CD integration**: Playwright (built-in support)

### For Development:

- **CORS during dev**: Local-CORS-Proxy or webpack/vite proxy
- **Console debugging**: Puppeteer or Playwright with event listeners
- **Quick prototypes**: Puppeteer + Local-CORS-Proxy

---

## Additional Resources

### Official Documentation:
- [Playwright Docs](https://playwright.dev/)
- [Puppeteer Docs](https://pptr.dev/)
- [Selenium Docs](https://www.selenium.dev/)
- [ScrapingBee Docs](https://www.scrapingbee.com/documentation/)
- [Browserless Docs](https://docs.browserless.io/)
- [Apify Docs](https://docs.apify.com/)

### Community Resources:
- [Awesome Playwright](https://github.com/mxschmitt/awesome-playwright)
- [Awesome Puppeteer](https://github.com/transitive-bullshit/awesome-puppeteer)
- [Web Scraping Best Practices](https://blog.apify.com/web-scraping-best-practices/)

---

**Last Updated**: January 2026

**Document Version**: 1.0
