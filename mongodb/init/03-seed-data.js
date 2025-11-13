// =============================================================================
// Dados Iniciais (Seed) - Pet Control System
// =============================================================================
// Este script insere dados de exemplo para testes e desenvolvimento
// Em produção, este script pode ser removido ou ajustado
// =============================================================================

print('🚀 [3/3] Inserindo dados de exemplo (seed data)...');

// Conectar ao banco de dados
db = db.getSiblingDB('pet_control');

// Verificar se já existem dados
const existingProfiles = db.profiles.countDocuments();
if (existingProfiles > 0) {
    print('⚠️  Banco já contém dados. Pulando seed...');
    print('');
} else {
    print('📝 Inserindo dados de exemplo...');

    // =============================================================================
    // PROFILES (Tutores/Usuários)
    // =============================================================================
    const profiles = [
        {
            _id: ObjectId('507f1f77bcf86cd799439011'),
            email: 'maria.silva@email.com',
            name: 'Maria Silva',
            bio: 'Tutora dedicada de pets, apaixonada por animais',
            phone: '(11) 98765-4321',
            address: {
                street: 'Rua das Flores, 123',
                city: 'São Paulo',
                state: 'SP',
                zip: '01310-100'
            },
            is_vet: false,
            deleted_at: null,
            created_at: new Date()
        },
        {
            _id: ObjectId('507f1f77bcf86cd799439012'),
            email: 'joao.santos@email.com',
            name: 'João Santos',
            bio: 'Veterinário especializado em animais de companhia',
            phone: '(21) 99876-5432',
            address: {
                street: 'Av. Brasil, 456',
                city: 'Rio de Janeiro',
                state: 'RJ',
                zip: '21040-361'
            },
            is_vet: true,
            deleted_at: null,
            created_at: new Date()
        },
        {
            _id: ObjectId('507f1f77bcf86cd799439013'),
            email: 'ana.costa@email.com',
            name: 'Ana Costa',
            bio: 'Protetora de animais e ativista pelos direitos dos pets',
            phone: '(31) 97654-3210',
            address: {
                street: 'Praça da Liberdade, 789',
                city: 'Belo Horizonte',
                state: 'MG',
                zip: '30140-010'
            },
            is_vet: false,
            deleted_at: null,
            created_at: new Date()
        }
    ];

    db.profiles.insertMany(profiles);
    print('  ✅ ' + profiles.length + ' perfis inseridos');

    // =============================================================================
    // PETS
    // =============================================================================
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];

    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const nextWeekStr = nextWeek.toISOString().split('T')[0];

    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];

    const pets = [
        {
            _id: ObjectId('507f1f77bcf86cd799439021'),
            name: 'Rex',
            nickname: 'Rexinho',
            species: 'Cão',
            breed: 'Labrador',
            birth_date: '2020-03-15',
            color: 'Dourado',
            weight: 28.5,
            users: [ObjectId('507f1f77bcf86cd799439011')],
            treatments: [
                {
                    _id: ObjectId(),
                    name: 'Consulta de rotina',
                    category: 'Consulta',
                    description: 'Check-up anual',
                    date: tomorrowStr,
                    time: '10:00',
                    done: false,
                    applier_type: 'Veterinário',
                    applier_name: 'Dr. Carlos Mendes'
                },
                {
                    _id: ObjectId(),
                    name: 'Banho e tosa',
                    category: 'Higiene',
                    description: 'Tosa verão',
                    date: nextWeekStr,
                    time: '14:00',
                    done: false,
                    applier_type: 'Pet Shop'
                }
            ],
            deleted_at: null,
            created_at: new Date()
        },
        {
            _id: ObjectId('507f1f77bcf86cd799439022'),
            name: 'Luna',
            nickname: 'Luninha',
            species: 'Gato',
            breed: 'Siamês',
            birth_date: '2021-07-20',
            color: 'Creme',
            weight: 4.2,
            users: [ObjectId('507f1f77bcf86cd799439012')],
            treatments: [
                {
                    _id: ObjectId(),
                    name: 'Vacinação antirrábica',
                    category: 'Vacina',
                    description: 'Vacina anual obrigatória',
                    date: yesterdayStr,
                    time: '09:00',
                    done: false,
                    applier_type: 'Veterinário',
                    applier_name: 'Dra. Fernanda Lima'
                }
            ],
            deleted_at: null,
            created_at: new Date()
        },
        {
            _id: ObjectId('507f1f77bcf86cd799439023'),
            name: 'Bob',
            nickname: 'Bobby',
            species: 'Cão',
            breed: 'Poodle',
            birth_date: '2019-11-10',
            color: 'Branco',
            weight: 6.8,
            users: [
                ObjectId('507f1f77bcf86cd799439011'),
                ObjectId('507f1f77bcf86cd799439013')
            ],
            treatments: [],
            deleted_at: null,
            created_at: new Date()
        }
    ];

    db.pets.insertMany(pets);
    print('  ✅ ' + pets.length + ' pets inseridos');

    print('');
    print('✅ [3/3] Dados de exemplo inseridos com sucesso!');
    print('');
    print('📊 Resumo dos dados:');
    print('  - Profiles: ' + db.profiles.countDocuments() + ' documentos');
    print('  - Pets: ' + db.pets.countDocuments() + ' documentos');
    print('');
}

print('🎉 Configuração do MongoDB concluída!');
print('');
print('📝 Credenciais padrão:');
print('  Usuário da aplicação: pet_control_user');
print('  Senha padrão: pet_control_password_change_me');
print('  ⚠️  IMPORTANTE: Altere a senha em produção!');
print('');

