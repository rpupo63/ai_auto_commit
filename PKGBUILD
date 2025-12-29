# Maintainer: Your Name <your.email@example.com>
pkgname=ai-auto-commit
pkgver=0.1.0
pkgrel=1
pkgdesc="AI-powered git commit and push tool with interactive setup"
arch=('any')
url="https://github.com/yourusername/ai_auto_commit"
license=('MIT')
depends=('python' 'python-pip' 'git')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("$pkgname-$pkgver.tar.gz::https://github.com/yourusername/ai_auto_commit/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl

    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"

    # Install README
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}

post_install() {
    echo ""
    echo "==================================================================="
    echo "  AI Auto Commit has been installed!"
    echo "==================================================================="
    echo ""
    To get started, run the interactive setup wizard:
      autocommit init

    This will guide you through:
      • Configuring AI provider API keys
      • Setting your default model
      • Configuring token budget

    For more information:
      autocommit --help
    echo "==================================================================="
    echo ""
}

post_upgrade() {
    post_install
}
