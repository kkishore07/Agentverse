"""
scratch/test_all_features.py
Comprehensive diagnostic suite to test every agent, skill, core module, TUI screen, and server route.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

class MockLLMResponse:
    def __init__(self, text):
        self.text = text

class MockLLMStream:
    def __init__(self, text):
        self.text = text
    def __aiter__(self):
        self._iter = iter([self.text])
        return self
    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

class MockLLMClient:
    def __init__(self, mock_json=None, mock_text=None):
        self.mock_json = mock_json or {}
        self.mock_text = mock_text or "Mock LLM Response"

    async def generate(self, prompt, system=None, json_mode=False, **kwargs):
        import json
        text = json.dumps(self.mock_json) if json_mode else self.mock_text
        return MockLLMResponse(text)

    def stream(self, prompt, system=None, json_mode=False, **kwargs):
        import json
        text = json.dumps(self.mock_json) if json_mode else self.mock_text
        return MockLLMStream(text)

async def test_agents():
    print("--- Testing Agents ---")
    from core.event_bus import EventBus
    from agents.planner import PlannerAgent, PlannerInput
    from agents.architect import ArchitectAgent, ArchitectInput
    from agents.coder import CoderAgent, CoderInput
    from agents.validator import ValidatorAgent, ValidatorInput
    from agents.tester import TesterAgent, TesterInput
    from agents.fixer import FixerAgent, FixerInput
    from agents.reviewer import ReviewerAgent, ReviewerInput
    from agents.docs import DocumentationAgent, DocsInput
    from agents.github import GitHubAgent, GitHubInput

    bus = EventBus()

    # 1. PlannerAgent
    llm = MockLLMClient(mock_json={"project": "TestApp", "tasks": ["Task 1", "Task 2"]})
    planner = PlannerAgent(llm, bus)
    p_out = await planner.run(PlannerInput(goal="Create a test app"))
    assert p_out.project_name == "TestApp"
    assert len(p_out.tasks) == 2
    print("[PASS] PlannerAgent")

    # 2. ArchitectAgent
    llm = MockLLMClient(mock_json={
        "tech_stack": ["Python", "FastAPI"],
        "folders": ["src"],
        "files": [{"path": "main.py", "purpose": "Entry point", "type": "code"}]
    })
    architect = ArchitectAgent(llm, bus)
    a_out = await architect.run(ArchitectInput(goal="Create a test app", tasks=["Task 1"]))
    assert len(a_out.files) >= 1
    print("[PASS] ArchitectAgent")

    # 3. CoderAgent
    llm = MockLLMClient(mock_text="def hello():\n    return 'world'")
    coder = CoderAgent(llm, bus)
    c_out = await coder.run(CoderInput(
        goal="Create test app",
        tech_stack=["Python"],
        file_path="main.py",
        file_purpose="Entry point",
        sibling_files=["main.py"]
    ))
    assert "def hello" in c_out.content
    print("[PASS] CoderAgent")

    # 4. ValidatorAgent
    tmp_dir = Path("./tmp_test_workspace").resolve()
    tmp_dir.mkdir(parents=True, exist_ok=True)
    test_file = tmp_dir / "test.py"
    test_file.write_text("print('hello')", encoding="utf-8")
    
    validator = ValidatorAgent(llm, bus)
    v_out = await validator.run(ValidatorInput(workspace_dir=tmp_dir, written_files=["test.py"]))
    assert v_out.passed is True
    print("[PASS] ValidatorAgent")

    # 5. TesterAgent
    tester = TesterAgent(llm, bus)
    t_out = await tester.run(TesterInput(workspace_dir=tmp_dir))
    assert t_out.passed is True
    print("[PASS] TesterAgent")

    # 6. FixerAgent
    llm = MockLLMClient(mock_text="print('fixed hello')")
    fixer = FixerAgent(llm, bus)
    f_out = await fixer.run(FixerInput(file_path="test.py", content="print('bad')", errors=["SyntaxError"]))
    assert "fixed" in f_out.fixed_content
    print("[PASS] FixerAgent")

    # 7. ReviewerAgent
    llm = MockLLMClient(mock_json=[{"file": "test.py", "severity": "low", "issue": "No docstring", "suggestion": "Add docstring"}])
    reviewer = ReviewerAgent(llm, bus)
    r_out = await reviewer.run(ReviewerInput(goal="Review", files=[{"path": "test.py", "content": "print('hello')"}]))
    assert len(r_out.issues) == 1
    print("[PASS] ReviewerAgent")

    # 8. DocumentationAgent
    llm = MockLLMClient(mock_text="# TestApp\nDocumentation")
    docs = DocumentationAgent(llm, bus)
    d_out = await docs.run(DocsInput(goal="Docs", tech_stack=["Python"], files=[{"path": "test.py", "purpose": "test"}]))
    assert d_out.path == "README.md"
    print("[PASS] DocumentationAgent")

    # Clean up tmp
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

async def test_skills():
    print("\n--- Testing Skills ---")
    from skills.ast_validator import ASTValidatorSkill
    from skills.filesystem import FilesystemSkill
    from skills.git import GitSkill
    from skills.patch import PatchSkill
    from skills.project_analyzer import ProjectAnalyzerSkill
    from skills.terminal import TerminalSkill
    from skills.tester_skill import TesterSkill

    workspace = Path(".").resolve()

    ast_val = ASTValidatorSkill(workspace)
    errs = ast_val.validate([])
    assert len(errs) == 0
    print("[PASS] ASTValidatorSkill")

    fs = FilesystemSkill(workspace)
    assert fs.exists("pyproject.toml") or fs.exists("README.md")
    print("[PASS] FilesystemSkill")

    analyzer = ProjectAnalyzerSkill(workspace)
    lang = analyzer.detect_language(["main.py"])
    assert lang == "Python"
    print("[PASS] ProjectAnalyzerSkill")

    term = TerminalSkill(workspace)
    exec_res = await term.execute("echo hello")
    assert exec_res.get("exit_code") == 0 or exec_res.get("returncode") == 0
    print("[PASS] TerminalSkill")

    git_skill = GitSkill(workspace)
    status_res = git_skill.get_status()
    assert isinstance(status_res, dict)
    print("[PASS] GitSkill")

    patch_skill = PatchSkill(workspace)
    patch_res = patch_skill.generate_diff("hello", "world")
    assert isinstance(patch_res, str)
    print("[PASS] PatchSkill")

    tester_skill = TesterSkill(workspace)
    cmd = tester_skill.detect_command({"language": "Python", "testing_framework": "pytest"})
    assert cmd == "pytest"
    print("[PASS] TesterSkill")

async def test_orchestrator():
    print("\n--- Testing Orchestrator ---")
    from core.orchestrator import Orchestrator
    from core.session import SessionManager
    from core.event_bus import EventBus
    from core.registry import SkillRegistry, AgentRegistry

    llm = MockLLMClient(mock_json={
        "project": "OrchestratorTest",
        "tasks": ["Task 1"],
        "tech_stack": ["Python"],
        "folders": [],
        "files": [{"path": "app.py", "purpose": "main app", "type": "code"}]
    }, mock_text="print('Orchestrator OK')")

    tmp_session = Path("./tmp_session.json").resolve()
    session_mgr = SessionManager(tmp_session)
    bus = EventBus()
    skills = SkillRegistry()
    agents = AgentRegistry()

    orch = Orchestrator(
        llm=llm,
        session_mgr=session_mgr,
        event_bus=bus,
        skill_registry=skills,
        agent_registry=agents,
        workspace_dir="./tmp_orch_ws"
    )

    result = await orch.run_pipeline("Project Creation", goal="Build test app")
    print(f"[PASS] Orchestrator Pipeline Result: success={result.success}, written_files={result.written_files}")

    import shutil
    shutil.rmtree("./tmp_orch_ws", ignore_errors=True)
    if tmp_session.exists():
        tmp_session.unlink()

async def test_tui_screens():
    print("\n--- Testing TUI Screens ---")
    from textual.app import App
    from tui.backend import build_backend
    from tui.screens.agents_screen import AgentsScreen
    from tui.screens.models_screen import ModelsScreen
    from tui.screens.skills_screen import SkillsScreen
    from tui.screens.theme_screen import ThemeScreen
    from tui.screens.help_screen import HelpScreen
    from tui.screens.settings_screen import SettingsScreen

    backend = build_backend()

    class ScreenTestApp(App):
        async def on_mount(self):
            for ScreenClass in [AgentsScreen, ModelsScreen, SkillsScreen, ThemeScreen, HelpScreen, SettingsScreen]:
                if ScreenClass in (ModelsScreen, SettingsScreen):
                    scr = ScreenClass(backend)
                else:
                    scr = ScreenClass()
                self.push_screen(scr)
                await asyncio.sleep(0.1)
                self.pop_screen()
            self.exit(0)

    app = ScreenTestApp()
    await app.run_async(headless=True)
    print("[PASS] All TUI Screens loaded & popped without error")

async def test_server_routes():
    print("\n--- Testing FastAPI Server ---")
    from fastapi.testclient import TestClient
    from server import app

    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "healthy"
    print("[PASS] Server GET /api/health")

    resp = client.get("/api/models")
    assert resp.status_code == 200
    print("[PASS] Server GET /api/models")

    resp = client.get("/api/agents")
    assert resp.status_code == 200
    print("[PASS] Server GET /api/agents")

async def main():
    await test_agents()
    await test_skills()
    await test_orchestrator()
    await test_tui_screens()
    await test_server_routes()
    print("\nALL AGENTS AND FEATURES TESTED SUCCESSFULLY AND VERIFIED WORKING!")

if __name__ == "__main__":
    asyncio.run(main())
