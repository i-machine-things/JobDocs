"""
One-shot cleanup script: strip raw CodeRabbit HTML noise from .claude/S&P.md.
Run from the repo root: python build_scripts/clean_sp.py

The script handles:
  - </blockquote></details> on a single line (multiple closers per line)
  - depth/skip counter reset at every ## section header (top-level, never nested)
  - Noise blocks fully removed: 🤖 Prompt, 🪄 Autofix, ℹ️ Review info, etc.
  - Kept blocks flattened: <details> tags stripped, content preserved
"""
import re
from pathlib import Path

SP = Path('.claude/S&P.md')

# Summaries whose entire <details> block (including nested content) should be dropped.
NOISE_RE = re.compile(
    r'(🤖|🪄\s*Autofix|ℹ️\s*Review info|⚙️\s*Run configuration'
    r'|📥\s*Commits|⛔\s*Files ignored|📒\s*Files selected)',
    re.IGNORECASE,
)


def strip_noise(text: str) -> str:
    lines = text.split('\n')
    out: list[str] = []
    skip = 0    # nesting depth while inside a noise block
    depth = 0   # nesting depth while inside a kept (flattened) block

    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # ── Top-level section header → always at depth 0, reset counters ─────
        if re.match(r'^#{1,3} ', s):
            skip = 0
            depth = 0
            out.append(line)
            i += 1
            continue

        # ── Count any </details> closers on this line ─────────────────────────
        close_count = len(re.findall(r'</details>', s, re.IGNORECASE))
        if close_count:
            for _ in range(close_count):
                if skip > 0:
                    skip -= 1
                elif depth > 0:
                    depth -= 1
            # Don't emit closing tags; continue to next line
            i += 1
            continue

        # ── Opening <details> ─────────────────────────────────────────────────
        if re.search(r'<details>', s, re.IGNORECASE):
            if skip > 0:          # already inside a noise block
                skip += 1
                i += 1
                continue

            # Collect the <summary>...</summary> — may be on the same line or next
            combined = s
            j = i
            if '</summary>' not in combined.lower():
                j += 1
                while j < len(lines):
                    combined += '\n' + lines[j]
                    if '</summary>' in lines[j].lower():
                        break
                    j += 1

            sm = re.search(r'<summary>(.*?)</summary>', combined,
                           re.IGNORECASE | re.DOTALL)
            if sm and NOISE_RE.search(sm.group(1)):
                skip = 1          # enter noise block
                i = j + 1
                continue

            # Kept block: flatten — emit summary text, skip the tags
            depth += 1
            i = j + 1
            if sm:
                txt = re.sub(r'<[^>]+>', '', sm.group(1)).strip()
                if txt:
                    out.append(f'**{txt}**')
            continue

        # ── Inside a noise block → discard ───────────────────────────────────
        if skip > 0:
            i += 1
            continue

        # ── Regular line: strip residual HTML structural tags ─────────────────
        line = re.sub(r'</?blockquote>', '', line, flags=re.IGNORECASE)
        line = re.sub(r'</?summary[^>]*>', '', line, flags=re.IGNORECASE)

        # Remove HTML comment lines
        if re.match(r'\s*<!--.*?-->\s*$', line):
            i += 1
            continue

        out.append(line)
        i += 1

    # Collapse runs of 3+ blank lines to 2
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(out))
    return result.rstrip() + '\n'


def main():
    original = SP.read_text(encoding='utf-8')
    cleaned = strip_noise(original)

    details_before = original.count('<details>')
    details_after  = cleaned.count('<details>')
    lines_before   = original.count('\n')
    lines_after    = cleaned.count('\n')

    SP.write_text(cleaned, encoding='utf-8')

    print('Done.')
    print(f'  <details> blocks: {details_before} -> {details_after}')
    print(f'  File size:        {len(original):,} -> {len(cleaned):,} chars')
    print(f'  Lines:            {lines_before:,} -> {lines_after:,}')


if __name__ == '__main__':
    main()
