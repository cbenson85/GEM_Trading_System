#!/usr/bin/env python3
"""
Quick Update Script for GEM Catch-Up Prompt
Usage: python3 update_prompt.py "Phase X" "What you just did" "The result"
"""

import sys
from catchup_prompt_generator import CatchUpPromptGenerator

if len(sys.argv) < 4:
    print("Usage: python3 update_prompt.py <phase> <action> <result>")
    print("\nExample:")
    print('  python3 update_prompt.py "Phase 2" "Created data folders" "Infrastructure ready"')
    sys.exit(1)

phase = sys.argv[1]
action = sys.argv[2]
result = sys.argv[3]

print(f"📝 Updating catch-up prompt...")
print(f"   Phase: {phase}")
print(f"   Action: {action}")
print(f"   Result: {result}")

generator = CatchUpPromptGenerator()
generator.update_progress(phase, action, result)

# Regenerate prompt
prompt = generator.generate_prompt()
with open("CURRENT_CATCHUP_PROMPT.md", 'w') as f:
    f.write(prompt)

print(f"\n✅ Catch-up prompt updated!")
print(f"📄 New version saved to CURRENT_CATCHUP_PROMPT.md")
print(f"📊 State saved to system_state.json")
