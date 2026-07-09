# RAG From Scratch (Video Notes)
dumps: from doc object to serialised string to be hashable for sets, loads: opposite of dumps, 
## Key Concepts

## Why RAG Exists

## Embeddings

## Chunking

## Vector Databases

## Retrieval

## Prompt Construction

## Limitations of Traditional RAG

## Ideas Applicable to EduTwin

## Questions Raised

## Architectural Decisions Influenced

## repo
https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqazZ4aWxDOFI4dWxZbHRkZWFzMGtsYTE5VThoZ3xBQ3Jtc0ttdjY2X2dDY3FqNUd1SlFPVU5rX01DWXYta1J6Y25tQ1YxenduZU1pcUhZcnB3cU1nQ1NJaElGVmd4S1NTejJaa3BHTERIUk9WY2w0WHdnc1I0UXVQTG43Wmo4ZEQwVDIyZDdpclVhZzBRbU44V2NtMA&q=https%3A%2F%2Fgithub.com%2Flangchain-ai%2Frag-from-scratch&v=sVcwVQRHIc8

## RAG note to return to
Retrieval-Augmented Generation, or RAG, is a way to make an LLM answer using external text that is retrieved at query time, rather than relying only on what the model learned during pretraining. The key idea from both the paper and the course is simple: index documents, retrieve relevant chunks, then generate an answer grounded in those chunks.

Core idea
RAG is not one thing; it is a pipeline with stages. The basic stages are:

Indexing: load documents, split them into chunks, embed them, and store them in a vector index.

Retrieval: embed the user question, search the index, and return the most relevant chunks.

Generation: put the retrieved chunks into the prompt and ask the model to answer from that context.

The reason RAG exists is that LLMs do not reliably know private, recent, or domain-specific information unless you give it to them. So RAG is mainly about grounding answers in external knowledge, not about learning new weights.

What the paper adds
The paper “Generative Agents” shows a more agent-like version of retrieval, where memory is long-term, dynamic, and tied to behavior over time. Its memory stream stores perceptions as natural-language events with timestamps and importance, then retrieval selects relevant memories using recency, importance, and semantic relevance. That means the paper goes beyond vanilla RAG: it is not just “fetch documents,” it is “remember experiences, reflect on them, and use them to plan”.

What the video teaches
The LangChain course emphasizes practical RAG building blocks and several upgrades to simple retrieval. It covers:

Multi-query: rewrite one question into several versions to improve retrieval.

RAG Fusion: retrieve for each rewritten query, then merge and rerank results.

Decomposition: break a hard question into subquestions and answer them step by step.

Step-back, HyDE, routing, query construction, multi-representation indexing, RAPTOR, ColBERT, CRAG, and Adaptive RAG.

The main lesson is that retrieval quality often improves when the system changes the query, not just the index. In other words, good RAG is usually not “one embedding search and done”; it is a set of design choices around how to ask, what to retrieve, and when to retry.

How to think about memory
If you get stuck, remember this distinction:

RAG = retrieval over external content.

Memory = persistent, evolving state about past interactions, goals, and preferences.

Vanilla RAG does not truly know the user, track goals, or evolve over time on its own. It can only look personal if you feed it user history or profile data as retrievable text.

What retrieved passages can and cannot do
Retrieved passages can improve answer quality and make outputs easier to justify because you can point to the source chunks. But retrieved passages are not the same as understanding; if the retrieval misses the right chunk, the answer can still be wrong or incomplete even though it looks grounded. So retrieval helps explainability, but it is not a guarantee of truth.

Limitations to remember
Plain RAG struggles when the task needs long-term memory evolution, learner modeling, goals, reflection, or planning across time. For years of learner history, a static vector store is usually too blunt because it does not naturally consolidate, update, or reason temporally. That is why educational systems often need RAG plus an actual memory layer and agent logic.

One-line takeaway
Use this sentence as your anchor: RAG retrieves evidence, but a true educational agent must remember, update, reflect, and plan on top of retrieval.

Quick reminder map
Paper: memory stream, retrieval by relevance/recency/importance, reflection, planning.

Video: indexing, retrieval, generation, query rewriting, fusion, decomposition, routing, advanced retrieval methods.

For EduTwin: treat RAG as evidence lookup, not as the whole memory system