def system_prompt(memory) -> str:
    m = memory.data
    return f"""
You are RoboDev, a robotics engineering assistant/expert that produces practical engineering outputs.
User context defaults:
- Stack: {m.get("stack")}
- Simulator: {m.get("sim")}
- Language: {m.get("language")}
- Robot Type: {m.get("robot_type")}
Style: {m.get("style")}

Rules:
- Be specific, robotics-first (control, planning, perception, integration).
- When generating artifacts, output in STRICT sections with filenames.
- Avoid fluff. Provide runnable skeletons and clear TODOs.
"""

def brainstorm_prompt(memory, query:str) -> str:
    return f"""
Task: Brainstorm robotics approaches/solutions

{project_context(memory)}

User query: {query}

Output format:
1) Assumptions(bullet list)
2) 2-3 approaches/solutions (each with: idea, when to use, pros/cons, pitfalls, tuning knobs)
3) Recommended approach/solution + why
4) Implementation plan (steps, resources, timeline)
"""

def codegen_prompt(memory, query:str, lang:str, xml: str) -> str:
    return f"""
Task: Generate robotics artifacts

{project_context(memory)}

User query: {query}

Constraints:
- Language: {lang}
- XML type: {xml}

Output MUST follow this exact structure.

=== SUMMARY ===
(What you generated, how to use it, and any important notes)

=== FILES ===
# filename: <relative_path_to_file>
```<language or text>
<file content>
"""

def diagnose_prompt(memory, log_text: str) -> str:
    return f"""
Task: Diagnose robotics compile/build errors and propose minimal fixes.

Log text: {log_text}

Output format:
1) Observations (bullet list)
2) Potential causes (bullet list)
3) Fix plan (ordered steps)
4) Patch Suggestions (show diffs if applicable)
5) Verification steps (how to confirm the fix works)
"""

def project_context(memory):
    root = memory.data.get("project_root")
    if not root:
        return "Project root is not set."
    return f"Project root: {root}"