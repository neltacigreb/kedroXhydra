kedro version : 0.17.7

hydra version : 1.1.1

# kedroXhydra

Workarounds to be able to use Hydra with Kedro. A reproducible example of the issue encountered when using hydra in a usual way can be found [in this branch](https://github.com/neltacigreb/kedroXhydra/tree/hydra_dec_samplebug). This repo contains examples of using Hydra in Kedro via 2 implemantations (decorator or hook), on the tutorial project using iris dataset.

### CLI

Hydra parameters can be passed to the decorator from the command line by doing like this example:

    kedro run --params "hydra: --multirun +base.parameters.test_append=success base.parameters.example_test_data_ratio=0.3"

Or if you use the Hook implementation, Hydra overrides can be passed like this:

    kedro run --params "hydra_overrides:+base.parameters.test_append=success base.parameters.example_test_data_ratio=0.3"
    
### Accessing the config

For both implementations, the config can be access from the datacalog by passing to nodes the parameters in this format:
- `"cfg:path>to>config_group"` : returns a DictConfig object
- `"cfg:path>to>parameter"` : returns the parameter
- `"config"` : returns the entire composed config


## Solution with a custom decorator

In branches `master` and [`custom_decorator`](https://github.com/neltacigreb/kedroXhydra/tree/custom_decorator) a custom decorator can be found, having the same behavior as the `hydra.main()` decorator. I haven't tested it extensively, so if you encounter any problems you should switch to the Hook implementation, which only makes use of the [compose API](https://hydra.cc/docs/advanced/compose_api/) but is safer.

### Pros/Cons

Pros: 
- Most of the `hydra.main()` behavior is reproduced.
- Access conf elements in the pipeline registry step, allowing for dynamically generated kedro pipelines at runtime.

Cons: 
- Requires to keep the config directory in the package directory.
- Crafty implementation, so unexpected behavior can show up.

### How to use
- Modify the project hook to allow the config to be accessed via the DataCatalog:
    -  In the `hooks.py` file, add a `datacalog_extension` attribute to the `ProjectHook` class, and modify its `register_catalog()` method to merge this extension to the session's datacatalog each time it is called. [Copy and paste the hook from here](https://github.com/neltacigreb/kedroXhydra/blob/custom_decorator/src/get_started/hooks.py).

- Import the decorator in your project:
    - Copy the folder [hydra_kedro](https://github.com/neltacigreb/kedroXhydra/tree/custom_decorator/src/get_started/hydra_kedro) in your package's directory. This folder contains the custom `hydra.main()` decorator.
    - Create a folder containing the hydra configuration yaml files in your package's directory, and add an `__init__.py` file at the root, [like here](https://github.com/neltacigreb/kedroXhydra/tree/custom_decorator/src/get_started/hydra_conf)
    - Import the decorator in your `pipeline_registry.py` file, and decorate the `register_pipelines()` function, like you would with the original `hydra.main()` decorator. [Example here](https://github.com/neltacigreb/kedroXhydra/blob/custom_decorator/src/get_started/pipeline_registry.py)


## Solution with a Hook

In the branch [`hook_implem_nodec`](https://github.com/neltacigreb/kedroXhydra/tree/hook_implem_nodec) a custom hook can be found, using the Compose API to generate the conf, and loading it into the DataCatalog.

### Pros/cons

pros: 
- Safe way to use Hydra in Kedro
- Can still make use of the overrides provided in the CLI

cons: 
- Doesn't make use of the additional features provided by the decorator.

### How to use
- Copy this [HydraConfigHook](https://github.com/neltacigreb/kedroXhydra/blob/hook_implem_nodec/src/get_started/hooks.py) and paste it to your project's `hooks.py`. Add the hook to the settings as you would usually do.

