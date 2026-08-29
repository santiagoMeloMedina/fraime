# Publishing fraime-sdk (maintainers only)

```bash
make install-sdk        # from repo root — installs build/twine dev tooling too
make publish-sdk        # builds + uploads to TestPyPI (sandbox, safe default)
make publish-sdk-pypi   # builds + uploads to the real, public PyPI
```

Or from `sdk/` directly: `make install`, `make publish`, `make publish-pypi`.

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

One thing not yet decided: `pyproject.toml` has no `license` field, since
there's no `LICENSE` file at the repo root yet. PyPI accepts unlicensed
packages, but it's worth adding one before a real publish.
