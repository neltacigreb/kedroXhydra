"""Project hooks."""
from typing import Any, Dict, Iterable, Optional, Union

from kedro.config import ConfigLoader
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.versioning import Journal
import hydra
import os

class HydraConfigLoader(ConfigLoader):
    def __init__(self, conf_paths: Union[str, Iterable[str]]):
        super().__init__(conf_paths)

        @hydra.main(self.conf_paths[0])
        def load_cfg(cfg):
            self.get()
            return cfg

        # load_cfg doesn(t
        self.cfg = load_cfg()

    def get(self, *patterns: Optional[str]):
        if not patterns:
            # return full cfg
            return self.cfg
        else:
            # todo loop over the patterns and match corresponding keys in the cfg dictionnary
            return self.cfg


class ProjectHooks:
    @hook_impl
    def register_config_loader(
        self, conf_paths: Iterable[str], env: str, extra_params: Dict[str, Any]
    ) -> HydraConfigLoader:
        # For hydra: conf_path should be a string, not a list
        # Retrieves the root folder of the conf located in the current project:
        conf_root_path = os.path.split(os.path.split(list(conf_paths)[0])[0])[1]
        return HydraConfigLoader(conf_root_path)

    @hook_impl
    def register_catalog(
        self,
        catalog: Optional[Dict[str, Dict[str, Any]]],
        credentials: Dict[str, Dict[str, Any]],
        load_versions: Dict[str, str],
        save_version: str,
        journal: Journal,
    ) -> DataCatalog:
        return DataCatalog.from_config(
            catalog, credentials, load_versions, save_version, journal
        )
