from functools import cached_property
from pathlib import Path
from typing import List, Optional, Set

from demisto_sdk.commands.common.constants import MarketplaceVersions
from demisto_sdk.commands.common.tools import get_value
from demisto_sdk.commands.content_graph.common import ContentType
from demisto_sdk.commands.content_graph.parsers.json_content_item import (
    JSONContentItemParser,
)


class IndicatorFieldParser(
    JSONContentItemParser, content_type=ContentType.INDICATOR_FIELD
):
    def __init__(
        self,
        path: Path,
        pack_marketplaces: List[MarketplaceVersions],
        git_sha: Optional[str] = None,
    ) -> None:
        super().__init__(path, pack_marketplaces, git_sha=git_sha)
        self.cli_name = self.json_data.get("cliName")
        self.type = self.json_data.get("type")
        self.associated_to_all = self.json_data.get("associatedToAll")

        self.connect_to_dependencies()

    @cached_property
    def field_mapping(self):
        super().field_mapping.update({"object_id": "cliName"})
        return super().field_mapping

    @property
    def object_id(self) -> Optional[str]:
        return get_value(self.json_data, self.field_mapping.get("object_id", ""))

    @property
    def supported_marketplaces(self) -> Set[MarketplaceVersions]:
        return {
            MarketplaceVersions.XSOAR,
            MarketplaceVersions.MarketplaceV2,
            MarketplaceVersions.XSOAR_SAAS,
            MarketplaceVersions.XSOAR_ON_PREM,
        }

    def connect_to_dependencies(self) -> None:
        """Collects indicator types used by the field as optional dependencies, and scripts as mandatory dependencies."""
        for associated_type in set(self.json_data.get("associatedTypes") or []):
            if associated_type:
                self.add_dependency_by_name(
                    associated_type, ContentType.INDICATOR_TYPE, is_mandatory=False
                )

        for system_associated_type in set(
            self.json_data.get("systemAssociatedTypes") or []
        ):
            if system_associated_type:
                self.add_dependency_by_name(
                    system_associated_type,
                    ContentType.INDICATOR_TYPE,
                    is_mandatory=False,
                )

        if script := self.json_data.get("script"):
            self.add_dependency_by_id(script, ContentType.SCRIPT)

        if field_calc_script := self.json_data.get("fieldCalcScript"):
            self.add_dependency_by_id(field_calc_script, ContentType.SCRIPT)
