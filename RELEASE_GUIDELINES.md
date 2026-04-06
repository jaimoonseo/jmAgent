# GitHub Release Guidelines for jmAgent

This document explains how to use the release templates and publish jmAgent releases on GitHub.

---

## Files Included

### 1. RELEASE_TEMPLATE.md
A **reusable template** for creating future releases. Customize this for v1.1.0, v1.2.0, etc.

**Use this when**: Creating releases for future versions  
**Frequency**: Update once per release cycle  
**Audience**: Release managers, maintainers  

### 2. GITHUB_RELEASE_v1.0.0.md
The **actual v1.0.0 release content** ready to post on GitHub. This is production-ready.

**Use this when**: Publishing the v1.0.0 release on GitHub  
**Frequency**: One-time use for v1.0.0  
**Audience**: GitHub releases page viewers  

### 3. RELEASE_GUIDELINES.md
This file - guidance for using the templates and releasing jmAgent.

---

## Step-by-Step: Publishing v1.0.0 on GitHub

### Step 1: Create Git Tag

```bash
cd /Users/jaimoonseo/Documents/jmAgent

# Create annotated tag for v1.0.0
git tag -a v1.0.0 -m "Release jmAgent v1.0.0 - Production Ready"

# Push tag to GitHub
git push origin v1.0.0

# Verify tag was created
git tag -l v1.0.0 -n1
```

### Step 2: Prepare Release Content

1. Open `GITHUB_RELEASE_v1.0.0.md`
2. Review and customize the content:
   - Replace `[yourusername]` with your GitHub username
   - Verify all links are correct (README.md, DEPLOYMENT.md, etc.)
   - Confirm dates and statistics are accurate
   - Add any personal notes or additional highlights
3. Copy the entire content

### Step 3: Create GitHub Release

1. Go to your GitHub repository: `https://github.com/yourusername/jmAgent`
2. Click **Releases** in the right sidebar
3. Click **"Draft a new release"**
4. Fill in the fields:
   - **Tag version**: `v1.0.0`
   - **Release title**: `jmAgent v1.0.0 - Production Ready`
   - **Description**: Paste the content from `GITHUB_RELEASE_v1.0.0.md`
5. Click **"Set as the latest release"** (if this is your first release)
6. Click **"Publish release"**

### Step 4: Add Release Assets (Optional)

To provide downloadable source code:

1. **Generate source archives**:
   ```bash
   # ZIP archive
   cd /tmp
   git clone https://github.com/yourusername/jmAgent.git jmAgent-v1.0.0
   cd jmAgent-v1.0.0
   git checkout v1.0.0
   cd ..
   zip -r jmAgent-v1.0.0.zip jmAgent-v1.0.0 -x "*/.*" "*/__pycache__/*" "*/.pytest_cache/*"
   tar -czf jmAgent-v1.0.0.tar.gz jmAgent-v1.0.0
   ```

2. **Calculate checksums**:
   ```bash
   sha256sum jmAgent-v1.0.0.zip
   sha256sum jmAgent-v1.0.0.tar.gz
   ```

3. **Upload to GitHub Release**:
   - Click on the published release
   - Click **"Edit release"**
   - Scroll to "Attach binaries" section
   - Drag and drop or click to upload:
     - `jmAgent-v1.0.0.zip`
     - `jmAgent-v1.0.0.tar.gz`
   - Add checksums to release description
   - Click **"Update release"**

### Step 5: Announce Release

After publishing:

1. **Share the release URL**: `https://github.com/yourusername/jmAgent/releases/tag/v1.0.0`
2. **Post announcement** (if desired):
   - Project website or blog
   - Social media (Twitter, LinkedIn, etc.)
   - Community forums or Slack channels
3. **Update documentation**:
   - Update version references in README.md
   - Update any install instructions
   - Link to release notes

---

## Using RELEASE_TEMPLATE.md for Future Releases

### For v1.1.0 (Example):

1. Open `RELEASE_TEMPLATE.md`
2. Create a copy: `GITHUB_RELEASE_v1.1.0.md`
3. Replace all placeholders:
   - `vX.Y.Z` → `v1.1.0`
   - `[Release Title]` → Your release title
   - `[Month Year]` → Actual release date
   - `[Feature 1]`, etc. → Your actual features
   - `[NUMBER]` → Your test counts
   - `[TIME]` → Your execution time
4. Add phase-specific details:
   - What changed in this phase
   - Which features are new/improved/fixed
   - Performance improvements
   - Known issues for this release
5. Update links to point to correct documentation
6. Remove template instructions (keep only content)
7. Review markdown formatting
8. Follow Steps 1-5 above to publish

---

## Release Checklist

Before publishing any release:

- [ ] All tests passing (verify with `pytest tests/`)
- [ ] Version updated in `src/__init__.py` and `setup.py`
- [ ] Git tag created: `git tag -a vX.Y.Z -m "..."`
- [ ] RELEASE_NOTES.md or similar updated
- [ ] Documentation links verified and working
- [ ] Installation instructions tested
- [ ] README.md reflects current version
- [ ] CHANGELOG.md updated (if maintained)
- [ ] No uncommitted changes: `git status`
- [ ] Release content reviewed for accuracy
- [ ] GitHub release page has all links working

---

## Template Sections Explained

### Release Overview
Provides quick status and audience context.

**Customize**: Release date, status (Alpha/Beta/Stable), key highlights

### What's New
Main feature list and improvements.

**Customize**: Include only features/fixes in this release

### Quality Metrics
Test coverage and performance data.

**Customize**: Run `pytest --tb=short` and update test counts

### Installation & Quick Start
For users getting started.

**Customize**: Links should match your actual file locations

### Breaking Changes
API/CLI changes that require migration.

**Customize**: List any backward-incompatible changes

### Known Issues
Problems users might encounter.

**Customize**: Add issues specific to this release

### Looking Forward
Future roadmap.

**Customize**: Update based on actual plans

---

## Common Customizations

### For Bug Fix Release (Patch)
- Emphasize bug fixes in "What's New"
- Keep feature list brief
- Add "Critical Fixes" section
- Include workarounds for known issues

### For Feature Release (Minor)
- Showcase new features prominently
- Include use cases for each feature
- Add "Migration Guide" if needed
- Link to feature documentation

### For Major Release (Major)
- Emphasize architecture changes
- Include "Upgrading from v1.x" section
- Provide detailed breaking changes
- Add comparison matrix (old vs new)

### For Early Releases (Alpha/Beta)
- Add "Stability Warning"
- Include feedback request
- Link to issue tracker for bug reports
- Suggest early adopter community

---

## GitHub Release Best Practices

### Title Format
- `jmAgent vX.Y.Z` - Always include version
- Add subtitle: `- Production Ready`, `- Bug Fixes`, etc.
- Keep under 70 characters total

### Description Structure
1. **Overview** (1-2 paragraphs)
2. **What's New** (bullet points)
3. **Installation** (code examples)
4. **Documentation** (links)
5. **Known Issues** (if any)
6. **Thanks** (contributors)

### Links
- Use relative links when possible: `[README](./README.md)`
- For issues/discussions, use full GitHub URLs
- Test all links before publishing

### Formatting Tips
- Use emojis for visual appeal (but not excessively)
- Use tables for comparisons
- Use code blocks for commands
- Use headers to organize sections
- Keep paragraphs short (2-3 sentences)

### Assets & Checksums
- Include source archives (ZIP, TAR.GZ)
- Provide SHA256 checksums
- Add download size for each asset
- Include installation instructions for each asset type

---

## Maintenance After Release

### Post-Release
1. Update version in code to next dev version (e.g., 1.0.1-dev)
2. Create release branch if needed: `git checkout -b release/v1.0.0`
3. Start next version development: `git checkout develop`
4. Update CHANGELOG for next version

### Bug Fixes After Release
- Create hotfix branch: `git checkout -b hotfix/v1.0.1`
- Fix the issue
- Create v1.0.1 release following same process
- Backport to main branches if needed

### Major Issues After Release
- Create security advisory if critical
- Publish emergency patch as vX.Y.Z+1
- Update all documentation
- Consider yanked release if severe

---

## Reference: Release History Template

Keep track of all releases in a central location. Example format:

```markdown
# jmAgent Release History

## v1.0.0 (April 2026)
- **Status**: Production Ready
- **Tests**: 618 passing
- **Phases Complete**: All 4
- **Release**: [GitHub Link](https://github.com/yourusername/jmAgent/releases/tag/v1.0.0)

## v1.1.0 (TBD)
- **Status**: Planning
- **Features**: [TBD]
- **Target Date**: [TBD]

## v2.0.0 (Future)
- **Status**: Planned
- **Phases**: Phase 5 (Web UI)
- **Target Date**: [TBD]
```

---

## Tips for Writing Great Release Notes

1. **Be Specific**: Instead of "Fixed bugs", say "Fixed authentication timeout issue when API key expires"

2. **Include Context**: Explain why features were added, not just what they do

3. **Use Examples**: Show command examples for new features

4. **Highlight Breaking Changes**: Put these in their own section

5. **Credit Contributors**: Thank people by name if possible

6. **Include Metrics**: Test counts, performance improvements, cost savings

7. **Link to Documentation**: Don't assume users will find docs on their own

8. **Be Honest About Limitations**: Mention what's not included in this release

9. **Make it Skimmable**: Use headers, bullets, and whitespace

10. **Proofread**: Run spell check and have someone else review

---

## Tools & Commands Reference

### Git Commands for Releases

```bash
# Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# List tags
git tag -l

# List tags with messages
git tag -l -n1

# Delete local tag (if needed)
git tag -d v1.0.0

# Delete remote tag (if needed)
git push origin --delete v1.0.0

# Checkout tag
git checkout v1.0.0
```

### File Commands

```bash
# Create source archive (ZIP)
zip -r jmAgent-v1.0.0.zip jmAgent-v1.0.0 \
  -x "*/.*" "*/__pycache__/*" "*/.pytest_cache/*"

# Create source archive (TAR.GZ)
tar --exclude='.*' --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  -czf jmAgent-v1.0.0.tar.gz jmAgent-v1.0.0

# Calculate checksum
sha256sum jmAgent-v1.0.0.zip
```

### Testing Before Release

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src

# Quick smoke test
jm --help
jm --version
jm config show
jm metrics summary
```

---

## Frequently Asked Questions

**Q: Can I edit a release after publishing?**  
A: Yes, click "Edit release" on the GitHub releases page. Updates are saved immediately.

**Q: Should I create a changelog?**  
A: Yes. Consider maintaining CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format.

**Q: What version should the next release be?**  
A: Follow semantic versioning: MAJOR.MINOR.PATCH (1.0.0, 1.1.0, 1.0.1, etc.)

**Q: How do I handle security releases?**  
A: Use GitHub Security Advisories for critical security issues.

**Q: Should I delete old releases?**  
A: No, keep all releases. Mark as prerelease if needed. Users may need old versions.

**Q: Can I release on a schedule?**  
A: You can use GitHub Actions to automate release creation. Configure in `.github/workflows/`.

---

## Support & Troubleshooting

### Common Issues

**Tags not showing up on GitHub**:
```bash
# Verify tag was pushed
git ls-remote --tags origin | grep v1.0.0

# Re-push if needed
git push origin v1.0.0
```

**Release page has broken links**:
- Check all relative paths start with `./`
- Use full URLs for external links
- Test clicking every link

**Assets won't upload**:
- File size too large? GitHub has limits (~100MB per release)
- Try uploading from GitHub CLI: `gh release create ...`
- Or upload through web interface individually

**Version mismatch**:
- Update `src/__init__.py`: `__version__ = "1.0.0"`
- Update `setup.py`: `version="1.0.0"`
- Update `CLAUDE.md` and other docs
- Verify with `jm --version`

---

## Next Steps

1. **For v1.0.0**: Copy `GITHUB_RELEASE_v1.0.0.md` and publish on GitHub
2. **For v1.1.0+**: Use `RELEASE_TEMPLATE.md` as your starting point
3. **For automation**: Consider setting up GitHub Actions for automated releases
4. **For documentation**: Keep this file in your docs for release team reference

---

**Version**: 1.0  
**Last Updated**: April 2026  
**For**: jmAgent Release Management  
**Location**: `/Users/jaimoonseo/Documents/jmAgent/RELEASE_GUIDELINES.md`
