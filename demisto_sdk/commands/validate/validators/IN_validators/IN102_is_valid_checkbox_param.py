from __future__ import annotations

from typing import ClassVar, Iterable, List

from demisto_sdk.commands.content_graph.objects.integration import (
    Integration,
    Parameter,
)
from demisto_sdk.commands.validate.validators.base_validator import (
    BaseValidator,
    FixResult,
    ValidationResult,
)

ContentTypes = Integration


class IsValidCheckboxParamValidator(BaseValidator[ContentTypes]):
    error_code = "IN102"
    description = "Validate that th a checkbox param is configured correctly with required argument set to true."
    error_message = "The following checkbox params required field is not set to True: {0}.\nMake sure to set it to True."
    fix_message = "Set required field of the following params was set to True: {0}."
    related_field = "configuration"
    is_auto_fixable = True
    misconfigured_checkbox_params_by_integration: ClassVar[dict] = {}

    def is_valid(self, content_items: Iterable[ContentTypes]) -> List[ValidationResult]:
        return [
            ValidationResult(
                validator=self,
                message=self.error_message.format(
                    ", ".join(misconfigured_checkbox_params)
                ),
                content_object=content_item,
            )
            for content_item in content_items
            if (
                misconfigured_checkbox_params := self.get_misconfigured_checkbox_params(
                    content_item.params, content_item.name
                )
            )
        ]

    def get_misconfigured_checkbox_params(
        self, params: List[Parameter], integration_name: str
    ):
        self.misconfigured_checkbox_params_by_integration[integration_name] = [
            param.name
            for param in params
            if param.type == 8
            and param.name not in ("insecure", "unsecure", "proxy", "isFetch")
            and not param.required
        ]
        return self.misconfigured_checkbox_params_by_integration[integration_name]

    def fix(self, content_item: ContentTypes) -> FixResult:
        for param in content_item.params:
            if (
                param.name
                in self.misconfigured_checkbox_params_by_integration[content_item.name]
            ):
                param.required = True
        return FixResult(
            validator=self,
            message=self.fix_message.format(
                ", ".join(
                    self.misconfigured_checkbox_params_by_integration[content_item.name]
                )
            ),
            content_object=content_item,
        )