# Publishing fraime-mcp (maintainers only)

```bash
make install-mcp        # from repo root — installs build/twine dev tooling too
make publish-mcp        # builds + uploads to TestPyPI (sandbox, safe default)
make publish-mcp-pypi   # builds + uploads to the real, public PyPI
```

Or from `mcp/` directly: `make install`, `make publish`, `make publish-pypi`.

`fraime-mcp` depends on `fraime-sdk>=1.0,<2.0` — that needs to already be
published (see [`sdk/PUBLISHING.md`](../sdk/PUBLISHING.md)) before this
package is genuinely installable by anyone else via `pip`/`uvx`, even though
`publish.sh` doesn't check that for you.

Auth uses a PyPI API token, not a password — generate one from your account
settings ([pypi.org](https://pypi.org/manage/account/token/) or
[test.pypi.org](https://test.pypi.org/manage/account/token/)) and export it
before publishing:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-token>
```

([`scripts/publish.sh`](scripts/publish.sh) also reads `~/.pypirc` if you'd
rather configure it there.) Publishing to the real PyPI asks you to type the
version number to confirm first — that upload is irreversible per version,
so it's worth testing against TestPyPI (the default) before ever running
`publish-pypi`.
