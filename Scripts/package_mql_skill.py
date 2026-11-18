"""Build and verify the portable MQL skill from the plugin's skill and the reference it pins."""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit
import zipfile

REPOSITORY_URL = "https://github.com/mnemic/agents"
REFERENCE_URL = "https://github.com/mnemic/mql"
PLUGIN = Path("plugins/mnemic")
MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"
SKILL = PLUGIN / "skills" / "mql"
REFERENCE = SKILL / "references"
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?")
COMMIT = re.compile(r"[0-9a-f]{40,64}")


def markdown_links(text):
    """Return destination spans, excluding fenced examples."""
    offset = 0
    fence = None
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            # Labels may contain code or nested brackets; destinations cannot.
            for match in re.finditer(r"\]\((<[^>\n]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", line):
                start, end = match.span(1)
                if line[start] == "<":
                    start += 1
                    end -= 1
                yield offset + start, offset + end, line[start:end]
            for match in re.finditer(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>\n]+>|\S+)", line):
                start, end = match.span(1)
                if line[start] == "<":
                    start += 1
                    end -= 1
                yield offset + start, offset + end, line[start:end]
        offset += len(line)


def anchors(text):
    found = set(re.findall(r'<a\s+(?:id|name)=[\"\']([^\"\']+)', text))
    counts = {}
    fence = None
    for line in text.splitlines():
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence is None:
            heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
            if heading:
                slug = re.sub(r"[^\w\- ]", "", heading[1].lower()).replace(" ", "-")
                count = counts.get(slug, 0)
                counts[slug] = count + 1
                found.add(slug if count == 0 else f"{slug}-{count}")
    return found


def validate_links(files):
    """Every relative link resolves to a bundled file and heading; the package has nothing outside itself to link to."""
    for name, data in files.items():
        if not name.endswith(".md"):
            continue
        for _, _, destination in markdown_links(data.decode("utf-8")):
            url = urlsplit(destination)
            if url.scheme or url.netloc:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path))) if url.path else name
            if target not in files:
                raise ValueError(f"{name}: missing bundled target {destination}")
            if url.fragment and target.endswith(".md") and unquote(url.fragment) not in anchors(files[target].decode("utf-8")):
                raise ValueError(f"{name}: missing heading {destination}")


def plugin_version(root):
    """The plugin's version, which the package carries: plugin.json is its one owner."""
    version = json.loads((root / MANIFEST).read_text(encoding="utf-8")).get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError(f"{MANIFEST.as_posix()} must hold the plugin's SemVer version")
    return version


def reference_sources(root):
    """The reference's files by package name. It is a submodule checkout, so the dot entries git keeps in it are not reference."""
    reference_root = root / REFERENCE
    if not (reference_root / "README.md").is_file():
        raise ValueError(f"{REFERENCE.as_posix()} holds no reference; initialize the submodule with git submodule update --init")
    sources = {}
    for path in sorted(reference_root.rglob("*")):
        relative = path.relative_to(reference_root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Unexpected symlink in the reference: {path}")
        if path.is_file():
            sources["mql/references/" + relative.as_posix()] = path
    return sources


def canonical_text(data):
    # Git's autocrlf setting must not change the portable artifact identity.
    return data.decode("utf-8").replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")


def collect(root, commit, reference_commit):
    if not COMMIT.fullmatch(commit):
        raise ValueError("Invalid source commit")
    if not COMMIT.fullmatch(reference_commit):
        raise ValueError("Invalid reference commit")
    version = plugin_version(root)
    entrypoint = (root / SKILL / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", entrypoint, re.S)
    if not frontmatter or not re.search(r"(?m)^name: mql\s*$", frontmatter[1]) or not re.search(r"(?m)^description: \S.+$", frontmatter[1]):
        raise ValueError("Skill frontmatter must declare name: mql and a description")
    # The package keeps the skill's own layout, so its relative links need no rewriting.
    sources = {"mql/SKILL.md": root / SKILL / "SKILL.md", **reference_sources(root)}
    files = {}
    hashes = {}
    for name, source in sources.items():
        data = source.read_bytes()
        if source.suffix == ".md":
            data = canonical_text(data)
        hashes[source.relative_to(root).as_posix()] = hashlib.sha256(data).hexdigest()
        files[name] = data
    validate_links(files)
    metadata = {"version": version, "commit": commit, "repository": REPOSITORY_URL,
                "referenceCommit": reference_commit, "referenceRepository": REFERENCE_URL,
                "sourceTextEncoding": "UTF-8 with CRLF line endings",
                "sourceSha256": hashes,
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    files["mql/package.json"] = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").replace("\n", "\r\n").encode("utf-8")
    return files


def build(root, commit, reference_commit, output):
    root = root.resolve()
    files = collect(root, commit, reference_commit)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"Mnemic.Mql.Skill-{plugin_version(root)}.zip"
    with archive.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                zipped.writestr(info, data, compresslevel=9)
    verify(archive, root, commit, reference_commit)
    return archive


def verify(archive, root, commit, reference_commit):
    expected = collect(root.resolve(), commit, reference_commit)
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("Archive has missing, extra, duplicate or escaping paths")
        for info in zipped.infolist():
            if (info.external_attr >> 16) & 0o170000 != 0o100000:
                raise ValueError(f"Archive contains a non-regular entry: {info.filename}")
            if info.file_size != len(expected[info.filename]) or zipped.read(info) != expected[info.filename]:
                raise ValueError(f"Archive differs from source: {info.filename}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", help="Must match HEAD; defaults to HEAD")
    parser.add_argument("--output-directory", type=Path)
    parser.add_argument("--verify", type=Path, help="Verify an existing ZIP against this source revision")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow local development packaging from modified sources")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    commit = args.commit or head
    if commit != head:
        parser.error("--commit must match the checked-out HEAD")
    # The commit HEAD pins; the clean-checkout rule below holds the checked-out reference to it.
    reference_commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", f"HEAD:{REFERENCE.as_posix()}"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=normal", "--", str(SKILL), str(MANIFEST), "Scripts/package_mql_skill.py", "Scripts/package-mql-skill.sh"], text=True)
    if dirty and not args.allow_dirty:
        parser.error("Checkout is dirty; use --allow-dirty only for local development artifacts")
    if args.verify:
        if args.output_directory:
            parser.error("--verify and --output-directory are mutually exclusive")
        verify(args.verify, root, commit, reference_commit)
        print(f"Verified {args.verify}")
    else:
        if not args.output_directory:
            parser.error("--output-directory is required when packaging")
        print(build(root, commit, reference_commit, args.output_directory))


if __name__ == "__main__":
    main()
