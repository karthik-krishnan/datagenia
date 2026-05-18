"""
Prompts for context_extractor.py — extract structured schema/generation requirements
from a user's free-form natural language description.

Usage:
    from prompts.extraction import SYSTEM, TEMPLATE
    prompt = TEMPLATE.format(context=truncated_text)
    raw = llm_provider.generate(prompt, SYSTEM)
"""

SYSTEM = (
    "You are a test data schema analyst. Extract structured generation requirements "
    "from the user's natural language description. Return ONLY valid JSON, no explanation."
)

TEMPLATE = """Extract structured test data generation requirements from this request:

\"{context}\"

Return a JSON object with EXACTLY this structure (use null for missing values):
{{
  "volume": <integer or null>,
  "entity_type": "<primary entity name, snake_case plural, e.g. users, orders, patients>",
  "tables": [
    {{
      "name": "<snake_case plural table name>",
      "is_root": <true|false>,
      "columns": [
        {{
          "name": "<snake_case field name>",
          "type": "<string|integer|float|date|email|phone|boolean|enum>",
          "enum_values": ["<val1>", "<val2>"]
        }}
      ]
    }}
  ],
  "relationships": [
    {{
      "source_table": "<parent_table_name>",
      "source_column": "<PK column in source table, e.g. id or user_id>",
      "target_table": "<child_table_name>",
      "target_column": "<FK column in target table, e.g. user_id>",
      "cardinality": "one_to_many",
      "per_parent_min": <integer or null>,
      "per_parent_max": <integer or null>
    }}
  ],
  "columns": [
    {{
      "name": "<snake_case field name>",
      "type": "<string|integer|float|date|email|phone|boolean|enum>",
      "enum_values": ["<val1>", "<val2>"]
    }}
  ],
  "distributions": {{
    "<column_name>": {{
      "<value>": <integer percentage>
    }}
  }},
  "compliance_rules": {{
    "<column_name>": {{
      "frameworks": ["<PII|PCI|HIPAA|GDPR|CCPA|SOX|FERPA>"],
      "action": "<Fake realistic|Format-preserving fake|Mask with ***|Redact|Custom>",
      "custom_rule": "<specific masking/handling instruction or null>"
    }}
  }},
  "temporal": {{
    "<column_name>": {{
      "aging_days": <integer or null>,
      "description": "<string>"
    }}
  }}
}}

Rules:
- volume: extract explicit count ("50 users" → 50, "generate 1000" → 1000). null if not stated. Always refers to the root table row count.
- tables: Include this array ONLY when the user describes multiple related entities (e.g. "customers with addresses", "orders containing line items", "patients with visits"). Each table gets its own columns array. The root/parent entity gets is_root: true. If only one entity is described, omit tables and use columns instead.
- relationships: Always include when tables is present. cardinality is always "one_to_many". per_parent_min/per_parent_max come from phrases like "1 to 3 addresses", "between 2 and 5 items", "up to 4 visits". Use null if not stated.
  source_column: the primary key of the parent table. Use the actual column name you defined in that table's columns array (e.g. if source_table has a column named "user_id", use "user_id"; otherwise default to "id").
  target_column: the foreign key in the child table that references the parent. Use the actual column name you defined (e.g. "user_id", "order_id", "patient_id"). If no FK column was explicitly named, use "<source_table_singular>_id" as a sensible default.
- columns: Use this flat list ONLY for single-entity prompts (when tables is omitted). List ALL fields mentioned or strongly implied by the entity type. Use snake_case.
- For enum fields (gender, status, type, category) list known enum_values if mentioned.
- distributions: ONLY if proportions/percentages/ratios explicitly stated. Preserve the EXACT values the user mentioned (e.g. "not-specified", "other", "non-binary") — do NOT collapse them into Male/Female. Values should sum to 100; if they don't, include only what was stated.
- compliance_rules: identify ALL sensitive fields and their applicable regulatory frameworks. Stays flat (keyed by column name across all tables):
    PII  → name, email, phone, address, ssn, dob, passport, ip_address, gender, race
    PCI  → credit_card, card_number, cvv, account_number, iban, routing_number, bank_account
    HIPAA→ diagnosis, mrn, npi, patient_id, prescription, lab_result, treatment, dea_number
    GDPR → any personal data of EU residents (email, name, ip, dob, location, device_id, cookie)
    CCPA → personal data of California residents (similar to GDPR scope)
    SOX  → salary, compensation, revenue, audit_log, tax_id, financial records
    FERPA→ student_id, gpa, grade, transcript, enrollment, academic records
  A field can belong to MULTIPLE frameworks (e.g. email → PII + GDPR + CCPA).
  If user describes masking (e.g. "last 4 digits visible", "mask SSN"), set action="Custom" with custom_rule.
  Always infer frameworks from BOTH column name AND domain context (e.g. "healthcare" → HIPAA).
- temporal: only include if aging/date-relative requirements are mentioned.
- Return ONLY the JSON object, no explanation.
"""
