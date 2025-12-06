# GitHub Setup Guide for RABWA Accounting System

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click **"+"** (top right) → **"New repository"**
3. Fill in:
   - **Repository name**: `rabwa-accounting` (or your preferred name)
   - **Description**: `Django 5.0 ERP accounting system with fleet management`
   - **Public/Private**: Choose based on your preference (Private recommended for business code)
   - **Initialize with**: Leave unchecked (we'll push existing code)
4. Click **"Create repository"**
5. **Copy the repository URL** (HTTPS or SSH format)

---

## Step 2: Initialize Local Git Repository

```bash
# Navigate to project directory
cd /Users/shahanadk/Desktop/Easy-Accounting/RABWA/accounts

# Initialize git
git init

# Add all files (respects .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: RABWA accounting system setup"
```

---

## Step 3: Connect to GitHub

### Option A: HTTPS (Easiest for beginners)
```bash
# Add remote (replace with your repository URL)
git remote add origin https://github.com/YOUR_USERNAME/rabwa-accounting.git

# Verify connection
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### Option B: SSH (Recommended for frequent pushes)
```bash
# Setup SSH key (if not already done)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add key to GitHub
# 1. Copy output of: cat ~/.ssh/id_ed25519.pub
# 2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
# 3. Paste and save

# Add SSH remote
git remote add origin git@github.com:YOUR_USERNAME/rabwa-accounting.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 4: Track Changes Locally

### View status
```bash
git status
```

### Stage specific files
```bash
git add filename.py
# or specific directory
git add accounts_app/
# or all changes
git add .
```

### Create commits (save snapshots)
```bash
git commit -m "Feature: Add payment processing logic"
```

### Best practices for commit messages
- **Clear & concise**: `"Fix: Correct decimal precision in ledger posting"`
- **Type prefix**: `Fix:`, `Feature:`, `Refactor:`, `Docs:`, `Test:`
- **Reference issue**: `"Fix #42: Resolve privilege check bypass"`
- **Example commits for this project**:
  - `"Feature: Add role-based access control to Payment view"`
  - `"Fix: LedgerPosting decimal rounding error"`
  - `"Refactor: Move ledger posting logic to fleet_app.common"`
  - `"Docs: Update copilot-instructions.md with new patterns"`

---

## Step 5: Push Changes to GitHub

```bash
# Push specific branch
git push origin main

# Or after subsequent commits
git push
```

---

## Typical Daily Workflow

```bash
# 1. Check what changed
git status

# 2. Stage your changes
git add .

# 3. Commit with descriptive message
git commit -m "Feature: Implement cheque bounce processing"

# 4. Push to GitHub
git push

# 5. (Optional) View commit history
git log --oneline -10
```

---

## Common Commands Reference

| Command | Purpose |
|---------|---------|
| `git status` | See what files changed |
| `git add .` | Stage all changes |
| `git add filename` | Stage specific file |
| `git commit -m "message"` | Create commit snapshot |
| `git push` | Upload to GitHub |
| `git pull` | Download latest from GitHub |
| `git log --oneline -5` | View last 5 commits |
| `git diff` | See exact changes in files |
| `git branch` | View/create branches |
| `git checkout -b feature/new-feature` | Create feature branch |

---

## Git Branches Strategy (Recommended)

```bash
# Main branch - production ready
git checkout main

# Create feature branch
git checkout -b feature/payment-processing

# Work on feature
# ... make changes ...

# Commit
git add .
git commit -m "Feature: Add payment processing"

# Push feature branch
git push origin feature/payment-processing

# On GitHub: Create Pull Request (PR) to merge into main
# After review: merge on GitHub
# Delete branch locally
git checkout main
git pull
```

---

## Setup Local Git Config (First Time)

```bash
# Set your name
git config --global user.name "Your Name"

# Set your email
git config --global user.email "your.email@example.com"

# Verify
git config --global --list
```

---

## Important: Protect Sensitive Data

✅ **Already in .gitignore:**
- `.env` files (database credentials)
- `__pycache__/`
- `*.pyc`
- `venv/`
- `db.sqlite3`

⚠️ **NEVER commit:**
- Database passwords
- SECRET_KEY
- API keys
- Personal information

✅ **For production**: Use environment variables:
```python
# accounts/settings.py - GOOD ✅
import os
from dotenv import load_dotenv

load_dotenv()
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

---

## Undoing Changes

```bash
# Undo uncommitted changes in a file
git checkout filename

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# View what was reset
git reflog
```

---

## Pulling Changes (if working with team)

```bash
# Get latest from GitHub
git pull

# Or if conflicts:
git pull --rebase
# (resolve conflicts in editor, then)
git add .
git rebase --continue
```

---

## GitHub Actions (Optional - for CI/CD)

Create `.github/workflows/tests.yml` to run tests automatically:

```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python manage.py test
```

---

## Troubleshooting

**"fatal: not a git repository"**
```bash
git init
git remote add origin <your-repo-url>
```

**"Permission denied (publickey)"** (SSH)
```bash
# Ensure SSH key is added to ssh-agent
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com  # Test connection
```

**"Would be overwritten by merge"**
```bash
git stash  # Save changes temporarily
git pull
git stash pop  # Restore changes
```

---

## Next Steps

1. Replace `YOUR_USERNAME` and `rabwa-accounting` in commands with your actual values
2. Run the initialization commands in Step 2-3
3. Make your first commit
4. Start tracking changes with daily commits
5. Consider inviting team members (Settings → Collaborators on GitHub)

---

## Resources
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com)
- [Atlassian Git Tutorials](https://www.atlassian.com/git)
