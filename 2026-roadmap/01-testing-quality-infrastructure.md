# Testing & Quality Infrastructure Overhaul

**Category:** Testing | Technical Debt
**Quarter:** Q1
**T-shirt Size:** M

## Why This Matters

A house built on sand will not stand. esporifai currently has ~30% test coverage with integration tests that depend on live Spotify API calls. This creates fragility: tests can fail due to network issues, rate limits, or Spotify UI changes—not actual code bugs. Before we can confidently build ambitious new features, we need a testing foundation that gives developers rapid feedback and confidence in their changes.

Beyond testing, there's accumulated technical debt (bare except clauses, bitwise operator bugs, global state) that creates hidden risks. Addressing these now prevents them from compounding as the codebase grows.

## Current State

- **Test coverage:** ~30% of features tested (auth, get_top, get_recently_played untested)
- **Test type:** Integration tests only—every test hits live Spotify API
- **Test infrastructure:** No mocking framework, no fixtures, no coverage measurement
- **Technical debt identified:**
  - Bare `except:` clause in `utils.py:51` swallows all errors
  - Bitwise `|` instead of logical `or` in `cli.py:185,339`
  - Global `token_info` variable pattern in `cli.py`
  - Missing type hints across all modules
  - Copy-paste errors in docstrings in `api.py`
  - Code duplication in file processing logic
- **CI/CD inconsistency:** `publish.yml` still references dropped Python 3.7

## Proposed Future State

A comprehensive testing suite that enables fearless refactoring and rapid development:

- **Unit tests** with mocked HTTP responses for all API functions
- **Integration tests** (opt-in) for end-to-end validation against real Spotify
- **95%+ code coverage** with coverage gates in CI
- **Property-based testing** for edge cases using Hypothesis
- **All technical debt eliminated**—no bare excepts, no global state, proper operators
- **Type-checked codebase** with mypy in CI
- **Sub-10-second test runs** for the unit test suite

## Key Deliverables

- [ ] Add `pytest-cov` and configure coverage measurement with 80% minimum gate
- [ ] Create mock fixtures for all Spotify API responses (`tests/fixtures/`)
- [ ] Write unit tests for all 9 API functions with mocked responses
- [ ] Write unit tests for all 9 utility functions
- [ ] Write tests for `auth`, `get_top`, and `get_recently_played` commands
- [ ] Add error path tests (invalid IDs, network failures, auth expiry)
- [ ] Fix bare except clause—catch specific `TimeoutError` or `ElementNotFoundError`
- [ ] Fix bitwise OR bugs (replace `|` with `or`)
- [ ] Refactor global `token_info` to dependency injection pattern
- [ ] Add return type hints to all functions
- [ ] Fix docstring copy-paste errors in `api.py`
- [ ] Extract duplicate file processing logic into shared utility
- [ ] Add `mypy` to CI with strict mode
- [ ] Update `publish.yml` and `force-auth.yml` to match current Python matrix
- [ ] Add `pre-commit` hooks for linting and type checking
- [ ] Create `CONTRIBUTING.md` with testing requirements

## Prerequisites

None—this is foundational work that unblocks everything else.

## Risks & Open Questions

- Mocking Spotify responses requires maintaining fixture accuracy as Spotify API evolves
- Should we use `responses` library, `pytest-httpx`, or `respx` for mocking httpx?
- How to handle tests that legitimately need real API access (mark with `@pytest.mark.integration`)?
- Coverage gate at 80% or 90%? Starting at 80% allows incremental improvement.

## Notes

Relevant files to modify:
- `tests/test_esporifai.py` - add unit tests alongside existing integration tests
- `esporifai/utils.py:51` - bare except fix
- `esporifai/cli.py:185,339` - bitwise OR fix
- `esporifai/cli.py:41,59` - global state refactor
- `.github/workflows/publish.yml` - version matrix update
- `.github/workflows/force-auth.yml` - version matrix update

Test framework recommendation: Use `respx` for mocking httpx (native integration), `pytest-cov` for coverage, `hypothesis` for property testing.
