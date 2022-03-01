"""Project hooks."""
import os
from typing import Any, Dict, Iterable, Optional

import hydra
from kedro.config import ConfigLoader
from kedro.framework.cli.hooks.specs import CLICommandSpecs
from kedro.framework.hooks import hook_impl
from kedro.framework.hooks.specs import PipelineSpecs
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.versioning import Journal
from kedro.framework.session import get_current_session
from kedro.framework.project import settings
from hydra.core.global_hydra import GlobalHydra

class HydraConfigHook(CLICommandSpecs, PipelineSpecs):
    @hook_impl
    def before_pipeline_run(
            self, run_params: Dict[str, Any], pipeline: Pipeline, catalog: DataCatalog
    ) -> None:
        if not GlobalHydra.instance().is_initialized():
            # get absolute
            kedro_session = get_current_session()
            project_root = kedro_session.load_context().project_path

            config_path = os.path.relpath(path=os.path.join(project_root, settings.CONF_ROOT),
                                          start=os.path.dirname(os.path.realpath(__file__)))
            hydra.initialize(config_path=config_path)

        config_name = 'config'

        if 'hydra_overrides' in run_params['extra_params']:
            overrides = run_params['extra_params']['hydra_overrides'].split(' ')
        else:
            overrides = []

        self.cfg = hydra.compose(config_name=config_name, overrides=overrides)

        catalog.add_feed_dict({'cfg': self.cfg})


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
