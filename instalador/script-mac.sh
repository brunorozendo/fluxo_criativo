#!/bin/bash
set -e

INSTALL_DIR="$HOME/Documents/workshop-ia"
REPO_URL="https://github.com/engdailyapp-rlv/workshop_inteligente.git"
DESKTOP="$HOME/Desktop"

echo ""
echo "========================================"
echo "   Workshop IA - Instalador Mac"
echo "========================================"
echo ""

# Homebrew
if ! command -v brew &>/dev/null; then
  echo "[1/6] Instalando Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null || true
else
  echo "[1/6] Homebrew ja instalado."
fi

# Python
echo "[2/6] Instalando Python 3..."
brew install python3 2>/dev/null || true

# Git
echo "[3/6] Instalando Git..."
brew install git 2>/dev/null || true

# Node
echo "[4/7] Instalando Node.js..."
brew install node 2>/dev/null || true

# Claude
echo "[5/7] Instalando Claude..."
brew install --cask claude 2>/dev/null || true

# Clone ou atualizar
echo "[6/7] Baixando o Workshop IA..."
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "  Repositorio encontrado. Atualizando..."
  cd "$INSTALL_DIR" && git pull origin main
else
  echo "  Clonando repositorio..."
  git clone -b main "$REPO_URL" "$INSTALL_DIR"
fi

# Dependencias
echo "[7/7] Instalando dependencias do painel..."
cd "$INSTALL_DIR"
npm install

# Launcher na area de trabalho
LAUNCHER="$DESKTOP/Workshop IA.command"
cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
cd "$HOME/Documents/workshop-ia"
npm start
EOF
chmod +x "$LAUNCHER"
xattr -cr "$LAUNCHER" 2>/dev/null || true

echo ""
echo "========================================"
echo "Instalacao concluida!"
echo ""
echo "Workshop IA instalado em:"
echo "  $INSTALL_DIR"
echo ""
echo "Para abrir: clique duas vezes em"
echo "  'Workshop IA.command' na sua area de trabalho."
echo "========================================"
echo ""
