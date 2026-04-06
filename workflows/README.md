# GitHub Actions Workflows

Template workflows for automated market intelligence delivery.

## Setup

1. Copy the template to `.github/workflows/`:
   ```bash
   mkdir -p .github/workflows
   cp workflows/morning_report.yml.template .github/workflows/morning_report.yml
   ```

2. Configure repository secrets (Settings → Secrets and variables → Actions):

   | Secret | Required | Purpose |
   |--------|:--------:|---------|
   | `ANTHROPIC_API_KEY` | Yes | Claude AI analysis |
   | `TELEGRAM_BOT_TOKEN` | For Telegram | Bot token from @BotFather |
   | `TELEGRAM_CHAT_ID` | For Telegram | Your chat or group ID |
   | `TELEGRAM_CHANNEL_ID` | Optional | Channel like @yourchannel |
   | `FRED_API_KEY` | Optional | FRED economic data |
   | `SOSOVALUE_API_KEY` | Optional | ETF flow data |

3. Adjust the cron schedule in the workflow file for your timezone.

4. Push to GitHub — the workflow will run on schedule.

## Timezone Quick Reference

| Your Timezone | 07:00 local | 19:00 local |
|---------------|-------------|-------------|
| US Eastern (EST) | `0 12 * * 1-5` | `0 0 * * 2-6` |
| US Pacific (PST) | `0 15 * * 1-5` | `0 3 * * 2-6` |
| Singapore (SGT) | `0 23 * * 0-4` | `0 11 * * 1-5` |
| London (GMT) | `0 7 * * 1-5` | `0 19 * * 1-5` |
| Tokyo (JST) | `0 22 * * 0-4` | `0 10 * * 1-5` |

## Manual Trigger

You can also trigger any workflow manually from the GitHub Actions tab → "Run workflow".
