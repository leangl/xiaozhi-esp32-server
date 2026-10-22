## Purpose

Allow the supported backend to serve account, device, and conversation workflows without depending on China-based external service operators or silently contacting unapproved substitutes.

## ADDED Requirements

### Requirement: Explicit service policy

The backend SHALL accept only explicitly permitted external service endpoints for active integrations. Removed providers and unclassified destinations MUST NOT be silently enabled by defaults, imported settings, custom endpoint aliases, redirects, or fallback behavior. Classification SHALL use documented operator evidence, not language or domain suffix alone.

#### Scenario: Removed provider or aliased endpoint
- **GIVEN** an administrator submits a removed provider or an endpoint resolving to a disallowed service, including a custom OpenAI-compatible URL
- **WHEN** configuration is validated or activated
- **THEN** activation is rejected with an actionable reason before credentials, conversation data, or audio are transmitted
- **AND** an existing working configuration remains unchanged

#### Scenario: Unknown service
- **GIVEN** an endpoint has no reviewed permission entry
- **WHEN** it is selected or an approved endpoint redirects to it
- **THEN** no request containing application data is sent to that destination until explicit review and approval

### Requirement: Provider-independent core flow

With approved ASR, LLM, and TTS endpoints explicitly configured, the backend SHALL support registration/login, assistant creation, device binding, conversation, and history access without a removed service account, credential, network connection, model download, or default provider.

#### Scenario: Complete synthetic conversation
- **GIVEN** local protocol-compatible ASR/LLM/TTS fakes and a network policy allowing only test infrastructure
- **WHEN** two users register, bind separate synthetic devices, and complete conversations
- **THEN** each user receives their own response/history and the entire flow completes with no connection attempt to a removed or unknown external service

### Requirement: Removed optional features fail explicitly

Unavailable SMS, geolocation, weather, news, search, and external memory integrations SHALL produce a documented unavailable outcome without contacting removed services or preventing unrelated account/device/conversation operations. Their removed entries SHALL not be offered as usable choices by the management API or its clients.

#### Scenario: SMS feature disabled
- **GIVEN** no approved SMS replacement is configured
- **WHEN** an SMS verification or SMS-dependent password-recovery operation is requested
- **THEN** the operation reports that the feature is unavailable before storing an apparently sent verification code
- **AND** account/password registration and login with local CAPTCHA remain usable

#### Scenario: Missing optional context
- **GIVEN** removed IP lookup and weather/news/search integrations
- **WHEN** a device connects and an optional context/tool operation is requested
- **THEN** there is no external lookup to the removed services and the core dialogue can continue without that context

### Requirement: Credentials remain server-side

Service configuration errors and migration reports SHALL not expose provider credentials or full sensitive URLs. Ordinary users SHALL select permitted offerings without receiving platform provider secrets or being required to create provider accounts.

#### Scenario: Invalid endpoint with credentials
- **GIVEN** legacy configuration containing a secret
- **WHEN** a disallowed endpoint is rejected or reported
- **THEN** the reason identifies the affected setting without logging or returning the secret
