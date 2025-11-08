import uuid
import shutil
from pathlib import Path
from PIL import Image
import io
from typing import Dict, Tuple, Optional
from fastapi import UploadFile, HTTPException

# File upload configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Extensões permitidas baseadas no suporte disponível
BASE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_EXTENSIONS = BASE_EXTENSIONS

THUMBNAIL_SIZE = (300, 300)


class FileService:
    """Serviço para gerenciar arquivos e imagens"""
    
    def __init__(self):
        # Cria diretório de uploads se não existir
        UPLOAD_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def validate_image_file(file: UploadFile) -> Tuple[bool, str]:
        """
        Valida se o arquivo é uma imagem válida.
        Retorna (is_valid, error_message)
        """
        if not file.filename:
            return False, "Nenhum arquivo selecionado"

        # Verifica extensão
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return (
                False,
                f"Formato de arquivo não suportado. Use: {', '.join(ALLOWED_EXTENSIONS).upper()}",
            )

        # Verifica se é um arquivo HEIC (não suportado)
        if file_ext in [".heic", ".heif"]:
            return False, "Arquivos HEIC não são suportados. Use JPG, PNG, GIF ou WebP."

        # Verifica tamanho
        if file.size and file.size > MAX_FILE_SIZE:
            max_size_mb = MAX_FILE_SIZE // (1024 * 1024)
            return False, f"Arquivo muito grande. Tamanho máximo: {max_size_mb}MB"

        return True, ""
    
    @staticmethod
    def save_image_with_thumbnail(file: UploadFile, pet_id: str) -> Dict[str, str]:
        """
        Salva a imagem original e cria uma miniatura.
        Retorna um dicionário com os caminhos dos arquivos.
        """
        # Gera nome único para o arquivo
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{pet_id}_{uuid.uuid4().hex}{file_ext}"

        # Cria diretório específico para o pet
        pet_upload_dir = UPLOAD_DIR / pet_id
        pet_upload_dir.mkdir(exist_ok=True)

        # Caminhos dos arquivos
        original_path = pet_upload_dir / unique_filename
        thumbnail_path = pet_upload_dir / f"thumb_{unique_filename}"

        try:
            # Lê o arquivo
            contents = file.file.read()

            # Salva arquivo original
            with open(original_path, "wb") as f:
                f.write(contents)

            # Processa a imagem
            try:
                # Abre a imagem com PIL
                image = Image.open(io.BytesIO(contents))

            except Exception as e:
                raise Exception(f"Formato de imagem não suportado: {str(e)}")

            # Converte para RGB se necessário
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")

            # Redimensiona mantendo proporção
            image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # Salva miniatura
            image.save(thumbnail_path, "JPEG", quality=85, optimize=True)

            return {
                "original": str(original_path),
                "thumbnail": str(thumbnail_path),
                "filename": unique_filename,
            }

        except Exception as e:
            # Remove arquivos em caso de erro
            if original_path.exists():
                original_path.unlink()
            if thumbnail_path.exists():
                thumbnail_path.unlink()
            raise HTTPException(
                status_code=400, detail=f"Erro ao processar imagem: {str(e)}"
            )
    
    @staticmethod
    def delete_pet_images(pet_id: str) -> bool:
        """
        Remove todas as imagens de um pet.
        Retorna True se removeu com sucesso
        """
        try:
            pet_upload_dir = UPLOAD_DIR / pet_id
            if pet_upload_dir.exists():
                shutil.rmtree(pet_upload_dir)
            return True
        except Exception as e:
            print(f"Erro ao remover imagens do pet {pet_id}: {e}")
            return False
    
    @staticmethod
    def move_temp_image_to_pet_folder(photo_data: Dict[str, str], pet_id: str) -> Optional[Dict[str, str]]:
        """
        Move arquivos da pasta temporária para a pasta correta do pet
        Retorna os novos caminhos ou None em caso de erro
        """
        if not photo_data or not photo_data.get("original"):
            return None
            
        try:
            temp_original_path = Path(photo_data["original"])
            temp_thumbnail_path = Path(photo_data["thumbnail"])

            if temp_original_path.exists():
                # Cria diretório do pet
                pet_dir = UPLOAD_DIR / pet_id
                pet_dir.mkdir(exist_ok=True)

                # Paths finais
                final_original_path = pet_dir / temp_original_path.name
                final_thumbnail_path = pet_dir / temp_thumbnail_path.name

                # Move arquivo original
                shutil.move(str(temp_original_path), str(final_original_path))

                # Move thumbnail se existir
                if temp_thumbnail_path.exists():
                    shutil.move(str(temp_thumbnail_path), str(final_thumbnail_path))

                # Retorna novos caminhos
                return {
                    "original": str(final_original_path),
                    "thumbnail": str(final_thumbnail_path),
                    "filename": photo_data.get("filename", temp_original_path.name)
                }
            
            return None
        except Exception as e:
            print(f"Erro ao mover imagem: {e}")
            return None
    
    @staticmethod
    def cleanup_temp_images():
        """
        Remove imagens temporárias antigas (pasta temp).
        """
        try:
            temp_dir = UPLOAD_DIR / "temp"
            if temp_dir.exists():
                # Remove arquivos mais antigos que 1 hora
                import time

                current_time = time.time()
                for file_path in temp_dir.glob("*"):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > 3600:  # 1 hora em segundos
                            file_path.unlink()
                            print(f"Removido arquivo temporário antigo: {file_path}")
        except Exception as e:
            print(f"Erro ao limpar arquivos temporários: {e}")
