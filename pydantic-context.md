The “JSON-LD-first Pydantic” workflow you’re looking for

Below is a concrete recipe for turning a Pydantic model into the only source-of-truth and then mechanically producing a standards-compliant JSON-LD @context that your vocabulary service can publish at {service}/contexts/….
It rests on three building blocks:

#	Building block	What it gives you
1	A slim Pydantic plug-in (pydantic_jsonld)	Lets developers annotate each field with its IRI once and provides an .export_context() helper
2	A Pydantic model that validates contexts	Ensures the exported file is a legal JSON-LD context before it ever reaches CI ✅
3	A CI step (GitHub Action) that writes artifacts to ont/, contexts/, shacl/	Keeps the vocabulary service in sync with the codebase—no hand editing

Why a plug-in?
Pydantic v2 added experimental plug-ins—entry-point packages that can hook into model creation and schema export  ￼.  We’ll use that to piggy-back our JSON-LD hints onto the normal json_schema() machinery.

⸻

1 Ship a micro-plug-in: pydantic_jsonld

# pydantic_jsonld/__init__.py
from pydantic import BaseModel, Field
from typing import Any, Dict

_JSONLD_META_KEY = "__jsonld__"   # avoid collisions with normal metadata

def Term(iri: str, type_: str | None = None, **field_kwargs):
    """
    Field helper that stores 'iri' and optional '@type' mapping.
    """
    field_kwargs.setdefault('metadata', {})[_JSONLD_META_KEY] = {
        "iri": iri,
        "type": type_,
    }
    return Field(**field_kwargs)

class JsonLDModel(BaseModel):
    """
    Mixin that can: 1) build a context  2) self-validate it
    """
    class Config:
        json_ld_base:   str | None = None   # e.g. "https://ex.org/resource/"
        json_ld_vocab:  str | None = None   # default @vocab

    @classmethod
    def export_context(cls) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {"@version": 1.1}
        if cls.Config.json_ld_base:
            ctx["@base"]  = cls.Config.json_ld_base
        if cls.Config.json_ld_vocab:
            ctx["@vocab"] = cls.Config.json_ld_vocab

        for name, fld in cls.model_fields.items():
            meta = fld.metadata.get(_JSONLD_META_KEY)
            if not meta:
                continue                   # skip un-annotated fields
            term = fld.alias or name
            entry: Dict[str, Any] = {"@id": meta["iri"]}
            if meta["type"]:
                entry["@type"] = meta["type"]
            ctx[term] = entry

        # Validate before returning
        _validate_context(ctx)
        return {"@context": ctx}

Usage:

class Entity(JsonLDModel):
    id          : str = Term("schema:identifier", alias='@id',
                             type_='@id')       # compacts to IRI
    name        : str = Term("schema:name")
    content_type: str = Term("schema:encodingFormat")
    sensitivity : list[str] = Term("ex:sensitivity", type_='@set') 

    class Config(JsonLDModel.Config):
        json_ld_base  = "https://ex.org/resource/"
        json_ld_vocab = "https://ex.org/vocab/"

Now every developer writes plain Pydantic but still gets:

Entity.export_context()
# {'@context': {...}}   ← ready to be dumped to contexts/entity-1.0.jsonld


⸻

2 Validate the context before you publish it

There is no official JSON Schema for JSON-LD contexts, but you can cover 98 % of foot-guns with a small Pydantic model:

class _ContextTerm(BaseModel):
    __root__: Dict[str, Any]

    @model_validator(mode='after')
    def check_term(cls, v):
        allowed = {"@id", "@type", "@language", "@container",
                   "@reverse", "@context"}
        extra = set(v.__root__.keys()) - allowed
        if extra:
            raise ValueError(f"Unknown JSON-LD keywords: {extra}")
        if "@id" not in v.__root__:
            raise ValueError("Every term *must* have @id")
        return v

_validate_context() simply walks the dictionary and instantiates _ContextTerm for each mapping; a failure throws a ValidationError that fails the build before the file is written.

⸻

3 Automate artifact publishing in CI

# .github/workflows/export-jsonld.yml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install .[dev]   # includes pydantic_jsonld and pyld
      - name: Export JSON-LD contexts
        run: |
          python - <<'PY'
          from my_package import models
          import json, pathlib
          for mdl in models.__all__:
              ctx = getattr(models, mdl).export_context()
              out = pathlib.Path('vocabulary/contexts')/f"{mdl.lower()}-1.0.jsonld"
              out.write_text(json.dumps(ctx, indent=2))
          PY
      - name: Commit & push
        uses: EndBug/add-and-commit@v9
        with:
          message: "CI: update generated contexts"

Your FastAPI vocabulary service can now statically serve the committed files at

/contexts/entity-1.0.jsonld
/shacl/entity-1.0.ttl
/ont/entity-1.0.ttl

Bonus: Because the context is generated in the same pass, you can also derive SHACL shapes from the same Pydantic metadata (field min_length, max_length, optional/required, etc.).  Hook that into your exporter exactly like the context writer.

⸻

4 Developer ergonomics
	•	Zero duplication – devs only touch the Pydantic class.
	•	Instant feedback – run Entity.export_context() in a REPL and you’ll know if you broke the mapping.
	•	LLM function-calling remains unchanged – Python-friendly keys (name, content_type, …) stay as is; only the exported context cares about IRIs.

⸻

5 Related tools & patterns
	•	pydantic_schemaorg – auto-generated Pydantic models for every Schema.org class; it uses a code-gen approach similar to ours but in reverse  ￼.
	•	LinkML – if your team ever wants a YAML DSL that already knows how to emit Pydantic+JSON-LD+SHACL, you can generate Pydantic models from LinkML and deprecate the plug-in, while keeping the same dev UX  ￼.

⸻

Take-away

Define once in Pydantic → export everything else.

A ~150-line plug-in gives Python developers LLM-friendly models and guarantees that whatever lands in {service}/contexts/… is a valid, versioned JSON-LD context—no hand-crafted files, no drift, no headaches.


Below I answer your two questions and sketch how you can drive the very same artefacts from Pydantic v2.

⸻

1  Is the current context/shape bundle “correct”?

✔ What looks good

Aspect	Comment
Two–item @context array	The first item pulls in the shared “context-base”, the second item overrides/extends it – a textbook JSON-LD 1.1 pattern.
Explicit @type hints (@id, xsd:string, @set, …)	Guarantees loss-free compact/expand.
Links to SHACL NodeShapes (sh:shapesGraph)	Makes validation resources discoverable.
Separating class metadata in @graph	Keeps the context itself a pure mapping layer (almost, see below).

⚠ Minor issues to watch

Issue	Why it matters	Quick fix
contextMetadata entry lives inside the context object	JSON-LD processors will treat "contextMetadata" as a term whose compact IRI is literally the embedded object – it isn’t “metadata about the file”.	Move those keys to the surrounding document (e.g. alongside the top-level @graph) or publish a tiny companion JSON file.
Namespace order–dependency ("@type": "xsd:string" before xsd is re-declared at bottom)	Works only because xsd was already defined in the imported context. A new consumer might load the fragment without the remote context first.	Keep all prefixes (xsd, dscdo, …) in the second object of the array to be safe.
Very large bundle (context + ontology snippets + shapes in one file)	Great for human inspection, heavy for clients that only need one piece.	Split: {service}/contexts/…, {service}/ont/…, {service}/shacl/… (you already plan this).

Nothing is wrong—but moving the descriptive bits out of @context will prevent surprises.

⸻

2  Can Pydantic emit the same artefacts?

2.1  Core idea
	1.	Annotate each Pydantic field with its IRI and desired @type.
	2.	Tell the model once what remote context(s) and prefix map it depends on.
	3.	Auto-export
	•	a pure JSON-LD @context file
	•	optional SHACL NodeShapes (derived from field metadata)

You already have 90 % of the metadata in your example – we just relocate it from the hand-written context into field definitions.

⸻

2.2  Minimal plug-in (pydantic_jsonld)

Pydantic v2 exposes a plug-in hook so you don’t need to fork Pydantic itself.  ￼

# pip install pydantic>=2.11
from pydantic import BaseModel, Field, ValidationError
from typing import Any, Dict, List

_JSONLD = "__jsonld__"          # private key

def Term(iri: str, type_: str | None = None, **kw):
    kw.setdefault("metadata", {})[_JSONLD] = {"iri": iri, "type": type_}
    return Field(**kw)

class JsonLDModel(BaseModel):
    class Config:
        json_ld_remote: List[str] = [
            # first item in the @context array
            "https://schema-earth616-ks18.blocks.simbachain.com/nd/scdoc/context/context-base.jsonld"
        ]
        json_ld_prefixes: Dict[str, str] = {           # will become second item
            "dscdo": "https://schema-earth616-ks18.blocks.simbachain.com/nd/scdoc/ont/",
            "schema": "https://schema.org/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            # …
        }

    # --- exporter ---------------------------------------------------------
    @classmethod
    def export_context(cls) -> Dict[str, Any]:
        remote, local = cls.Config.json_ld_remote, cls.Config.json_ld_prefixes.copy()

        # field → term mapping
        for name, fld in cls.model_fields.items():
            meta = fld.metadata.get(_JSONLD)
            if not meta:
                continue
            term = fld.alias or name
            entry: Dict[str, Any] = {"@id": meta["iri"]}
            if meta["type"]:
                entry["@type"] = meta["type"]
            local[term] = entry

        ctx = {"@context": remote + [local]}            # two-item array
        _validate_jsonld_context(ctx)                   # fails fast
        return ctx

Validation can be a 20-line Pydantic model that checks every term has an @id and only whitelisted keywords—leveraging plain Pydantic validation logic (see json_schema_extra trick in docs)  ￼.

⸻

2.3  Example model → context

class DocumentChunk(JsonLDModel):
    id              : str      = Term("dscdo:DocumentChunk", alias='@id', type_='@id')
    chunkMainText   : str      = Term("dscdo:chunkMainText", type_="xsd:string")
    chunkIndex      : int      = Term("dscdo:chunkIndex", type_="xsd:integer")
    hasChunkConcepts: str | None = Term("dscdo:hasChunkConcepts", type_='@id')
    # …add the rest

ctx = DocumentChunk.export_context()

ctx serialises (pretty-printed):

{
  "@context": [
    "…/context-base.jsonld",
    {
      "dscdo": "https://…/ont/",
      "schema": "https://schema.org/",
      "xsd": "http://www.w3.org/2001/XMLSchema#",

      "DocumentChunk": "dscdo:DocumentChunk",
      "chunkMainText": { "@id": "dscdo:chunkMainText", "@type": "xsd:string" },
      "chunkIndex":    { "@id": "dscdo:chunkIndex",    "@type": "xsd:integer" },
      "hasChunkConcepts": { "@id": "dscdo:hasChunkConcepts", "@type": "@id" }
    }
  ]
}

Exactly the pattern you hand-crafted – now guaranteed never to drift.

⸻

2.4  Generating SHACL, too (optional)

def export_shacl(cls) -> dict:
    props = []
    for fld in cls.model_fields.values():
        meta = fld.metadata.get(_JSONLD)
        if not meta:
            continue
        node = {
            "sh:path": {"@id": meta["iri"]},
            "sh:datatype": {"@id": meta["type"]} if meta["type"].startswith("xsd:") else None,
            # use fld.is_required(), fld.min_length, fld.max_length, etc.
        }
        props.append({"@id": f"_:{fld.name}", **{k:v for k,v in node.items() if v}})
    return {
        "@graph": [{
            "@id": f"https://…/shacl/{cls.__name__}Shape-v1",
            "@type": "sh:NodeShape",
            "sh:targetClass": {"@id": meta["iri"]},        # class IRI
            "sh:property": [{"@id": p["@id"]} for p in props]
        }] + props,
        "@context": cls.export_context()["@context"][-1]  # reuse prefixes
    }

Field constraints (max_length, Enum, ge/le, etc.) flow naturally into sh:minCount, sh:maxCount, sh:in, … because Pydantic already carries that info.

When that feels brittle, switch to LinkML → Pydantic code-gen (LinkML natively emits JSON-LD contexts and SHACL).

⸻

2.5  Wire it into CI

# generate-vocab.yml
- name: Export contexts & shapes
  run: |
    python - <<'PY'
    import json, pathlib, importlib
    from my_package import models    # every JsonLDModel lives here

    OUT = pathlib.Path("vocabulary")
    for mdl_name in models.__all__:
        mdl = getattr(models, mdl_name)
        (OUT/"contexts").mkdir(parents=True, exist_ok=True)
        (OUT/"shacl").mkdir(parents=True, exist_ok=True)

        (OUT/"contexts"/f"{mdl_name}-v0.2.jsonld").write_text(
            json.dumps(mdl.export_context(), indent=2)
        )
        (OUT/"shacl"/f"{mdl_name}Shape-v1.jsonld").write_text(
            json.dumps(mdl.export_shacl(), indent=2)
        )
    PY

The GitHub Action commits whatever changes arose in the Pydantic source. Your FastAPI vocabulary service just serves the repo at

/contexts/DocumentChunk-v0.2.jsonld
/shacl/DocumentChunkShape-v1.jsonld
/ont/…   <-- your hand-crafted ontology Turtle or OWL


⸻

Take-aways
	•	Yes, your current JSON-LD pattern is valid; move contextMetadata out of the mapping to stay 100 % spec-clean.
	•	Pydantic can absolutely be the single source-of-truth for both the compact context mapping and SHACL NodeShapes – by storing IRI/type metadata in Field.metadata and emitting artefacts in CI.
	•	If your models grow huge, LinkML → Pydantic gives the same ergonomics while taking over the heavy-lifting of shape generation.

That workflow lets Python devs stay in their familiar Pydantic world while your Linked-Data infrastructure remains perfectly in sync and standards-compliant.