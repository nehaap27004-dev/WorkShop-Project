# Git Quick Reference - RABWA Accounting System

## ⚡ Super Quick Start

```bash
# 1. Navigate to project
cd /Users/shahanadk/Desktop/Easy-Accounting/RABWA/accounts

# 2. Check status
git status

# 3. Stage changes
git add .

# 4. Commit
git commit -m "Feature: description of your change"

# 5. Push to GitHub
git push
```

---

## 🔗 Connect to GitHub (One-Time Setup)

### Step 1: Create repo on GitHub.com
1. Go to github.com → Click **+** → **New repository**
2. Name: `rabwa-accounting`
3. Choose Private/Public
4. **Don't initialize** - click Create

### Step 2: Connect locally (copy-paste the command GitHub shows)
```bash
cd /Users/shahanadk/Desktop/Easy-Accounting/RABWA/accounts
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rabwa-accounting.git
git push -u origin main
```

**That's it!** Your code is now on GitHub.

---

## 📝 Daily Workflow

### Check what changed
```bash
git status
```
Shows: files added/modified/deleted

### See actual code changes
```bash
git diff
```
Shows: line-by-line changes (green = added, red = removed)

### Stage changes
```bash
git add .              # Stage everything
git add filename.py    # Stage specific file
git add accounts_app/  # Stage entire folder
```

### Commit (save snapshot with message)
```bash
git commit -m "Feature: Add payment processing"
git commit -m "Fix: Correct decimal precision bug"
git commit -m "Docs: Update README"
```

### Push to GitHub
```bash
git push
```

---

## 📚 Commit Message Examples (for this project)

✅ **Good:**
- `"Feature: Add role-based privilege check to Payment form"`
- `"Fix: LedgerPosting decimal rounding error (fixes #42)"`
- `"Refactor: Extract ledger posting logic to fleet_app.common"`
- `"Docs: Update copilot-instructions with FormSet pattern"`
- `"Test: Add unit tests for check_privilege function"`

❌ **Bad:**
- `"update"`
- `"changes"`
- `"bug fix"`
- `"asdf"`

---

## 🌳 Branches (for teams)

### Create feature branch
```bash
git checkout -b feature/new-payment-feature
```

### Work on it
```bash
# Make changes...
git add .
git commit -m "Feature: Implement payment processing"
git push origin feature/new-payment-feature
```

### Merge via Pull Request on GitHub
1. Go to github.com/your-repo
2. Click "Pull Requests" → "New Pull Request"
3. Select your feature branch
4. Add description, click "Create"
5. After review → "Merge"

### Delete branch locally
```bash
git checkout main
git pull
git branch -d feature/new-payment-feature
```

---

## 🔍 View History

### Last 5 commits
```bash
git log --oneline -5
```

### Detailed view
```bash
git log --oneline --graph --all
```

### Changes by a person
```bash
git log --author="Shahana"
```

### Changes in a file
```bash
git log -p accounts_app/models.py
```

---

## ⚠️ Undo Changes

### Before commit (discard changes)
```bash
git checkout filename.py
```

### After commit (keep changes, undo commit)
```bash
git reset --soft HEAD~1
```

### After commit (discard completely)
```bash
git reset --hard HEAD~1
```

### What was that commit?
```bash
git reflog
```

---

## 🚀 Push to GitHub After Changes

```bash
# Scenario: You modified accounts_app/models.py
git status                           # See it changed
git add accounts_app/models.py       # Stage it
git commit -m "Fix: Custom User field validation"  # Commit
git push                             # Send to GitHub
```

**Done!** Your change is now on GitHub and visible to your team.

---

## 🛡️ Credentials & Secrets

**NEVER commit:**
- `.env` files
- Database passwords
- SECRET_KEY
- API keys

**Already ignored in `.gitignore`:**
- `*.pyc`, `__pycache__/`
- `venv/`, `db.sqlite3`
- `*.log`, `.env`

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| "fatal: not a git repository" | You're in wrong folder. `cd` to project root |
| "permission denied" (SSH) | Add SSH key to GitHub Settings |
| "branch diverged" | `git pull --rebase` then `git push` |
| Accidentally deleted file | `git checkout filename` to restore |
| Want to revert to old commit | `git revert COMMIT_HASH` |

---

## 📱 GitHub Mobile

You can also:
- View code changes
- Review Pull Requests
- Approve/merge PRs
- See commit history

Download GitHub app for iPhone/Android.

---

## 💡 Pro Tips

1. **Commit frequently** - Every feature or bugfix gets a commit
2. **Write clear messages** - Future you will thank you
3. **Push daily** - Backup your code to GitHub
4. **Use branches** - Keep main clean for production
5. **Review before commit** - `git diff` before `git add .`

---

## 📖 Next Reading

- **Full Guide**: `GITHUB_SETUP.md`
- **Codebase Patterns**: `.github/copilot-instructions.md`
- **Git Docs**: https://git-scm.com/doc
