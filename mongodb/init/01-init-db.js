// =============================================================================
// Script de Inicialização do MongoDB - Pet Control System
// =============================================================================
// Este script é executado automaticamente na primeira inicialização do MongoDB
// Cria o banco de dados, usuários e configurações iniciais
// =============================================================================

print('🚀 [1/3] Iniciando configuração do banco de dados Pet Control...');

// Conectar ao banco de dados admin para criar usuários
db = db.getSiblingDB('admin');

// Criar usuário root (com tratamento de erro se já existir)
if (process.env.MONGO_INITDB_ROOT_USERNAME && process.env.MONGO_INITDB_ROOT_PASSWORD) {
    try {
        print('📝 Criando usuário root...');
        db.createUser({
            user: process.env.MONGO_INITDB_ROOT_USERNAME,
            pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
            roles: [
                { role: 'root', db: 'admin' },
                { role: 'userAdminAnyDatabase', db: 'admin' }
            ]
        });
        print('✅ Usuário root criado com sucesso!');
    } catch (e) {
        if (e.code === 51003) {  // Código de erro para usuário já existente
            print('⚠️  Usuário root já existe. Continuando...');
        } else {
            print('⚠️  Erro ao criar usuário root: ' + e.message);
        }
    }
}

// Conectar ao banco de dados da aplicação
db = db.getSiblingDB('pet_control');

print('📝 Criando usuário da aplicação...');

// Criar usuário específico para a aplicação (com permissões limitadas)
try {
    db.createUser({
        user: 'pet_control_user',
        pwd: process.env.MONGO_APP_PASSWORD || 'pet_control_password_change_me',
        roles: [
            {
                role: 'readWrite',
                db: 'pet_control'
            },
            {
                role: 'dbAdmin',
                db: 'pet_control'
            }
        ]
    });
    print('✅ Usuário da aplicação criado: pet_control_user');
} catch (e) {
    print('⚠️  Usuário da aplicação já existe ou erro: ' + e.message);
}

// Criar coleções com validações
print('📝 Criando coleções com validações...');

// Coleção de Profiles (usuários/tutores)
db.createCollection('profiles', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['email', 'name'],
            properties: {
                email: {
                    bsonType: 'string',
                    pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
                    description: 'Email deve ser válido'
                },
                name: {
                    bsonType: 'string',
                    minLength: 2,
                    description: 'Nome é obrigatório'
                },
                bio: {
                    bsonType: ['string', 'null'],
                    description: 'Biografia do usuário'
                },
                phone: {
                    bsonType: ['string', 'null']
                },
                address: {
                    bsonType: ['object', 'null'],
                    properties: {
                        street: {
                            bsonType: ['string', 'null']
                        },
                        city: {
                            bsonType: ['string', 'null']
                        },
                        state: {
                            bsonType: ['string', 'null']
                        },
                        zip: {
                            bsonType: ['string', 'null']
                        }
                    }
                },
                is_vet: {
                    bsonType: 'bool',
                    description: 'Indica se o usuário é veterinário'
                },
                deleted_at: {
                    bsonType: ['date', 'null']
                }
            }
        }
    }
});
print('✅ Coleção profiles criada');

// Coleção de Pets
db.createCollection('pets', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['name', 'users'],
            properties: {
                name: {
                    bsonType: 'string',
                    minLength: 1,
                    description: 'Nome do pet é obrigatório'
                },
                nickname: {
                    bsonType: ['string', 'null']
                },
                species: {
                    bsonType: ['string', 'null'],
                    enum: ['Cão', 'Gato', 'Pássaro', 'Outro', null]
                },
                breed: {
                    bsonType: ['string', 'null']
                },
                birth_date: {
                    bsonType: ['string', 'null'],
                    description: 'Data de nascimento (formato: YYYY-MM-DD)'
                },
                color: {
                    bsonType: ['string', 'null'],
                    description: 'Cor do pet'
                },
                weight: {
                    bsonType: ['number', 'null'],
                    description: 'Peso do pet em kg'
                },
                users: {
                    bsonType: 'array',
                    minItems: 1,
                    items: {
                        bsonType: ['objectId', 'string']
                    },
                    description: 'Pelo menos um tutor é obrigatório'
                },
                treatments: {
                    bsonType: ['array', 'null'],
                    items: {
                        bsonType: 'object',
                        required: ['name', 'date'],
                        properties: {
                            _id: { 
                                bsonType: ['objectId', 'null']
                            },
                            name: { 
                                bsonType: 'string' 
                            },
                            date: { 
                                bsonType: 'string' 
                            },
                            time: {
                                bsonType: ['string', 'null']
                            },
                            done: { 
                                bsonType: 'bool' 
                            },
                            category: { 
                                bsonType: ['string', 'null'] 
                            },
                            description: {
                                bsonType: ['string', 'null']
                            },
                            applier_type: {
                                bsonType: ['string', 'null']
                            },
                            applier_name: {
                                bsonType: ['string', 'null']
                            }
                        }
                    }
                },
                deleted_at: {
                    bsonType: ['date', 'null']
                },
                created_at: {
                    bsonType: ['date', 'null']
                }
            }
        }
    }
});
print('✅ Coleção pets criada');

// Coleção de Vacinas (Informações gerais sobre vacinas)
db.createCollection('vacinas', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['nome_vacina', 'especie_alvo', 'tipo_vacina'],
            properties: {
                nome_vacina: {
                    bsonType: 'string',
                    description: 'Nome da vacina é obrigatório'
                },
                especie_alvo: {
                    bsonType: 'string',
                    description: 'Espécie alvo da vacina (Cão, Gato, etc)'
                },
                tipo_vacina: {
                    bsonType: 'string',
                    description: 'Tipo da vacina (Polivalente, Obrigatória, Recomendada)'
                },
                descricao: {
                    bsonType: ['string', 'null']
                },
                protege_contra: {
                    bsonType: ['array', 'null'],
                    items: {
                        bsonType: 'string'
                    },
                    description: 'Lista de doenças contra as quais a vacina protege'
                },
                idade_recomendada: {
                    bsonType: ['string', 'null']
                },
                reforco: {
                    bsonType: ['string', 'null']
                },
                observacoes: {
                    bsonType: ['string', 'null']
                }
            }
        }
    }
});
print('✅ Coleção vacinas criada');

// Coleção de Ectoparasitas (Informações gerais sobre ectoparasitas)
db.createCollection('ectoparasitas', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['nome_praga', 'tipo_praga', 'especies_alvo'],
            properties: {
                nome_praga: {
                    bsonType: 'string',
                    description: 'Nome da praga é obrigatório'
                },
                tipo_praga: {
                    bsonType: 'string',
                    description: 'Tipo da praga (Inseto, Ácaro, etc)'
                },
                especies_alvo: {
                    bsonType: 'array',
                    items: {
                        bsonType: 'string'
                    },
                    description: 'Espécies afetadas pela praga'
                },
                transmissor_de_doencas: {
                    bsonType: ['array', 'null'],
                    items: {
                        bsonType: 'string'
                    },
                    description: 'Doenças transmitidas pela praga'
                },
                sintomas_no_animal: {
                    bsonType: ['array', 'null'],
                    items: {
                        bsonType: 'string'
                    },
                    description: 'Sintomas causados no animal'
                },
                medicamentos_de_combate: {
                    bsonType: ['array', 'null'],
                    items: {
                        bsonType: 'object',
                        properties: {
                            descricao: { bsonType: 'string' },
                            principios_ativos: {
                                bsonType: 'array',
                                items: { bsonType: 'string' }
                            }
                        }
                    },
                    description: 'Medicamentos usados no combate'
                },
                observacoes_adicionais: {
                    bsonType: ['string', 'null']
                }
            }
        }
    }
});
print('✅ Coleção ectoparasitas criada');

// Coleção de Vermífugos (Informações gerais sobre vermífugos)
// Estrutura: documento único contendo array de parasitas
db.createCollection('vermifugos', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['parasitas_e_tratamentos'],
            properties: {
                parasitas_e_tratamentos: {
                    bsonType: 'array',
                    items: {
                        bsonType: 'object',
                        required: ['nome_praga', 'tipo_praga', 'especies_alvo'],
                        properties: {
                            nome_praga: {
                                bsonType: 'string',
                                description: 'Nome do parasita'
                            },
                            tipo_praga: {
                                bsonType: 'string',
                                description: 'Tipo do parasita (Nematódeo, Cestódeo, etc)'
                            },
                            especies_alvo: {
                                bsonType: 'array',
                                items: {
                                    bsonType: 'string'
                                },
                                description: 'Espécies afetadas'
                            },
                            sintomas_no_animal: {
                                bsonType: ['array', 'null'],
                                items: {
                                    bsonType: 'string'
                                },
                                description: 'Sintomas causados'
                            },
                            medicamentos_de_combate: {
                                bsonType: ['array', 'null'],
                                items: {
                                    bsonType: 'object',
                                    properties: {
                                        descricao: { bsonType: 'string' },
                                        principios_ativos: {
                                            bsonType: 'array',
                                            items: { bsonType: 'string' }
                                        }
                                    }
                                },
                                description: 'Medicamentos usados no combate'
                            },
                            observacoes_adicionais: {
                                bsonType: ['string', 'null']
                            }
                        }
                    },
                    description: 'Lista de parasitas internos e seus tratamentos'
                }
            }
        }
    }
});
print('✅ Coleção vermifugos criada');

print('✅ [1/3] Inicialização do banco de dados concluída!');
print('');

