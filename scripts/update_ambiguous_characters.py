"""Generate the confusables.rs file from the VS Code ambiguous.json file."""
import json
import subprocess
from pathlib import Path

CONFUSABLES_RS_PATH = "crates/ruff/src/rules/ruff/rules/confusables.rs"
AMBIGUOUS_JSON_URL = "https://raw.githubusercontent.com/hediet/vscode-unicode-data/main/out/ambiguous.json"


def get_mapping_data() -> dict:
    """
    Get the ambiguous character mapping data from the vscode-unicode-data repository.

    Uses the system's `curl` command to download the data,
    instead of adding a dependency to a Python-native HTTP client.
    """
    content = subprocess.check_output(
        ["curl", "-sSL", AMBIGUOUS_JSON_URL],
        encoding="utf-8",
    )
    # The content is a JSON object literal wrapped in a JSON string, so double decode:
    return json.loads(json.loads(content))


def format_confusables_rs(raw_data: dict) -> str:
    """Format the downloaded data into a Rust source file."""
    prelude = """
/// This file is auto-generated by scripts/update_ambiguous_characters.py.

use once_cell::sync::Lazy;
use rustc_hash::FxHashMap;

/// Via: <https://github.com/hediet/vscode-unicode-data/blob/main/out/ambiguous.json>
/// See: <https://github.com/microsoft/vscode/blob/095ddabc52b82498ee7f718a34f9dd11d59099a8/src/vs/base/common/strings.ts#L1094>
pub(crate) static CONFUSABLES: Lazy<FxHashMap<u32, u8>> = Lazy::new(|| {
    #[allow(clippy::unreadable_literal)]
    FxHashMap::from_iter([
""".lstrip()
    tuples = []
    for _category, items in raw_data.items():
        for i in range(0, len(items), 2):
            tuples.append(f"({items[i]}, {items[i + 1]}),")
    postlude = """])});"""

    print(f"{len(tuples)} confusable tuples.")

    return prelude + "\n".join(tuples) + postlude


def main() -> None:  # noqa: D103
    print("Retrieving data...")
    mapping_data = get_mapping_data()
    formatted_data = format_confusables_rs(mapping_data)
    confusables_path = Path(__file__).parent.parent / CONFUSABLES_RS_PATH
    confusables_path.write_text(formatted_data, encoding="utf-8")
    print("Formatting Rust file with cargo fmt...")
    subprocess.check_call(["cargo", "fmt", "--", confusables_path])
    print("Done.")


if __name__ == "__main__":
    main()