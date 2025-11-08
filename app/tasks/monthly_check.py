#!/usr/bin/env python3
"""
Task mensal para verificação e notificação de tratamentos do mês atual e expirados

Execução:
    # Execução normal (envia emails)
    uv run python app/tasks/monthly_check.py

    # Execução em modo dry-run (não envia emails)
    uv run python app/tasks/monthly_check.py --dry-run

    # Execução com verbose logs
    uv run python app/tasks/monthly_check.py --verbose

    # Combinando opções
    uv run python app/tasks/monthly_check.py --dry-run --verbose
"""

import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Adiciona o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.monthly_report_service import MonthlyReportService
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
    logger = logging.getLogger('monthly_check')
    
    return logger


def print_summary_table(result: dict):
    """Imprime um resumo formatado dos resultados"""
    print("\n" + "="*65)
    print("           RESUMO DA EXECUÇÃO - RELATÓRIOS MENSAIS")
    print("="*65)
    
    # Status
    status = "✅ SUCESSO" if result["success"] else "❌ ERRO"
    print(f"Status: {status}")
    
    # Modo de execução
    mode = "🔍 DRY RUN (Simulação)" if result.get("dry_run") else "📧 EXECUÇÃO REAL"
    print(f"Modo: {mode}")
    
    # Estatísticas
    print(f"Total de pets com tratamentos: {result['total_pets']}")
    print(f"Total de tutores únicos: {result.get('total_tutors', 0)}")
    print(f"Relatórios consolidados enviados/simulados: {result['emails_sent']}")
    
    # Detalhes dos tratamentos
    if 'total_current_treatments' in result and 'total_expired_treatments' in result:
        print(f"Tratamentos do mês atual: {result['total_current_treatments']}")
        print(f"Tratamentos expirados: {result['total_expired_treatments']}")
    
    print(f"Erros encontrados: {len(result.get('errors', []))}")
    
    # Mês de referência
    current_month = datetime.now().strftime('%B de %Y')
    print(f"Mês de referência: {current_month}")
    
    # Mensagem principal
    print(f"\nMensagem: {result['message']}")
    
    # Erros (se houver)
    if result.get('errors'):
        print("\n🚨 ERROS ENCONTRADOS:")
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")
    
    print("="*65)


def print_detailed_treatments(report_service: MonthlyReportService, verbose: bool):
    """Imprime detalhes dos tratamentos encontrados"""
    if not verbose:
        return
        
    print("\n📋 DETALHES DOS TRATAMENTOS ENCONTRADOS:")
    print("-" * 55)
    
    success, treatments_data, message = report_service.get_monthly_treatments_with_tutors()
    
    if not success:
        print(f"❌ Erro ao buscar tratamentos: {message}")
        return
    
    if not treatments_data:
        print("ℹ️  Nenhum tratamento encontrado para o mês atual ou expirados.")
        return
    
    for i, pet_data in enumerate(treatments_data, 1):
        pet = pet_data["pet"]
        current_treatments = pet_data["current_month_treatments"]
        expired_treatments = pet_data["expired_treatments"]
        tutors = pet_data["tutors"]
        
        print(f"\n{i}. Pet: {pet['name']} (Apelido: {pet['nickname']})")
        print(f"   ID: {pet['id']}")
        
        # Tratamentos do mês atual
        if current_treatments:
            print(f"   📅 Tratamentos do Mês Atual ({len(current_treatments)}):")
            for j, treatment in enumerate(current_treatments, 1):
                print(f"     {j}. {treatment.get('name', 'Sem nome')} - {treatment.get('category', 'Categoria não especificada')}")
                print(f"        Data: {treatment.get('date', 'Sem data')}")
                if treatment.get('time'):
                    print(f"        Horário: {treatment['time']}")
        else:
            print(f"   📅 Tratamentos do Mês Atual: Nenhum")
        
        # Tratamentos expirados
        if expired_treatments:
            print(f"   ⚠️  Tratamentos Expirados ({len(expired_treatments)}):")
            for j, treatment in enumerate(expired_treatments, 1):
                # Calcula dias de atraso
                try:
                    treatment_date = datetime.strptime(treatment.get('date', ''), "%Y-%m-%d")
                    days_late = (datetime.now() - treatment_date).days
                except:
                    days_late = "?"
                
                print(f"     {j}. {treatment.get('name', 'Sem nome')} - {treatment.get('category', 'Categoria não especificada')}")
                print(f"        Data: {treatment.get('date', 'Sem data')} ({days_late} dias atrasado)")
                if treatment.get('description'):
                    print(f"        Descrição: {treatment['description']}")
        else:
            print(f"   ⚠️  Tratamentos Expirados: Nenhum")
        
        # Tutores
        print(f"   👥 Tutores com email ({len(tutors)}):")
        for tutor in tutors:
            print(f"     - {tutor['name']} ({tutor['email']})")


def main():
    """Função principal da task"""
    parser = argparse.ArgumentParser(description='Relatório mensal de tratamentos agendados e expirados')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Executa em modo simulação (não envia emails)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Exibe logs detalhados')
    
    args = parser.parse_args()
    
    # Configura logging
    logger = setup_logging(args.verbose)
    
    # Header da execução
    print("📋 PET CONTROL - RELATÓRIO MENSAL DE TRATAMENTOS")
    print("=" * 55)
    print(f"Início da execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    current_month = datetime.now().strftime('%B de %Y')
    print(f"Mês de referência: {current_month}")
    
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
        
        # Inicializa o serviço de relatórios
        logger.info("Inicializando serviço de relatórios mensais...")
        report_service = MonthlyReportService()
        
        # Exibe detalhes dos tratamentos se verbose
        print_detailed_treatments(report_service, args.verbose)
        
        # Processa os relatórios
        logger.info("Iniciando processamento de relatórios mensais...")
        result = report_service.process_monthly_reports(dry_run=args.dry_run)
        
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
