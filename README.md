
**Project Overview**

- Purpose: This project implements an agent-based debate workflow that uses configurable LLM backends (OpenAI or Azure OpenAI) to power different roles (proponent, opponent, judge, moderator, fact-checker, etc.). It demonstrates how multiple LLM-driven nodes can be composed to run structured debates.
- Intended audience: researchers, developers, and educators who want to learn how to orchestrate multiple LLM agents into a coordinated workflow.

**High-level Structure**
- Entry point: `main.py` — example/demo runner.
- Workflow definition: [workflow/debate_workflow.py](workflow/debate_workflow.py) — defines how nodes connect, message flows, and stage transitions.
- Node implementations: `nodes/` — each file implements a role node (pro_debater, con_debater, judge, fact_check_router, fact_checker, moderator). Example: [nodes/pro_debater_node.py](nodes/pro_debater_node.py).
- Configuration: `configurations/` — LLM and constants configuration, e.g. [configurations/llm_config.py](configurations/llm_config.py).

**Core Concepts & Workflow**
- Nodes: The system is composed of modular nodes where each node encapsulates the behavior of a role (generate arguments, evaluate rebuttals, run fact-checks, score, etc.).
- Message flow: The workflow advances by passing messages between nodes: the moderator initiates the topic and stages; pro/con debaters generate arguments according to the current stage; fact-checkers validate claims; the judge scores results.
- Stages: Typical stages include `opening`, `rebuttal`, `counter`, `final_argument`, and `end`. Stage names are defined in [configurations/debate_constants.py](configurations/debate_constants.py).
- LLM backend switching: The project supports using OpenAI (via `OPENAI_API_KEY`) or Azure OpenAI (via various `AZURE_*` environment variables). See [configurations/llm_config.py](configurations/llm_config.py) for details.

**Quick Start**
- 1) Install dependencies:

	```bash
	pip install -r requirements.txt
	```

- 2) Prepare environment variables: The project reads sensitive API keys and endpoints from a `.env` file (do not commit this file). Copy the provided template and fill in real values:

	```bash
	cp .env.example .env
	# Edit .env and add your keys/endpoints
	```

- 3) Run the demo:

	```bash
	python main.py
	```

**Required Environment Variables (in `.env`)**
- The project currently reads the following environment variables in `configurations/llm_config.py`. Fill in at least the keys/endpoints for the backend you plan to use:

- `OPENAI_API_KEY`
- `AZURE_ENDPOINT_GPT4O`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_API_KEY_GPT4O`
- `AZURE_ENDPOINT_GPT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_ENDPOINT_EMBEDDING_3`
- `AZURE_OPENAI_API_VERSION_EMBEDDING_3`
- `AZURE_OPENAI_API_KEY_EMBEDDING_3_LARGE`

If you only use OpenAI's direct API, typically only `OPENAI_API_KEY` is required. Leave unused variables empty.

**About `.env` and Security (Important)**
- Do not commit your local `.env` file to any remote repository. I have added `.env` to `.gitignore`.
- If you have accidentally committed `.env`, stop tracking it locally and commit the change:

	```bash
	# Stop tracking but keep the file locally
	git rm --cached .env
	git commit -m "Stop tracking .env"
	git push
	```

- If `.env` has already been pushed to a remote and you need to remove it from history, use a history-rewriting tool such as BFG or `git-filter-repo`. This rewrites history and usually requires a forced push — back up your repository first. Example (dangerous; backup before running):

	```bash
	# Example using git filter-branch (not recommended for large repos)
	# git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
	# git push origin --force --all
	```

- Keep real secrets out of `.env.example`; the example file lists only environment variable names for user convenience.

**Development Notes & Extensibility**
- To add a new node, create a new file under `nodes/` following the existing node interface, then register it in [workflow/debate_workflow.py](workflow/debate_workflow.py) and define the message flow and stage transitions.
- To add or change LLM backends, add the appropriate configuration mapping and environment variables in `configurations/llm_config.py`.

**File Index (Quick Links)**
- Main workflow: [workflow/debate_workflow.py](workflow/debate_workflow.py)
- Node implementations: [nodes/](nodes)
- LLM configuration: [configurations/llm_config.py](configurations/llm_config.py)
- Constants: [configurations/debate_constants.py](configurations/debate_constants.py)

If you'd like, I can help remove an already pushed `.env` from remote history (requires confirmation and backup) or run a local demo to verify the steps above.

