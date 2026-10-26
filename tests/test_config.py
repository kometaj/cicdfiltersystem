import pytest

from ci_filter.config import ConfigError, load_filters


def test_loads_valid_config(tmp_path):
    config = tmp_path / "filters.yaml"
    config.write_text('filters:\n  docs:\n    - "README.md"\n', encoding="utf-8")
    assert load_filters(config) == {"docs": ["README.md"]}


@pytest.mark.parametrize(
    "content",
    [
        "other: {}\n",
        "filters: []\n",
        "filters:\n  docs: README.md\n",
        "filters:\n  docs:\n    - '!README.md'\n",
    ],
)
def test_rejects_invalid_config(tmp_path, content):
    config = tmp_path / "filters.yaml"
    config.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigError):
        load_filters(config)
