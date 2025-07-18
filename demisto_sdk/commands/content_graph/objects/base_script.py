from typing import Callable, List, Optional, Set, Union

import demisto_client
from pydantic import DirectoryPath, Field

from demisto_sdk.commands.common.constants import (
    SKIP_PREPARE_SCRIPT_NAME,
    MarketplaceVersions,
)
from demisto_sdk.commands.common.logger import logger
from demisto_sdk.commands.common.tools import (
    write_dict,
)
from demisto_sdk.commands.content_graph.common import (
    ContentType,
    RelationshipType,
)
from demisto_sdk.commands.content_graph.objects.integration import (
    Integration,
)
from demisto_sdk.commands.content_graph.objects.integration_script import (
    Argument,
    IntegrationScript,
    Output,
)
from demisto_sdk.commands.prepare_content.preparers.marketplace_incident_to_alert_scripts_prepare import (
    MarketplaceIncidentToAlertScriptsPreparer,
)


class BaseScript(IntegrationScript, content_type=ContentType.BASE_SCRIPT):  # type: ignore[call-arg]
    tags: List[str]
    skip_prepare: List[str]
    runas: str = ""
    args: List[Argument] = Field([], exclude=True)
    outputs: List[Output] = Field([], exclude=True)
    compliantpolicies: Optional[list[str]] = Field([])

    def metadata_fields(self) -> Set[str]:
        return (
            super()
            .metadata_fields()
            .union(
                {
                    "tags",
                }
            )
        )

    def prepare_for_upload(
        self,
        current_marketplace: MarketplaceVersions = MarketplaceVersions.XSOAR,
        **kwargs,
    ) -> dict:
        data = super().prepare_for_upload(current_marketplace, **kwargs)

        if supported_native_images := self.get_supported_native_images(
            ignore_native_image=kwargs.get("ignore_native_image") or False,
        ):
            logger.debug(
                f"Adding the following native images {supported_native_images} to script {self.object_id}"
            )
            data["nativeimage"] = supported_native_images

        return data

    @property
    def imported_by(self) -> List[Integration]:
        return [
            r.content_item_to  # type: ignore[misc]
            for r in self.relationships_data[RelationshipType.IMPORTS]
            if r.content_item_to.database_id == r.source_id
        ]  # type: ignore[return-value]

    def dump(self, dir: DirectoryPath, marketplace: MarketplaceVersions) -> None:
        dir.mkdir(exist_ok=True, parents=True)
        data = self.prepare_for_upload(current_marketplace=marketplace)

        for data in MarketplaceIncidentToAlertScriptsPreparer.prepare(
            data, marketplace, self.is_incident_to_alert(marketplace)
        ):
            # Two scripts return from the preparation, one the original, and other the new script,
            # in order to normalize the name of the new script, make a copy of the original object
            # in case it is a new script with an update of the name and path.
            script_name = data.get("name")

            if script_name == self.name:  # the original script
                obj = self

            else:  # a modified script, replaced incidents->alerts
                obj = self.copy(
                    update={
                        "name": script_name,
                        "path": self.path.with_name(f"{script_name}.yml"),
                    }
                )
            try:
                write_dict(dir / obj.normalize_name, data=data, handler=obj.handler)

            except FileNotFoundError as e:
                logger.warning(f"Failed to dump {obj.path} to {dir}: {e}")

    def is_incident_to_alert(
        self, marketplace: Union[List[MarketplaceVersions], MarketplaceVersions]
    ) -> bool:
        """
        Checks whether the script needs the preparation
        of an `incident to alert`,
        and this affects the `metadata.json` and the `dump` process of the script.

        Args:
            marketplace (MarketplaceVersions): the destination marketplace.

        Returns:
            bool: True if all conditions are true otherwise False
        """
        if not isinstance(marketplace, list):
            marketplace = [marketplace]
        return all(
            (
                MarketplaceVersions.MarketplaceV2 in marketplace
                or MarketplaceVersions.PLATFORM in marketplace,
                "incident" in self.name.lower(),
                SKIP_PREPARE_SCRIPT_NAME not in self.skip_prepare,
            )
        )

    @classmethod
    def _client_upload_method(cls, client: demisto_client) -> Callable:
        return client.import_script
