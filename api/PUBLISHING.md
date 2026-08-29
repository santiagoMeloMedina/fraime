# Publishing the Fraime API Docker image (maintainers only)

```bash
make publish-api   # from repo root
# or
make publish       # from api/
```

Builds and pushes `santsq18/framie-api:latest` for `linux/amd64` (see
[`scripts/publish.sh`](scripts/publish.sh) — repo/tag are hardcoded there,
not passed as arguments).

## You must be logged in to Docker Hub first

`docker login` — this script deliberately does **not** check whether you're
logged in (Docker Desktop routes real credentials through an OS credential
store that isn't reliably visible from a script), so if you skip this it'll
fail during the actual push, not up front with a clear "not logged in"
message.

Three separate things need to be true for the push to succeed, and the error
you get back rarely tells you which one is wrong:

1. **You're actually logged in as `santsq18`** — run `docker login` fresh and
   check the username it reports. Logged into a different account (or not
   logged in at all) means push access to that namespace is denied.
2. **Your access token has Read & Write scope.** If you used a Docker Hub
   Personal Access Token for login (Account Settings → Security → Access
   Tokens), a "Read-only" token will authenticate fine but fail on push with
   `insufficient_scope: authorization failed` — regenerate one with
   **Read & Write** access.
3. **The repository already exists on Docker Hub.** Docker Hub often
   requires the repo to be created through the web UI (Create Repository →
   name it `framie-api` under `santsq18`) before the first push, rather than
   auto-creating it.

If you hit `push access denied, repository does not exist or may require
authorization: server message: insufficient_scope: authorization failed` —
that's items 2 and/or 3 above, not a bug in the script. Re-running
`docker login` right before retrying is the fastest way to rule out item 1.
