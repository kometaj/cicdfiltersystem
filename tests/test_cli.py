from ci_filter.cli import main


def test_cli_writes_env_file(tmp_path, monkeypatch, capsys):
    config = tmp_path / "filters.yaml"
    config.write_text(
        'filters:\n  backend:\n    - "app/**/*.kt"\n  docs:\n    - "docs/**/*.md"\n',
        encoding="utf-8",
    )
    output = tmp_path / "results.env"
    monkeypatch.setattr(
        "sys.argv",
        ["ci-filter", "--config", str(config), "--files", "app/src/Main.kt", "README.md",
         "--output", str(output)],
    )

    assert main() == 0
    assert output.read_text(encoding="utf-8") == "backend=true\ndocs=false\n"
    assert "backend=true" in capsys.readouterr().out
