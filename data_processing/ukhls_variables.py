# data_processing/ukhls_variables.py

# --- VARIABLE DICTIONARY & ENGLISH DESCRIPTIONS ---
# These are the base names; the ingestion scripts handle the wave prefix (e.g., o_)
VARIABLE_MAP = {
    # 0. Anchors & Processing
    'pidp': 'Unique Person ID (The "Anchor" for all joins)',
    'disdif': 'Disability indicator prefix (multi-response 1-96) - turned into one-hot memory/mobility/etc.',
    'oprlg1': 'Religion', # 1=No religion, 2=Christian, 3=Buddhist, 4=Hindu, 5=Jewish, 6=Muslim, 7=Sikh, 8=Other
    
    # 1. Clustering Variables (Core Demographics)
    'age_dv': 'Derived Age (Current age at interview)',
    'sex_dv': 'Gender (1=Male, 2=Female)', # 1=Male, 2=Female
    'englang': 'English is first language', # turned into binary englang_binary in feature engineering step (2=No/False, All other=True)
    
    # 2. Clustering Variables (Socioeconomic & Education)
    'hiqual_dv': 'Highest Qualification (1=Degree, 4=A-Level, 9=None)', # 1=Degree, 2=Other Higher, 3=A-Level, 4=GCSE, 5=Other, 9=None
    'payn_dv': 'Monthly Net Pay (Total take-home pay)',
    'jbnssec8_dv': 'Social Class (1=Managerial, 7=Routine)', # 1=Higher managerial, 2=Lower managerial, 3=Intermediate, 4=Small employers, 5=Lower supervisory, 6=Semi-routine, 7=Routine
    'fimngrs_dv': 'Total monthly personal income gross',

    # 3. Clustering Variables (Household & Environment)
    'hhsize': 'Household Size',
    'nchild_dv': 'Number of children in household',
    'urban_dv': 'Settlement Type (1=Urban, 2=Rural)', # 1=Urban, 2=Rural
    
    # 4. Clustering Variables (Health & Wellbeing)
    'sf12mcs_dv': 'Mental Health Score (SF-12 MCS)',
    'sf12pcs_dv': 'Physical Health Score (SF-12 PCS)',

    # 5. Clustering Variables (Community & Local Services)
    'nbrsnci_dv': "Buckner Neighbourhood Cohesion Index",
    'locserd': 'Standard of local services: Shopping', # 1=Excellent, 2=Good, 3=Fair, 4=Poor, 5=Very Poor/Bad
    'locserc': 'Standard of public transport', # 1=Excellent, 2=Good, 3=Fair, 4=Poor, 5=Very Poor/Bad
    'locsere': 'Standard of local services: Leisure', # 1=Excellent, 2=Good, 3=Fair, 4=Poor, 5=Very Poor/Bad
    'locsera': 'Standard of local services: Schools',
    
    # 6. Clustering Variables (Transport Habits)
    'jbttwt': 'Minutes spent travelling to work',
    'envhabit8': 'Environmental habit: public transport', # 1=Always, 2=Very often, 3=Quite often, 4=Not very often, 5=Never
    'carmiles': 'Miles driven in last 12 months',

    # 7. Additional Features (Transport & Movement)
    'caruse': 'Has use of car or van',
    'jbpl': 'work location', # turned into binary work_at_home in feature engineering step (1=Work from home)
    'wktrvfar': 'Main mode of transport to work', # turned into binary drive_to_work in feature engineering step (1=Drive myself by car or van)

    # 8. Additional Features (Social & Job Detail)
    'jbstat': 'Employment Status (2=Employed, 5=Retired, 7=Student)',
    'jlsic07_cc': 'Last job: SIC 2007, condensed', # too detailed for now
    'socialkid': 'Frequency of leisure with child', # too detailed for now
    
    # 9. Target Binary Classification States
    'alljbstat7': 'Full-time student', # 1=Yes, 0/missing=No
    'alljbstat8': 'LT sick/disabled', # 1=Yes, 0/missing=No
    'alljbstat4': 'Retired', # 1=Yes, 0/missing=No
    'alljbstat3': 'Unemployed', # 1=Yes, 0/missing=No
    'alljbstat2': 'Employed' # 1=Yes, 0/missing=No
}

# 4. Multi-Response Disability Mapping (Collapsing o_disdif1...96)
DISABILITY_LABELS = {
    '1': 'Mobility', '2': 'Visual', '3': 'Hearing', '4': 'Learning',
    '5': 'Mental Health', '6': 'Manual Dexterity', '7': 'Stamina/Fatigue',
    '8': 'Memory', '9': 'Behavioral', '10': 'Progressive', '11': 'Other', '96': 'Other'
}

# Categorical Value Mappings for translation to plain English
CATEGORY_MAPS = {
    'sex_dv': {1.0: 'Male', 2.0: 'Female'},
    'englang': {1.0: 'Yes', 2.0: 'No'},
    'englang_binary': {1.0: 'Yes', 0.0: 'No'},
    'oprlg1': {1.0: 'No Religion', 2.0: 'Christian', 3.0: 'Buddhist', 4.0: 'Hindu', 5.0: 'Jewish', 6.0: 'Muslim', 7.0: 'Sikh', 8.0: 'Other'},
    'hiqual_dv': {1.0: 'Degree', 2.0: 'Other Higher', 3.0: 'A-Level', 4.0: 'GCSE', 5.0: 'Other', 9.0: 'None'},
    'urban_dv': {1.0: 'Urban', 2.0: 'Rural'},
    'jbnssec8_dv': {1.0: 'Higher managerial', 2.0: 'Lower managerial', 3.0: 'Intermediate', 4.0: 'Small employers', 5.0: 'Lower supervisory', 6.0: 'Semi-routine', 7.0: 'Routine'},
    'jbpl': {1.0: 'At home', 2.0: 'Employer premises', 3.0: 'Driving/travel', 4.0: 'Various'},
    'work_at_home': {1.0: 'Yes', 0.0: 'No'},
    'drive_to_work': {1.0: 'Yes', 0.0: 'No'},
    'locserc': {1.0: 'Excellent', 2.0: 'Good', 3.0: 'Fair', 4.0: 'Poor', 5.0: 'Very Poor/Bad'},
    'locserd': {1.0: 'Excellent', 2.0: 'Good', 3.0: 'Fair', 4.0: 'Poor', 5.0: 'Very Poor/Bad'},
    'locsere': {1.0: 'Excellent', 2.0: 'Good', 3.0: 'Fair', 4.0: 'Poor', 5.0: 'Very Poor/Bad'},
    'envhabit8': {1.0: 'Always', 2.0: 'Very often', 3.0: 'Quite often', 4.0: 'Not very often', 5.0: 'Never'},
    'alljbstat7': {1.0: 'Yes', 0.0: 'No'},
    'alljbstat8': {1.0: 'Yes', 0.0: 'No'},
    'alljbstat4': {1.0: 'Yes', 0.0: 'No'},
    'alljbstat3': {1.0: 'Yes', 0.0: 'No'},
    'alljbstat2': {1.0: 'Yes', 0.0: 'No'}
}


