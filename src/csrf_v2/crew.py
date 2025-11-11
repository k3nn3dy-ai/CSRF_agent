from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.agents import Tool
from langchain_community.tools import ShellTool
import os
import logging
import warnings
import shlex
import signal
import socket
import subprocess
import sys
import time


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


def _configure_warnings():
	# Suppress noisy shell tool warning unless explicitly allowed
	if (os.getenv("ALLOW_SHELL_WARNINGS") or "0").lower() not in ("1", "true", "yes", "y"):
		warnings.filterwarnings(
			"ignore",
			message="The shell tool has no safeguards by default. Use at your own risk.",
			category=UserWarning,
			module=r"langchain_community\.tools\.shell\.tool",
		)

	# Suppress Pydantic v2 deprecation warnings from upstream libs (crewai, crewai-tools)
	if (os.getenv("ALLOW_PYDANTIC_WARNINGS") or "0").lower() not in ("1", "true", "yes", "y"):
		try:
			# Pydantic v2 exposes a specific warning class
			from pydantic import PydanticDeprecatedSince20 as _PydanticV2Dep
		except Exception:
			_PydanticV2Dep = DeprecationWarning

		# Ignore pydantic v1-style usage coming from crewai and crewai-tools only
		warnings.filterwarnings("ignore", category=_PydanticV2Dep, module=r"^crewai(\.|$)")
		warnings.filterwarnings("ignore", category=_PydanticV2Dep, module=r"^crewai_tools(\.|$)")
		# Extra guards using message regex for environments lacking the specific class
		warnings.filterwarnings(
			"ignore",
			message=r".*class-based `config` is deprecated.*",
			category=DeprecationWarning,
			module=r"^crewai(\.|$)",
		)
		warnings.filterwarnings(
			"ignore",
			message=r".*V1 style `@validator` validators are deprecated.*",
			category=DeprecationWarning,
			module=r"^crewai_tools(\.|$)",
		)


_configure_warnings()


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


def _pid_file_for_port(port: int) -> str:
	return f".http_server_{port}.pid"


def _log_file_for_port(port: int) -> str:
	return f"http_server_{port}.log"


def _is_process_running(pid: int) -> bool:
	try:
		os.kill(pid, 0)
		return True
	except Exception:
		return False


def _is_port_open(port: int) -> bool:
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.settimeout(0.2)
		return s.connect_ex(("127.0.0.1", port)) == 0


def http_server_tool(command: str) -> str:
	"""
	Manage a background Python HTTP server without blocking the agent.
	Usage:
	  - "start [port] [directory]"  (defaults: port=8001, directory=".")
	  - "stop [port]"               (default port=8001)
	  - "status [port]"             (default port=8001)
	"""
	try:
		tokens = shlex.split(command) if command else []
		action = (tokens[0].lower() if tokens else "start")
		port = int(tokens[1]) if len(tokens) >= 2 and tokens[1].isdigit() else 8001
		directory = tokens[2] if len(tokens) >= 3 else "."
		pid_file = _pid_file_for_port(port)
		log_file = _log_file_for_port(port)

		if action == "status":
			if os.path.exists(pid_file):
				try:
					with open(pid_file, "r") as f:
						pid = int(f.read().strip())
				except Exception:
					pid = None
				running = (pid is not None and _is_process_running(pid))
				port_open = _is_port_open(port)
				return f"HTTP server status: pid={pid or 'unknown'} running={running} port_open={port_open} port={port}"
			return f"HTTP server status: no pid file, port_open={_is_port_open(port)} port={port}"

		if action == "stop":
			if os.path.exists(pid_file):
				try:
					with open(pid_file, "r") as f:
						pid = int(f.read().strip())
				except Exception:
					pid = None
				try:
					if pid:
						# terminate the whole process group if available
						try:
							os.killpg(os.getpgid(pid), signal.SIGTERM)
						except Exception:
							os.kill(pid, signal.SIGTERM)
						time.sleep(0.5)
				except Exception as e:
					# ignore failures but report
					pass
				try:
					os.remove(pid_file)
				except Exception:
					pass
				return f"Stopped HTTP server on port {port}"
			return f"No HTTP server pid file found for port {port}"

		# default: start
		# If already running, short-circuit
		if os.path.exists(pid_file):
			try:
				with open(pid_file, "r") as f:
					existing_pid = int(f.read().strip())
				if _is_process_running(existing_pid):
					return f"HTTP server already running on port {port} (pid={existing_pid})"
			except Exception:
				pass

		cmd = [
			sys.executable,
			"-m",
			"http.server",
			str(port),
			"--bind",
			"127.0.0.1",
		]
		if directory:
			cmd += ["--directory", directory]

		with open(log_file, "ab") as lf:
			# Detach in a new process group so it doesn't block or capture stdin
			proc = subprocess.Popen(
				cmd,
				stdout=lf,
				stderr=lf,
				stdin=subprocess.DEVNULL,
				preexec_fn=os.setsid if hasattr(os, "setsid") else None,
				close_fds=True,
			)
		with open(pid_file, "w") as pf:
			pf.write(str(proc.pid))

		# Wait briefly for the server to bind
		for _ in range(20):
			if _is_port_open(port):
				break
			time.sleep(0.1)

		return f"Started HTTP server on port {port} (pid={proc.pid}) logging to {log_file}"
	except Exception as e:
		return f"HttpServer error: {e}"


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
		self.http_server_tool = Tool(
			name="HttpServer",
			func=http_server_tool,
			description=(
				"Manage a local Python HTTP server in the background to host HTML payloads.\n"
				"Usage:\n"
				"- start [port] [directory]  (defaults: 8001, .)\n"
				"- stop [port]\n"
				"- status [port]\n"
				"Examples: 'start', 'start 8001 ./public', 'status 8001', 'stop 8001'\n"
				"Logs are written to http_server_<port>.log and PID to .http_server_<port>.pid"
			),
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
			tools=[self.shell_tool, self.http_server_tool],
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
			context=[self.authentication_task()],
			output_file="crawler.md"
		)

	@task
	def csrf_testing_task(self) -> Task:
		return Task(
			config=self.tasks_config['csrf_testing_task'],
			agent=self.tester(),
			context=[self.csrf_identification_task(), self.authentication_task()],
			output_file="payloads.md"
		)

	@task
	def reporting_task(self) -> Task:
		return Task(
			config=self.tasks_config['reporting_task'],
			agent=self.reporting_agent(),
			context=[self.csrf_testing_task(), self.csrf_identification_task()],
			output_file='report.md'
		)

	@task
	def vuln_verification_task(self) -> Task:
		return Task(
			config=self.tasks_config['vuln_verification_task'],
			agent=self.tester(),
			context=[self.reporting_task(), self.csrf_testing_task()],
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

