import functools
import inspect
import os
import shlex
import sys
from copy import deepcopy
from typing import Optional

import hydra
from flatten_dict import flatten
from hydra.main import _UNSPECIFIED_
from hydra.types import TaskFunction
from kedro.framework.hooks.manager import get_hook_manager
from kedro.framework.session import get_current_session
from kedro.io import DataCatalog
from omegaconf import DictConfig

from ..hooks import ProjectHooks

# A function decorated with hydra.main can only return None.
# This global variable is used to get a return anyway when a function
#  is decorated with the decorator in this script.
_pipelines_registered = None


def main(
        config_path: Optional[str] = _UNSPECIFIED_,
        config_name: Optional[str] = None,
):
    """
    Decorate register_pipelines()

    Args:
        config_path: The config path, a directory relative to the declaring python file.
                     If config_path is None no directory is added to the Config search path.
        config_name: The name of the config (usually the file name without the .yaml extension)

    """

    # save sys.argv state before adapting it to the hydra decorator
    argv_bckp = deepcopy(sys.argv)

    # initialise sys.argv with only the running script path (../env/ENV_NAME/bin/kedro)
    sys.argv = [sys.argv[0]]

    # fetch the extra parameters given to kedro via the --params flag
    kedro_session = get_current_session()
    kedro_context = kedro_session.load_context()
    kedro_extra_params = kedro_context.params

    if ('hydra_overrides' in kedro_extra_params) or ('ho' in kedro_extra_params):
        hydra_overrides = shlex.split(kedro_extra_params['hydra_overrides'])
        sys.argv = sys.argv + hydra_overrides

    def root_decorator(pipeline_registry_fun: TaskFunction):
        # caller_abs_filepath = inspect.getfile(pipeline_registry_fun)
        # caller_abs_directory = os.path.split(caller_abs_filepath)[0]

        # The config folder must be placed inside the package src/PACKAGE_NAME,
        #  and must contain an __init__.py file at the root (conf/__init__.py)
        # It's because when hydra is not called inside the initial " if __name__=='__main__' "
        #  he will looks for config_path using the module name as the root directory
        decorated_filepath = inspect.getfile(pipeline_registry_fun)
        decorator_filepath = os.path.realpath(__file__)

        # assuming the config is in the same directory as the file containing the decorated function
        config_realpath = os.path.join(os.path.split(decorated_filepath)[0],
                                       config_path)

        config_relpath = os.path.relpath(path=config_realpath, start=os.path.split(decorator_filepath)[0])

        @functools.wraps(pipeline_registry_fun)
        @hydra.main(config_relpath, config_name)
        def task_function_execution(cfg: DictConfig):
            # restore sys.argv state before running hydra decorator
            sys.argv = argv_bckp
            # load the cfg and its branches into this session's catalog
            update_catalog_extension(cfg)

            # run the task function, register_pipelines() for example
            # then update the global variable _pipelines_registered to allow for a return outside of hydra
            global _pipelines_registered
            _pipelines_registered = pipeline_registry_fun(cfg)

        def bridge_fun(*args, **kwargs):
            """
            Bridge the output of the function decorated by hydra.main
            to the caller of said function.
            """
            # run the decorated pipeline_registry_fun
            task_function_execution()  # updates the global variable _pipelines_registered

            # then return to the caller the output of the function decorated with hydra.main
            global _pipelines_registered
            return _pipelines_registered

        return bridge_fun

    return root_decorator


def update_catalog_extension(cfg: DictConfig):
    """
    The catalog is recreated at each call of context.catalog, which happens later in the code,
     before running a pipeline for example.
    This function will modify the registered ProjectHooks to set him an attribute
     containing the hydra config in catalog format.
    The hook ProjectHooks has been modified to add this extension to the session's catalog
     everytime it is called to compute it.

    Args:
        cfg:

    Returns:

    """

    # Creates a datacatalog containing the hydra config
    catalog = DataCatalog()
    catalog.add_feed_dict({'config': cfg}, replace=True)
    max_cfg_depth = max(map(len, flatten(cfg).keys()))
    for depth in range(1, max_cfg_depth):
        for keys_to_parameter, parameter in flatten(cfg, max_flatten_depth=depth).items():
            catalog.add_feed_dict({f'cfg:{">".join(keys_to_parameter)}': parameter}, replace=True)

    # updates the datacalog_extension attribute of the registered ProjectHook
    hook_manager = get_hook_manager()
    for k, v in hook_manager._plugin2hookcallers.items():
        if isinstance(k, ProjectHooks):
            k.__setattr__('datacatalog_extension', catalog)
