from ci_filter.matcher import evaluate_filters, path_matches


def test_star_matches_only_within_path_segment():
    assert path_matches("web/app.ts", "web/*.ts")
    assert not path_matches("web/src/app.ts", "web/*.ts")


def test_double_star_matches_zero_or_more_segments():
    assert path_matches("App.kt", "**/*.kt")
    assert path_matches("app/src/main/App.kt", "**/*.kt")
    assert path_matches("docs/guide.md", "docs/**/*.md")


def test_exclusion_applies_to_same_file_not_other_files():
    filters = {"kotlin": ["**/*.kt", "!**/test/**"]}
    result = evaluate_filters(filters, ["src/main/App.kt", "src/test/AppTest.kt"])
    assert result == {"kotlin": True}


def test_only_excluded_matches_is_false():
    filters = {"kotlin": ["**/*.kt", "!**/test/**"]}
    assert evaluate_filters(filters, ["src/test/AppTest.kt"]) == {"kotlin": False}


def test_empty_changed_paths_yield_false():
    assert evaluate_filters({"docs": ["README.md"]}, []) == {"docs": False}


def test_normalizes_windows_and_dot_prefix():
    assert path_matches(".\\web\\app.ts", "web/**/*.ts")
