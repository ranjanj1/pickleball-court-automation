# Court Reserve Auto-Registration

Automation script for registering for pickleball open play sessions on Court Reserve.

## Features

- ✅ Auto-login to Court Reserve
- ✅ Filter by skill level (Intermediate 3.0-3.49)
- ✅ Filter by price (FREE only)
- ✅ Smart time filtering (Evening for weekdays, Morning for weekends)
- ✅ Auto-register or join waitlist
- ✅ Detailed logging
- ✅ Dry-run mode for testing

## Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Credentials

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your credentials
# CR_USERNAME=your_email@example.com
# CR_PASSWORD=your_password
```

### 3. Test Login

```bash
# Run in dry-run mode to test without registering
python register.py --dry-run
```

## Usage

### Register for Events 21 Days Out

```bash
python register.py
```

### Dry Run (Test Without Registering)

```bash
python register.py --dry-run
```

### Check a Specific Date

```bash
python register.py --date 2026-03-08
```

### Run in Headless Mode

```bash
python register.py --headless
```

## How It Works

1. Logs in to Court Reserve with your credentials
2. Navigates to Pickleball Programs > Open Play
3. Applies filters:
   - Skill Level: Intermediate (3.0-3.49)
   - Day Type: Weekend or Weekday (based on target date)
   - Time: Evening (weekdays) or Morning (weekends)
   - Price: FREE only
4. Finds events on the target date (21 days from now by default)
5. Registers for available spots or joins waitlist if full
6. Logs all actions to `logs/` directory

## Time Preferences

- **Weekdays** (Mon-Fri): Evening sessions only
- **Weekends** (Sat-Sun): Morning sessions only

To change these, edit `config.py`:
```python
WEEKDAY_TIME = "Evening"
WEEKEND_TIME = "Morning"
```

## Logs

All registrations are logged to `logs/registration_YYYY-MM-DD_HH-MM-SS.log`

Screenshots are saved on errors for debugging.

## Troubleshooting

### Login fails
- Verify credentials in `.env`
- Check if site requires 2FA
- Run without `--headless` to see what's happening

### No events found
- Run `--dry-run` to see filter results
- Check that events exist 21 days out
- Verify the page structure hasn't changed

### Registration doesn't complete
- The script may need adjustment for the confirmation flow
- Check the screenshot in `logs/` directory
- Run without `--headless` to observe the process
