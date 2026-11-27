## Summary
- What does this PR change and why? (1–5 bullets)

## Type of change
- [ ] Bugfix
- [ ] New feature / effect
- [ ] Performance
- [ ] Refactor / docs / repo standards
- [ ] Release (version bump)

## How was it tested?
- [ ] `python -m unittest discover -s tests -v` — green
- [ ] `python -m seanimation --selftest` — `ERGEBNIS: PASS`
- [ ] Manual test on Win11 with release exe: `.\SeAnimation-<X.Y.Z>.exe ...` (console log / screenshot attached)
- [ ] CI green (`test` + `build-exe`)

## Checklist
- [ ] Version bumped in `seanimation/__init__.py` **and** `pyproject.toml` (if release)
- [ ] Docs updated (`README.md` / `ANFORDERUNGEN.md` incl. decision log §10) if behaviour or CLI changed
- [ ] No changes to `media/` or branch `dist-exe`
- [ ] Branch follows `vibe/<slug>-1ac69e`, base is `main`

## Related issues
Closes #
