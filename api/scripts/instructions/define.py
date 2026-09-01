#!/usr/bin/env python3
"""Interactive editor for the instruction catalogs under api/instructions/.

Each instruction type (models, rules, ...) is driven by a `*_schema.json`
file living alongside this script, which declares the data file it edits,
which top-level key holds the collection of named entries, and the field
schema for one entry. Add a new `<name>_schema.json` here to manage another
instruction file without touching this script.
"""

import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
INSTRUCTIONS_DIR = SCRIPT_DIR.parent.parent / "instructions"

OMIT = object()  # field should be left out of the entry entirely


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    with path.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Saved {path.relative_to(INSTRUCTIONS_DIR.parent.parent)}")


def prompt(text: str) -> str:
    try:
        return input(text)
    except EOFError:
        return "b"


def confirm(text: str) -> bool:
    return prompt(f"{text} [y/N] ").strip().lower() == "y"


class Collection:
    """Normalizes a dict-of-entries or a list-of-objects into the same interface."""

    def __init__(self, container: Any, key_field: str | None):
        self.container = container
        self.key_field = key_field

    def keys(self) -> list[str]:
        if self.key_field is None:
            return list(self.container.keys())
        return [item[self.key_field] for item in self.container]

    def get(self, key: str) -> dict:
        if self.key_field is None:
            return self.container[key]
        for item in self.container:
            if item[self.key_field] == key:
                return item
        raise KeyError(key)

    def set(self, key: str, value: dict) -> None:
        if self.key_field is None:
            self.container[key] = value
            return
        for i, item in enumerate(self.container):
            if item[self.key_field] == key:
                self.container[i] = value
                return
        self.container.append(value)

    def delete(self, key: str) -> None:
        if self.key_field is None:
            del self.container[key]
            return
        self.container[:] = [item for item in self.container if item[self.key_field] != key]

    def clear(self) -> None:
        if self.key_field is None:
            self.container.clear()
        else:
            self.container.clear()


def parse_scalar(raw: str, field_def: dict) -> Any:
    field_type = field_def["type"]
    if field_type == "string":
        return raw
    if field_type == "number":
        return float(raw) if "." in raw else int(raw)
    if field_type == "enum":
        choices = field_def["choices"]
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        if raw in choices:
            return raw
        raise ValueError(f"'{raw}' is not one of {choices}")
    if field_type == "list":
        choices = field_def.get("choices")
        values = [v.strip() for v in raw.split(",") if v.strip()]
        if choices:
            resolved = []
            for v in values:
                if v.isdigit() and 1 <= int(v) <= len(choices):
                    resolved.append(choices[int(v) - 1])
                elif v in choices:
                    resolved.append(v)
                else:
                    raise ValueError(f"'{v}' is not one of {choices}")
            return resolved
        return values
    raise ValueError(f"Unhandled scalar field type: {field_type}")


def describe_field(name: str, field_def: dict) -> None:
    required = "required" if field_def.get("required") else "optional"
    suffix = ""
    if field_def["type"] == "enum":
        suffix = f" (choices: {', '.join(f'{i + 1}={c}' for i, c in enumerate(field_def['choices']))})"
    elif field_def["type"] == "list" and field_def.get("choices"):
        choices = field_def["choices"]
        suffix = f" (choices: {', '.join(f'{i + 1}={c}' for i, c in enumerate(choices))}, comma-separated)"
    print(f"  {name} [{required}]: {field_def['description']}{suffix}")


def prompt_scalar_field(name: str, field_def: dict, has_existing: bool, existing_value: Any) -> Any:
    required = field_def.get("required", False)
    nullable = field_def.get("nullable", False)
    while True:
        describe_field(name, field_def)
        if has_existing:
            print(f"    current: {existing_value!r}  (blank = keep, '-' = clear)")
        raw = prompt("    > ").strip()

        if raw == "":
            if has_existing:
                return existing_value
            if required:
                print("    This field is required.")
                continue
            return OMIT

        if raw == "-":
            if not has_existing:
                print("    Nothing to clear.")
                continue
            if required and not nullable:
                print("    This field is required and cannot be cleared.")
                continue
            if required and nullable:
                return None
            return OMIT

        if required and nullable and raw.lower() == "null":
            return None

        try:
            return parse_scalar(raw, field_def)
        except ValueError as e:
            print(f"    {e}")


def prompt_dict_field(name: str, field_def: dict, existing_value: dict | None) -> Any:
    current = dict(existing_value) if existing_value else {}
    print(f"  {name} [{'required' if field_def.get('required') else 'optional'}]: {field_def['description']}")
    while True:
        if current:
            for i, (k, v) in enumerate(current.items(), 1):
                print(f"    {i}) {k}: {v}")
        else:
            print("    (empty)")
        choice = prompt("    a) add/update  r) remove  d) done > ").strip().lower()
        if choice == "d":
            break
        if choice == "a":
            key = prompt("      key: ").strip()
            if not key:
                continue
            current[key] = prompt(f"      value for '{key}': ").strip()
        elif choice == "r":
            key = prompt("      key to remove: ").strip()
            current.pop(key, None)
    if not current and not field_def.get("required"):
        return OMIT
    return current


def build_entry(schema_name: str, schemas: dict, existing: dict | None = None) -> dict:
    entry: dict = {}
    for field_name, field_def in schemas[schema_name].items():
        existing_value = existing.get(field_name) if existing else None
        has_existing = existing is not None and field_name in existing

        if field_def["type"] == "dict":
            value = prompt_dict_field(field_name, field_def, existing_value)
        elif field_def["type"] == "list_of_objects":
            items = list(existing_value) if has_existing else []
            manage_collection(
                Collection(items, key_field=field_def["key_field"]),
                schemas,
                field_def["item_schema"],
                field_name,
            )
            if not items and field_def.get("required"):
                print(f"  Warning: '{field_name}' is required but empty.")
            value = items if (items or field_def.get("required")) else OMIT
        else:
            value = prompt_scalar_field(field_name, field_def, has_existing, existing_value)

        if value is not OMIT:
            entry[field_name] = value
    return entry


def manage_collection(
    collection: Collection,
    schemas: dict,
    item_schema_name: str,
    entry_label: str,
    key_prompt: str | None = None,
) -> None:
    while True:
        keys = collection.keys()
        print(f"\n{entry_label} entries ({len(keys)}):")
        for i, key in enumerate(keys, 1):
            print(f"  {i}) {key}")
        print("  a) Add new" + f" {entry_label}")
        print("  e) Erase all")
        print("  b) Back")
        choice = prompt("> ").strip().lower()

        if choice == "b":
            return

        if choice == "e":
            if keys and confirm(f"Erase all {len(keys)} {entry_label} entries?"):
                collection.clear()
            continue

        if choice == "a":
            if key_prompt is not None:
                key = prompt(f"{key_prompt}: ").strip()
                if not key:
                    continue
                if key in keys:
                    print(f"'{key}' already exists.")
                    continue
                entry = build_entry(item_schema_name, schemas, existing=None)
                collection.set(key, entry)
            else:
                entry = build_entry(item_schema_name, schemas, existing=None)
                key_field = collection.key_field
                new_key = entry.get(key_field)
                if not new_key:
                    print(f"Entry needs a non-empty '{key_field}'; discarded.")
                    continue
                if new_key in keys:
                    print(f"'{new_key}' already exists.")
                    continue
                collection.set(new_key, entry)
            continue

        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            selected = keys[int(choice) - 1]
            _manage_single_entry(collection, schemas, item_schema_name, entry_label, selected)
            continue

        print("Unrecognized choice.")


def _manage_single_entry(
    collection: Collection, schemas: dict, item_schema_name: str, entry_label: str, key: str
) -> None:
    while True:
        entry = collection.get(key)
        print(f"\n{entry_label} '{key}':")
        print(json.dumps(entry, indent=2))
        choice = prompt("  edit / delete / back > ").strip().lower()
        if choice in ("b", "back", ""):
            return
        if choice in ("e", "edit"):
            updated = build_entry(item_schema_name, schemas, existing=entry)
            collection.set(key, updated)
            return
        if choice in ("d", "delete"):
            if confirm(f"Delete '{key}'?"):
                collection.delete(key)
                return
            continue
        print("Unrecognized choice.")


def discover_instruction_schemas() -> list[tuple[str, Path]]:
    return sorted(
        (path.stem[: -len("_schema")], path) for path in SCRIPT_DIR.glob("*_schema.json")
    )


def _collection_configs(config: dict) -> list[dict]:
    """Normalizes a schema config into a list of collection configs. A schema file
    either declares one collection directly at its top level (legacy shape, implicit
    item_schema "entry") or multiple named collections under "collections" (each with
    its own item_schema), so a single instruction type can manage more than one
    independent collection within the same data file."""
    if "collections" in config:
        return config["collections"]
    return [
        {
            "key": config["collection_key"],
            "entry_label": config["entry_label"],
            "item_schema": "entry",
            "key_prompt": config.get("key_prompt"),
            "key_field": config.get("key_field", "name"),
        }
    ]


def _run_collection(data: dict, schemas: dict, coll_config: dict) -> None:
    key = coll_config["key"]
    key_prompt = coll_config.get("key_prompt")
    data.setdefault(key, {} if key_prompt else [])

    collection = Collection(
        data[key],
        key_field=None if key_prompt else coll_config.get("key_field", "name"),
    )
    manage_collection(
        collection,
        schemas,
        coll_config.get("item_schema", "entry"),
        coll_config["entry_label"],
        key_prompt=key_prompt,
    )


def _choose_collection(data: dict, schemas: dict, collections: list[dict]) -> None:
    while True:
        print("\nCollections:")
        for i, coll_config in enumerate(collections, 1):
            print(f"  {i}) {coll_config['entry_label']}  ({coll_config['key']})")
        print("  b) Back")
        choice = prompt("> ").strip().lower()

        if choice == "b":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(collections):
            _run_collection(data, schemas, collections[int(choice) - 1])
            continue
        print("Unrecognized choice.")


def run_instruction_type(name: str, schema_path: Path) -> None:
    config = load_json(schema_path)
    data_path = INSTRUCTIONS_DIR / config["data_file"]

    if data_path.exists():
        data = load_json(data_path)
    else:
        data = {}

    collections = _collection_configs(config)
    if len(collections) == 1:
        _run_collection(data, config["schemas"], collections[0])
    else:
        _choose_collection(data, config["schemas"], collections)

    save_json(data_path, data)


def main() -> None:
    instruction_types = discover_instruction_schemas()
    if not instruction_types:
        print(f"No *_schema.json files found in {SCRIPT_DIR}")
        sys.exit(1)

    while True:
        print("\nInstruction types:")
        for i, (name, path) in enumerate(instruction_types, 1):
            print(f"  {i}) {name}  ({path.name})")
        print("  q) Quit")
        choice = prompt("> ").strip().lower()

        if choice == "q":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(instruction_types):
            name, path = instruction_types[int(choice) - 1]
            run_instruction_type(name, path)
            continue
        print("Unrecognized choice.")


if __name__ == "__main__":
    main()
