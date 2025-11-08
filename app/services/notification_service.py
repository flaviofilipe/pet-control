import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from ..repositories.pet_repository import PetRepository
from ..repositories.user_repository import UserRepository
from ..config import (
    GMAIL_EMAIL, 
    GMAIL_PASSWORD, 
    GMAIL_SMTP_SERVER, 
    GMAIL_SMTP_PORT,
    validate_gmail_config
)


class NotificationService:
    """Serviço para envio de notificações de tratamentos"""
    
    def __init__(self):
        self.pet_repo = PetRepository()
        self.user_repo = UserRepository()
        self.logger = logging.getLogger(__name__)
        
        # Configura Jinja2 para templates
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def get_tomorrow_treatments_with_tutors(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Busca tratamentos de amanhã com dados dos tutores
        Retorna: (sucesso, lista_tratamentos_com_tutores, mensagem)
        """
        try:
            # Busca tratamentos de amanhã
            treatments_data = self.pet_repo.get_tomorrow_scheduled_treatments()
            
            if not treatments_data:
                return True, [], "Nenhum tratamento agendado para amanhã."
            
            # Para cada pet, busca dados dos tutores
            enriched_data = []
            
            for pet_data in treatments_data:
                # Busca emails dos tutores
                tutors = self.user_repo.get_user_emails_by_ids(pet_data["users"])
                
                # Só adiciona se houver tutores com email
                if tutors:
                    enriched_data.append({
                        "pet": {
                            "id": pet_data["_id"],
                            "name": pet_data["name"],
                            "nickname": pet_data["nickname"]
                        },
                        "treatments": pet_data["treatments"],
                        "tutors": tutors
                    })
            
            message = f"Encontrados {len(enriched_data)} pets com tratamentos agendados para amanhã."
            return True, enriched_data, message
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar tratamentos de amanhã: {e}")
            return False, [], f"Erro ao buscar tratamentos: {str(e)}"
    
    def format_treatments_for_email(self, pet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata dados de tratamentos para o template de email
        """
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_formatted = tomorrow.strftime("%d/%m/%Y")
        
        formatted_treatments = []
        for treatment in pet_data["treatments"]:
            formatted_treatment = {
                "name": treatment.get("name", "Tratamento"),
                "category": treatment.get("category", "Não especificado"),
                "description": treatment.get("description", ""),
                "time": treatment.get("time", "Não especificado"),
                "applier_type": treatment.get("applier_type", "Não especificado"),
                "applier_name": treatment.get("applier_name", "")
            }
            formatted_treatments.append(formatted_treatment)
        
        return {
            "pet_name": pet_data["pet"]["name"],
            "pet_nickname": pet_data["pet"]["nickname"],
            "date": tomorrow_formatted,
            "treatments": formatted_treatments,
            "total_treatments": len(formatted_treatments)
        }
    
    def send_email_notification(self, tutor_email: str, tutor_name: str, email_data: Dict[str, Any], dry_run: bool = False) -> Tuple[bool, str]:
        """
        Envia email de notificação para um tutor
        """
        try:
            # Carrega template de email
            template = self.jinja_env.get_template("treatment_reminder.html")
            
            # Renderiza o conteúdo do email
            html_content = template.render(
                tutor_name=tutor_name,
                **email_data
            )
            
            # Se for dry-run, só retorna sucesso sem enviar
            if dry_run:
                self.logger.info(f"[DRY RUN] Email seria enviado para {tutor_email}")
                return True, f"[DRY RUN] Email preparado para {tutor_email}"
            
            # Valida configuração do Gmail
            is_valid, validation_message = validate_gmail_config()
            if not is_valid:
                return False, validation_message
            
            # Cria mensagem de email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🐾 Lembrete: Tratamentos agendados para {email_data['pet_name']} amanhã"
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
            
            self.logger.info(f"Email enviado com sucesso para {tutor_email}")
            return True, f"Email enviado para {tutor_email}"
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email para {tutor_email}: {e}")
            return False, f"Erro ao enviar email para {tutor_email}: {str(e)}"
    
    def process_daily_notifications(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Processa todas as notificações diárias de tratamentos
        """
        self.logger.info("Iniciando processamento de notificações diárias")
        
        # Busca tratamentos de amanhã
        success, treatments_data, message = self.get_tomorrow_treatments_with_tutors()
        
        if not success:
            self.logger.error(f"Erro ao buscar tratamentos: {message}")
            return {
                "success": False,
                "message": message,
                "total_pets": 0,
                "emails_sent": 0,
                "errors": [],
                "dry_run": dry_run
            }
        
        if not treatments_data:
            self.logger.info("Nenhum tratamento encontrado para amanhã")
            return {
                "success": True,
                "message": "Nenhum tratamento agendado para amanhã",
                "total_pets": 0,
                "emails_sent": 0,
                "errors": [],
                "dry_run": dry_run
            }
        
        # Processa cada pet com tratamentos
        total_pets = len(treatments_data)
        emails_sent = 0
        errors = []
        
        for pet_treatments in treatments_data:
            try:
                # Formata dados para email
                email_data = self.format_treatments_for_email(pet_treatments)
                
                # Envia email para cada tutor
                for tutor in pet_treatments["tutors"]:
                    success, result_message = self.send_email_notification(
                        tutor["email"], 
                        tutor["name"], 
                        email_data, 
                        dry_run
                    )
                    
                    if success:
                        emails_sent += 1
                        self.logger.info(result_message)
                    else:
                        errors.append(result_message)
                        self.logger.error(result_message)
            
            except Exception as e:
                error_msg = f"Erro ao processar pet {pet_treatments['pet']['name']}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        # Retorna resumo da execução
        final_message = f"Processamento concluído: {emails_sent} emails enviados para {total_pets} pets"
        if errors:
            final_message += f", {len(errors)} erros encontrados"
        
        self.logger.info(final_message)
        
        return {
            "success": True,
            "message": final_message,
            "total_pets": total_pets,
            "emails_sent": emails_sent,
            "errors": errors,
            "dry_run": dry_run
        }
