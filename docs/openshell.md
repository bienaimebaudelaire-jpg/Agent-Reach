# NVIDIA OpenShell

Agent-Reach can use the NVIDIA OpenShell CLI to execute upstream collection
tools inside an isolated OpenShell sandbox. Agent-Reach remains the installer
and configuration tool; OpenShell provides the governed runtime, and the
platform tools (such as `twitter`, `bili`, `gh`, or `mcporter`) do the
searching and retrieval.

## Install and prepare OpenShell

Install the OpenShell CLI and start or select a gateway by following the
[NVIDIA OpenShell installation guide](https://docs.nvidia.com/openshell/latest/).
OpenShell requires a supported host and a container or VM runtime. Its Python
SDK is available as an optional Agent-Reach extra on Python 3.11+:

```bash
pip install 'agent-reach[openshell] @ git+https://github.com/Panniantong/agent-reach.git'
```

The extra installs the SDK, not the OpenShell CLI or gateway. Agent-Reach
supports Python 3.10; use the CLI wrapper without this extra on Python 3.10.
The wrapper also has no SDK import requirement.

Create a sandbox image that contains Agent-Reach and the upstream tools your
workflow needs, then start it with a persistent main process. For example:

```bash
openshell sandbox create \
  --name research \
  --from your-registry/agent-reach-tools:latest \
  --detach \
  -- sh -c 'while sleep 3600; do :; done'
```

Set up credentials and network access using OpenShell providers and sandbox
policies. Do not bake access tokens or cookies into the image or pass secrets
in command arguments.

## Execute collection commands

Run upstream tools inside the named sandbox with the Agent-Reach wrapper:

```python
from agent_reach.integrations.openshell import exec_in_sandbox

result = exec_in_sandbox(
    "research",
    ["mcporter", "call", "exa.web_search_exa", "query=OpenShell", "numResults=5"],
    timeout=60,
)
if not result.ok:
    raise RuntimeError(result.stderr or f"OpenShell exited {result.returncode}")
print(result.stdout)
```

The command is an argument list and is passed directly to OpenShell without
running a shell on the host. Use one upstream tool invocation per call and
inspect the exit status and output before proceeding. For commands that support
structured results, request JSON or YAML and parse the result in the calling
agent.

Examples of upstream searches can be run through the same wrapper:

```python
queries = [
    ["twitter", "search", "AI safety", "-n", "10"],
    ["bili", "search", "AI safety", "--type", "video", "-n", "5"],
    ["gh", "search", "repos", "AI safety", "--limit", "5"],
    ["opencli", "reddit", "search", "AI safety", "-f", "yaml"],
]
for command in queries:
    result = exec_in_sandbox("research", command, timeout=90)
    if result.ok:
        print(result.stdout)
    else:
        print(f"{command[0]} failed ({result.returncode}): {result.stderr}")
```

Use only tools installed in the sandbox image and sources allowed by its
OpenShell network policy. The equivalent direct CLI form is
`openshell sandbox exec --name research -- <command>`. See the
[OpenShell sandbox guide](https://docs.nvidia.com/openshell/latest/how-it-works/sandboxes/overview)
for lifecycle, upload, and policy controls.
