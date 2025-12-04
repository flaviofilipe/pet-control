"""
Script para executar todos os seeds do banco de dados
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.connection import AsyncSessionLocal
from app.database.models import Vaccine, Ectoparasite, Vermifugo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_vaccines(session: AsyncSession) -> int:
    """Seed de vacinas"""
    
    # Verifica se já existem vacinas
    result = await session.execute(select(Vaccine).limit(1))
    if result.scalar_one_or_none():
        logger.info("Vacinas já existem, pulando seed...")
        return 0
    
    vaccines_data = [
        {
            "nome_vacina": "V8",
            "descricao": "Vacina óctupla que protege contra 8 doenças",
            "especie_alvo": "Cão",
            "tipo_vacina": "Múltipla",
            "protege_contra": ["Cinomose", "Hepatite Infecciosa", "Adenovirose", "Parainfluenza", "Parvovirose", "Coronavirose", "Leptospirose Canicola", "Leptospirose Icterohaemorrhagiae"],
            "efeitos_colaterais": ["Dor no local da aplicação", "Febre leve", "Apatia temporária"],
            "cronograma_vacinal": {"filhote": "Primeira dose aos 45 dias, reforços a cada 21-30 dias até 16 semanas", "adulto": "Reforço anual"}
        },
        {
            "nome_vacina": "V10",
            "descricao": "Vacina décupla que protege contra 10 doenças",
            "especie_alvo": "Cão",
            "tipo_vacina": "Múltipla",
            "protege_contra": ["Cinomose", "Hepatite Infecciosa", "Adenovirose", "Parainfluenza", "Parvovirose", "Coronavirose", "Leptospirose Canicola", "Leptospirose Icterohaemorrhagiae", "Leptospirose Grippotyphosa", "Leptospirose Pomona"],
            "efeitos_colaterais": ["Dor no local da aplicação", "Febre leve", "Apatia temporária"],
            "cronograma_vacinal": {"filhote": "Primeira dose aos 45 dias, reforços a cada 21-30 dias até 16 semanas", "adulto": "Reforço anual"}
        },
        {
            "nome_vacina": "Antirrábica",
            "descricao": "Vacina contra a raiva",
            "especie_alvo": "Cão",
            "tipo_vacina": "Única",
            "protege_contra": ["Raiva"],
            "efeitos_colaterais": ["Dor no local da aplicação", "Febre leve"],
            "cronograma_vacinal": {"filhote": "Dose única a partir dos 4 meses", "adulto": "Reforço anual obrigatório"}
        },
        {
            "nome_vacina": "Gripe Canina",
            "descricao": "Vacina contra a tosse dos canis",
            "especie_alvo": "Cão",
            "tipo_vacina": "Única",
            "protege_contra": ["Traqueobronquite Infecciosa Canina", "Bordetella bronchiseptica"],
            "efeitos_colaterais": ["Espirros temporários", "Secreção nasal leve"],
            "cronograma_vacinal": {"filhote": "A partir de 8 semanas, 2 doses com intervalo de 2-4 semanas", "adulto": "Reforço anual ou semestral para cães expostos"}
        },
        {
            "nome_vacina": "V4 Felina",
            "descricao": "Vacina quádrupla felina",
            "especie_alvo": "Gato",
            "tipo_vacina": "Múltipla",
            "protege_contra": ["Panleucopenia Felina", "Rinotraqueíte Felina", "Calicivirose Felina", "Clamidiose Felina"],
            "efeitos_colaterais": ["Dor no local da aplicação", "Febre leve", "Letargia"],
            "cronograma_vacinal": {"filhote": "Primeira dose às 8 semanas, reforços a cada 3-4 semanas até 16 semanas", "adulto": "Reforço anual"}
        },
        {
            "nome_vacina": "V5 Felina",
            "descricao": "Vacina quíntupla felina",
            "especie_alvo": "Gato",
            "tipo_vacina": "Múltipla",
            "protege_contra": ["Panleucopenia Felina", "Rinotraqueíte Felina", "Calicivirose Felina", "Clamidiose Felina", "Leucemia Felina"],
            "efeitos_colaterais": ["Dor no local da aplicação", "Febre leve", "Letargia"],
            "cronograma_vacinal": {"filhote": "Primeira dose às 8 semanas, reforços a cada 3-4 semanas até 16 semanas", "adulto": "Reforço anual"}
        },
        {
            "nome_vacina": "Antirrábica Felina",
            "descricao": "Vacina contra a raiva para gatos",
            "especie_alvo": "Gato",
            "tipo_vacina": "Única",
            "protege_contra": ["Raiva"],
            "efeitos_colaterais": ["Dor no local da aplicação", "Febre leve"],
            "cronograma_vacinal": {"filhote": "Dose única a partir das 12 semanas", "adulto": "Reforço anual obrigatório"}
        },
    ]
    
    for vaccine_data in vaccines_data:
        vaccine = Vaccine(**vaccine_data)
        session.add(vaccine)
    
    await session.flush()
    logger.info(f"Inseridas {len(vaccines_data)} vacinas")
    return len(vaccines_data)


async def seed_ectoparasites(session: AsyncSession) -> int:
    """Seed de ectoparasitas"""
    
    # Verifica se já existem ectoparasitas
    result = await session.execute(select(Ectoparasite).limit(1))
    if result.scalar_one_or_none():
        logger.info("Ectoparasitas já existem, pulando seed...")
        return 0
    
    ectoparasites_data = [
        {
            "nome_praga": "Pulga",
            "tipo_praga": "Inseto",
            "especies_alvo": ["Cão", "Gato"],
            "transmissor_de_doencas": ["Dipilidiose (verme)", "Dermatite alérgica à picada de pulga"],
            "sintomas_no_animal": ["Coceira intensa", "Irritação da pele", "Queda de pelo", "Feridas por mordidas"],
            "medicamentos_de_combate": [
                {"descricao": "Fipronil", "principios_ativos": ["Fipronil"]},
                {"descricao": "Imidacloprid", "principios_ativos": ["Imidacloprid"]},
                {"descricao": "Selamectina", "principios_ativos": ["Selamectina"]}
            ],
            "observacoes_adicionais": "Tratamento mensal recomendado. Tratar também o ambiente."
        },
        {
            "nome_praga": "Carrapato",
            "tipo_praga": "Aracnídeo",
            "especies_alvo": ["Cão", "Gato"],
            "transmissor_de_doencas": ["Babesiose", "Erliquiose", "Anaplasmose", "Doença de Lyme"],
            "sintomas_no_animal": ["Anemia", "Febre", "Perda de apetite", "Fraqueza"],
            "medicamentos_de_combate": [
                {"descricao": "Fipronil", "principios_ativos": ["Fipronil"]},
                {"descricao": "Fluralaner", "principios_ativos": ["Fluralaner"]},
                {"descricao": "Afoxolaner", "principios_ativos": ["Afoxolaner"]}
            ],
            "observacoes_adicionais": "Verificar o animal após passeios em áreas verdes. Remover carrapatos manualmente se encontrados."
        },
        {
            "nome_praga": "Sarna Sarcóptica",
            "tipo_praga": "Ácaro",
            "especies_alvo": ["Cão"],
            "transmissor_de_doencas": [],
            "sintomas_no_animal": ["Coceira intensa", "Queda de pelo", "Crostas na pele", "Infecções secundárias"],
            "medicamentos_de_combate": [
                {"descricao": "Ivermectina", "principios_ativos": ["Ivermectina"]},
                {"descricao": "Selamectina", "principios_ativos": ["Selamectina"]}
            ],
            "observacoes_adicionais": "Altamente contagiosa. Isolar o animal e tratar todos os pets da casa."
        },
        {
            "nome_praga": "Sarna Demodécica",
            "tipo_praga": "Ácaro",
            "especies_alvo": ["Cão"],
            "transmissor_de_doencas": [],
            "sintomas_no_animal": ["Queda de pelo localizada", "Pele escamosa", "Infecções bacterianas secundárias"],
            "medicamentos_de_combate": [
                {"descricao": "Ivermectina", "principios_ativos": ["Ivermectina"]},
                {"descricao": "Milbemicina", "principios_ativos": ["Milbemicina"]}
            ],
            "observacoes_adicionais": "Não é contagiosa. Relacionada à imunidade baixa."
        },
    ]
    
    for ectoparasite_data in ectoparasites_data:
        ectoparasite = Ectoparasite(**ectoparasite_data)
        session.add(ectoparasite)
    
    await session.flush()
    logger.info(f"Inseridos {len(ectoparasites_data)} ectoparasitas")
    return len(ectoparasites_data)


async def seed_vermifugos(session: AsyncSession) -> int:
    """Seed de vermífugos/endoparasitas"""
    
    # Verifica se já existem vermífugos
    result = await session.execute(select(Vermifugo).limit(1))
    if result.scalar_one_or_none():
        logger.info("Vermífugos já existem, pulando seed...")
        return 0
    
    vermifugos_data = [
        {
            "nome_praga": "Ascaris (Lombriga)",
            "tipo_praga": "Nematódeo",
            "especies_alvo": ["Cão", "Gato"],
            "sintomas_no_animal": ["Barriga inchada", "Vômito", "Diarreia", "Pelo opaco", "Perda de peso"],
            "medicamentos_de_combate": [
                {"descricao": "Pamoato de Pirantel", "principios_ativos": ["Pamoato de Pirantel"]},
                {"descricao": "Fenbendazol", "principios_ativos": ["Fenbendazol"]}
            ],
            "observacoes_adicionais": "Muito comum em filhotes. Vermifugar a partir de 2 semanas de vida."
        },
        {
            "nome_praga": "Ancilostoma (Bicho Geográfico)",
            "tipo_praga": "Nematódeo",
            "especies_alvo": ["Cão", "Gato"],
            "sintomas_no_animal": ["Anemia", "Diarreia com sangue", "Fraqueza", "Perda de peso"],
            "medicamentos_de_combate": [
                {"descricao": "Pamoato de Pirantel", "principios_ativos": ["Pamoato de Pirantel"]},
                {"descricao": "Fenbendazol", "principios_ativos": ["Fenbendazol"]}
            ],
            "observacoes_adicionais": "Pode infectar humanos através da pele. Recolher fezes dos animais."
        },
        {
            "nome_praga": "Dipylidium (Tênia)",
            "tipo_praga": "Cestódeo",
            "especies_alvo": ["Cão", "Gato"],
            "sintomas_no_animal": ["Prurido anal", "Arrastar o traseiro", "Segmentos nas fezes (parecem grãos de arroz)"],
            "medicamentos_de_combate": [
                {"descricao": "Praziquantel", "principios_ativos": ["Praziquantel"]}
            ],
            "observacoes_adicionais": "Transmitido por pulgas. Controlar pulgas para prevenir reinfestação."
        },
        {
            "nome_praga": "Giárdia",
            "tipo_praga": "Protozoário",
            "especies_alvo": ["Cão", "Gato"],
            "sintomas_no_animal": ["Diarreia crônica", "Fezes pastosas e fétidas", "Perda de peso", "Desidratação"],
            "medicamentos_de_combate": [
                {"descricao": "Metronidazol", "principios_ativos": ["Metronidazol"]},
                {"descricao": "Fenbendazol", "principios_ativos": ["Fenbendazol"]}
            ],
            "observacoes_adicionais": "Zoonose. Higienizar bem o ambiente e bebedouros."
        },
        {
            "nome_praga": "Dirofilaria (Verme do Coração)",
            "tipo_praga": "Nematódeo",
            "especies_alvo": ["Cão", "Gato"],
            "sintomas_no_animal": ["Tosse", "Intolerância ao exercício", "Perda de peso", "Insuficiência cardíaca"],
            "medicamentos_de_combate": [
                {"descricao": "Ivermectina (prevenção)", "principios_ativos": ["Ivermectina"]},
                {"descricao": "Selamectina (prevenção)", "principios_ativos": ["Selamectina"]}
            ],
            "observacoes_adicionais": "Transmitido por mosquitos. Prevenção mensal essencial em áreas endêmicas."
        },
    ]
    
    for vermifugo_data in vermifugos_data:
        vermifugo = Vermifugo(**vermifugo_data)
        session.add(vermifugo)
    
    await session.flush()
    logger.info(f"Inseridos {len(vermifugos_data)} vermífugos")
    return len(vermifugos_data)


async def run_all_seeds() -> dict:
    """Executa todos os seeds"""
    logger.info("Iniciando seeds do banco de dados...")
    
    results = {
        "vaccines": 0,
        "ectoparasites": 0,
        "vermifugos": 0,
    }
    
    async with AsyncSessionLocal() as session:
        try:
            results["vaccines"] = await seed_vaccines(session)
            results["ectoparasites"] = await seed_ectoparasites(session)
            results["vermifugos"] = await seed_vermifugos(session)
            
            await session.commit()
            
            total = sum(results.values())
            logger.info(f"Seeds concluídos: {total} registros inseridos")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Erro ao executar seeds: {e}")
            raise
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_seeds())

