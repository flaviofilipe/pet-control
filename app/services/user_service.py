from typing import Dict, Any, Optional, List, Tuple
from ..repositories import UserRepository


class UserService:
    """Serviço para regras de negócio relacionadas a usuários/profiles"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def get_user_profile(self, user_id: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Busca perfil do usuário ou retorna dados básicos do Auth0
        """
        profile = self.user_repo.get_profile_by_id(user_id)
        
        if profile:
            return profile
        else:
            # Se não houver perfil completo, usa os dados do Auth0 como fallback
            return {
                "name": user_info.get("name", "Usuário"),
                "email": user_info.get("email"),
                "bio": "Complete seu perfil para adicionar uma biografia.",
                "address": None,
                "is_vet": False,
            }
    
    def create_or_update_profile(self, user_id: str, profile_data: Dict[str, Any], user_email: str) -> Tuple[bool, str]:
        """
        Cria ou atualiza perfil do usuário
        Retorna: (sucesso, mensagem)
        """
        try:
            # Adiciona email do Auth0
            profile_data["email"] = user_email
            
            success = self.user_repo.create_or_update_profile(user_id, profile_data)
            
            if success:
                return True, "Perfil salvo com sucesso!"
            else:
                return False, "Erro ao salvar perfil."
        except Exception as e:
            return False, f"Erro ao salvar perfil: {str(e)}"
    
    def search_veterinarians(self, search_term: str, requesting_user_id: str) -> List[Dict[str, Any]]:
        """
        Busca veterinários por nome para vinculação a pets.
        Apenas tutores podem buscar veterinários.
        """
        try:
            veterinarians = self.user_repo.search_veterinarians(search_term, requesting_user_id, limit=10)
            
            # Formata dados dos veterinários
            formatted_vets = []
            for vet in veterinarians:
                formatted_vets.append({
                    "id": str(vet["_id"]),
                    "name": vet.get("name", "Sem nome"),
                    "email": vet.get("email", ""),
                })
            
            return formatted_vets
        except Exception as e:
            print(f"Erro ao buscar veterinários: {e}")
            return []
    
    def validate_veterinarian(self, vet_id: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Valida se o ID corresponde a um veterinário válido
        Retorna: (é_válido, dados_vet, mensagem)
        """
        try:
            vet = self.user_repo.get_veterinarian_by_id(vet_id)
            
            if vet:
                return True, vet, "Veterinário válido."
            else:
                return False, None, "Veterinário não encontrado."
        except Exception as e:
            return False, None, f"Erro ao validar veterinário: {str(e)}"
