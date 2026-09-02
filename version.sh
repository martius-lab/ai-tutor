#!/bin/bash
# Helper script to bump package version and sychronize pyproject.toml with
# aitutor/_version.py.
# This may be obsolete if https://github.com/astral-sh/uv/issues/13827 gets
# implemented.

# bump version using given arguments (no arguments just print the current
# version)
uv version "$@"

# if arguments were given, assume a bump and update the variable in
# aitutor/_version.py
if [ "$#" -gt 0 ]; then
    echo "Update aitutor/_version.py with new version"
    VERSION=$(uv version --short)
    echo "version: str = \"$VERSION\"" > aitutor/_version.py
fi
