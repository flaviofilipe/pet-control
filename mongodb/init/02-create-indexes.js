// =============================================================================
// Criação de Índices - Pet Control System
// =============================================================================
// Este script cria índices para otimizar queries e garantir constraints únicos
// =============================================================================

print('🚀 [2/3] Criando índices para otimização de performance...');

// Conectar ao banco de dados
db = db.getSiblingDB('pet_control');

// =============================================================================
// ÍNDICES DA COLEÇÃO PROFILES
// =============================================================================
print('📊 Criando índices para profiles...');

// Email único (constraint de unicidade)
db.profiles.createIndex(
    { email: 1 },
    { 
        unique: true, 
        name: 'idx_profiles_email_unique',
        background: true,
        partialFilterExpression: { deleted_at: null }
    }
);
print('  ✅ Índice único no email criado');

// Índice composto para soft delete
db.profiles.createIndex(
    { _id: 1, deleted_at: 1 },
    { 
        name: 'idx_profiles_id_deleted',
        background: true 
    }
);
print('  ✅ Índice de soft delete criado');

// Índice de texto para busca por nome
db.profiles.createIndex(
    { name: 'text', email: 'text' },
    { 
        name: 'idx_profiles_text_search',
        background: true 
    }
);
print('  ✅ Índice de texto criado');

// =============================================================================
// ÍNDICES DA COLEÇÃO PETS
// =============================================================================
print('📊 Criando índices para pets...');

// Índice para buscar pets por tutor
db.pets.createIndex(
    { users: 1 },
    { 
        name: 'idx_pets_users',
        background: true 
    }
);
print('  ✅ Índice de usuários criado');

// Índice de soft delete
db.pets.createIndex(
    { deleted_at: 1 },
    { 
        name: 'idx_pets_deleted',
        background: true 
    }
);
print('  ✅ Índice de soft delete criado');

// Índice composto para buscar pets ativos de um tutor
db.pets.createIndex(
    { users: 1, deleted_at: 1 },
    { 
        name: 'idx_pets_users_deleted',
        background: true 
    }
);
print('  ✅ Índice composto usuários-deleted criado');

// Índice para data de tratamentos
db.pets.createIndex(
    { 'treatments.date': 1 },
    { 
        name: 'idx_pets_treatments_date',
        background: true,
        sparse: true
    }
);
print('  ✅ Índice de data de tratamentos criado');

// Índice composto para tratamentos não concluídos
db.pets.createIndex(
    { 'treatments.done': 1, 'treatments.date': 1 },
    { 
        name: 'idx_pets_treatments_done_date',
        background: true,
        sparse: true
    }
);
print('  ✅ Índice de tratamentos pendentes criado');

// Índice composto para buscar tratamentos ativos
db.pets.createIndex(
    { deleted_at: 1, 'treatments.done': 1, 'treatments.date': 1 },
    { 
        name: 'idx_pets_active_treatments',
        background: true,
        sparse: true
    }
);
print('  ✅ Índice de tratamentos ativos criado');

// Índice de texto para busca por nome e apelido
db.pets.createIndex(
    { name: 'text', nickname: 'text', breed: 'text' },
    { 
        name: 'idx_pets_text_search',
        background: true,
        weights: {
            name: 10,
            nickname: 5,
            breed: 1
        }
    }
);
print('  ✅ Índice de texto criado');

// Índice para espécie
db.pets.createIndex(
    { species: 1 },
    { 
        name: 'idx_pets_species',
        background: true,
        sparse: true
    }
);
print('  ✅ Índice de espécie criado');

// =============================================================================
// ÍNDICES DA COLEÇÃO VACINAS (catálogo de informações)
// =============================================================================
print('📊 Criando índices para vacinas...');

// Índice para buscar vacinas por nome
db.vacinas.createIndex(
    { nome_vacina: 1 },
    { 
        name: 'idx_vacinas_nome',
        background: true 
    }
);
print('  ✅ Índice de nome_vacina criado');

// Índice para buscar por espécie
db.vacinas.createIndex(
    { especie_alvo: 1 },
    { 
        name: 'idx_vacinas_especie',
        background: true 
    }
);
print('  ✅ Índice de espécie criado');

// Índice para buscar por tipo
db.vacinas.createIndex(
    { tipo_vacina: 1 },
    { 
        name: 'idx_vacinas_tipo',
        background: true 
    }
);
print('  ✅ Índice de tipo criado');

// Índice de texto para busca
db.vacinas.createIndex(
    { nome_vacina: 'text', descricao: 'text' },
    { 
        name: 'idx_vacinas_text_search',
        background: true 
    }
);
print('  ✅ Índice de texto criado');

// =============================================================================
// ÍNDICES DA COLEÇÃO ECTOPARASITAS (catálogo de informações)
// =============================================================================
print('📊 Criando índices para ectoparasitas...');

// Índice para buscar por nome da praga
db.ectoparasitas.createIndex(
    { nome_praga: 1 },
    { 
        name: 'idx_ectoparasitas_nome',
        background: true 
    }
);
print('  ✅ Índice de nome_praga criado');

// Índice para buscar por tipo
db.ectoparasitas.createIndex(
    { tipo_praga: 1 },
    { 
        name: 'idx_ectoparasitas_tipo',
        background: true 
    }
);
print('  ✅ Índice de tipo_praga criado');

// Índice para buscar por espécies afetadas
db.ectoparasitas.createIndex(
    { especies_alvo: 1 },
    { 
        name: 'idx_ectoparasitas_especies',
        background: true 
    }
);
print('  ✅ Índice de especies_alvo criado');

// Índice de texto para busca
db.ectoparasitas.createIndex(
    { nome_praga: 'text', observacoes_adicionais: 'text' },
    { 
        name: 'idx_ectoparasitas_text_search',
        background: true 
    }
);
print('  ✅ Índice de texto criado');

// =============================================================================
// ÍNDICES DA COLEÇÃO VERMIFUGOS (catálogo de informações)
// =============================================================================
print('📊 Criando índices para vermifugos...');

// Índice para buscar dentro do array de parasitas por nome
db.vermifugos.createIndex(
    { 'parasitas_e_tratamentos.nome_praga': 1 },
    { 
        name: 'idx_vermifugos_nome_praga',
        background: true 
    }
);
print('  ✅ Índice de nome_praga criado');

// Índice para buscar dentro do array por tipo
db.vermifugos.createIndex(
    { 'parasitas_e_tratamentos.tipo_praga': 1 },
    { 
        name: 'idx_vermifugos_tipo_praga',
        background: true 
    }
);
print('  ✅ Índice de tipo_praga criado');

// Índice para buscar dentro do array por espécies
db.vermifugos.createIndex(
    { 'parasitas_e_tratamentos.especies_alvo': 1 },
    { 
        name: 'idx_vermifugos_especies',
        background: true 
    }
);
print('  ✅ Índice de especies_alvo criado');

// =============================================================================
// RESUMO
// =============================================================================
print('');
print('✅ [2/3] Todos os índices foram criados com sucesso!');
print('');
print('📊 Resumo dos índices:');
print('  - Profiles: ' + db.profiles.getIndexes().length + ' índices');
print('  - Pets: ' + db.pets.getIndexes().length + ' índices');
print('  - Vacinas: ' + db.vacinas.getIndexes().length + ' índices');
print('  - Ectoparasitas: ' + db.ectoparasitas.getIndexes().length + ' índices');
print('  - Vermífugos: ' + db.vermifugos.getIndexes().length + ' índices');
print('');

