You are building an MVP Expert Discovery Pipeline.

Problem:
We receive already-filtered relevant patent/research documents from an external Landscapes API. The API already does the retrieval part, so we do NOT need search, vector database, or Milvus for this MVP.

Our goal:
Given a list of relevant patent JSON documents, identify the best experts (inventors/authors/researchers) to contact first.

The system should transform:
Relevant Documents -> Expert Profiles -> Ranked Experts -> Contact Information


INPUT DATA FORMAT:
The API response format is fixed and will not change.

Example:

{
 "_id":"AU2008305666B2",
 "_source":{
    "title":"Valomaciclovir polymorphs",

    "assignees":[
       "Epiphany Biosciences Inc"
    ],

    "inventors":[
       "Butke Gregory P",
       "O'neill Mike H"
    ],

    "applicants":[
       "Epiphany Biosciences Inc"
    ],

    "publicationDate":"2014-08-28",

    "filingDate":"2008-09-18",

    "priorityDate":"2007-09-21",

    "abstract":"...",
    
    "summary":{
       "claims.raw":[]
    }
 }
}


SYSTEM REQUIREMENTS:

Build a FastAPI based backend pipeline.

No database required for MVP.

No Milvus required.

No document storage required.

Everything works on incoming JSON.


PIPELINE:

1. Patent Document Parser

Create a parser that converts incoming JSON into a clean internal document object.

Input:
Raw API JSON

Output:

{
 document_id,
 type,
 title,
 abstract,
 claims,
 inventors,
 assignees,
 applicants,
 publication_date,
 text_content
}


text_content should combine:

title +
abstract +
claims

This will be used for AI processing.


--------------------------------------------------


2. Expert Extraction Layer

Goal:
Convert documents into people profiles.

Input:

Document:

{
title,
abstract,
inventors,
assignees
}


Extract people:

Example:

Before:

Patent 1:
inventor:
John


Patent 2:
inventor:
John


After:

Expert profile:

{
 name:"John",

documents:[
 patent1,
 patent2
],

roles:[
 inventor
]
}


Rules:

Inventors are highest priority.

Roles ranking:

inventor > author > applicant > assignee


Merge duplicate people.


--------------------------------------------------


3. Technology / Expertise Extraction Layer

Use LLM.

For each document extract:

- technology domain
- sub-domain
- skills
- keywords
- research area


Example:

Input:

Title:
Valomaciclovir polymorphs

Abstract:
Crystalline forms of valomaciclovir...


Output:

{
 domain:"Pharmaceutical",

skills:[
 "Drug formulation",
 "Polymorph chemistry",
 "Antiviral compounds"
]
}


Attach extracted skills to expert profiles.


Final expert profile:

{
 name:"Butke Gregory P",

 expertise:[
   "Drug formulation",
   "Antiviral compounds"
 ],

documents:[
 ...
]
}


--------------------------------------------------


4. Embedding Layer

Use embeddings for semantic similarity.

Do NOT use vector database.

Create embeddings in memory.

Create an expert text representation:

Example:

"Butke Gregory P is an expert in Drug formulation,
Polymorph chemistry, Antiviral compounds.
Relevant works:
Valomaciclovir polymorphs."


Generate embedding for:

1. Expert profile
2. User query


Calculate cosine similarity.

This becomes:

technical_match_score


--------------------------------------------------


5. Expert Ranking Engine

Create ranking algorithm.

The goal:

Find the top experts who should be contacted first.


Score formula:

final_score =
0.50 * technical_match_score
+
0.25 * expertise_strength
+
0.15 * role_score
+
0.10 * recency_score


Details:


Technical Match:

Calculated using embeddings similarity.

Range:
0-1


Expertise Strength:

Based on number of relevant documents.

Example:

20 patents > 2 patents

Normalize score.


Role Score:

inventor:
1.0

author:
0.9

researcher:
0.8

applicant:
0.7

assignee:
0.5


Recency:

Use publicationDate.

Recent documents get higher score.


Return:

{
name,
score,
ranking_reason,
expertise,
evidence_documents
}


--------------------------------------------------


6. Contact Enrichment Layer

Only enrich top ranked experts.

Do not enrich everyone.


Input:

{
name,
organization
}


Output:

{
email,
organization,
profile_url
}


For MVP create service interface.

Can use mocked provider initially.


--------------------------------------------------


7. Final API

Create endpoint:


POST /discover-experts


Input:

{
 query:"Find experts in lithium battery cathode materials",

 documents:[
   API JSON documents
 ]
}


Output:

{
 query,

 experts:[
 {

 rank:1,

 name,

 score,

 expertise,

 reasoning,

 evidence:[
   {
    title,
    patent_id
   }
 ],

 contact:{
   email,
   organization
 }

 }
 ]
}


--------------------------------------------------


TECH STACK:

Backend:
FastAPI

Language:
Python

LLM:
OpenAI compatible abstraction

Embeddings:
OpenAI embeddings compatible abstraction

No database.

No vector DB.

Keep services modular.


Project structure:


app/

 main.py

 api/
   routes.py

 pipeline/

   parser.py
   expert_extractor.py
   technology_extractor.py
   embedding_service.py
   ranking_engine.py
   enrichment_service.py
   response_builder.py


models/

 schemas.py


services/

 llm_client.py
 embedding_client.py


--------------------------------------------------

Important design principles:

1. Keep every pipeline step independent.
2. Every step should have input/output schemas.
3. Ranking should be explainable.
4. Do not let LLM decide final ranking.
5. LLM extracts knowledge.
6. Python scoring ranks experts.

Build this as a clean MVP that can later scale.





User sends: POST /discover-experts
├── Body: { "query": "lithium battery...", "top_k": 5 }
│
├─► Step 0: Route checks → documents provided?
│   ├── YES → Use documents directly (skip X-Search)
│   └── NO  → Call X-Search API ═══════════════════════╗
│               POST /patent_search/xsearch            ║
│               Header: X-Gravitee-Api-Key             ║
│               Body: { nl_query, page, page_size }    ║
│               ↓                                      ║
│             Returns: { xsearch_id, patent: { hits } } ║
│               ↓                                      ║
│             Pass hits to pipeline ◄═══════════════════╝
│
├─► Step 1: Parser ─────────────────────────────────────
│   Raw JSON patents → ParsedDocument
│   { _id, _source }  → { title, abstract, inventors,
│                          text_content, ... }
│
├─► Step 2: Expert Extractor ───────────────────────────
│   Documents → Merged Expert Profiles
│   • Extracts inventors, applicants, assignees
│   • Deduplicates by name
│   • Assigns highest-priority role (inventor > author > applicant > assignee)
│
├─► Step 3: Tech Extractor (LLM) ───────────────────────
│   For each document → { domain, sub-domain, skills, keywords }
│   Then attaches all skills to the matching expert profiles
│   Uses OpenRouter (OpenAI-compatible) LLM
│
├─► Step 4: Embedding ──────────────────────────────────
│   Creates text representation per expert:
│     "Butke Gregory P is an expert in Drug formulation...
│      Relevant works: Valomaciclovir polymorphs."
│   Computes cosine similarity with user query
│   → technical_match_score (0-1)
│   No vector DB — all in memory
│
├─► Step 5: Ranking Engine ─────────────────────────────
│   final_score = 
│     0.50 × technical_match_score
│     0.25 × expertise_strength (document count)
│     0.15 × role_score (inventor=1.0, assignee=0.5)
│     0.10 × recency_score (newer = higher)
│   → Sorted list of RankedExpert with explainable reasoning
│
├─► Step 6: Contact Enrichment ─────────────────────────
│   Only top-K experts enriched (MVP mocked)
│   → email, organization, profile_url
│
└─► Step 7: Response Builder ───────────────────────────
    Returns: {
      query,
      xsearch_id,          ← for pagination
      total_documents_found,
      experts: [{
        rank, name, score, expertise,
        reasoning, evidence: [{title, patent_id}],
        contact: { email, organization, profile_url }
      }]
    }





     for external api request 
     Paste this into a terminal, replace the API key, and run it:

```bash
curl --location 'http://192.168.0.57:8082/patent_search/xsearch' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--header 'X-Gravitee-Api-Key: YOUR_API_KEY_HERE' \
--data '{
    "nl_query": "lithium battery thermal management"
}'
```

Alternatively you can use 'https://gateway.greyb.com/patent_search/xsearch'

You will get back a list of matching patents and the `xsearch_id` — a session key you can use to page through results or refine your search without re-running the AI translation.

---


reposne format 
{
            "_id":"CN203520460U",
            "_source":{
               "images":[
                  
               ],
               "title":"FRID technological is based intelligent mechanical property comprehensive testing apparatus for MOTOROLA lithium cell total management system",
               "assignees":[
                  "Suzhou Tergar Iot Technology Co Ltd"
               ],
               "inventors":[
                  "Huang Fuming",
                  "Li Yunfei",
                  "Huang Junning"
               ],
               "applicants":[
                  "Suzhou Tergar Iot Technology Co Ltd"
               ],
               "publicationDate":"2014-04-02",
               "filingDate":"2013-09-22",
               "priorityDate":"2013-09-22",
               "expirationDate":"2023-09-22",
               "link":"None",
               "summary":{
                  "claims.raw":[
                     "<claim-text>1. 1 Kinds RFID technology of based intelligent mechanical property comprehensive testing apparatus for MOTOROLA <mark>lithium</mark> <mark>cell</mark> total management system, comprising a <mark>lithium</mark> <mark>battery</mark> board unit is <mark>lithium</mark> <mark>battery</mark>, a card reader and <mark>lithium</mark> <mark>battery</mark> service platform pipe, a characterised is: The <mark>lithium</mark> <mark>battery</mark> board unit comprises a battery pack protection module and <mark>lithium</mark> <mark>battery</mark> MCU processor and RFID electronic label, wherein the battery pack protection module and RFID electronic label",
                     "with the <mark>lithium</mark> <mark>battery</mark> MCU processor is connected with, wherein the battery pack protection module is used to the working state perform managing of <mark>lithium</mark> <mark>battery</mark>; and when the <mark>lithium</mark> <mark>battery</mark> with the transmitting the feedback information connected to the <mark>lithium</mark> <mark>battery</mark> MCU processor; The card reader comprises AN radiofrequency module and card MCU processor and a GPS module and a network communication module, the RF radiofrequency module, a GPS module and a network communication module connected",
                     "According to claim 1 RFID technology of based intelligent mechanical property comprehensive testing apparatus for MOTOROLA <mark>lithium</mark> <mark>cell</mark> total management system, a characterised is: The management system farther comprising user terminal, wherein the <mark>lithium</mark> <mark>battery</mark> service platform pipe connected to the user terminal communication connection.</claim-text><claim-text>4."
                  ],
                  "descriptions.raw":[
                     "<br><br>[0008]\t\tfor the upper purposes of the related to purposes, the utility model providing a based on RFID technology the intelligent mechanical property comprehensive testing apparatus for MOTOROLA <mark>lithium</mark> <mark>cell</mark> total management system, comprising a <mark>lithium</mark> <mark>battery</mark> board unit is <mark>lithium</mark> <mark>battery</mark>, a card reader and <mark>lithium</mark> <mark>battery</mark> service platform pipe; the <mark>lithium</mark> <mark>battery</mark> board unit comprises a battery pack protection module and <mark>lithium</mark> <mark>battery</mark> MCU processor and RFID electronic label, wherein",
                     "<br><br>[0027]\t\tShown as a digital 1, The invention claims a based on RFID technology the intelligent mechanical property comprehensive testing apparatus for MOTOROLA <mark>lithium</mark> <mark>cell</mark> total management system, the management system comprises a <mark>lithium</mark> <mark>battery</mark> board unit is <mark>lithium</mark> <mark>battery</mark>, a card reader and <mark>lithium</mark> <mark>battery</mark> service platform pipe 8, wherein the <mark>lithium</mark> <mark>battery</mark> board unit is used in acquire the real-timely state information on <mark>lithium</mark> <mark>battery</mark> and connected with the CPU card reader 8 to the",
                     "<br><br>[0031]\t\tThe reader and a <mark>lithium</mark> <mark>batteries</mark> service platform pipe is 8 TCP (Transmission Control Protocol transmission control protocol) protocol as data communication way, and guaranteed the data transmission reliability. <mark>Lithium</mark> <mark>battery</mark> information data storage of <mark>lithium</mark> <mark>battery</mark> service platform pipe 8 to collect to database, comprising a <mark>lithium</mark> <mark>battery</mark> pack of the statuses, the information, geographical position information, identity information."
                  ],
                  "abstract.raw":[
                     "<p>The utility model providing a based on RFID technology the intelligent mechanical property comprehensive testing apparatus for MOTOROLA <mark>lithium</mark> <mark>cell</mark> total management system, comprising a <mark>lithium</mark> <mark>battery</mark> board unit, a card reader and <mark>lithium</mark> <mark>battery</mark> service platform pipe, a <mark>lithium</mark> <mark>battery</mark> board unit comprises a battery pack protection module and <mark>lithium</mark> <mark>battery</mark> MCU processor and RFID electronic label, the card reader comprises an RF radiofrequency module and card MCU processor and a GPS module",
                     "The card reader and <mark>lithium</mark> <mark>battery</mark> collection of information joint, and collecting of <mark>lithium</mark> <mark>battery</mark> data real-timely to the upper computer management server platform, for each pair of applications of <mark>lithium</mark> <mark>battery</mark> managing.</p>",
                     "and a network communication module, the management system the real-time detecting <mark>lithium</mark> <mark>battery</mark>, and directly connected with the RFID electronic label and transmission to the card, and connected with the Internet transmission to the <mark>lithium</mark> <mark>battery</mark> management server, the Internet network is connected with real-time time, and is directly been strong of the interference property, arrangement and a receiving space limitation of the advantages, the operation type comparison for."
                  ]
               },
               "abstract":"<p>The utility model providing a based on RFID technology the intelligent mechanical property comprehensive testing apparatus for MOTOROLA lithium cell total management system, comprising a lithium battery board unit, a card reader and lithium battery service platform pipe, a lithium battery board unit comprises a battery pack protection module and lithium battery MCU processor and RFID electronic label, the card reader comprises an RF radiofrequency module and card MCU processor and a GPS module and a network communication module, the management system the real-time detecting lithium battery, and directly connected with the RFID electronic label and transmission to the card, and connected with the Internet transmission to the lithium battery management server, the Internet network is connected with real-time time, and is directly been strong of the interference property, arrangement and a receiving space limitation of the advantages, the operation type comparison for. The card reader and lithium battery collection of information joint, and collecting of lithium battery data real-timely to the upper computer management server platform, for each pair of applications of lithium battery managing.</p>",
               "legalStatus":"Expired Fee Related",
               "simpleLegalStatus":"Dead",
               "isLitigated":"False",
               "sepData":{
                  "sep":false,
                  "tags":null,
                  "declaration_company":null,
                  "true_sep":null,
                  "sources":null,
                  "tgpp_numbers":null,
                  "standard":null
               },
               "awardData":{
                  "awarded":false,
                  "summary":{
                     "contracts_display":[
                        
                     ],
                     "contractNum_total":0,
                     "agencies_display":[
                        
                     ],
                     "agencyName_total":0
                  },
                  "rows":[
                     
                  ]
               }
            },
            "words":[
               
            ]
         },