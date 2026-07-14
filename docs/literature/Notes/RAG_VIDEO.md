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



## Timed_stamped notes


### 1. Core RAG Pipeline

- **Indexing (0:05:53):** Documents are split into manageable chunks, converted into semantic vectors via embedding models, and saved in a vector store for efficient searching.
- **Retrieval (0:10:40):** The system performs a **K-nearest neighbor search** in the embedding space to retrieve the most semantically relevant chunks based on a user's question.
- **Generation (0:15:52):** The retrieved documents are injected as context into an LLM, which then generates a grounded answer based on the provided data.

### 2. Query Translation (Optimizing retrieval inputs)

- **Multi-Query (0:22:14):** We send the question to an LLM to generate multiple differently-worded variations, perform retrieval for each, and take the unique union of documents to improve recall.


- **RAG Fusion (0:28:20):** Similar to multi-query, but it applies **Reciprocal Rank Fusion** to intelligently re-rank the aggregated search results before generation.


- **Decomposition (0:33:57):** The question is sent to an LLM to break it into sub-questions; we answer the first, add that answer to the context, and use it to help solve the second sub-question, and so on.


- **Step Back Prompting (0:40:31):** We ask the LLM to generate a more abstract, high-level question to retrieve broad conceptual context, which is then combined with the specific original question to form the final answer.



- **HyDE (0:47:24):** The LLM generates a hypothetical answer to the user's question; we use this "fake" document to perform the retrieval, as it is often closer to the target content in the embedding space than the original question.



### 3. Routing & Construction

- **Routing (0:52:07):** An LLM analyzes the user's question and decides which data source is appropriate—such as a Vector Store, Graph DB, or Web Search—and directs the query accordingly.


- **Query Construction (0:59:08):** Using **function calling**, the LLM converts natural language requests into structured metadata filters (e.g., filtering a vector store by date or author) to narrow down search results.


### 4. Advanced Indexing

- **Multi-Representation Indexing (1:05:05):** We index small, high-quality summaries or propositions instead of raw chunks, while maintaining a link to the full source document to retrieve the entire text for the final generation.


- **RAPTOR (1:11:39):** A hierarchical approach where we cluster similar document chunks and recursively summarize them, creating a tree structure that supports both fine-grained and high-level retrieval.


### 5. Adaptive & Agentic RAG

- **CRAG (Corrective RAG) (1:26:32):** We use a grader to verify if retrieved documents are relevant. If they are irrelevant, the system triggers a web search to fetch accurate data.
- **Adaptive RAG (1:44:09):** A sophisticated **state-machine** flow using *LangGraph*. The system uses an LLM as an orchestrator to route the question, grade document relevance, check for hallucinations, and loop back to retry or transform the query if the verification steps fail.