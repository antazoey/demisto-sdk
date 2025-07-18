from __future__ import annotations

from typing import Iterable, List

from demisto_sdk.commands.common.constants import ExecutionMode
from demisto_sdk.commands.content_graph.objects import AgentixAction
from demisto_sdk.commands.validate.validators.base_validator import ValidationResult
from demisto_sdk.commands.validate.validators.GR_validators.GR110_is_agentix_action_using_existing_content_item_valid import (
    IsAgentixActionUsingExistingContentItemValidator,
)

ContentTypes = AgentixAction


class IsAgentixActionUsingExistingContentItemValidatorListFiles(
    IsAgentixActionUsingExistingContentItemValidator
):
    expected_execution_mode = [ExecutionMode.SPECIFIC_FILES, ExecutionMode.USE_GIT]

    def obtain_invalid_content_items(
        self, content_items: Iterable[ContentTypes]
    ) -> List[ValidationResult]:
        return self.obtain_invalid_content_items_using_graph(content_items, False)
