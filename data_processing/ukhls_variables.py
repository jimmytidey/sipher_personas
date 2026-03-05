# data_processing/ukhls_variables.py

# --- VARIABLE DICTIONARY & ENGLISH DESCRIPTIONS ---
# These are the base names; the ingestion scripts handle the wave prefix (e.g., o_)
VARIABLE_MAP = {
    # 1. Identity & Socio-Economics
    'pidp': 'Unique Person ID (The "Anchor" for all joins)',
    'age_dv': 'Derived Age (Current age at interview)',
    'sex_dv': 'Gender (1=Male, 2=Female)',
    'hiqual_dv': 'Highest Qualification (1=Degree, 4=A-Level, 9=None)',

    'payn_dv': 'Monthly Net Pay (Total take-home pay)',
    'jbnssec8_dv': 'Social Class (1=Managerial, 7=Routine)',
    'oprlg1': 'Religion',
    'englang': 'English is first language',


    
    # 2. Transport & Movement
    'caruse': 'Has use of car or van',
    'jbpl': 'work location',
    'jbttwt': 'Minutes spent travelling to work',
    'wktrvfar': 'Main mode of transport to work',
    'envhabit8': 'Environmental habit: public transport',
    'urban_dv': 'Settlement Type (1=Urban, 2=Rural)',
    'locserd': 'Standard of local services: Shopping',
    'locserc': 'Standard of public transport',
    'locsere': 'Standard of local services: Leisure',
    'locsera': 'Standard of local services: Schools',
    
    
    
    # 3. Social & Job Detail
    'jbstat': 'Employment Status (2=Employed, 5=Retired, 7=Student)',
    'nbrsnci_dv': "Buckner's Neighbourhood Cohesion Instrument",
    'jlsic07_cc': 'Last job: SIC 2007, condensed)',
    'socialkid': 'Frequency of leisure with child'
  
    
}

# 4. Multi-Response Disability Mapping (Collapsing o_disdif1...96)
DISABILITY_LABELS = {
    '1': 'Mobility', '2': 'Visual', '3': 'Hearing', '4': 'Learning',
    '5': 'Mental Health', '6': 'Manual Dexterity', '7': 'Stamina/Fatigue',
    '8': 'Memory', '9': 'Behavioral', '10': 'Progressive', '11': 'Other', '96': 'Other'
}
