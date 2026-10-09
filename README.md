# VulnLab - Deliberately Vulnerable Web Application

VulnLab is a full-featured, interactive cybersecurity playground built with Python (Flask) and SQLite. It is specifically designed to let you practice finding and exploiting web vulnerabilities, featuring a prominent **Pastejacking / Clipboard Hijacking** lab along with the top OWASP vulnerabilities.

---

## 🚀 Quick Start

1. Open PowerShell or Command Prompt in this folder (`d:\4th_sem\allvul`).
2. Run the application:
   ```cmd
   run.bat
   ```
   *Or directly with Python:*
   ```bash
   pip install -r requirements.txt
   python database.py
   python app.py
   ```
3. Open your web browser and navigate to:
   **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📋 Special Feature: Pastejacking & Clipboard Hijacking (`/pastejack`)

### What is it?
When copying commands from tutorials, documentation, or forums into a terminal, users expect to paste what they saw on screen. **Pastejacking** alters the clipboard contents so that what gets pasted is completely different from what is visually displayed. If an auto-executing newline (`\n`) is attached, the shell executes the malicious command immediately!

### Techniques Demonstrated in VulnLab:
1. **JavaScript `copy` Event Interception:**
   - Visual: `git clone https://github.com/torvalds/linux.git`
   - Actual Copied: `echo "ALERT: PASTEJACKING ATTACK TRIGGERED!" && calc.exe\n`
2. **CSS DOM Stealth Injection (Works with JS Disabled!):**
   - Uses `position: absolute; left: -9999px` to place hidden text off-screen.
   - When a user highlights the visible text with their mouse and presses `Ctrl + C`, the browser includes the hidden DOM elements in the clipboard!
3. **Built-in Safe Clipboard Inspector:**
   - A safe quarantine pastebox on the `/pastejack` page analyzes whatever you paste, extracts escape sequences, detects hidden `\n` characters, and warns you before you ever touch a real terminal.

---

## 🎯 OWASP Vulnerability Matrix Included

| Module | Route | Vulnerability Type | Description & Exploit |
|---|---|---|---|
| **Pastejacking** | `/pastejack` | Client-Side / Clipboard | Display text differs from copied text (JS & CSS tricks) |
| **SQL Injection** | `/sqli` | Server-Side / Database | Login bypass (`' OR '1'='1' --`) & UNION credit card dump |
| **Cross-Site Scripting** | `/xss` | Client-Side Script Injection | Stored guestbook, Reflected query, and DOM `innerHTML` sink |
| **Command Injection** | `/rce` | Remote Code Execution | Network ping tool executing shell commands (`127.0.0.1 & whoami`) |
| **Path Traversal** | `/traversal` | Local File Inclusion (LFI) | Directory escaping (`../../app.py`) to read source code |
| **SSRF** | `/ssrf` | Server-Side Request Forgery | Fetching `127.0.0.1:5000/internal/cloud-metadata` |
| **IDOR** | `/idor` | Broken Access Control | Changing `?id=1` to view admin API tokens and financial balances |
| **CSRF** | `/csrf` | Session Riding | Fund transfer without anti-CSRF token + Attacker PoC site |
| **Deserialization** | `/deserial` | Python `eval()` & `pickle` | Evaluating arbitrary Python expressions & unpickling objects |
| **Info Disclosure** | `/.git/config` | Information Leakage | Exposed `.git` configuration and secrets |

---

## 🔄 Resetting the Environment
At any time, you can click the **Reset DB** button in the top navigation bar or send a POST request to `/reset-db` to restore all database tables and seed data to factory defaults.
"# justvul" 
