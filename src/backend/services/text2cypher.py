"""
Text2Cypher service for ad-hoc agent queries against the ECI knowledge graph.

Follows GraphRAG best practices:
  - Schema-in-prompt (ECI_SCHEMA)
  - Causal-inference terminology mapping (ECI_TERMINOLOGY)
  - Few-shot examples (ECI_FEW_SHOT) — expand as failure patterns emerge
  - Format instructions enforce Cypher-only output
"""
from openai import OpenAI

from backend.settings import settings

# ── ECI graph schema ─────────────────────────────────────────────────────────

ECI_SCHEMA = """
Node labels and properties:
  Concept  {concept_id: STRING, name: STRING, chapter: INTEGER,
            difficulty: INTEGER, page_refs: LIST, misconceptions: LIST}
  Section  {node_id: STRING, section_id: STRING, label: STRING,
            chapter: INTEGER, depth: INTEGER,
            start_page: INTEGER, end_page: INTEGER}
  Category {name: STRING, label: STRING}

Relationship types (no properties on any):
  PREREQUISITE_OF
  COVERED_IN
  SUBTOPIC_OF
  RELATED_TO_SEE_ALSO
  COMMONLY_CONFUSED
  NEXT_IN_SEQUENCE
  RELATED_TO_ALIAS

The relationships:
  (:Concept)-[:PREREQUISITE_OF]->(:Concept)
  (:Concept)-[:COVERED_IN]->(:Section)
  (:Concept)-[:SUBTOPIC_OF]->(:Category)
  (:Concept)-[:RELATED_TO_SEE_ALSO]->(:Concept)
  (:Concept)-[:COMMONLY_CONFUSED]-(:Concept)
  (:Section)-[:NEXT_IN_SEQUENCE]->(:Section)
  (:Concept)-[:RELATED_TO_ALIAS]->(:Concept)
"""

# ── Terminology mapping ──────────────────────────────────────────────────────

ECI_TERMINOLOGY = """
TERMINOLOGY MAPPING (causal inference domain):
- "concept", "topic", "term" → node with label Concept
- "section", "subsection", "chapter subsection" → node with label Section
- "prerequisite", "required concept", "must know first", "depends on" →
    follow PREREQUISITE_OF edges backwards:
    MATCH (:Concept)-[:PREREQUISITE_OF]->(target:Concept)
- "next concept", "what to learn after", "unlocked by" →
    follow PREREQUISITE_OF edges forwards:
    MATCH (source:Concept)-[:PREREQUISITE_OF]->(:Concept)
- "covered in", "appears in", "textbook section" →
    follow COVERED_IN edges from Concept to Section
- "commonly confused with", "often mixed up", "misconception" →
    follow COMMONLY_CONFUSED edges
- "related to", "see also" → follow RELATED_TO_SEE_ALSO edges
- concept_id values are slugified (underscores not spaces):
    e.g., "d_separation", "backdoor_criterion", "structural_causal_model_scm"
"""

# ── Few-shot examples ────────────────────────────────────────────────────────

ECI_FEW_SHOT = """
Question: What are the prerequisites of d-separation?
Cypher: MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(c:Concept {concept_id: 'd_separation'}) RETURN prereq.concept_id, prereq.name

Question: Which concepts are in chapter 6?
Cypher: MATCH (c:Concept {chapter: 6}) RETURN c.concept_id, c.name ORDER BY c.concept_id

Question: What should I learn after mastering conditional independence?
Cypher: MATCH (c:Concept {concept_id: 'conditional_independence'})-[:PREREQUISITE_OF]->(next:Concept) RETURN next.concept_id, next.name

Question: Which concepts are commonly confused with counterfactuals?
Cypher: MATCH (c:Concept {concept_id: 'counterfactuals'})-[:COMMONLY_CONFUSED]-(other:Concept) RETURN other.concept_id, other.name

Question: Which textbook sections cover the backdoor criterion?
Cypher: MATCH (c:Concept {concept_id: 'backdoor_criterion'})-[:COVERED_IN]->(s:Section) RETURN s.section_id, s.label, s.start_page, s.end_page
"""

# ── Prompt template ──────────────────────────────────────────────────────────

TEXT2CYPHER_PROMPT = """Instructions:
Generate a Cypher statement to query the ECI knowledge graph to answer the following question.
Use ONLY the provided relationship types and properties in the schema.
Do not use any other relationship types or properties.
ONLY RESPOND WITH CYPHER — NO CODE BLOCKS, NO EXPLANATIONS, NO APOLOGIES.

Graph database schema:
{schema}

{terminology}

Examples:
{examples}

User question: {question}"""


# ── Lazy singleton client ─────────────────────────────────────────────────────

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _client


def generate_cypher(question: str) -> str:
    """Call OpenRouter/OpenAI to generate a Cypher query for the given question."""
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured — set it in .env")
    client = _get_client()
    prompt = TEXT2CYPHER_PROMPT.format(
        schema=ECI_SCHEMA,
        terminology=ECI_TERMINOLOGY,
        examples=ECI_FEW_SHOT,
        question=question,
    )
    response = client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",  # fast + cheap for structured output
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=256,
    )
    return response.choices[0].message.content.strip()
