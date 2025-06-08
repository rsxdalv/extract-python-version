# Extract Python Version (GitHub Action)

Extracts the version number from `setup.py`, `pyproject.toml`, or `__init__.py` in your repo.

## Example: Tag and Release If New Version

```yaml
name: Release on Version Change

on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get version
        id: version
        uses: rsxdalv/extract-python-version@v1

      - name: Skip if tag exists
        id: check
        run: |
          git fetch --tags
          if git rev-parse "${{ steps.version.outputs.tag }}" >/dev/null 2>&1; then
            echo "release=false" >> $GITHUB_OUTPUT
          else
            echo "release=true" >> $GITHUB_OUTPUT
          fi

      - name: Create GitHub Release
        if: steps.check.outputs.release == 'true'
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ steps.version.outputs.tag }}
          release_name: ${{ steps.version.outputs.version }}
```
