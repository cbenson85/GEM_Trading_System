# Catch-Up Prompt System - Usage Guide

## What This Does

This system creates and maintains a comprehensive catch-up prompt that can be used to bring a new AI conversation up to speed on exactly where you left off in the GEM Trading System development.

## Files Created

1. **CURRENT_CATCHUP_PROMPT.md** - The prompt itself (copy/paste this to new AI)
2. **catchup_prompt_generator.py** - Script that generates and updates the prompt
3. **system_state.json** - Stores the current state of the system

## How to Use

### Starting a New AI Conversation

1. Open `CURRENT_CATCHUP_PROMPT.md`
2. Copy the entire contents
3. Paste into a new Claude conversation
4. The AI will understand exactly where you left off

### Updating the Prompt (After Completing a Phase)

You (or the AI) should run:

```bash
python3 catchup_prompt_generator.py
```

This regenerates `CURRENT_CATCHUP_PROMPT.md` with current timestamp and state.

### Manually Updating Progress

The AI can update progress by editing `system_state.json` and re-running the generator.

Or you can use the Python API:

```python
from catchup_prompt_generator import CatchUpPromptGenerator

generator = CatchUpPromptGenerator()

# Update progress
generator.update_progress(
    phase="Phase 2",
    action="Created data infrastructure", 
    result="All folders and templates ready"
)

# Update current phase
generator.update_current_phase(
    phase_name="Phase 3: Stock Discovery",
    immediate_priority="Run 10-year scan for explosive stocks"
)

# Add a refinement
generator.add_refinement(
    change="Lowered minimum volume to 5,000",
    reason="Missing too many low-float explosive stocks"
)

# Regenerate prompt
prompt = generator.generate_prompt()
with open("CURRENT_CATCHUP_PROMPT.md", 'w') as f:
    f.write(prompt)
```

## Where to Store These Files

### Option 1: GitHub (Recommended)
Create a folder in your GitHub repo:
```
/System_State/
  ├── CURRENT_CATCHUP_PROMPT.md
  ├── catchup_prompt_generator.py
  └── system_state.json
```

### Option 2: Local + Manual Upload
Keep files locally and manually upload the prompt when needed.

## What Gets Tracked

The system automatically tracks:
- Current phase and priority
- Portfolio status
- Data verification status
- All decisions made
- All rules established
- Progress log with timestamps
- Refinement history
- Next steps
- Blockers

## Tips

1. **Update after EVERY phase** - Don't let it get stale
2. **Be specific in progress notes** - Future you (or future AI) will thank you
3. **Keep system_state.json backed up** - It's the source of truth
4. **Version control** - Commit to GitHub after major updates

## Recovering from Conversation Limit

When you hit conversation limits:

1. Download latest `CURRENT_CATCHUP_PROMPT.md` from GitHub
2. Start new Claude conversation
3. Paste the entire prompt
4. Say "I've provided the catch-up prompt. Please confirm you understand the current state and what phase we're on."
5. Continue from there!

## Modifying the Prompt Template

Edit the `self.template` string in `catchup_prompt_generator.py` to change the format or add new sections.

---

**Created**: 2025-11-01
**For**: GEM Trading System Rebuild
**Purpose**: Ensure continuity across AI conversation sessions
