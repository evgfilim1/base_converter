from configparser import ConfigParser
from pathlib import Path

DEFAULT_CONFIG = {
    'core': {
        'strip_zeros': 'yes'
    },
    'ui': {
        'auto_convert': 'yes'
    }
}
config_path = Path('config.ini').resolve()
_config: ConfigParser = ConfigParser()


def get_config() -> ConfigParser:
    if not config_path.exists():
        _config.update(DEFAULT_CONFIG)
    else:
        _config.read(config_path)
    return _config
