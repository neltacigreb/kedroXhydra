"""Project hooks."""
from typing import Any, Dict, Iterable, Optional

from kedro.config import ConfigLoader
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.versioning import Journal


class ProjectHooks:
    # is modified in the hydra_kedro decorator
    datacatalog_extension: Dict[str, Dict[str, Any]] = None

    @hook_impl
    def register_config_loader(
            self, conf_paths: Iterable[str], env: str, extra_params: Dict[str, Any],
    ) -> ConfigLoader:
        return ConfigLoader(conf_paths)

    @hook_impl
    def register_catalog(
            self,
            catalog: Optional[Dict[str, Dict[str, Any]]],
            credentials: Dict[str, Dict[str, Any]],
            load_versions: Dict[str, str],
            save_version: str,
            journal: Journal,
    ) -> DataCatalog:
        datacatalog = DataCatalog.from_config(
            catalog, credentials, load_versions, save_version, journal
        )

        if self.datacatalog_extension:
            datacatalog.add_all(self.datacatalog_extension._data_sets)

        return datacatalog
