# Upload to GitHub

Complete the Windows/MySQL checklist first. Keep .env only on your computer.

1. Sign in to GitHub and create an empty repository named gym-manager. Choose public or private. Do not initialize it with README because this project includes one.
2. Install Git for Windows if needed, then open PowerShell in this project folder.
3. Run:

```powershell
git init
git add .
git status
```

Confirm .env, .venv, exports and receipts are absent from staged files. .env.example should contain placeholders only.

```powershell
git commit -m "Complete gym membership desktop project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/gym-manager.git
git push -u origin main
```

Replace YOUR_USERNAME with your GitHub username. Complete Git's browser sign-in when prompted. If Git requests your identity, set your name and GitHub email using `git config user.name "Your Name"` and `git config user.email "Your GitHub email"`, then retry the commit. Do not enter a GitHub password into project code.

For later updates: git add ., git commit -m "Describe change", then git push. This package has not been uploaded to GitHub automatically.
