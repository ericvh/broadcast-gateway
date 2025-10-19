# Development Guidelines

This document contains reminders and best practices for maintaining consistency in development workflow.

## 🔄 Always Remember to...

### 1. Git Commit Practices
**ALWAYS commit your changes with meaningful messages:**
```bash
# Before starting work
git status

# During development
git add <files>
git commit -m "descriptive commit message"

# Before finishing
git push origin <branch>
```

**Commit Message Format:**
- Use present tense ("Add feature" not "Added feature")
- Start with a verb and be specific
- Include scope if relevant: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

### 2. TODO.md Maintenance
**ALWAYS update TODO.md when:**
- Completing tasks (move from Current Tasks to Completed Tasks)
- Starting new work (add to Current Tasks)
- Discovering new requirements (add to Future Considerations)
- Blockers or issues arise (document in Current Tasks)

**Update template:**
```markdown
## Current Tasks
- [ ] Your new task description

## Completed Tasks  
- [x] Task you just finished

## Future Considerations
- New idea or requirement discovered
```

### 3. README.md Updates
**ALWAYS update README.md when:**
- Adding new features or capabilities
- Changing installation/deployment instructions
- Modifying configuration options
- Updating image names or repository references
- Adding new sections (architecture, troubleshooting, etc.)

### 4. CHANGES.md Maintenance
**ALWAYS update CHANGES.md when:**
- Adding new features or functionality
- Fixing bugs or issues
- Making breaking changes
- Updating dependencies or configuration defaults
- Changing behavior or implementation details
- Releasing new versions

**CHANGES.md Format Guidelines:**
```markdown
## [vX.X.X] - YYYY-MM-DD

### Added
- New features and capabilities

### Changed  
- Modifications to existing functionality

### Fixed
- Bug fixes and issue resolutions

### Technical Details
- Implementation specifics, breaking changes, migration notes
```

### 5. Development Workflow Checklist

Before considering any task "done":
- [ ] Code changes implemented and tested
- [ ] Changes committed to git with descriptive message
- [ ] TODO.md updated with completed task
- [ ] README.md updated if user-facing changes made
- [ ] **CHANGES.md updated for any changes** (features, fixes, config changes, etc.)

## 📝 File-Specific Guidelines

### README.md
- Keep installation instructions current
- Update Docker run examples when image references change
- Maintain accurate configuration table
- Update architecture diagrams if needed

### TODO.md
- Keep tasks organized and prioritized
- Mark completed items immediately
- Add context for complex tasks
- Review and clean up outdated items

### CHANGES.md
- **ALWAYS document changes** - no change is too small
- Use consistent section headers: Added, Changed, Fixed, Technical Details
- Include version numbers and dates for each entry
- Document breaking changes prominently
- Note configuration defaults or behavior changes
- Include migration instructions when applicable
- Be specific about what files/components were modified

## 🚨 Quick Reference Commands

```bash
# Check current status
git status
git log --oneline -5

# Stage all changes
git add .

# Commit with message
git commit -m "descriptive message"

# Push to remote
git push origin main

# Check what files need updating
ls -la *.md
```

## 📋 Pre-Release Checklist

Before each release or major update:
- [ ] All changes committed and pushed
- [ ] TODO.md reflects current project status
- [ ] README.md has latest installation/docs
- [ ] **CHANGES.md updated with ALL changes since last release**
- [ ] Docker images build successfully
- [ ] Kubernetes manifests validated
- [ ] Helm chart tested

---

**Remember: Good documentation is as important as good code!** 🎯
