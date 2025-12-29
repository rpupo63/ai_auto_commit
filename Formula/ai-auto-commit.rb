class AiAutoCommit < Formula
  include Language::Python::Virtualenv

  desc "AI-powered git commit and push tool with interactive setup"
  homepage "https://github.com/yourusername/ai_auto_commit"
  url "https://files.pythonhosted.org/packages/source/a/ai-auto-commit/ai-auto-commit-0.1.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"
  license "MIT"

  depends_on "python@3.11"
  depends_on "git"

  def install
    # Create a virtualenv and install the package
    virtualenv_create(libexec, "python3.11")
    system libexec/"bin/pip", "install", "--no-binary", ":all:", buildpath

    # Create wrapper script
    (bin/"autocommit").write_env_script libexec/"bin/autocommit", PATH: "#{libexec}/bin:$PATH"
  end

  def caveats
    <<~EOS
      ╔═══════════════════════════════════════════════════════════════╗
      ║  AI Auto Commit has been installed!                           ║
      ╚═══════════════════════════════════════════════════════════════╝

      To get started, run the interactive setup wizard:
        autocommit init

      This will guide you through:
        • Configuring AI provider API keys
        • Setting your default model
        • Configuring token budget

      For more information:
        autocommit --help
    EOS
  end

  test do
    system "#{bin}/autocommit", "--help"
  end
end
