import json
import pathlib
import os
from . import install_directory


class Config:
    configs = ["colors", "color_pairs"]

    def __init__(self, logging_function: callable):
        self.logger = logging_function
        for conf in self.configs:
            setattr(self, conf, self.get_config(conf))

    def get_config(self, config_name: str, paths=str(install_directory / "resource")):
        config = {}
        self.logger(f"Config: Loading config {config_name}", 9)
        for i in paths.split(":")[::-1]:
            filename = pathlib.Path(i) / (config_name + ".json")
            if not os.path.exists(filename):
                raise FileNotFoundError(filename)
            with open(filename, "r") as f:
                config.update(json.load(f))
        return config
