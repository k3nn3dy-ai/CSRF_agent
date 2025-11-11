from dotenv import load_dotenv
load_dotenv()

from csrf_v2.crew import CsrfCrew


def _print_highlight_banner(lines):
	# Use 256-color orange (38;5;208) with bold for high visibility
	ORANGE = "\033[38;5;208m"
	BOLD = "\033[1m"
	RESET = "\033[0m"
	border = "═" * 64
	try:
		print(f"{ORANGE}{BOLD}{border}{RESET}")
		for line in lines:
			print(f"{ORANGE}{BOLD}{line}{RESET}")
		print(f"{ORANGE}{BOLD}{border}{RESET}")
	except Exception:
		# Fallback without ANSI if terminal doesn't support it
		print(border)
		for line in lines:
			print(line)
		print(border)


def run():
	# Inputs read from .env as defaults; can be overridden here if desired.
	from os import getenv
	inputs = {
		"TARGET": getenv("TARGET", ""),
		"CREDENTIALS": getenv("CREDENTIALS", ""),
	}
	# Resolve provider/model (mirrors crew logic)
	provider = (getenv("LLM_PROVIDER") or "").lower()
	openai_key = getenv("OPENAI_API_KEY")
	anthropic_key = getenv("ANTHROPIC_API_KEY")
	openai_model = getenv("OPENAI_MODEL", "gpt-5")
	anthropic_model = getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
	if provider == "openai" or (provider == "" and openai_key):
		resolved_provider = "openai"
		resolved_model = openai_model
	elif provider == "anthropic" or anthropic_key:
		resolved_provider = "anthropic"
		resolved_model = anthropic_model
	else:
		resolved_provider = "(none)"
		resolved_model = "(unconfigured)"

	_print_highlight_banner([
		f"[CSRF v2] Target: {inputs['TARGET'] or '(empty)'}",
		f"[CSRF v2] Credentials: {inputs['CREDENTIALS'] or '(empty)'}",
		f"[CSRF v2] LLM: provider={resolved_provider} model={resolved_model}",
	])
	CsrfCrew().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
	run()

