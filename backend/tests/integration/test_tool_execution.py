import pytest

from apps.tools.models import ToolExecution
from apps.tools.services.script_repository import ScriptRepositoryService
from apps.tools.services.tool_runner import ToolRunnerService
from apps.tools.tasks.run_tool_task import run_tool_task


@pytest.mark.django_db
def test_tool_execution_flow(django_user_model):
    user = django_user_model.objects.create(username="tester")
    repo_service = ScriptRepositoryService(actor=user)
    tool = repo_service.create_tool(
        name="echo-tool",
        category="diagnostic",
        tags=["demo"],
        description="Return parameters as JSON",
        initial_script="""
import json

def main(message: str = 'hello'):
    return json.dumps({'message': message}, ensure_ascii=False)
""",
    )

    runner = ToolRunnerService(actor=user)
    execution = runner.enqueue(tool, parameters={"message": "world"})

    run_tool_task(str(execution.run_id))

    execution.refresh_from_db()
    assert execution.status == ToolExecution.Status.SUCCEEDED
    assert "world" in execution.output
