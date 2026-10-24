"""'Where am I testing, and for whom?' as DATA instead of code.

Layers, later wins:
  1. profiles/defaults.ini
  2. profiles/deployment-<saas|single_tenant>.ini
  3. profiles/<target>.ini            (selected with LAB_TARGET)
  4. environment variables            LAB_<SECTION>_<KEY>, e.g. LAB_URLS_WEB
"""
import configparser
import os
from functools import lru_cache
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"
TRUE = {"1", "true", "yes", "on"}


def _read(name):
    path = PROFILE_DIR / f"{name}.ini"
    if not path.exists():
        raise FileNotFoundError(f"Missing config layer {path} (check LAB_TARGET)")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(path, encoding="utf-8")
    return {f"{section}.{key}": value.strip()
            for section in parser.sections()
            for key, value in parser.items(section)}


class EnvConfig:
    def __init__(self, name, environ=None):
        environ = os.environ if environ is None else environ
        self.name = name
        self._values = _read("defaults")
        profile = _read(name)
        deployment = profile.get("target.deployment", self._values["target.deployment"])
        self._values.update(_read(f"deployment-{deployment.lower()}"))
        self._values.update(profile)
        for key in self._values:
            override = environ.get("LAB_" + key.upper().replace(".", "_"))
            if override is not None:
                self._values[key] = override.strip()

    def str(self, key):
        if key not in self._values:
            raise KeyError(f"No config value '{key}' for target {self.name}")
        return self._values[key]

    def bool(self, key):
        return self.str(key).lower() in TRUE

    @property
    def deployment(self):
        return self.str("target.deployment")

    @property
    def version(self):
        return self.str("target.version")


@lru_cache(maxsize=1)
def get_config():
    return EnvConfig(os.environ.get("LAB_TARGET", "saas-tenant-a"))


def version_tuple(text):
    return tuple(int(part) for part in text.split("."))


def skip_reason(cfg, required_keys=(), min_version=None):
    """Return why this target cannot run a test, or None if it can."""
    for key in required_keys:
        if not cfg.bool(key):
            return f"Target '{cfg.name}' does not offer {key}"
    if min_version is not None and version_tuple(cfg.version) < version_tuple(min_version):
        return f"Target '{cfg.name}' runs v{cfg.version}, test needs >= {min_version}"
    return None
