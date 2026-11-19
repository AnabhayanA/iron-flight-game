# IS218 Creative Project — Review 2 Plan / SPEC

**Project:** Iron Flight — Drone Assault and Flight Academy  
**Checkpoint:** November 19, 2026. This submission is the **plan/SPEC only**, not a claim that the final application is finished.  
**Repository:** https://github.com/AnabhayanA/iron-flight-game  
**Owner:** Individual student project  
**Status:** The browser prototype includes two game modes. Account creation, persistent mission results, private dashboard, and account maintenance are planned, not implemented.

## 1. Problem, audience, and scope

I want to create a browser game for college students and casual players who enjoy short skill-based missions. A player chooses either **Drone Assault** (defeat five drones and a boss) or **Flight Academy** (clear eight checkpoints before the timer ends). The completed course project should allow players to create accounts, save results, inspect their own mission history, and manage their accounts securely.

**In scope:** choose a mode; finish a mission; account registration/login/logout; save one result per completed mission; private history/dashboard; update display name/password; meaningful automated tests; clear documentation.

**Out of scope for first working slice:** open-world city, cinematic 3D combat, multiplayer, suit inventory, leaderboards, payments, AI-driven enemies. Blender armor experiments remain optional art exploration. No claim of exact movie replication.

### Existing prototype vs proposed application

| Existing repository evidence | Still planned |
| --- | --- |
| Flask app serves homepage via `create_app()` | Registration/login/logout routes |
| `game.js` contains Drone Assault state, drones, boss and combat | Server-side mission result validation and saving |
| `flight.js` contains eight-checkpoint timed flight mode | SQLite users/results schema and migrations |
| JavaScript canvas mode selector and HUD in `index.html` | Account settings and private dashboard |
| Blender `.blend` / `.glb` assets and runtime pose sprites | Any live 3D renderer in gameplay |
| Seven Flask route/static tests defined in `tests/test_app.py` | Auth/DB tests and browser end-to-end checks |

**Architecture honesty:** the current browser game uses rendered 2D PNG poses from Blender through `armor-model.js`, with a drawn fallback; `.glb` files are stored for experiments, not loaded as a live 3D character.

## 2. Agile user stories and acceptance criteria

1. **Register:** As a new player, I can create an account to save my results.  
   **Accept:** unique username/email, validated input, password stored with a secure hash, duplicate registration rejected; invalid input does not crash the server.
2. **Sign in/out:** As a returning player, I can log in and out to protect my history.  
   **Accept:** successful login creates a server-backed session; bad credentials rejected without revealing which field is wrong; logout invalidates session; private routes redirect or return unauthorized when signed out.
3. **Play:** As a player, I can select Drone Assault or Flight Academy and finish a mission.  
   **Accept:** both modes launch; mission displays win/loss and relevant measures (e.g., kills or elapsed time); restart and mode switching do not break the page.
4. **Save and review:** As a signed-in player, I can save a completed mission and see my private history.  
   **Accept:** record associates with authenticated user and mode; expected fields validated; dashboard lists only that user's own results; another user's record is inaccessible.
5. **Maintain account:** As a player, I can change my display name or password.  
   **Accept:** change requires authenticated session; password changes require current password; names follow validation rules; session and data access remain correct.

## 3. Prioritized backlog, milestones, responsibilities

| Priority | Task/milestone | Dependency | Owner | Status |
| --- | --- | --- | --- | --- |
| P0 | Document requirements and acceptance checks | None | Me | This SPEC |
| P0 | Database design: users + mission_results | Chosen fields, Flask app factory | Me | Planned |
| P0 | Registration/login/logout and session protection | Schema, hash/validation | Me | Planned |
| P0 | **First working slice:** register → log in → submit one valid mock mission result → view own history → log out | Auth + DB | Me | Planned, not done |
| P1 | Connect both live game modes to secure result endpoint | First slice works | Me | Planned |
| P1 | Private dashboard with mode-specific result summaries | Saved records | Me | Planned |
| P1 | Account settings and password change | Auth | Me | Planned |
| P1 | Unit, integration and E2E regression suite | Working endpoints | Me; peer reviewer for UX | Planned |
| P2 | Visual improvements, performance and optional 3D experiments | Core functionality stable | Me | Experimental |

**Milestones:** (1) plan and schema reviewed; (2) first secure saved-result vertical slice; (3) both mode integrations and dashboard; (4) account settings; (5) tests and peer review. These are sequencing milestones, not promised delivery dates. Since this is an individual project, I own implementation and verification; a classmate may give genuine user feedback, not be presented as a group contributor.

## 4. Technical architecture

```text
Browser
  HTML/CSS + JavaScript Canvas
  game.js / flight.js  ── game controls, mission display
       |                 authenticated result request (future)
       v
Flask app (create_app)
  routes / blueprints: auth, missions, dashboard, account
       |
  services: validate result / account operations
       |
  SQLite via small repository/data-access layer
  users (id, login, password_hash, display_name, created_at)
  mission_results (id, user_id, mode, outcome, score, elapsed_s, created_at)
```

**Current stack:** Flask/Python server, JavaScript Canvas frontend, HTML/CSS, pytest, Blender asset-generation scripts. **Planned persistence:** SQLite, because it is simple for a single-host course prototype. Use Python's secure password-hashing helpers (e.g., Werkzeug) and parameterized queries/ORM; never store plaintext passwords. Use CSRF protection for state-changing form requests, secure session-cookie settings in deployment, and server-side checks for ownership. **Security caveat:** client-reported score can be tampered with; for a coursework demo initially validate format/bounds and clearly label results untrusted, or design a server-verifiable result scheme before treating scores as authoritative.

**Alternatives and tradeoffs:** Django provides built-in auth but is heavier than the existing Flask prototype. PostgreSQL fits multi-user deployed services better than SQLite but adds setup and hosting overhead. Three.js/WebGL could enable interactive 3D but would distract from login/persistence/testing requirements. Keep 2D as first playable path, revisit 3D as a separate experiment.

## 5. Code architecture, SOLID and design patterns

- `app/__init__.py`: current application factory. Extend via route blueprints, app config and DB initialization.
- `app/routes/auth.py` (planned): HTTP forms/login/logout; no business rules embedded in templates.
- `app/routes/missions.py` (planned): authenticated result submission and history routes.
- `app/services/results.py` (planned): validation of mode-specific results and record construction.
- `app/db.py` or `app/repositories/` (planned): parameterized persistence and ownership-scoped retrieval.
- `app/templates/`: server-rendered pages; `app/static/js/game.js` and `flight.js`: client-side missions and interactions.
- `tests/`: fixtures, validation unit tests and auth/DB integration tests.
- `tools/` and `app/static/models/`: optional Blender pipeline and art assets kept separate from core game rules.

**SOLID decisions:** Single Responsibility for routes (HTTP), service (rules) and repository (data). Dependency Inversion via injected repository interfaces only if unit tests or storage alternatives need it; avoid creating unnecessary abstraction. **Strategy pattern experiment:** distinct mode-specific result validators, e.g., DroneAssaultResultValidator vs FlightAcademyResultValidator; compare against one simple conditional validator, and keep the simpler solution if two modes do not justify polymorphism. The current game modes do not yet implement this server-side pattern. **App factory** already exists and allows isolated Flask tests.

## 6. Efficient testing, static analysis and CI

| What to verify | Level | Local | CI after setup |
| --- | --- | --- | --- |
| Password validation and result bounds | Unit | pytest | pytest |
| Registration, login, logout, protected routes | Integration (Flask test client) | pytest, temp SQLite | pytest |
| Record ownership, private history, SQL injection attempts | Integration/security | pytest, temp SQLite | pytest |
| Existing homepage/mode assets | Smoke/integration | existing seven pytest cases | pytest |
| Full browser first slice: sign up → sign in → save → view → log out | E2E | Manual initially; Playwright later | Optional Playwright |
| Game controls, canvas behavior, mobile viewport | Manual/browser | Chrome + keyboard | Optional visual tests |

**Current evidence:** `tests/test_app.py` defines seven smoke tests for Flask homepage, title, modes, canvas and asset loading. Prior project record reports seven passing; **this update has not rerun them**, so present this as historical until checked locally. These tests do not establish that the gameplay, security or database features work.

**Lint/static plan:** `ruff check app tests` for Python; `python -m compileall app` for syntax; `node --check` on each JS file; ESLint when a JS config is introduced; `pytest -q` and coverage reports. Add GitHub Actions for Python lint/tests and JS syntax checks once dependencies/configs are pinned. Fix failed checks before merge; document known issues rather than ignoring CI failures. Avoid checking generated `.blend` files as Python code.

## 7. Build order, review, open questions

1. Freeze the minimal user flow and sketch DB schema.
2. Create temporary SQLite schema and tests before production login.
3. Implement register/login/logout and protected history route.
4. Implement bounded result validation + saving; complete **first working slice** using a mock result without requiring the game engine to be rebuilt.
5. Connect actual Drone Assault and Flight Academy outcomes to result submission.
6. Add dashboard, account maintenance and security regression tests.
7. Have classmate attempt registration, one mission, and finding their own result; record specific observations in an issue; implement one response and ask them to retry.
8. Improve cosmetics or 3D only after core requirements work.

**Open questions:** Should login use username or email? Which score fields are comparable across modes? Can gameplay outcomes be verified server-side? Where will the app be hosted with a durable SQLite volume or managed database? Which armor sprite version should be default?

**Risks and mitigations:** scope creep from 3D modeling → keep 2D first slice; fake or tampered client score → validate and disclose trust limits; poor security → hash passwords, protect sessions and enforce ownership; deployment data loss → choose persistent hosting before final release; tests pass but gameplay breaks → add manual/E2E checks.

## 8. Evidence, AI use and review status

Existing evidence: [Flask app factory](app/__init__.py), [mode selector](app/templates/index.html), [combat engine](app/static/js/game.js), [flight engine](app/static/js/flight.js), [smoke tests](tests/test_app.py), [Blender assets and explanation](app/static/models/README.md), [prior project record](PROJECT-RECORD.md).

AI-assisted coding and planning need human review. I will explain each design choice, verify file behavior and testing claims, and keep actual contributions distinct from generated suggestions.

**Peer feedback:** Not yet completed for this checkpoint. **Automated test execution for this updated version:** Not run. **Local deployment verification:** Not run in this update.

## Changed / Checked / Next

- **Changed:** Added full Creative Project Plan/SPEC based on existing prototype and November 19 planning checklist.
- **Checked:** Inspected current GitHub repository files and existing tests; confirmed two Canvas game modes and Blender assets; did not execute the local application.
- **Next:** Review security and schema choices, run tests locally, then implement and verify the first account/result/history working slice.

This is the **November 19 plan/SPEC checkpoint**. Later implementation is intentionally not represented as completed.
