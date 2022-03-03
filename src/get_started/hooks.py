"""Project hooks."""
import os
from typing import Any, Dict, Iterable, Optional

import hydra
from flatten_dict import flatten
from hydra.core.global_hydra import GlobalHydra
from kedro.config import ConfigLoader
from kedro.framework.cli.hooks.specs import CLICommandSpecs
from kedro.framework.hooks import hook_impl
from kedro.framework.hooks.specs import PipelineSpecs
from kedro.framework.project import settings
from kedro.framework.session import get_current_session
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.versioning import Journal
from omegaconf import DictConfig


class HydraConfigHook(CLICommandSpecs, PipelineSpecs):
    cfg: DictConfig

    @hook_impl
    def before_pipeline_run(
            self, run_params: Dict[str, Any], pipeline: Pipeline, catalog: DataCatalog
    ) -> None:

        if not GlobalHydra.instance().is_initialized():
            # get absolute path of project
            kedro_session = get_current_session()
            project_root = kedro_session.load_context().project_path

            # get the config path relative to the current script path
            config_path = os.path.relpath(path=os.path.join(project_root, settings.CONF_ROOT),
                                          start=os.path.dirname(os.path.realpath(__file__)))
            hydra.initialize(config_path=config_path)

        # get overrides provided in kedro run --params "hydra_overrides:...."
        if 'hydra_overrides' in run_params['extra_params']:
            overrides = run_params['extra_params']['hydra_overrides'].split(' ')
        else:
            overrides = []

        # compose the config and store it in the data catalog
        self.cfg = hydra.compose(config_name='config', overrides=overrides)
        max_cfg_depth = max(map(len, flatten(self.cfg).keys()))

        # config is reloaded from the root folder each time this method is called
        # it's actually executed only once when calling kedro run
        catalog.add_feed_dict({'config': self.cfg}, replace=True)
        for depth in range(1, max_cfg_depth):
            for keys_to_parameter, parameter in flatten(self.cfg, max_flatten_depth=depth).items():
                catalog.add_feed_dict({f'cfg:{">".join(keys_to_parameter)}': parameter}, replace=True)


class ProjectHooks:
    @hook_impl
    def register_config_loader(
            self, conf_paths: Iterable[str], env: str, extra_params: Dict[str, Any]
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
        return DataCatalog.from_config(
            catalog, credentials, load_versions, save_version, journal
        )
