#!/usr/bin/env python3
"""
Script de conveniência para executar a verificação diária de tratamentos

Este script é um wrapper para app/tasks/daily_check.py
Pode ser executado diretamente da raiz do projeto:

Exemplos:
    uv run python daily_check.py
    uv run python daily_check.py --dry-run
    uv run python daily_check.py --verbose
    uv run python daily_check.py --dry-run --verbose
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Caminho para o script real
    script_path = Path(__file__).parent / "app" / "tasks" / "daily_check.py"
    
    # Executa o script real com todos os argumentos passados
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n❌ Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao executar script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
