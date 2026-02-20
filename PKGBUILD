# Maintainer: Beto
pkgname=ai-auto-commit
pkgver=0.1.1
pkgrel=1
pkgdesc="AI-powered git commit and push tool with interactive setup"
arch=('any')
url="https://github.com/yourusername/ai_auto_commit"
license=('MIT')
depends=('python' 'git')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools' 'python-pip')
install=ai-auto-commit.install
options=('!debug')
source=()
sha256sums=()

# Sibling project providing model picker (use local source, not stale PyPI version)
_model_picker_dir="$startdir/../model_picker"

build() {
    cd "$startdir"
    python -m build --wheel --no-isolation

    # Build model_picker wheel from local source
    cd "$_model_picker_dir"
    python -m build --wheel --no-isolation
}

package() {
    cd "$startdir"

    _lib="/usr/lib/ai-auto-commit"

    # Install the wheel (no deps, just the package itself)
    pip install --isolated --ignore-installed --no-deps --no-warn-script-location \
        --target="$pkgdir/$_lib" \
        dist/*.whl

    # Install local model_picker (no deps for it either, we install its deps below)
    pip install --isolated --ignore-installed --no-deps --no-warn-script-location \
        --target="$pkgdir/$_lib" \
        "$_model_picker_dir"/dist/*.whl

    # Install all remaining dependencies into the private directory
    pip install --isolated --ignore-installed --no-warn-script-location \
        --target="$pkgdir/$_lib" \
        "langchain-core>=1.0.0" \
        "langchain-openai>=1.0.0" \
        "langchain-anthropic>=1.0.0" \
        "langchain-google-genai>=2.0.0" \
        "google-generativeai>=0.5.0" \
        "langchain-mistralai>=1.0.0" \
        "langchain-cohere>=0.4.0" \
        "tiktoken>=0.5.0" \
        "python-dotenv>=1.0.0"

    # Create wrapper script that sets the private lib on PYTHONPATH
    install -d "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/autocommit" << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/ai-auto-commit')
from ai_auto_commit.cli import main
main()
EOF
    chmod 755 "$pkgdir/usr/bin/autocommit"

    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
