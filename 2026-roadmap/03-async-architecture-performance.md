# Async Architecture & Performance Overhaul

**Category:** Architecture | Performance
**Quarter:** Q1-Q2
**T-shirt Size:** L

## Why This Matters

esporifai's current synchronous architecture processes one request at a time. When analyzing 100 tracks' audio features, that's 100 sequential API calls—each waiting for the previous to complete. This becomes painfully slow for any meaningful data analysis workflow.

The Spotify API supports batch operations (up to 50 items per request for many endpoints), but esporifai doesn't fully leverage this. Combined with async I/O, we could achieve 10-50x performance improvements for batch operations.

This architectural change is foundational: every future feature (real-time monitoring, AI analysis, data export) will benefit from async capabilities and efficient batching.

## Current State

- **I/O Model:** Synchronous—all `httpx` calls block
- **Batching:** Partial—`get_several_tracks` exists but not used optimally
- **Connection handling:** New connection per request, no pooling
- **Rate limiting:** None—vulnerable to Spotify's rate limits
- **Parallelism:** Zero—file processing in `cli.py` is sequential loop
- **httpx usage:** Synchronous client only, despite httpx supporting async

Current batch processing flow (from `cli.py:167-208`):
```python
for _id in ids:  # Sequential loop
    response = handle_response(...)  # Blocking call
    # Process one at a time
```

## Proposed Future State

A fully async architecture optimized for throughput:

- **Async core:** All API calls use `async/await` with `httpx.AsyncClient`
- **Smart batching:** Automatic chunking into optimal batch sizes (max 50 for Spotify)
- **Connection pooling:** Persistent connections with configurable pool size
- **Rate limit awareness:** Token bucket algorithm respecting Spotify's limits
- **Concurrent processing:** Semaphore-controlled parallelism for batch operations
- **Progress feedback:** Rich progress bars for long-running operations
- **Streaming responses:** Memory-efficient processing of large datasets
- **CLI compatibility:** Sync wrapper for CLI commands (using `asyncio.run`)

Expected improvements:
- Batch operations: **10-50x faster**
- Memory usage for large exports: **60-80% reduction**
- Rate limit errors: **Near zero** (proactive throttling)

## Key Deliverables

- [ ] Migrate `api.py` to async functions using `httpx.AsyncClient`
- [ ] Create connection pool manager with configurable limits
- [ ] Implement automatic request batching (chunk large ID lists)
- [ ] Add rate limiter using token bucket algorithm
- [ ] Implement concurrent request handling with semaphores
- [ ] Add progress bars using Rich for batch operations
- [ ] Create async versions of all utility functions
- [ ] Add sync wrappers for CLI compatibility
- [ ] Implement streaming JSON output for large results
- [ ] Add retry logic with exponential backoff for transient failures
- [ ] Create performance benchmarks comparing sync vs async
- [ ] Add `--parallel` flag for explicit concurrency control
- [ ] Implement request queue for managing burst traffic
- [ ] Add caching layer for frequently accessed data (optional TTL)
- [ ] Document async architecture in developer guide

## Prerequisites

- Initiative 01 (Testing Infrastructure) enables confident refactoring
- Initiative 02 (Auth Security) should be complete or in progress

## Risks & Open Questions

- CLI commands need sync interface—how clean is the sync-over-async wrapper?
- Spotify's rate limits vary by endpoint—need endpoint-specific configurations?
- Cache invalidation strategy for frequently changing data (recently played)?
- Should we use `trio` or `anyio` for better async primitives, or stick with `asyncio`?
- Memory implications of connection pooling—acceptable tradeoff?
- How to handle partial batch failures (some IDs succeed, some fail)?

## Notes

Spotify API batch limits:
- `Get Several Tracks`: max 50 IDs
- `Get Several Artists`: max 50 IDs
- `Get Tracks' Audio Features`: max 100 IDs
- `Get Several Albums`: max 20 IDs

Recommended async stack:
- `httpx.AsyncClient` for HTTP
- `asyncio.Semaphore` for concurrency control
- `rich.progress` for progress bars
- `tenacity` for retry logic (or custom implementation)

Files requiring changes:
- `esporifai/api.py` - All functions become async
- `esporifai/utils.py` - Async HTTP utilities
- `esporifai/cli.py` - Sync wrappers with `asyncio.run()`
- New: `esporifai/rate_limiter.py`
- New: `esporifai/batch.py`
