# SquadSync Frontend — Architecture & Folder Structure

Built with React 19 + Vite 8. State management via React Context.

## Directory Map

```
frontend-react/
+-- index.html                  # Vite HTML entry point
+-- vite.config.js              # Vite build configuration
+-- package.json                # Dependencies (name: squadsync-frontend)
¦
+-- public/                     # Static assets served as-is
¦   +-- favicon.svg
¦   +-- icons.svg
¦   +-- assets/
¦
+-- src/                        # Application source code
    +-- main.jsx                # React DOM entry point
    +-- App.jsx                 # Root component + routing logic
    +-- App.css                 # Root-level styles
    +-- index.css               # Global CSS design system & tokens
    ¦
    +-- api/                    # HTTP client & API call layer
    ¦   +-- client.js           # Axios instance with interceptors
    ¦   +-- authApi.js
    ¦   +-- adminApi.js
    ¦   +-- chatApi.js
    ¦   +-- friendsApi.js
    ¦   +-- matchmakerApi.js
    ¦   +-- newsApi.js
    ¦   +-- squadsApi.js
    ¦
    +-- context/                # React Context providers
    ¦   +-- AuthContext.jsx     # Authentication state & helpers
    ¦
    +-- hooks/                  # Custom React hooks
    ¦   +-- (place use*.js files here)
    ¦
    +-- pages/                  # Page/route-level components
    ¦   +-- (place page-level wrappers here)
    ¦
    +-- utils/                  # Pure utility functions
    ¦   +-- (place helper modules here)
    ¦
    +-- assets/                 # Images, fonts, media imported in JS
    ¦
    +-- components/             # Reusable UI components, grouped by feature
        +-- admin/
        ¦   +-- AdminDashboard.jsx
        +-- auth/
        ¦   +-- AuthModal.jsx
        ¦   +-- LoginForm.jsx
        ¦   +-- RegisterForm.jsx
        +-- chat/
        +-- common/
        ¦   +-- Navbar.jsx
        ¦   +-- ReportUserModal.jsx
        +-- friends/
        +-- landing/
        +-- matchmaker/
        +-- news/
        +-- squads/
```

## Data Flow

```
User Action
    ¦
    ?
Component (components/)
    ¦
    +-? Context (context/)       ? Global shared state
    +-? Hook (hooks/)            ? Reusable stateful logic
    ¦
    ?
API Layer (api/)
    ¦
    ?
Backend REST API (http://localhost:8000/api/v1/*)
```

## Conventions

- **Components**: PascalCase filenames, one component per file
- **Hooks**: `use<Name>.js`, always starts with `use`
- **API modules**: `<feature>Api.js`, exports named async functions
- **Context**: `<Name>Context.jsx`, exports Provider + `use<Name>` hook
- **Utils**: camelCase filenames, pure functions only (no React imports)
