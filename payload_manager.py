from itertools import product
import sys
import os
from typing import Dict, Iterable, Iterator, List, Tuple


def load_file(file_path: str) -> List[str]:
    """Load non-empty lines from a file into a list."""
    if not os.path.isfile(file_path):
        print(f"[-] Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not os.access(file_path, os.R_OK):
        print(f"[-] Error: File not readable: {file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = [line.strip() for line in file if line.strip()]

        if not lines:
            print(f"[-] Warning: File is empty or contains only empty lines: {file_path}", file=sys.stderr)

        return lines
    except Exception as e:
        print(f"[-] Error reading file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def generate_payload(payload_spec: str) -> List[str]:
    """Generate payloads from 'generate:chars:length' spec or load from file."""
    if payload_spec.startswith("generate:"):
        try:
            _, chars, length_str = payload_spec.split(":", 2)
            length = int(length_str)

            if length <= 0:
                raise ValueError("Length must be a positive integer.")
            if not chars:
                raise ValueError("Character set for generation cannot be empty.")
            if length > 10:
                print(
                    f"[-] Warning: Large payload generation (length={length}). This may consume significant memory.",
                    file=sys.stderr,
                )

            return [''.join(combo) for combo in product(chars, repeat=length)]

        except (ValueError, IndexError) as e:
            print(f"[-] Invalid payload format: {payload_spec}. Use 'generate:chars:length'. Error: {e}", file=sys.stderr)
            sys.exit(1)

    return load_file(payload_spec)


class PayloadManager:
    """Parses user params and streams payload combinations.

    Public attributes:
    - brute_fields: List[Tuple[str, str]] of fields with varying payloads (key, source)
    - constants: Dict[str, str] fixed params applied to every request (supports header:/cookie:)
    - increment_fields: List[str] of fields that receive the attempt counter
    - zip_fields: List[str]
    - product_fields: List[str]
    """

    def __init__(
        self,
        param_vars: Dict[str, Iterable[str] | None],
        zip_fields: str | None,
        product_fields: str | None,
        attempt_counter,
    ) -> None:
        self.attempt_counter = attempt_counter

        merged_params = self._merge_params(param_vars.get('param'), param_vars.get('cookie'))
        self.brute_fields, self.constants, self.increment_fields = self._parse_params(merged_params)
        self.zip_fields, self.product_fields = self._normalize_combination_fields(zip_fields, product_fields)
        self._validate_combination_fields()

        # Preload payload lists for brute fields
        self._payload_lists = self._prepare_payloads()

    @staticmethod
    def _merge_params(param_list: Iterable[str] | None, cookie_list: Iterable[str] | None) -> List[str]:
        combined: List[str] = []
        if param_list:
            combined.extend(param_list)
        if cookie_list:
            for cookie in cookie_list:
                if "=" not in cookie:
                    print(f"[-] Error: Invalid cookie format: {cookie}. Use 'name=source'.", file=sys.stderr)
                    sys.exit(1)
                name, source = cookie.split("=", 1)
                combined.append(f"cookie:{name}={source}")
        return combined

    @staticmethod
    def _parse_params(param_args: Iterable[str]) -> Tuple[List[Tuple[str, str]], Dict[str, str], List[str]]:
        brute_fields: List[Tuple[str, str]] = []
        constants: Dict[str, str] = {}
        increment_fields: List[str] = []

        for param in param_args or []:
            if param.startswith("increment:"):
                field = param[10:]
                if not field:
                    print("[-] Error: Increment field name cannot be empty.", file=sys.stderr)
                    sys.exit(1)
                increment_fields.append(field)
                continue

            if "=" not in param:
                print(f"[-] Error: Invalid --param format: {param}. Use 'key=source' or 'increment:field'.", file=sys.stderr)
                sys.exit(1)

            key, source = param.split("=", 1)
            source = source.strip('"')

            # Treat as brute-field if it's a file or a generator spec
            if os.path.isfile(source) or source.startswith("generate:"):
                brute_fields.append((key, source))
            else:
                # Otherwise it's a constant value
                constants[key] = source

        return brute_fields, constants, increment_fields

    @staticmethod
    def _normalize_combination_fields(zip_fields: str | None, product_fields: str | None) -> Tuple[List[str], List[str]]:
        z = (zip_fields or "").replace(',', ' ').split()
        p = (product_fields or "").replace(',', ' ').split()
        return z, p

    def _validate_combination_fields(self) -> None:
        all_brute_keys = {key for key, _ in self.brute_fields}
        # Default to all fields in product mode if none provided
        if not self.zip_fields and not self.product_fields and self.brute_fields:
            self.product_fields = list(all_brute_keys)

        invalid_zip = set(self.zip_fields) - all_brute_keys
        invalid_product = set(self.product_fields) - all_brute_keys

        if invalid_zip or invalid_product:
            if invalid_zip:
                print(f"[-] Invalid zip fields: {', '.join(sorted(invalid_zip))}", file=sys.stderr)
            if invalid_product:
                print(f"[-] Invalid product fields: {', '.join(sorted(invalid_product))}", file=sys.stderr)
            print("[-] Error: Invalid fields found in --zip-fields or --product-fields.", file=sys.stderr)
            sys.exit(1)

    def _prepare_payloads(self) -> List[List[str]]:
        if not self.brute_fields:
            return []
        keys, sources = zip(*self.brute_fields)
        if len(keys) != len(sources):
            print("[-] Error: Mismatch between number of brute-force fields and payload sources.", file=sys.stderr)
            sys.exit(1)
        return [generate_payload(src) for src in sources]

    def generate_combinations(self) -> Iterator[Tuple[Dict[str, str], int]]:
        """Yields (payload_dict, attempt_id) lazily.

        Supports a mix of zip and product fields; constants are merged into each yielded payload.
        """
        if not self.brute_fields:
            # No brute fields: just yield constants once and keep incrementing until max_attempts caps it
            while True:
                yield self.constants.copy(), next(self.attempt_counter)

        brute_keys = [key for key, _ in self.brute_fields]
        # Map field names to indices in the payload list
        name_to_index = {name: i for i, name in enumerate(brute_keys)}
        zip_indices = [name_to_index[f] for f in self.zip_fields]
        product_indices = [name_to_index[f] for f in self.product_fields]

        zip_payloads = [self._payload_lists[i] for i in zip_indices]
        product_payloads = [self._payload_lists[i] for i in product_indices]

        # Build zipped part; if none, a single empty tuple is used
        zip_combos = zip(*zip_payloads) if zip_payloads else [()]

        for zip_combo in zip_combos:
            prod_combos = product(*product_payloads) if product_payloads else [()]
            for prod_combo in prod_combos:
                payload = self.constants.copy()
                for i, val in enumerate(zip_combo):
                    payload[self.zip_fields[i]] = val
                for i, val in enumerate(prod_combo):
                    payload[self.product_fields[i]] = val
                yield payload, next(self.attempt_counter)