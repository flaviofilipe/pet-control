// =============================================================================
// Dados de Informações - Pet Control System
// =============================================================================
// Este script insere dados informativos sobre vacinas, ectoparasitas e vermífugos
// =============================================================================

print('🚀 [4/4] Inserindo dados informativos (vacinas, ectoparasitas, vermífugos)...');

// Conectar ao banco de dados
db = db.getSiblingDB('pet_control');

// =============================================================================
// VACINAS (Informações sobre tipos de vacinas)
// =============================================================================
const vacinasData = [
  {
    "nome_vacina": "V10",
    "especie_alvo": "Cão",
    "tipo_vacina": "Polivalente",
    "obrigatoria_por_lei": false,
    "descricao": "Vacina polivalente que protege contra 10 doenças caninas graves.",
    "protege_contra": [
      "Cinomose",
      "Parvovirose",
      "Hepatite Infecciosa Canina",
      "Adenovírus Tipo 2",
      "Parainfluenza",
      "Coronavírus",
      "Leptospirose (4 sorovares)"
    ],
    "cronograma_vacinal": {
      "filhote": "Primeira dose: 6-8 semanas (45-60 dias), Segunda dose: 10-12 semanas, Terceira dose: 14-16 semanas",
      "adulto": "Reforço anual após primeira imunização completa"
    },
    "idade_recomendada": "A partir de 45 dias de vida",
    "reforco": "Anual",
    "efeitos_colaterais": [
      "Leve inchaço ou dor no local da aplicação",
      "Febre leve nas primeiras 24-48 horas",
      "Apatia temporária por 1-2 dias",
      "Perda de apetite leve",
      "Reações alérgicas (raras)"
    ],
    "observacoes": "Requer série de 3 doses com intervalo de 21 dias para imunização completa"
  },
  {
    "nome_vacina": "Antirrábica",
    "especie_alvo": "Cão",
    "tipo_vacina": "Obrigatória",
    "obrigatoria_por_lei": true,
    "descricao": "Vacina contra a raiva, doença viral fatal que pode ser transmitida para humanos.",
    "protege_contra": [
      "Raiva"
    ],
    "cronograma_vacinal": {
      "filhote": "Dose única a partir de 4 meses de idade",
      "adulto": "Reforço anual obrigatório"
    },
    "idade_recomendada": "A partir de 4 meses",
    "reforco": "Anual",
    "efeitos_colaterais": [
      "Inchaço no local da aplicação",
      "Febre leve",
      "Letargia por 24-48 horas",
      "Raramente: reações alérgicas graves (anafilaxia)"
    ],
    "observacoes": "Obrigatória por lei em todo território nacional. Campanha gratuita anual."
  },
  {
    "nome_vacina": "V8",
    "especie_alvo": "Cão",
    "tipo_vacina": "Polivalente",
    "obrigatoria_por_lei": false,
    "descricao": "Vacina polivalente que protege contra 8 doenças principais.",
    "protege_contra": [
      "Cinomose",
      "Parvovirose",
      "Hepatite Infecciosa Canina",
      "Adenovírus Tipo 2",
      "Parainfluenza",
      "Coronavírus",
      "Leptospirose (2 sorovares)"
    ],
    "cronograma_vacinal": {
      "filhote": "Primeira dose: 6-8 semanas, Segunda dose: 10-12 semanas, Terceira dose: 14-16 semanas",
      "adulto": "Reforço anual após primeira imunização completa"
    },
    "idade_recomendada": "A partir de 45 dias",
    "reforco": "Anual",
    "efeitos_colaterais": [
      "Dor ou inchaço no local da injeção",
      "Febre baixa",
      "Sonolência por 1-2 dias",
      "Diminuição temporária do apetite",
      "Reações alérgicas (raras)"
    ],
    "observacoes": "Opção mais econômica que a V10, mas com menos proteção contra Leptospirose"
  },
  {
    "nome_vacina": "V4 Felina (Quádruple)",
    "especie_alvo": "Gato",
    "tipo_vacina": "Polivalente",
    "obrigatoria_por_lei": false,
    "descricao": "Vacina polivalente essencial para gatos.",
    "protege_contra": [
      "Panleucopenia Felina",
      "Rinotraqueíte Viral Felina",
      "Calicivirose Felina",
      "Clamidiose Felina"
    ],
    "cronograma_vacinal": {
      "filhote": "Primeira dose: 8-9 semanas (60 dias), Segunda dose: 12 semanas, Terceira dose: 16 semanas",
      "adulto": "Reforço anual"
    },
    "idade_recomendada": "A partir de 60 dias",
    "reforco": "Anual",
    "efeitos_colaterais": [
      "Pequeno nódulo no local da aplicação",
      "Febre leve",
      "Letargia por 24 horas",
      "Espirros temporários (se aplicação intranasal)",
      "Raramente: sarcoma no local da injeção (requer monitoramento)"
    ],
    "observacoes": "Primeira imunização requer 2-3 doses com intervalo de 21-30 dias"
  },
  {
    "nome_vacina": "Antirrábica Felina",
    "especie_alvo": "Gato",
    "tipo_vacina": "Obrigatória",
    "obrigatoria_por_lei": true,
    "descricao": "Vacina contra a raiva para gatos.",
    "protege_contra": [
      "Raiva"
    ],
    "cronograma_vacinal": {
      "filhote": "Dose única a partir de 4 meses de idade",
      "adulto": "Reforço anual obrigatório"
    },
    "idade_recomendada": "A partir de 4 meses",
    "reforco": "Anual",
    "efeitos_colaterais": [
      "Nódulo no local da aplicação (comum em gatos)",
      "Febre leve",
      "Apatia por 1-2 dias",
      "Raramente: reação alérgica",
      "Muito raramente: sarcoma no local (monitorar nódulos persistentes)"
    ],
    "observacoes": "Obrigatória por lei. Pode causar reação local no ponto de aplicação."
  },
  {
    "nome_vacina": "Leucemia Felina (FeLV)",
    "especie_alvo": "Gato",
    "tipo_vacina": "Recomendada",
    "obrigatoria_por_lei": false,
    "descricao": "Vacina contra o vírus da leucemia felina.",
    "protege_contra": [
      "Leucemia Felina (FeLV)"
    ],
    "cronograma_vacinal": {
      "filhote": "Primeira dose: 8 semanas, Segunda dose: 12 semanas",
      "adulto": "Reforço anual para gatos de risco"
    },
    "idade_recomendada": "A partir de 8 semanas",
    "reforco": "Anual",
    "efeitos_colaterais": [
      "Sensibilidade no local da injeção",
      "Febre leve",
      "Letargia temporária",
      "Perda de apetite por 1 dia",
      "Raramente: reações alérgicas"
    ],
    "observacoes": "Recomendada para gatos com acesso externo ou contato com outros gatos. Teste FeLV antes da vacinação."
  },
  {
    "nome_vacina": "Gripe Canina (Tosse dos Canis)",
    "especie_alvo": "Cão",
    "tipo_vacina": "Recomendada",
    "obrigatoria_por_lei": false,
    "descricao": "Vacina contra a traqueobronquite infecciosa canina.",
    "protege_contra": [
      "Bordetella bronchiseptica",
      "Parainfluenza canina"
    ],
    "cronograma_vacinal": {
      "filhote": "Primeira dose: 8 semanas, Segunda dose: 12 semanas",
      "adulto": "Reforço semestral ou anual conforme risco de exposição"
    },
    "idade_recomendada": "A partir de 8 semanas",
    "reforco": "Semestral ou Anual (dependendo do risco)",
    "efeitos_colaterais": [
      "Espirros leves (forma intranasal)",
      "Tosse leve por 2-3 dias",
      "Corrimento nasal discreto",
      "Leve inchaço local (forma injetável)",
      "Raramente: reação alérgica"
    ],
    "observacoes": "Essencial para cães que frequentam creches, hotéis ou parques. Pode ser intranasal ou injetável."
  },
  {
    "nome_vacina": "Giardíase",
    "especie_alvo": "Cão",
    "tipo_vacina": "Recomendada",
    "obrigatoria_por_lei": false,
    "descricao": "Vacina contra o protozoário Giardia.",
    "protege_contra": [
      "Giardíase"
    ],
    "cronograma_vacinal": {
      "filhote": "Primeira dose: 8 semanas, Segunda dose: 12 semanas",
      "adulto": "Reforço anual"
    },
    "idade_recomendada": "A partir de 8 semanas",
    "reforco": "Anual",
    "efeitos_colaterais": [
      "Dor leve no local da aplicação",
      "Febre baixa",
      "Apatia por 24 horas",
      "Vômito leve (raro)",
      "Diarreia leve e temporária (raro)"
    ],
    "observacoes": "Recomendada para cães em ambientes com alto risco de contaminação (canis, abrigos)."
  }
];

const existingVacinas = db.vacinas.countDocuments();
if (existingVacinas > 0) {
    print('⚠️  Vacinas já existem. Pulando...');
} else {
    db.vacinas.insertMany(vacinasData);
    print('  ✅ ' + vacinasData.length + ' vacinas inseridas');
}

// =============================================================================
// ECTOPARASITAS (Informações sobre pragas externas)
// =============================================================================
const ectoparasitasData = [
  {
    "nome_praga": "Pulgas",
    "tipo_praga": "Inseto",
    "especies_alvo": [
      "Cão",
      "Gato"
    ],
    "transmissor_de_doencas": [
      "Dipilidiose (verme Dipylidium caninum)",
      "Dermatite alérgica",
      "Anemia (em infestações graves)"
    ],
    "sintomas_no_animal": [
      "Coceira intensa",
      "Lambedura excessiva",
      "Perda de pelos",
      "Feridas na pele",
      "Inquietação"
    ],
    "medicamentos_de_combate": [
      {
        "descricao": "Comprimidos mastigáveis mensais",
        "principios_ativos": [
          "Afoxolaner",
          "Fluralaner",
          "Sarolaner"
        ]
      },
      {
        "descricao": "Pipetas spot-on (tópico)",
        "principios_ativos": [
          "Fipronil",
          "Selamectina",
          "Imidaclopride"
        ]
      }
    ],
    "observacoes_adicionais": "Tratar ambiente (casa, camas) é essencial. Pulgas adultas representam apenas 5% da população."
  },
  {
    "nome_praga": "Carrapatos",
    "tipo_praga": "Ácaro",
    "especies_alvo": [
      "Cão",
      "Gato"
    ],
    "transmissor_de_doencas": [
      "Erliquiose",
      "Babesiose",
      "Doença de Lyme",
      "Febre maculosa"
    ],
    "sintomas_no_animal": [
      "Febre",
      "Letargia",
      "Perda de apetite",
      "Manchas vermelhas na pele",
      "Anemia",
      "Problemas de coagulação"
    ],
    "medicamentos_de_combate": [
      {
        "descricao": "Comprimidos mastigáveis",
        "principios_ativos": [
          "Afoxolaner",
          "Fluralaner",
          "Sarolaner"
        ]
      },
      {
        "descricao": "Coleiras antiparasitárias",
        "principios_ativos": [
          "Deltametrina",
          "Flumetrina"
        ]
      }
    ],
    "observacoes_adicionais": "Verificar diariamente após passeios. Remover carrapatos com pinça apropriada. Doenças podem ser graves."
  },
  {
    "nome_praga": "Sarnas (Ácaros da Sarna)",
    "tipo_praga": "Ácaro",
    "especies_alvo": [
      "Cão",
      "Gato"
    ],
    "transmissor_de_doencas": [
      "Sarna Sarcóptica (Scabies)",
      "Sarna Demodécica",
      "Sarna Otodécica (orelhas)"
    ],
    "sintomas_no_animal": [
      "Coceira extrema",
      "Perda de pelos (especialmente em orelhas, cotovelos, abdômen)",
      "Crostas e feridas",
      "Espessamento da pele",
      "Odor desagradável"
    ],
    "medicamentos_de_combate": [
      {
        "descricao": "Antiparasitários sistêmicos",
        "principios_ativos": [
          "Ivermectina",
          "Selamectina",
          "Moxidectina"
        ]
      },
      {
        "descricao": "Banhos medicamentosos",
        "principios_ativos": [
          "Peróxido de benzoíla",
          "Amitraz"
        ]
      }
    ],
    "observacoes_adicionais": "Altamente contagiosa entre animais. Pode afetar humanos (sarna sarcóptica). Tratamento pode ser longo."
  },
  {
    "nome_praga": "Piolhos",
    "tipo_praga": "Inseto",
    "especies_alvo": [
      "Cão",
      "Gato"
    ],
    "transmissor_de_doencas": [
      "Anemia (em casos graves)",
      "Estresse",
      "Infecções secundárias por coceira"
    ],
    "sintomas_no_animal": [
      "Coceira",
      "Pelos opacos e emaranhados",
      "Pequenos pontos brancos (lêndeas) grudados nos pelos",
      "Inquietação",
      "Perda de pelos"
    ],
    "medicamentos_de_combate": [
      {
        "descricao": "Shampoos antiparasitários",
        "principios_ativos": [
          "Permetrina",
          "Piretrina"
        ]
      },
      {
        "descricao": "Spot-on tópico",
        "principios_ativos": [
          "Fipronil",
          "Selamectina"
        ]
      }
    ],
    "observacoes_adicionais": "Menos comum que pulgas. Transmissão por contato direto. Escovar para remover lêndeas."
  }
];

const existingEcto = db.ectoparasitas.countDocuments();
if (existingEcto > 0) {
    print('⚠️  Ectoparasitas já existem. Pulando...');
} else {
    db.ectoparasitas.insertMany(ectoparasitasData);
    print('  ✅ ' + ectoparasitasData.length + ' ectoparasitas inseridos');
}

// =============================================================================
// VERMÍFUGOS (Informações sobre parasitas internos)
// =============================================================================
const vermifugosData = [
  {
    "parasitas_e_tratamentos": [
      {
        "nome_praga": "Ancilostomose (Ancylostoma)",
        "tipo_praga": "Nematódeo (verme redondo)",
        "especies_alvo": [
          "Cão",
          "Gato"
        ],
        "sintomas_no_animal": [
          "Diarreia com sangue",
          "Anemia",
          "Fraqueza",
          "Perda de peso",
          "Pelo opaco"
        ],
        "medicamentos_de_combate": [
          {
            "descricao": "Vermífugos de amplo espectro",
            "principios_ativos": [
              "Pamoato de pirantel",
              "Fenbendazol",
              "Milbemicina oxima"
            ]
          }
        ],
        "observacoes_adicionais": "Transmissão por solo contaminado. Pode penetrar pela pele. Zoonose (afeta humanos)."
      },
      {
        "nome_praga": "Ascaridíase (Toxocara)",
        "tipo_praga": "Nematódeo (verme redondo)",
        "especies_alvo": [
          "Cão",
          "Gato"
        ],
        "sintomas_no_animal": [
          "Abdômen distendido (barriga inchada)",
          "Vômitos",
          "Diarreia",
          "Perda de peso",
          "Pelos opacos",
          "Tosse (migração larval)"
        ],
        "medicamentos_de_combate": [
          {
            "descricao": "Vermífugos comuns",
            "principios_ativos": [
              "Pamoato de pirantel",
              "Praziquantel",
              "Fenbendazol"
            ]
          }
        ],
        "observacoes_adicionais": "Muito comum em filhotes. Transmissão fecal-oral. Zoonose importante (Larva Migrans Visceral em crianças)."
      },
      {
        "nome_praga": "Tênia (Dipylidium caninum)",
        "tipo_praga": "Cestódeo (verme chato)",
        "especies_alvo": [
          "Cão",
          "Gato"
        ],
        "sintomas_no_animal": [
          "Arrastar o traseiro no chão",
          "Prurido anal",
          "Segmentos de verme nas fezes (parecem grãos de arroz)",
          "Perda de peso",
          "Aumento do apetite"
        ],
        "medicamentos_de_combate": [
          {
            "descricao": "Vermífugos específicos para cestódeos",
            "principios_ativos": [
              "Praziquantel",
              "Epsiprantel"
            ]
          }
        ],
        "observacoes_adicionais": "Transmitida por pulgas infectadas. Tratar pulgas simultaneamente. Raro em humanos."
      },
      {
        "nome_praga": "Giardíase (Giardia)",
        "tipo_praga": "Protozoário",
        "especies_alvo": [
          "Cão",
          "Gato"
        ],
        "sintomas_no_animal": [
          "Diarreia aguda ou crônica",
          "Fezes pastosas, amareladas e com mau cheiro",
          "Vômitos",
          "Perda de peso",
          "Desidratação"
        ],
        "medicamentos_de_combate": [
          {
            "descricao": "Antiprotozoários",
            "principios_ativos": [
              "Metronidazol",
              "Fenbendazol",
              "Secnidazol"
            ]
          }
        ],
        "observacoes_adicionais": "Transmissão por água contaminada. Pode ser resistente ao tratamento. Zoonose (afeta humanos)."
      },
      {
        "nome_praga": "Dirofilariose (Verme do Coração)",
        "tipo_praga": "Nematódeo (verme filarial)",
        "especies_alvo": [
          "Cão"
        ],
        "sintomas_no_animal": [
          "Tosse crônica",
          "Dificuldade respiratória",
          "Cansaço fácil",
          "Perda de peso",
          "Ascite (líquido no abdômen)",
          "Insuficiência cardíaca"
        ],
        "medicamentos_de_combate": [
          {
            "descricao": "Prevenção mensal",
            "principios_ativos": [
              "Ivermectina",
              "Milbemicina oxima",
              "Moxidectina"
            ]
          },
          {
            "descricao": "Tratamento adulticida (veterinário)",
            "principios_ativos": [
              "Melarsomina"
            ]
          }
        ],
        "observacoes_adicionais": "Transmitida por mosquitos. Prevenção é essencial. Tratamento é caro e arriscado. Teste anual recomendado."
      }
    ]
  }
];

const existingVerm = db.vermifugos.countDocuments();
if (existingVerm > 0) {
    print('⚠️  Vermífugos já existem. Pulando...');
} else {
    db.vermifugos.insertMany(vermifugosData);
    print('  ✅ ' + vermifugosData.length + ' documento de vermífugos inserido');
}

print('');
print('✅ [4/4] Dados informativos inseridos com sucesso!');
print('');
print('📊 Resumo dos dados informativos:');
print('  - Vacinas: ' + db.vacinas.countDocuments() + ' documentos');
print('  - Ectoparasitas: ' + db.ectoparasitas.countDocuments() + ' documentos');
print('  - Vermífugos: ' + db.vermifugos.countDocuments() + ' documentos');
print('');

