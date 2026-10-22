# HTTP client

Alova is the project's only HTTP request library.

## Usage

- **HTTP instance:** `src/http/request/alova.ts`
- **API examples:** `src/api/agent/agent.ts` and `src/api/device/device.ts`
- **API documentation:** [Alova](https://alova.js.org/)

## Configuration

The Alova instance provides:

- Token authentication and authentication-response handling
- Shared error handling and notifications
- Dynamic domain switching
- Request and response interceptors

## Example

```typescript
import { http } from '@/http/request/alova'

// GET request
http.Get<ResponseType>('/api/path', {
  params: { id: 1 },
  headers: { 'Custom-Header': 'value' },
  meta: { toast: false } // Disable error notifications
})

// POST request
http.Post<ResponseType>('/api/path', data, {
  params: { query: 'param' },
  headers: { 'Content-Type': 'application/json' }
})
```

The application-error prefix remains a compatibility contract; see [translation notes](../../TRANSLATION_NOTES.md).
