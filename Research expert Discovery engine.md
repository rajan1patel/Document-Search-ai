You are implementing an Expert Discovery Pipeline.

Goal:

Given a user problem, identify the best researchers/inventors who are true experts in that technical area.

The system should optimize for:

"Find the person who has deep expertise in solving this exact problem"

Not:

"Find the person who appeared in one related paper/patent"

add loogger for every api call so that we can debug properly... 


==================================================
FINAL PIPELINE
==================================================


User Problem

    |
    v

Research Retrieval Layer

    |
    v

Fetch Relevant Research Works

(using XSearch API)

    |
    v

Extract All Authors

    |
    v

Fetch Author Profiles

(OpenAlex API)

    |
    v

Build Author Research Profile

    |
    v

LLM Topic Validation

    |
    v

Expert Ranking Engine

    |
    v

Top K Experts



==================================================
STEP 1
RESEARCH RETRIEVAL
==================================================


Input:

User problem


Fetch relevant research papers/patents using XSearch API.


Store temporarily:


{
 paper_id,

 title,

 abstract,

 authors
}



==================================================
STEP 2
AUTHOR EXTRACTION
==================================================


Extract ALL authors from retrieved research.


Important:

Do not rank authors from the paper.

Do not remove authors early.


If a paper has 10 authors:

all 10 enter the author pool.


Use:

author_id

as unique identity.



==================================================
STEP 3
AUTHOR PROFILE ENRICHMENT
==================================================


For each author:


Fetch OpenAlex author details.


Use:


- author name
- works_count
- cited_by_count
- h_index
- i10_index
- counts_by_year
- topics
- subfields


Example topic data:


{
 "display_name":

 "Battery Materials",


 "count":50,


 "subfield":

 {
   "display_name":
   "Energy Storage"
 }

}



==================================================
STEP 4
CREATE AUTHOR RESEARCH PROFILE
==================================================


Create profile:


{
 author_id,

 name,


 research_topics:[

   {
    topic_name,

    subfield,

    work_count
   }

 ],


 metrics:{

   total_works,

   citations,

   h_index

 },


 research_activity:{


   counts_by_year

 }

}



Important:

The main expertise signal comes from:

topic + count of work performed on that topic.



==================================================
STEP 5
LLM TOPIC VALIDATION
==================================================


Use LLM only to validate topic relevance.


Input:


User problem:

{problem}



Author topics:

[
 {
  topic_name,
  work_count,
  subfield
 }
]



Ask LLM:


"Does this author have research experience related to the user problem?"



Return strict JSON:


{
 "match": "yes/no",

 "matched_topics":[

   {
    "topic_name",

    "count",

    "reason"
   }

 ]

}



Rules:


If no relevant topic exists:

return:


{
 "match":"no"
}



If match exists:

return exact OpenAlex topic name and count.


Example:


{
 "match":"yes",

 "matched_topics":[

  {
   "topic_name":
   "Battery Materials",

   "count":45
  }

 ]

}



==================================================
STEP 6
FILTERING
==================================================


If LLM returns:


match = no


Remove author from expert pool.



If:


match = yes


Keep author and update profile:


Add:


matched_topic

matched_topic_count

topic_match_score



==================================================
STEP 7
EXPERT RANKING
==================================================


Rank remaining authors.


Score:


expert_score =


0.45 * problem_topic_match


+

0.25 * topic_depth


+

0.15 * research_continuity


+

0.10 * research_ownership


+

0.05 * impact



==================================================
RANKING FEATURES
==================================================



1. Problem Topic Match

Most important.


Based on:


LLM validated topic similarity.



Question:

Does this author actually work on this problem?



--------------------------------------------------



2. Topic Depth


Question:


How much work has author done in this topic?


Use:


OpenAlex topic count.



Example:


Battery Materials:

50 works


higher than:


Battery Materials:

3 works



--------------------------------------------------



3. Research Continuity


Question:


Is this a long-term expertise?


Use:


topic works across years.



--------------------------------------------------



4. Research Ownership


Question:


Did author lead the research?


Use:


first author

last author

middle author



--------------------------------------------------



5. Impact


Use:


h_index

citations


Low weight only.



==================================================
FINAL OUTPUT
==================================================


Return:


[
 {

  author_id,

  name,


  expert_score,


  metrics:{


    works_count,

    citations,

    h_index

  },


  matched_topic:{


    topic_name,

    topic_count

  },


  all_topics:[


    {
      topic_name,

      count,

      subfield

    }

  ]

 }
]



==================================================
IMPORTANT
==================================================


Do not rank based on a single paper.

The retrieved paper is only the entry point.

The real expert signal comes from:

- historical research topics
- topic work count
- continuity
- validated problem similarity


The system should prefer:

A researcher with 50 relevant works

over

A researcher with 1 matching paper.



api for xsearch for research paper
curl --location 'http://192.168.0.57:8082/patent_search/xsearch' \
--header 'Accept: application/json' \
--header 'Content-Type: application/json' \
--header 'X-Gravitee-Api-Key: YOUR_API_KEY_HERE' \
--data '{
    "nl_query": "lithium battery thermal management"
}'




api from openalex for author details.. using author which we take from xsearch author profile..
https://api.openalex.org/authors/{author_id}/api_key=YOUR api key