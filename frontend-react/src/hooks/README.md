# hooks/

Custom React hooks for SquadSync.

## Convention

Each hook file should:
- Be named `use<HookName>.js` or `use<HookName>.jsx`
- Export a single default hook function
- Have a JSDoc comment describing its purpose and return value

## Examples

```
 hooks/
 +-- useAuth.js          ? Auth state and helpers (wraps AuthContext)
 +-- useWebSocket.js     ? WebSocket connection management
 +-- useDebounce.js      ? Debounced value utility
 +-- usePagination.js    ? Pagination state management
 +-- useLocalStorage.js  ? Persistent local state
```

