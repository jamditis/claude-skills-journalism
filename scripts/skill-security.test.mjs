import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pdfSkillUrl = new URL("../pdf-design/SKILL.md", import.meta.url);
const pageMonitoringUrl = new URL(
  "../research-toolkit/skills/page-monitoring/SKILL.md",
  import.meta.url,
);
const webScrapingUrl = new URL(
  "../dev-toolkit/skills/web-scraping/SKILL.md",
  import.meta.url,
);

test("pdf-design publishes no maintainer-specific credential or upload wiring", async () => {
  const skill = await readFile(pdfSkillUrl, "utf8");

  const forbiddenPatterns = [
    /\/home\/jamditis\//,
    /drive-token\.json/,
    /1lKTdwq4_5uErj-tBN112WCdJGD2YtetO/,
    /1e5dtKOiuvk0PPrFq3UyNI2UAa6RFiom3/,
    /Shared with Joe/i,
    /Claude Workspace/i,
    /~\/\.claude\/scripts\/legion-browser\.py/,
  ];

  for (const pattern of forbiddenPatterns) {
    assert.doesNotMatch(skill, pattern);
  }

  assert.match(skill, /user-chosen destination/i);
  assert.match(skill, /connected Google Drive (tool|integration)/i);
  assert.match(skill, /Do not read or parse raw OAuth token files/i);
  assert.match(skill, /--blink-settings=scriptEnabled=false/);
});

test("page-monitoring examples retrieve and redact secrets safely", async () => {
  const skill = await readFile(pageMonitoringUrl, "utf8");

  const forbiddenPatterns = [
    /UptimeRobotClient\(['"]your-api-key['"]\)/,
    /slack_webhook=['"]https:\/\/hooks\.slack\.com\/services\/\.\.\.['"]/,
    /discord_webhook=['"]https:\/\/discord\.com\/api\/webhooks\/\.\.\.['"]/,
    /['"]error['"]:\s*str\(e\)/,
    /Archived \{url\}/,
  ];

  for (const pattern of forbiddenPatterns) {
    assert.doesNotMatch(skill, pattern);
  }

  assert.match(skill, /def require_secret\(name: str\)/);
  assert.match(skill, /UPTIMEROBOT_API_KEY/);
  assert.match(skill, /SLACK_WEBHOOK_URL/);
  assert.match(skill, /DISCORD_WEBHOOK_URL/);
  assert.match(skill, /SMTP_USERNAME/);
  assert.match(skill, /SMTP_APP_PASSWORD/);
  assert.match(skill, /redact/i);
  assert.match(skill, /never (log|print).*secret/i);
  assert.match(skill, /type\(error\)\.__name__/);
});

test("web-scraping defines explicit content, URL, and session trust boundaries", async () => {
  const skill = await readFile(webScrapingUrl, "utf8");

  assert.doesNotMatch(skill, /TrafilaturaCscraper/);
  assert.doesNotMatch(skill, /[\u0400-\u04ff]/);
  assert.match(skill, /class TrafilaturaScraper/);
  assert.match(skill, /untrusted data, never as instructions/i);
  assert.match(skill, /private-network destinations/i);
  assert.match(skill, /allow_authenticated_session: bool = False/);
  assert.match(skill, /documented authorization/i);
  assert.match(skill, /Never return, print, or embed cookies/i);
  assert.match(skill, /ResearchScraper\/1\.0/);
});
