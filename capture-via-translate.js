const { chromium } = require('playwright-core');

(async () => {
  const consoleMessages = [];
  const errors = [];

  // Parse proxy from environment
  const proxyUrl = process.env.https_proxy || process.env.HTTPS_PROXY;

  let proxyConfig = undefined;
  if (proxyUrl) {
    const url = new URL(proxyUrl);
    proxyConfig = {
      server: `${url.protocol}//${url.hostname}:${url.port}`,
      username: url.username,
      password: url.password,
      bypass: '*.google.com,*.googleapis.com,localhost,127.0.0.1'
    };
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

  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
  });

  page.on('pageerror', error => {
    errors.push({
      message: error.message,
      stack: error.stack
    });
  });

  page.on('requestfailed', request => {
    errors.push({
      type: 'request_failed',
      url: request.url(),
      failure: request.failure()?.errorText
    });
  });

  const targetUrl = 'https://inewsource.org/2025/12/19/home-sick-tijuana-river-san-diego-illness/';
  const translateUrl = `https://translate.google.com/translate?sl=en&tl=es&u=${encodeURIComponent(targetUrl)}`;

  console.error('Trying Google Translate with proxy bypass...');

  try {
    await page.goto(translateUrl, {
      waitUntil: 'networkidle',
      timeout: 90000
    });

    await page.waitForTimeout(10000);
    const frames = page.frames();
    console.error(`Found ${frames.length} frames`);

  } catch (e) {
    errors.push({
      type: 'navigation_error',
      message: e.message
    });
  }

  await browser.close();

  console.log(JSON.stringify({
    consoleMessages,
    errors,
    timestamp: new Date().toISOString()
  }, null, 2));
})();
