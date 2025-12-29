# Modern Authentication & Security Hardening

**Category:** Security | Architecture
**Quarter:** Q1
**T-shirt Size:** M

## Why This Matters

The current authentication system uses Playwright to automate browser-based OAuth by literally typing usernames and passwords into Spotify's login form. This approach is:

1. **Fragile:** Any Spotify UI change breaks authentication
2. **Slow:** Full browser launch with 300ms artificial delays
3. **Insecure:** Requires storing plaintext passwords in environment variables
4. **Unscalable:** Cannot work in headless server environments without display

For esporifai to become a serious tool for developers and analysts, it needs authentication that is robust, secure, and works everywhere—from local development to cloud pipelines to embedded systems.

## Current State

- **OAuth method:** Browser automation via Playwright (`utils.py:39-53`)
- **Credential storage:** Plaintext JSON files in `~/.config/esporifai/`
- **Required secrets:** `USERNAME`, `PASSWORD` stored in environment variables
- **Hardcoded values:** 300ms slow_mo, 3s/90s timeouts
- **Error handling:** Silent failure with `except: pass`
- **Token refresh:** Implemented but basic, no encryption

The current flow:
1. Launch Chromium browser
2. Navigate to Spotify authorize URL
3. Fill username/password fields programmatically
4. Click login button
5. Wait for redirect with auth code
6. Exchange code for tokens

## Proposed Future State

A modern, secure, multi-mode authentication system:

- **OAuth Device Flow (RFC 8628):** User authorizes on any device, no password handling
- **PKCE Support:** Secure public client authorization for CLI
- **Encrypted token storage:** AES-256 encryption for stored credentials
- **Keychain integration:** macOS Keychain, Windows Credential Manager, Linux Secret Service
- **Multiple auth strategies:** Device flow (default), browser-based (opt-in), service accounts
- **Token management dashboard:** View active sessions, revoke tokens
- **Configurable timeouts:** Environment-based configuration for all timing values
- **Graceful degradation:** Clear error messages when auth fails

## Key Deliverables

- [ ] Implement OAuth 2.0 Device Authorization Flow for Spotify
- [ ] Add PKCE (Proof Key for Code Exchange) support for enhanced security
- [ ] Create encrypted token storage using `cryptography` library
- [ ] Integrate with system keychains via `keyring` library
- [ ] Replace hardcoded timeouts with configurable values
- [ ] Add `--auth-method` flag: `device` (default), `browser`, `token`
- [ ] Implement `esporifai auth status` command showing token info
- [ ] Add `esporifai auth revoke` for explicit token revocation
- [ ] Create secure credential migration from old to new format
- [ ] Remove password-based authentication as default
- [ ] Add rate limit handling with exponential backoff
- [ ] Implement token refresh proactively (before expiry)
- [ ] Add audit logging for authentication events
- [ ] Document security model in SECURITY.md

## Prerequisites

- Initiative 01 (Testing Infrastructure) should be in progress for confident refactoring

## Risks & Open Questions

- Does Spotify's API fully support Device Flow? Need to verify against their OAuth documentation
- Keychain integration adds platform-specific dependencies—worth the complexity?
- Migration path for existing users with plaintext tokens?
- Should we support service account / client credentials flow for server-to-server use cases?
- How to handle environments without keychain (Docker containers, CI)?

## Notes

Relevant Spotify OAuth documentation:
- Authorization Code Flow: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
- PKCE Extension: https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow

Files requiring major changes:
- `esporifai/utils.py` - Complete auth rewrite
- `esporifai/constants.py` - New OAuth configuration
- `esporifai/cli.py` - New auth subcommands

New dependencies to consider:
- `keyring` - Cross-platform keychain access
- `cryptography` - Token encryption
