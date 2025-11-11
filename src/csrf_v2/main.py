from dotenv import load_dotenv
load_dotenv()

from csrf_v2.crew import CsrfCrew


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

	print(f"[CSRF v2] Target: {inputs['TARGET'] or '(empty)'}")
	print(f"[CSRF v2] Credentials: {inputs['CREDENTIALS'] or '(empty)'}")
	print(f"[CSRF v2] LLM: provider={resolved_provider} model={resolved_model}")
	CsrfCrew().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
	run()

