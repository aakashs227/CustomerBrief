import re

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    USE_SPACY = True
except ImportError:
    USE_SPACY = False

company_suffixes = [
    'Inc', 'Ltd', 'LLC', 'PLC', 'GmbH', 'Industries', 'AG', 'Corp',
    'Corporation', 'Co', 'Pvt', 'Limited', 'Group', 'S.A.', 'S.A.S.', 'S.L.', 'S.L.U.'
]

# Suffix-based pattern (case insensitive)
suffix_pattern = r'\b([A-Za-z][\w&.\'-]*(?:\s+[A-Za-z][\w&.\'-]*)*\s+(?:' + '|'.join(company_suffixes) + r'))\b'

# Capitalized phrase pattern (case insensitive)
capitalized_pattern = r'\b(?:[A-Za-z][a-zA-Z&.\'-]+(?:\s+[A-Za-z][a-zA-Z&.\'-]+){0,3})\b'

def extract_companies(text: str):
    companies = set()

    # 1. From suffix-based regex (case insensitive)
    suffix_matches = re.findall(suffix_pattern, text)
    companies.update([m.strip() for m in suffix_matches if m.strip()])

    # 2. From capitalized word phrases (case insensitive)
    capitalized_matches = re.findall(capitalized_pattern, text)
    companies.update([m.strip() for m in capitalized_matches if m.strip()])

    # 3. From spaCy NER if available
    if USE_SPACY:
        doc = nlp(text)
        ner_matches = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
        companies.update(ner_matches)

    return list(companies)  # Will keep case-sensitive company names intact

# Example of usage
text = "Apple Inc and apple Inc are different companies. Also, Acme Corp and acme corp are distinct."
companies = extract_companies(text)
print(companies)
