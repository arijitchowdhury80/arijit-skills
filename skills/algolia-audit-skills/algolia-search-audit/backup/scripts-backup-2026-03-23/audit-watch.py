#!/usr/bin/env python3
"""
audit-watch.py — Live execution tree for Algolia Search Audit
Tails audit-progress.jsonl and renders pipeline status in terminal.

Usage:
  python3 audit-watch.py <company-name>
  python3 audit-watch.py Costco
  python3 audit-watch.py Costco --stop-after 3      # stop pipeline after phase 3
  python3 audit-watch.py Costco --resume-from 3     # write resume instruction
"""

import sys, os, json, time, argparse
from datetime import datetime
from pathlib import Path

AUDIT_DIR = os.environ.get('ALGOLIA_AUDIT_DIR', os.path.expanduser('~/algolia-audits'))

PHASES = {
    1: {'name': 'algolia-audit-research',  'label': 'Phase 1: Research',          'icon': '📋'},
    2: {'name': 'algolia-live-signals',    'label': 'Phase 2: Live Signals',       'icon': '📡'},
    3: {'name': 'algolia-audit-browser',   'label': 'Phase 3: Browser Audit',      'icon': '🌐'},
    4: {'name': 'algolia-audit-report',    'label': 'Phase 4: Report + Deliverables', 'icon': '📊'},
    5: {'name': 'algolia-audit-factcheck', 'label': 'Phase 5: Factcheck',          'icon': '✅'},
}

STATUS_ICON = {
    'running':  '⏳',
    'complete': '✅',
    'failed':   '❌',
    'skipped':  '⏭️',
    'waiting':  '⬜',
}

def load_events(progress_file):
    events = []
    if not progress_file.exists():
        return events
    with open(progress_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return events

def build_state(events):
    state = {p: {'status': 'waiting', 'ts_start': None, 'ts_end': None} for p in PHASES}
    for e in events:
        phase = e.get('phase')
        status = e.get('status')
        ts = e.get('ts', '')
        if phase and phase in state:
            if status == 'running' and state[phase]['ts_start'] is None:
                state[phase]['ts_start'] = ts
            state[phase]['status'] = status
            if status in ('complete', 'failed', 'skipped'):
                state[phase]['ts_end'] = ts
    return state

def elapsed(ts_start, ts_end=None):
    if not ts_start:
        return ''
    try:
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        start = datetime.strptime(ts_start, fmt)
        end = datetime.strptime(ts_end, fmt) if ts_end else datetime.utcnow()
        secs = int((end - start).total_seconds())
        return f'{secs//60}m {secs%60:02d}s'
    except Exception:
        return ''

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def render(company, state, progress_file):
    print(f'\n  ╔══════════════════════════════════════════════════════╗')
    print(f'  ║   ALGOLIA SEARCH AUDIT — {company.upper():<29}║')
    print(f'  ║   Watching: {str(progress_file)[-42:]:<42}║')
    print(f'  ╚══════════════════════════════════════════════════════╝\n')

    running_any = False
    for phase_num, phase_info in PHASES.items():
        s = state[phase_num]
        status = s['status']
        icon = STATUS_ICON.get(status, '⬜')
        label = phase_info['label']
        phase_icon = phase_info['icon']
        dur = elapsed(s['ts_start'], s['ts_end'] if status != 'running' else None)
        dur_str = f'  [{dur}]' if dur else ''

        # Tree connector
        connector = '├──' if phase_num < max(PHASES) else '└──'

        if status == 'running':
            running_any = True
            print(f'  {connector} {icon} {phase_icon} {label}{dur_str}  ← RUNNING')
        elif status == 'complete':
            print(f'  {connector} {icon} {phase_icon} {label}{dur_str}')
        elif status == 'failed':
            print(f'  {connector} {icon} {phase_icon} {label}  ← FAILED')
        elif status == 'skipped':
            print(f'  {connector} {icon} {phase_icon} {label}  (skipped)')
        else:
            print(f'  {connector} {icon} {phase_icon} {label}')

    # Summary line
    complete = sum(1 for s in state.values() if s['status'] == 'complete')
    failed = sum(1 for s in state.values() if s['status'] == 'failed')
    total_active = sum(1 for s in state.values() if s['status'] != 'waiting')

    print(f'\n  Progress: {complete}/{len(PHASES)} phases complete', end='')
    if failed:
        print(f'  |  ❌ {failed} failed', end='')
    if running_any:
        print(f'  |  ⏳ running...', end='')
    print()

    # Control file hint
    control_file = progress_file.parent / 'audit-control.json'
    if control_file.exists():
        try:
            ctrl = json.loads(control_file.read_text())
            action = ctrl.get('action', '')
            if action:
                print(f'\n  Control: [{action.upper()}] instruction pending')
        except Exception:
            pass

    print(f'\n  Controls (edit {progress_file.parent}/audit-control.json):')
    print(f'    Stop:   {{"action":"stop"}}')
    print(f'    Resume: {{"action":"resume","from":N}}')
    print(f'\n  Last updated: {datetime.now().strftime("%H:%M:%S")}  (Ctrl+C to exit)')

def write_control(progress_file, action, from_phase=None):
    control_file = progress_file.parent / 'audit-control.json'
    payload = {'action': action}
    if from_phase:
        payload['from'] = from_phase
    control_file.write_text(json.dumps(payload, indent=2))
    print(f'Written to {control_file}')

def main():
    parser = argparse.ArgumentParser(description='Watch Algolia audit pipeline progress')
    parser.add_argument('company', help='Company name (e.g., Costco)')
    parser.add_argument('--stop-after', type=int, help='Stop pipeline after this phase number')
    parser.add_argument('--resume-from', type=int, help='Write resume instruction for this phase')
    parser.add_argument('--once', action='store_true', help='Print once and exit (no live watching)')
    args = parser.parse_args()

    company = args.company
    progress_file = Path(AUDIT_DIR) / company / 'audit-progress.jsonl'

    if args.stop_after:
        write_control(progress_file, 'stop_after', args.stop_after)
        return

    if args.resume_from:
        write_control(progress_file, 'resume', args.resume_from)
        return

    print(f'Watching {progress_file} ...')
    print(f'(File will be created when audit starts)')

    try:
        while True:
            events = load_events(progress_file)
            state = build_state(events)
            clear_screen()
            render(company, state, progress_file)

            if args.once:
                break

            # Check if all done
            statuses = [s['status'] for s in state.values()]
            if all(s in ('complete', 'skipped', 'failed', 'waiting') for s in statuses):
                complete = sum(1 for s in statuses if s == 'complete')
                if complete > 0:
                    # Some work was done and nothing is running — stable end state
                    time.sleep(2)
                    break

            time.sleep(2)

    except KeyboardInterrupt:
        print('\n\nWatcher stopped.')

if __name__ == '__main__':
    main()
