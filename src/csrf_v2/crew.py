from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.agents import Tool
from langchain_community.tools import ShellTool
import os
import logging


def _configure_logging():
	# LOG_LEVEL defaults to WARNING to reduce console noise
	level_name = (os.getenv("LOG_LEVEL") or "WARNING").upper()
	level = getattr(logging, level_name, logging.WARNING)
	logging.basicConfig(level=level)
	for noisy in ("crewai", "langchain", "httpx", "urllib3", "openai", "anthropic"):
		try:
			logging.getLogger(noisy).setLevel(level)
		except Exception:
			pass


_configure_logging()


provider = (os.getenv("LLM_PROVIDER") or "").lower()
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

llm = None
if provider == "openai" or (provider == "" and openai_key):
	# Default to GPT-5 if provided; override via OPENAI_MODEL
	llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5"))
elif provider == "anthropic" or anthropic_key:
	llm = ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"))
else:
	raise RuntimeError("No LLM configured. Set LLM_PROVIDER=openai with OPENAI_API_KEY (and OPENAI_MODEL=gpt-5), or LLM_PROVIDER=anthropic with ANTHROPIC_API_KEY.")


@CrewBase
class CsrfCrew():
	"""CSRF crew v2"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self):
		shell = ShellTool()
		self.shell_tool = Tool(
			name="Shell", func=shell.run, description="Run shell commands like curl and gospider"
		)

	@agent
	def authentication_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['authentication_agent'],
			tools=[self.shell_tool],
			llm=llm,
		)

	@agent
	def web_crawler(self) -> Agent:
		return Agent(
			config=self.agents_config['web_crawler'],
			tools=[self.shell_tool],
			llm=llm,
		)

	@agent
	def tester(self) -> Agent:
		return Agent(
			config=self.agents_config['tester'],
			tools=[self.shell_tool],
			llm=llm,
		)

	@agent
	def reporting_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['reporting_agent'],
			llm=llm,
		)

	@task
	def authentication_task(self) -> Task:
		return Task(
			config=self.tasks_config['authentication_task'],
			agent=self.authentication_agent(),
			output_file="auth.md"
		)

	@task
	def csrf_identification_task(self) -> Task:
		return Task(
			config=self.tasks_config['csrf_identification_task'],
			agent=self.web_crawler(),
			output_file="crawler.md"
		)

	@task
	def csrf_testing_task(self) -> Task:
		return Task(
			config=self.tasks_config['csrf_testing_task'],
			agent=self.tester(),
			output_file="payloads.md"
		)

	@task
	def reporting_task(self) -> Task:
		return Task(
			config=self.tasks_config['reporting_task'],
			agent=self.reporting_agent(),
			output_file='report.md'
		)

	@task
	def vuln_verification_task(self) -> Task:
		return Task(
			config=self.tasks_config['vuln_verification_task'],
			agent=self.tester(),
			output_file='verification.md'
		)

	@crew
	def crew(self) -> Crew:
		verbose_flag = (os.getenv("VERBOSE", "true").lower() in ("1", "true", "yes", "y"))
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=verbose_flag,
			output_log_file="logs.txt",
			memory=False,
		)

