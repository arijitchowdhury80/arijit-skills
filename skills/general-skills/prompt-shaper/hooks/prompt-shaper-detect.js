#!/usr/bin/env node
// UserPromptSubmit hook: detect big stream-of-consciousness inputs and
// remind the model to invoke the prompt-shaper skill.
//
// Fires when the prompt looks like unstructured "blabber":
//   - long (>= MIN_CHARS) OR multi-paragraph (>= MIN_PARAS paragraphs and >= SOFT_CHARS)
// Never fires on:
//   - slash commands
//   - inputs dominated by code fences (pasted code/logs, not blabber)
//   - short confirmations / answers

const MIN_CHARS = 700;   // long single-block blabber
const SOFT_CHARS = 400;  // shorter but clearly multi-paragraph
const MIN_PARAS = 3;

let input = '';
process.stdin.on('data', (d) => (input += d));
process.stdin.on('end', () => {
  let prompt = '';
  try {
    prompt = (JSON.parse(input).prompt || '').trim();
  } catch {
    process.exit(0);
  }

  if (!prompt || prompt.startsWith('/')) process.exit(0);

  // System/task notifications arrive through the same channel — not user blabber.
  if (
    prompt.includes('<task-notification>') ||
    prompt.includes('[SYSTEM NOTIFICATION') ||
    prompt.includes('<system-reminder>')
  )
    process.exit(0);

  // Pasted code/logs are not stream-of-consciousness.
  const fencedLen = (prompt.match(/```[\s\S]*?```/g) || []).join('').length;
  if (fencedLen > prompt.length * 0.4) process.exit(0);

  const paras = prompt.split(/\n\s*\n/).filter((p) => p.trim().length > 0).length;
  const isBlob =
    prompt.length >= MIN_CHARS || (paras >= MIN_PARAS && prompt.length >= SOFT_CHARS);

  if (!isBlob) process.exit(0);

  const out = {
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext:
        'LARGE UNSTRUCTURED INPUT DETECTED (' +
        prompt.length +
        ' chars, ' +
        paras +
        ' paragraphs). You MUST invoke the prompt-shaper skill BEFORE any other action — ' +
        'no exploring, no tool calls, no clarifying questions first. ' +
        'Do NOT skip because the input "looks already structured" or because you think you understand it — ' +
        'that rationalization is the exact failure this guards against. ' +
        'ONLY valid skips: (a) answers to clarifying questions you just asked, ' +
        '(b) a continuation of an in-flight prompt-shaper exchange, (c) the user explicitly said to skip shaping. ' +
        'If none of (a)(b)(c) apply, invoke prompt-shaper now.',
    },
  };
  console.log(JSON.stringify(out));
  process.exit(0);
});
