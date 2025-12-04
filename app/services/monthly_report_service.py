"""
Serviço para relatórios mensais de tratamentos
"""

import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Tuple
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import PetRepository, UserRepository
from app.config import (
    GMAIL_EMAIL, 
    GMAIL_PASSWORD, 
    GMAIL_SMTP_SERVER, 
    GMAIL_SMTP_PORT,
    validate_gmail_config
)


class MonthlyReportService:
    """Serviço para relatórios mensais de tratamentos"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pet_repo = PetRepository(session)
        self.user_repo = UserRepository(session)
        self.logger = logging.getLogger(__name__)
        
        # Configura Jinja2 para templates
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    async def get_monthly_treatments_with_tutors(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Busca tratamentos do mês atual e expirados com dados dos tutores
        Retorna: (sucesso, lista_tratamentos_com_tutores, mensagem)
        """
        try:
            # Busca tratamentos do mês atual
            current_month_treatments = await self.pet_repo.get_current_month_treatments()
            
            # Busca tratamentos expirados
            expired_treatments = await self.pet_repo.get_expired_treatments()
            
            # Combina todos os tratamentos
            all_treatments = {}
            
            # Adiciona tratamentos do mês atual
            for pet_data in current_month_treatments:
                pet_id = pet_data["_id"]
                if pet_id not in all_treatments:
                    all_treatments[pet_id] = {
                        "_id": pet_id,
                        "name": pet_data["name"],
                        "nickname": pet_data["nickname"],
                        "users": pet_data["users"],
                        "current_month_treatments": pet_data["treatments"],
                        "expired_treatments": []
                    }
                else:
                    all_treatments[pet_id]["current_month_treatments"] = pet_data["treatments"]
            
            # Adiciona tratamentos expirados
            for pet_data in expired_treatments:
                pet_id = pet_data["_id"]
                if pet_id not in all_treatments:
                    all_treatments[pet_id] = {
                        "_id": pet_id,
                        "name": pet_data["name"],
                        "nickname": pet_data["nickname"],
                        "users": pet_data["users"],
                        "current_month_treatments": [],
                        "expired_treatments": pet_data["treatments"]
                    }
                else:
                    all_treatments[pet_id]["expired_treatments"] = pet_data["treatments"]
            
            if not all_treatments:
                return True, [], "Nenhum tratamento encontrado para o mês atual ou expirados."
            
            # Para cada pet, busca dados dos tutores
            enriched_data = []
            
            for pet_data in all_treatments.values():
                # Busca emails dos tutores
                tutors = await self.user_repo.get_user_emails_by_ids(pet_data["users"])
                
                # Só adiciona se houver tutores com email
                if tutors:
                    enriched_data.append({
                        "pet": {
                            "id": pet_data["_id"],
                            "name": pet_data["name"],
                            "nickname": pet_data["nickname"]
                        },
                        "current_month_treatments": pet_data["current_month_treatments"],
                        "expired_treatments": pet_data["expired_treatments"],
                        "tutors": tutors
                    })
            
            total_current = sum(len(pet["current_month_treatments"]) for pet in enriched_data)
            total_expired = sum(len(pet["expired_treatments"]) for pet in enriched_data)
            
            message = f"Encontrados {len(enriched_data)} pets com tratamentos: {total_current} do mês atual, {total_expired} expirados."
            return True, enriched_data, message
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar tratamentos mensais: {e}")
            return False, [], f"Erro ao buscar tratamentos: {str(e)}"
    
    def format_consolidated_report_for_email(
        self,
        tutor: Dict[str, Any],
        pets_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Formata dados consolidados de múltiplos pets para um único email
        """
        now = datetime.now()
        current_month_name = now.strftime("%B de %Y")
        
        consolidated_pets = []
        total_current_treatments = 0
        total_expired_treatments = 0
        
        for pet_data in pets_list:
            # Formata tratamentos do mês atual
            formatted_current = []
            for treatment in pet_data["current_month_treatments"]:
                formatted_treatment = {
                    "name": treatment.get("name", "Tratamento"),
                    "category": treatment.get("category", "Não especificado"),
                    "description": treatment.get("description", ""),
                    "date": treatment.get("date", ""),
                    "time": treatment.get("time", "Não especificado"),
                    "applier_type": treatment.get("applier_type", "Não especificado"),
                    "applier_name": treatment.get("applier_name", ""),
                    "status": "Agendado"
                }
                formatted_current.append(formatted_treatment)
            
            # Formata tratamentos expirados
            formatted_expired = []
            for treatment in pet_data["expired_treatments"]:
                # Calcula quantos dias está atrasado
                treatment_date = datetime.strptime(treatment.get("date", ""), "%Y-%m-%d")
                days_late = (now - treatment_date).days
                
                formatted_treatment = {
                    "name": treatment.get("name", "Tratamento"),
                    "category": treatment.get("category", "Não especificado"),
                    "description": treatment.get("description", ""),
                    "date": treatment.get("date", ""),
                    "time": treatment.get("time", "Não especificado"),
                    "applier_type": treatment.get("applier_type", "Não especificado"),
                    "applier_name": treatment.get("applier_name", ""),
                    "status": "Expirado",
                    "days_late": days_late
                }
                formatted_expired.append(formatted_treatment)
            
            # Adiciona pet consolidado
            consolidated_pets.append({
                "pet_name": pet_data["pet"]["name"],
                "pet_nickname": pet_data["pet"]["nickname"],
                "current_month_treatments": formatted_current,
                "expired_treatments": formatted_expired,
                "total_current_treatments": len(formatted_current),
                "total_expired_treatments": len(formatted_expired),
                "has_current_treatments": len(formatted_current) > 0,
                "has_expired_treatments": len(formatted_expired) > 0
            })
            
            total_current_treatments += len(formatted_current)
            total_expired_treatments += len(formatted_expired)
        
        return {
            "current_month": current_month_name,
            "pets": consolidated_pets,
            "total_pets": len(consolidated_pets),
            "total_current_treatments": total_current_treatments,
            "total_expired_treatments": total_expired_treatments,
            "has_treatments": total_current_treatments > 0 or total_expired_treatments > 0,
            "report_date": now.strftime("%d/%m/%Y")
        }
    
    def send_consolidated_monthly_email(
        self,
        tutor_email: str,
        tutor_name: str,
        consolidated_data: Dict[str, Any],
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """
        Envia email consolidado de relatório mensal para um tutor (todos os pets)
        """
        try:
            # Carrega template de email mensal consolidado
            template = self.jinja_env.get_template("consolidated_monthly_report.html")
            
            # Renderiza o conteúdo do email
            html_content = template.render(
                tutor_name=tutor_name,
                **consolidated_data
            )
            
            # Se for dry-run, só retorna sucesso sem enviar
            if dry_run:
                self.logger.info(
                    f"[DRY RUN] Relatório mensal consolidado seria enviado para {tutor_email} "
                    f"({consolidated_data['total_pets']} pets)"
                )
                return True, f"[DRY RUN] Relatório consolidado preparado para {tutor_email}"
            
            # Valida configuração do Gmail
            is_valid, validation_message = validate_gmail_config()
            if not is_valid:
                return False, validation_message
            
            # Cria mensagem de email
            msg = MIMEMultipart('alternative')
            subject = (
                f"📋 Relatório Mensal Consolidado - {consolidated_data['total_pets']} pets "
                f"({consolidated_data['current_month']})"
            )
            msg['Subject'] = subject
            msg['From'] = GMAIL_EMAIL
            msg['To'] = tutor_email
            
            # Anexa conteúdo HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Conecta ao servidor SMTP e envia
            with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(GMAIL_EMAIL, GMAIL_PASSWORD)
                server.send_message(msg)
            
            self.logger.info(f"Relatório mensal consolidado enviado com sucesso para {tutor_email}")
            return True, f"Relatório consolidado enviado para {tutor_email}"
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar relatório consolidado para {tutor_email}: {e}")
            return False, f"Erro ao enviar relatório consolidado para {tutor_email}: {str(e)}"

    async def process_monthly_reports(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Processa todos os relatórios mensais de tratamentos
        NOVA VERSÃO: Consolida por tutor (1 email por tutor com todos os seus pets)
        """
        self.logger.info("Iniciando processamento de relatórios mensais consolidados")
        
        # Busca tratamentos do mês e expirados
        success, treatments_data, message = await self.get_monthly_treatments_with_tutors()
        
        if not success:
            self.logger.error(f"Erro ao buscar tratamentos: {message}")
            return {
                "success": False,
                "message": message,
                "total_pets": 0,
                "total_tutors": 0,
                "emails_sent": 0,
                "errors": [],
                "dry_run": dry_run
            }
        
        if not treatments_data:
            self.logger.info("Nenhum tratamento encontrado para relatório mensal")
            return {
                "success": True,
                "message": "Nenhum tratamento encontrado para relatório mensal",
                "total_pets": 0,
                "total_tutors": 0,
                "emails_sent": 0,
                "errors": [],
                "dry_run": dry_run
            }
        
        # NOVA LÓGICA: Agrupa pets por tutor
        tutors_pets = {}
        
        for pet_treatments in treatments_data:
            for tutor in pet_treatments["tutors"]:
                tutor_key = f"{tutor['id']}|{tutor['email']}"
                if tutor_key not in tutors_pets:
                    tutors_pets[tutor_key] = {
                        "tutor": tutor,
                        "pets": []
                    }
                tutors_pets[tutor_key]["pets"].append(pet_treatments)
        
        # Processa cada tutor (1 email por tutor)
        total_pets = len(treatments_data)
        total_tutors = len(tutors_pets)
        emails_sent = 0
        errors = []
        total_current = 0
        total_expired = 0
        
        for tutor_key, tutor_data in tutors_pets.items():
            try:
                tutor = tutor_data["tutor"]
                pets_list = tutor_data["pets"]
                
                # Formata dados consolidados para email
                consolidated_data = self.format_consolidated_report_for_email(tutor, pets_list)
                total_current += consolidated_data["total_current_treatments"]
                total_expired += consolidated_data["total_expired_treatments"]
                
                # Envia 1 email consolidado para o tutor
                success_send, result_message = self.send_consolidated_monthly_email(
                    tutor["email"], 
                    tutor["name"], 
                    consolidated_data, 
                    dry_run
                )
                
                if success_send:
                    emails_sent += 1
                    self.logger.info(result_message)
                else:
                    errors.append(result_message)
                    self.logger.error(result_message)
            
            except Exception as e:
                error_msg = f"Erro ao processar tutor {tutor['name']}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        # Retorna resumo da execução
        final_message = (
            f"Processamento concluído: {emails_sent} relatórios consolidados enviados para "
            f"{total_tutors} tutores ({total_pets} pets, {total_current} agendados, {total_expired} expirados)"
        )
        if errors:
            final_message += f", {len(errors)} erros encontrados"
        
        self.logger.info(final_message)
        
        return {
            "success": True,
            "message": final_message,
            "total_pets": total_pets,
            "total_tutors": total_tutors,
            "emails_sent": emails_sent,
            "total_current_treatments": total_current,
            "total_expired_treatments": total_expired,
            "errors": errors,
            "dry_run": dry_run
        }
