#!/usr/bin/env python3
"""
Task diária para verificação e notificação de tratamentos agendados

Execução:
    # Execução normal (envia emails)
    uv run python app/tasks/daily_check.py

    # Execução em modo dry-run (não envia emails)
    uv run python app/tasks/daily_check.py --dry-run

    # Execução com verbose logs
    uv run python app/tasks/daily_check.py --verbose

    # Combinando opções
    uv run python app/tasks/daily_check.py --dry-run --verbose
"""

import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Adiciona o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.notification_service import NotificationService
from app.database import Database


def setup_logging(verbose: bool = False):
    """Configura logging para a task"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configuração do formato de log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configura logging para console
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Cria logger específico para a task
    logger = logging.getLogger('daily_check')
    
    return logger


def print_summary_table(result: dict):
    """Imprime um resumo formatado dos resultados"""
    print("\n" + "="*60)
    print("           RESUMO DA EXECUÇÃO - NOTIFICAÇÕES DIÁRIAS")
    print("="*60)
    
    # Status
    status = "✅ SUCESSO" if result["success"] else "❌ ERRO"
    print(f"Status: {status}")
    
    # Modo de execução
    mode = "🔍 DRY RUN (Simulação)" if result.get("dry_run") else "📧 EXECUÇÃO REAL"
    print(f"Modo: {mode}")
    
    # Estatísticas
    print(f"Total de pets com tratamentos: {result['total_pets']}")
    print(f"Emails enviados/simulados: {result['emails_sent']}")
    print(f"Erros encontrados: {len(result.get('errors', []))}")
    
    # Data alvo
    tomorrow = datetime.now() + timedelta(days=1)
    print(f"Data alvo: {tomorrow.strftime('%d/%m/%Y')}")
    
    # Mensagem principal
    print(f"\nMensagem: {result['message']}")
    
    # Erros (se houver)
    if result.get('errors'):
        print("\n🚨 ERROS ENCONTRADOS:")
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")
    
    print("="*60)


def print_detailed_treatments(notification_service: NotificationService, verbose: bool):
    """Imprime detalhes dos tratamentos encontrados"""
    if not verbose:
        return
        
    print("\n📋 DETALHES DOS TRATAMENTOS ENCONTRADOS:")
    print("-" * 50)
    
    success, treatments_data, message = notification_service.get_tomorrow_treatments_with_tutors()
    
    if not success:
        print(f"❌ Erro ao buscar tratamentos: {message}")
        return
    
    if not treatments_data:
        print("ℹ️  Nenhum tratamento encontrado para amanhã.")
        return
    
    for i, pet_data in enumerate(treatments_data, 1):
        pet = pet_data["pet"]
        treatments = pet_data["treatments"]
        tutors = pet_data["tutors"]
        
        print(f"\n{i}. Pet: {pet['name']} (Apelido: {pet['nickname']})")
        print(f"   ID: {pet['id']}")
        
        # Tratamentos
        print(f"   Tratamentos ({len(treatments)}):")
        for j, treatment in enumerate(treatments, 1):
            print(f"     {j}. {treatment.get('name', 'Sem nome')} - {treatment.get('category', 'Categoria não especificada')}")
            if treatment.get('time'):
                print(f"        Horário: {treatment['time']}")
            if treatment.get('description'):
                print(f"        Descrição: {treatment['description']}")
        
        # Tutores
        print(f"   Tutores com email ({len(tutors)}):")
        for tutor in tutors:
            print(f"     - {tutor['name']} ({tutor['email']})")


def main():
    """Função principal da task"""
    parser = argparse.ArgumentParser(description='Verificação diária de tratamentos agendados')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Executa em modo simulação (não envia emails)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Exibe logs detalhados')
    
    args = parser.parse_args()
    
    # Configura logging
    logger = setup_logging(args.verbose)
    
    # Header da execução
    print("🐾 PET CONTROL - VERIFICAÇÃO DIÁRIA DE TRATAMENTOS")
    print("=" * 50)
    print(f"Início da execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    if args.dry_run:
        print("⚠️  MODO DRY-RUN ATIVADO - Emails não serão enviados")
    
    if args.verbose:
        print("🔍 MODO VERBOSE ATIVADO - Logs detalhados")
    
    try:
        # Conecta ao banco de dados
        logger.info("Conectando ao banco de dados...")
        database = Database()
        database.connect()
        logger.info("Conexão com banco de dados estabelecida")
        
        # Inicializa o serviço de notificações
        logger.info("Inicializando serviço de notificações...")
        notification_service = NotificationService()
        
        # Exibe detalhes dos tratamentos se verbose
        print_detailed_treatments(notification_service, args.verbose)
        
        # Processa as notificações
        logger.info("Iniciando processamento de notificações...")
        result = notification_service.process_daily_notifications(dry_run=args.dry_run)
        
        # Imprime resumo
        print_summary_table(result)
        
        # Fecha conexão com banco
        database.close()
        logger.info("Conexão com banco de dados fechada")
        
        # Define código de saída
        exit_code = 0 if result["success"] else 1
        
        if exit_code == 0:
            logger.info("Task concluída com sucesso")
        else:
            logger.error("Task concluída com erros")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n❌ Execução interrompida pelo usuário")
        logger.info("Execução interrompida pelo usuário")
        sys.exit(1)
        
    except Exception as e:
        error_msg = f"Erro crítico durante execução: {str(e)}"
        print(f"\n❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
