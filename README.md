# Kuí

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kui?label=Support%20Python%20Version&style=flat-square)](https://pypi.org/project/kui/)

An easy-to-use web framework. Based on [baize](https://baize.aber.sh) and [pydantic](https://docs.pydantic.dev/).

## Install

```
pip install kui
```

## Documentation

- [Online docs](https://kui.aber.sh) — Full bilingual (EN/ZH) documentation

## AI-Assisted Development

This project ships a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill — a comprehensive Kuí framework reference that AI coding agents can use.

### Install

```bash
npx skills add abersheeran/kui
```

Or manually: copy [`skills/kui-framework/SKILL.md`](./skills/kui-framework/SKILL.md) into your project's `.claude/skills/kui-framework/` directory.

### Usage

In Claude Code, type `/kui-framework` to load the full Kuí API reference, or just start writing Kuí code — the skill is automatically activated when relevant imports are detected.

Covers routing, parameter binding, dependency injection, OpenAPI, middleware, authentication, class-based views, and more.
