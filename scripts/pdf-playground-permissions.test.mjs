import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const COMMANDS = join(ROOT, 'pdf-playground/commands');
const SCRIPT = join(ROOT, 'pdf-playground/scripts/playground.py');
const PYTHON = process.platform === 'win32' ? 'python' : 'python3';

function allowedTools(name) {
  const source = readFileSync(join(COMMANDS, name), 'utf8');
  const line = source.match(/^---\n[\s\S]*?^allowed-tools:(.*)$/mu)?.[1] || '';
  return line.split(/,\s*(?![^()]*\))/u).map((tool) => tool.trim()).filter(Boolean);
}

function playground(...args) {
  return spawnSync(PYTHON, [SCRIPT, ...args], { encoding: 'utf8' });
}

// The marketplace validator holds plugins that pre-approve unscoped Bash,
// Write, or Edit. A grant must name a path or an exact command.
test('pdf-playground commands never pre-approve unscoped Bash, Write, or Edit', () => {
  for (const name of readdirSync(COMMANDS).filter((file) => file.endsWith('.md'))) {
    for (const tool of allowedTools(name)) {
      assert.doesNotMatch(tool, /^(?:Bash|Write|Edit)$/u, `${name}: ${tool}`);
      assert.doesNotMatch(tool, /^(?:Write|Edit)\((?:\*\*?|\.\/\*\*)\)$/u, `${name}: ${tool}`);
    }
  }
});

test('pdf-playground Bash grants name only the plugin script or the update command', () => {
  const allowed = new Set([
    'Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py *)',
    'Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/playground.py *)',
    'Bash(claude plugin update pdf-playground@claude-skills-journalism)',
  ]);
  for (const name of readdirSync(COMMANDS).filter((file) => file.endsWith('.md'))) {
    for (const tool of allowedTools(name).filter((entry) => entry.startsWith('Bash'))) {
      assert.ok(allowed.has(tool), `${name}: ${tool}`);
    }
  }
});

test('commands that pre-approve the script call it in the approved form', () => {
  for (const name of ['preview.md', 'proposal.md']) {
    const source = readFileSync(join(COMMANDS, name), 'utf8');
    const body = source.replace(/^---\n[\s\S]*?\n---\n/u, '');
    assert.match(body, /python3 \$\{CLAUDE_PLUGIN_ROOT\}\/scripts\/playground\.py (?:setup|serve|clean)/u, name);
    assert.doesNotMatch(body, /python -c|python -m http\.server|rm -rf|^\s*cp /mu, name);
  }
});

test('playground.py setup copies the controls and clean removes them', () => {
  const dir = mkdtempSync(join(tmpdir(), 'playground-'));
  try {
    const doc = join(dir, 'doc.html');
    writeFileSync(doc, '<!doctype html><title>t</title>');

    const setup = playground('setup', doc, '--template', 'proposal');
    assert.equal(setup.status, 0, setup.stderr);
    assert.match(setup.stdout, /playground-wrapper\.html\?doc=doc\.html&template=proposal/u);
    for (const file of [
      'playground-wrapper.html',
      'playground-controls/control-panel.css',
      'playground-controls/control-panel.js',
      'playground-controls/prompt-generator.js',
      'playground-controls/template-maps/proposal.js',
    ]) {
      assert.ok(existsSync(join(dir, file)), file);
    }

    const clean = playground('clean', doc);
    assert.equal(clean.status, 0, clean.stderr);
    assert.ok(!existsSync(join(dir, 'playground-controls')));
    assert.ok(!existsSync(join(dir, 'playground-wrapper.html')));
    assert.ok(existsSync(doc), 'clean must keep the document');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('playground.py rejects non-HTML files and path-like template names', () => {
  const dir = mkdtempSync(join(tmpdir(), 'playground-'));
  try {
    const doc = join(dir, 'doc.html');
    writeFileSync(doc, '<!doctype html>');
    writeFileSync(join(dir, 'notes.txt'), 'x');
    assert.equal(playground('setup', join(dir, 'notes.txt')).status, 1);
    assert.equal(playground('clean', join(dir, 'notes.txt')).status, 1);
    assert.equal(playground('setup', doc, '--template', '../proposal').status, 1);
    assert.equal(playground('setup', doc, '--template', 'missing').status, 1);
    assert.ok(!existsSync(join(dir, 'playground-wrapper.html')));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('playground.py serve binds to loopback and serves the directory', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'playground-'));
  writeFileSync(join(dir, 'doc.html'), 'hello');
  const child = spawn(PYTHON, [SCRIPT, 'serve', dir, '--port', '18787']);
  try {
    const url = await new Promise((resolve, reject) => {
      let out = '';
      child.stdout.on('data', (chunk) => {
        out += chunk;
        const match = out.match(/Serving (http:\/\/localhost:\d+\/)/u);
        if (match) resolve(match[1]);
      });
      child.on('exit', (code) => reject(new Error(`serve exited ${code}`)));
      setTimeout(() => reject(new Error('serve did not start')), 5000).unref();
    });
    const response = await fetch(`${url.replace('localhost', '127.0.0.1')}doc.html`);
    assert.equal(await response.text(), 'hello');
  } finally {
    child.kill();
    rmSync(dir, { recursive: true, force: true });
  }
});
