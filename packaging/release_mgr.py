#!/usr/bin/env python3
"""
Release Management Tool for ai-auto-commit

This tool manages package distribution across multiple package managers
by generating manifests from templates with pyproject.toml as the single source of truth.

Usage:
    python -m packaging.release_mgr generate        # Generate all manifests
    python -m packaging.release_mgr bump [patch|minor|major]  # Bump version
    python -m packaging.release_mgr build           # Build package and update checksums
    python -m packaging.release_mgr validate        # Validate generated manifests
"""

import sys
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

try:
    # Python 3.11+
    import tomllib
except ImportError:
    # Python 3.8-3.10
    import tomli as tomllib

import tomli_w
import semver
import requests
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class MetadataLoader:
    """Load and merge metadata from pyproject.toml"""

    @staticmethod
    def load(pyproject_path: Path) -> Dict[str, Any]:
        """
        Load metadata from pyproject.toml, combining [project] and [tool.package-metadata]

        Args:
            pyproject_path: Path to pyproject.toml

        Returns:
            Dict containing merged metadata
        """
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        tool_meta = data.get("tool", {}).get("package-metadata", {})

        # Extract license text
        license_info = project.get("license", {})
        if isinstance(license_info, dict):
            license_text = license_info.get("text", "MIT")
        else:
            license_text = str(license_info)

        # Merge metadata
        metadata = {
            "version": project.get("version", "0.1.0"),
            "name": project.get("name", "ai-auto-commit"),
            "description": project.get("description", ""),
            "license": license_text,
            "homepage": project.get("urls", {}).get("Homepage", ""),
            "repository": project.get("urls", {}).get("Repository", ""),
            "issues": project.get("urls", {}).get("Issues", ""),
            "changelog": project.get("urls", {}).get("Changelog", ""),
            "keywords": project.get("keywords", []),
            "requires_python": project.get("requires-python", ">=3.8"),
            "dependencies": project.get("dependencies", []),
            **tool_meta  # Merge all tool.package-metadata fields
        }

        # Ensure nested dicts exist
        if "checksums" not in metadata:
            metadata["checksums"] = {}
        if "release-notes" not in metadata:
            metadata["release-notes"] = {}

        return metadata


class TemplateRenderer:
    """Render Jinja2 templates with metadata"""

    def __init__(self, template_dir: Path):
        """
        Initialize the template renderer

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

        # Add custom filters
        import re
        self.env.filters['indent'] = lambda s, width=4: '\n'.join(
            ' ' * width + line if line.strip() else line
            for line in s.splitlines()
        )
        self.env.filters['regex_replace'] = lambda s, pattern, replacement: re.sub(pattern, replacement, s)

    def render(self, template_name: str, metadata: Dict[str, Any]) -> str:
        """
        Render a template with metadata

        Args:
            template_name: Name of the template file
            metadata: Metadata dict to use in template

        Returns:
            Rendered template as string
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(metadata=metadata)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template not found: {template_name}")


class ChecksumCalculator:
    """Calculate SHA256 checksums for packages"""

    @staticmethod
    def sha256_file(filepath: Path) -> str:
        """
        Calculate SHA256 checksum of a local file

        Args:
            filepath: Path to file

        Returns:
            Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def sha256_url(url: str, timeout: int = 30) -> str:
        """
        Download file from URL and calculate SHA256 checksum

        Args:
            url: URL to download from
            timeout: Request timeout in seconds

        Returns:
            Hex digest of SHA256 hash
        """
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        sha256 = hashlib.sha256()
        for chunk in response.iter_content(8192):
            sha256.update(chunk)
        return sha256.hexdigest()


class VersionBumper:
    """Semantic version bumping and pyproject.toml updates"""

    @staticmethod
    def bump(current: str, part: str) -> str:
        """
        Bump semantic version

        Args:
            current: Current version string (e.g., "0.1.0")
            part: Part to bump ("major", "minor", or "patch")

        Returns:
            New version string
        """
        try:
            version = semver.VersionInfo.parse(current)
        except ValueError as e:
            raise ValueError(f"Invalid version format '{current}': {e}")

        if part == "major":
            new_version = version.bump_major()
        elif part == "minor":
            new_version = version.bump_minor()
        elif part == "patch":
            new_version = version.bump_patch()
        else:
            raise ValueError(f"Invalid part '{part}'. Must be 'major', 'minor', or 'patch'")

        return str(new_version)

    @staticmethod
    def update_pyproject(pyproject_path: Path, new_version: str):
        """
        Update version in pyproject.toml

        Args:
            pyproject_path: Path to pyproject.toml
            new_version: New version string
        """
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Update version
        if "project" not in data:
            data["project"] = {}
        data["project"]["version"] = new_version

        # Also update release notes version if it exists
        if "tool" in data and "package-metadata" in data["tool"]:
            if "release-notes" in data["tool"]["package-metadata"]:
                data["tool"]["package-metadata"]["release-notes"]["version"] = new_version

        # Write back
        with open(pyproject_path, "wb") as f:
            tomli_w.dump(data, f)


class ManifestValidator:
    """Validate generated package manifests"""

    @staticmethod
    def validate_file_exists(path: Path) -> bool:
        """Check if file exists and is non-empty"""
        return path.exists() and path.stat().st_size > 0

    @staticmethod
    def validate_all(generated_dir: Path) -> Dict[str, bool]:
        """
        Validate all generated manifests

        Args:
            generated_dir: Directory containing generated files

        Returns:
            Dict mapping file paths to validation status
        """
        results = {}

        # List of expected files
        expected_files = [
            "PKGBUILD",
            "Formula/ai-auto-commit.rb",
            "chocolatey/ai-auto-commit.nuspec",
            "chocolatey/tools/chocolateyinstall.ps1",
            "chocolatey/tools/chocolateyuninstall.ps1",
            "scoop/ai-auto-commit.json",
            "install.sh",
            "install.ps1",
        ]

        for file_path in expected_files:
            full_path = generated_dir / file_path
            results[file_path] = ManifestValidator.validate_file_exists(full_path)

        return results


class ReleaseManager:
    """Main release management orchestrator"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the release manager

        Args:
            project_root: Project root directory (default: auto-detect)
        """
        if project_root is None:
            # Auto-detect: assume script is in packaging/
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

        self.packaging_dir = self.project_root / "packaging"
        self.template_dir = self.packaging_dir / "templates"
        self.generated_dir = self.packaging_dir / "generated"
        self.pyproject_path = self.project_root / "pyproject.toml"

        # Ensure directories exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    def generate_manifests(self):
        """Generate all package manager manifests from templates"""
        print("Loading metadata from pyproject.toml...")
        metadata = MetadataLoader.load(self.pyproject_path)

        print(f"Current version: {metadata['version']}")
        print(f"\nRendering templates...")

        renderer = TemplateRenderer(self.template_dir)

        # Map of template files to output paths
        manifest_map = {
            "PKGBUILD.j2": self.generated_dir / "PKGBUILD",
            "Formula.rb.j2": self.generated_dir / "Formula" / "ai-auto-commit.rb",
            "nuspec.xml.j2": self.generated_dir / "chocolatey" / "ai-auto-commit.nuspec",
            "chocolatey-install.ps1.j2": self.generated_dir / "chocolatey" / "tools" / "chocolateyinstall.ps1",
            "chocolatey-uninstall.ps1.j2": self.generated_dir / "chocolatey" / "tools" / "chocolateyuninstall.ps1",
            "scoop.json.j2": self.generated_dir / "scoop" / "ai-auto-commit.json",
            "winget-installer.yaml.j2": self.generated_dir / "winget" / "manifests" / "YourPublisher.AIAutoCommit.installer.yaml",
            "winget-locale.yaml.j2": self.generated_dir / "winget" / "manifests" / "YourPublisher.AIAutoCommit.locale.en-US.yaml",
            "winget-version.yaml.j2": self.generated_dir / "winget" / "manifests" / "ai-auto-commit.yaml",
            "flatpak.yaml.j2": self.generated_dir / "flatpak" / "com.github.yourusername.AIAutoCommit.yaml",
            "flatpak-metainfo.xml.j2": self.generated_dir / "flatpak" / "com.github.yourusername.AIAutoCommit.metainfo.xml",
            "debian-control.j2": self.generated_dir / "debian" / "control",
            "debian-changelog.j2": self.generated_dir / "debian" / "changelog",
            "debian-postinst.j2": self.generated_dir / "debian" / "postinst",
            "install.sh.j2": self.generated_dir / "install.sh",
            "install.ps1.j2": self.generated_dir / "install.ps1",
        }

        generated_count = 0
        skipped_count = 0

        for template_name, output_path in manifest_map.items():
            # Check if template exists
            if not (self.template_dir / template_name).exists():
                print(f"  ⚠ Skipping {template_name} (template not found)")
                skipped_count += 1
                continue

            # Create parent directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Render template
            try:
                content = renderer.render(template_name, metadata)
                output_path.write_text(content)
                print(f"  ✓ Generated {output_path.relative_to(self.generated_dir)}")
                generated_count += 1
            except Exception as e:
                print(f"  ✗ Error generating {template_name}: {e}")

        print(f"\nGenerated {generated_count} manifests")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} templates (not found)")

    def bump_version(self, part: str):
        """
        Bump version and regenerate manifests

        Args:
            part: Version part to bump ("major", "minor", or "patch")
        """
        print(f"Bumping {part} version...")

        # Load current version
        metadata = MetadataLoader.load(self.pyproject_path)
        current_version = metadata["version"]

        # Calculate new version
        new_version = VersionBumper.bump(current_version, part)

        print(f"  {current_version} → {new_version}")

        # Update pyproject.toml
        VersionBumper.update_pyproject(self.pyproject_path, new_version)
        print(f"  ✓ Updated pyproject.toml")

        # Regenerate all manifests
        print("\nRegenerating manifests...")
        self.generate_manifests()

        print(f"\n✓ Version bumped to {new_version}")
        print("\nNext steps:")
        print("  1. Update release notes in pyproject.toml")
        print("  2. Run: python -m packaging.release_mgr build")
        print("  3. Review changes: git diff")
        print(f"  4. Commit: git commit -am 'chore: bump version to {new_version}'")
        print(f"  5. Tag: git tag -a v{new_version} -m 'Release v{new_version}'")

    def build_package(self):
        """Build Python package and calculate checksums"""
        print("Building package...")

        # Build the package
        try:
            subprocess.run(
                [sys.executable, "-m", "build"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"✗ Build failed: {e.stderr}")
            return
        except FileNotFoundError:
            print("✗ Build module not found. Install it with: pip install build")
            return

        print("  ✓ Package built successfully")

        # Find the tarball
        metadata = MetadataLoader.load(self.pyproject_path)
        version = metadata["version"]
        dist_dir = self.project_root / "dist"
        tarball = dist_dir / f"ai-auto-commit-{version}.tar.gz"

        if not tarball.exists():
            # Try alternative name with underscores
            tarball = dist_dir / f"ai_auto_commit-{version}.tar.gz"

        if not tarball.exists():
            print(f"✗ Could not find built tarball in {dist_dir}")
            return

        # Calculate checksum
        print("\nCalculating SHA256 checksum...")
        sha256 = ChecksumCalculator.sha256_file(tarball)
        print(f"  SHA256: {sha256}")

        # Update pyproject.toml with checksum
        with open(self.pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Ensure structure exists
        if "tool" not in data:
            data["tool"] = {}
        if "package-metadata" not in data["tool"]:
            data["tool"]["package-metadata"] = {}
        if "checksums" not in data["tool"]["package-metadata"]:
            data["tool"]["package-metadata"]["checksums"] = {}

        data["tool"]["package-metadata"]["checksums"]["sha256"] = sha256
        data["tool"]["package-metadata"]["checksums"]["tarball_url"] = f"https://files.pythonhosted.org/packages/source/a/ai-auto-commit/ai-auto-commit-{version}.tar.gz"

        with open(self.pyproject_path, "wb") as f:
            tomli_w.dump(data, f)

        print("  ✓ Updated pyproject.toml with checksum")

        # Regenerate manifests with new checksum
        print("\nRegenerating manifests with checksum...")
        self.generate_manifests()

        print(f"\n✓ Build complete: {tarball}")
        print(f"✓ SHA256: {sha256}")

    def validate_manifests(self):
        """Validate all generated manifests"""
        print("Validating generated manifests...")

        results = ManifestValidator.validate_all(self.generated_dir)

        all_valid = True
        for file_path, is_valid in results.items():
            status = "✓" if is_valid else "✗"
            print(f"  {status} {file_path}")
            if not is_valid:
                all_valid = False

        if all_valid:
            print("\n✓ All manifests validated successfully")
        else:
            print("\n✗ Some manifests are missing or invalid")
            return False

        return True


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable commands:")
        print("  generate         Generate all manifests from templates")
        print("  bump <part>      Bump version (major, minor, or patch)")
        print("  build            Build package and calculate checksums")
        print("  validate         Validate generated manifests")
        sys.exit(1)

    command = sys.argv[1]
    manager = ReleaseManager()

    if command == "generate":
        manager.generate_manifests()

    elif command == "bump":
        if len(sys.argv) < 3:
            print("Error: Missing version part (major, minor, or patch)")
            sys.exit(1)
        part = sys.argv[2]
        if part not in ["major", "minor", "patch"]:
            print(f"Error: Invalid part '{part}'. Must be 'major', 'minor', or 'patch'")
            sys.exit(1)
        manager.bump_version(part)

    elif command == "build":
        manager.build_package()

    elif command == "validate":
        if not manager.validate_manifests():
            sys.exit(1)

    else:
        print(f"Error: Unknown command '{command}'")
        print("\nRun without arguments to see usage")
        sys.exit(1)


if __name__ == "__main__":
    main()
