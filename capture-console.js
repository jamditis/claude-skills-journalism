const { chromium } = require('playwright-core');

(async () => {
  const consoleMessages = [];
  const errors = [];

  // Parse proxy from environment
  const proxyUrl = process.env.https_proxy || process.env.HTTPS_PROXY;
  console.error('Using proxy:', proxyUrl ? 'Yes' : 'No');

  let proxyConfig = undefined;
  if (proxyUrl) {
    // Parse proxy URL: http://user:pass@host:port
    const url = new URL(proxyUrl);
    proxyConfig = {
      server: `${url.protocol}//${url.hostname}:${url.port}`,
      username: url.username,
      password: url.password
    };
    console.error('Proxy server:', proxyConfig.server);
  }

  const browser = await chromium.launch({
    executablePath: '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome',
    headless: true,
    proxy: proxyConfig,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
    ]
  });

  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
  });

  const page = await context.newPage();

  // Capture console messages
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });

  // Capture page errors
  page.on('pageerror', error => {
    errors.push({
      message: error.message,
      stack: error.stack
    });
  });

  // Capture request failures
  page.on('requestfailed', request => {
    errors.push({
      type: 'request_failed',
      url: request.url(),
      failure: request.failure()?.errorText
    });
  });

  try {
    console.error('Navigating to page...');
    await page.goto('https://inewsource.org/2025/12/19/home-sick-tijuana-river-san-diego-illness/', {
      waitUntil: 'networkidle',
      timeout: 90000
    });

    console.error('Waiting for page to fully load...');
    await page.waitForTimeout(5000);

    console.error('Page loaded. Capturing output...');
  } catch (e) {
    errors.push({
      type: 'navigation_error',
      message: e.message
    });
  }

  await browser.close();

  // Output results
  console.log(JSON.stringify({
    consoleMessages,
    errors,
    timestamp: new Date().toISOString()
  }, null, 2));
})();
