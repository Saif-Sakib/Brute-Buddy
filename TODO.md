# TODO

This project is organized into focused modules:
- `run.py`: Orchestrates the brute-force engine.
- `arguments.py`: CLI parsing and UX.
- `payload_manager.py`: Parses params and generates combinations.
- `request_manager.py`: Makes HTTP attempts and evaluates success.
- `authenticator.py`: Login and re-authentication support.
- `utilities.py`: Extended help guide.

Potential enhancements:
- Add payload generators (e.g., masks, permutations, word mangling) to `payload_manager.py`.
- Support OAuth/JWT or multi-step auth flows in `authenticator.py`.
- Add success criteria for JSON responses (path-based checks) in `request_manager.py`.
- Optional CSV/HTML reporting module for successes.
- Adaptive throttling/rate limiting based on server feedback.
