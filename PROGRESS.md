name: Progress
description: Short-lived progress log for the current repository state.

# Progress

- Updated project metadata, package layout, CLI imports, and README to use the new `repomap` name.
- Regenerated `repo_map.md` and kept `MEMORY.md` aligned with the new package path.
- Implemented hierarchical `.gitignore` support using `pathspec` library:
  - Added `GitignoreRules` class to manage .gitignore patterns at all directory levels
  - Patterns such as `*`, `?`, `**/` and negation (`!`) are now fully supported
  - Updated `find_python_files()`, `build_exclude_set()`, and CLI to use the new system
  - Added comprehensive tests for hierarchical and negation patterns
