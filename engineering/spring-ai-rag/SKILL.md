---
name: spring-ai-rag
description: >
  RAG inside a Spring Boot service with Spring AI — VectorStore (pgvector /
  Vertex AI), DocumentReader, Embedding clients, RetrievalAugmentation /
  QuestionAnswerAdvisor, exposing RAG over REST. Use this skill when the
  RAG component is itself a Spring Boot microservice.
category: engineering
tags: [java, spring-boot, rag, llm, ai-agent, integration, backend, gcp]
keywords: [Spring AI, VectorStore, RetrievalAugmentationAdvisor, QuestionAnswerAdvisor, DocumentReader, TextSplitter, Embedding, ChatClient, pgvector, Vertex AI]
related: [spring-boot-fundamentals, java-restful-api, rag-deep-dive, rag-for-code, gcp-vertex-ai-rag]
---

# Spring AI RAG

> Spring AI gives you `VectorStore`, `Document`, `ChatClient`, and advisors. The right way to build RAG in Spring is to lean on those abstractions, not roll your own HTTP clients to OpenAI / Vertex.

## When to Use This Skill

- Building a RAG-powered endpoint in a Spring Boot service
- Exposing "ask the docs/codebase" over your existing REST API
- Choosing between pgvector (Cloud SQL / AlloyDB), Vertex AI Vector Search, Redis, etc.
- Wiring a model provider (Vertex AI, Anthropic, OpenAI, Bedrock) behind one abstraction
- Adding observability and auth to a RAG endpoint that mirrors the rest of your API

For RAG strategy, pair with [`rag-deep-dive`](../../ai-engineering/rag-deep-dive/SKILL.md) and [`rag-for-code`](../../ai-engineering/rag-for-code/SKILL.md). For GCP infrastructure choices, [`gcp-vertex-ai-rag`](../../devops/gcp-vertex-ai-rag/SKILL.md).

---

## Pick a Spring AI Stack

```gradle
dependencies {
    implementation 'org.springframework.ai:spring-ai-starter-vertex-ai-gemini'        // Or -anthropic, -openai, -bedrock
    implementation 'org.springframework.ai:spring-ai-starter-vector-store-pgvector'   // Or -vertex-ai, -redis, -qdrant
    implementation 'org.springframework.ai:spring-ai-advisors-vector-store'           // Q&A and RAG advisors
}
```

1. **Use Spring AI 1.0 GA or later.** Earlier milestones rename packages on every release. Pin a stable version in your BOM.

2. **One model provider per service.** Spring AI lets you bind multiple, but multi-provider routing belongs in a gateway, not a controller. See `llm-cost-optimization` for routing strategies.

3. **`pgvector` on Cloud SQL is the boring default.** No new infra; transactional with your domain data; integrates with existing Flyway migrations. Switch to Vertex AI Vector Search when you cross ~1M chunks or need multi-region serving.

---

## Configuration

```yaml
spring:
  ai:
    vertex:
      ai:
        gemini:
          project-id: ${GOOGLE_CLOUD_PROJECT}
          location: asia-east1
          chat:
            options:
              model: gemini-2.5-pro
              temperature: 0.2
    vectorstore:
      pgvector:
        index-type: hnsw
        distance-type: cosine_distance
        dimensions: 768                    # match the embedding model
        initialize-schema: false           # Flyway owns the schema in prod

  datasource:
    url: jdbc:postgresql:///rag?cloudSqlInstance=acme-orders-prod:asia-east1:rag-db&socketFactory=com.google.cloud.sql.postgres.SocketFactory&user=rag-app@acme-orders-prod.iam&enableIamAuth=true
```

4. **`initialize-schema: false` in production.** Spring AI can create its `vector_store` table; in production let Flyway own it so migrations are reviewable.

5. **Match `dimensions` to the embedding model.** Mismatched dims silently truncate or error at insert time.

6. **Set `temperature` low (0.0–0.3) for grounded RAG answers.** Creativity is not a feature when you want citations.

---

## Schema (Flyway)

```sql
-- V1__create_vector_store.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE vector_store (
    id UUID PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding vector(768)
);

CREATE INDEX idx_vector_store_embedding
    ON vector_store USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_vector_store_metadata
    ON vector_store USING gin (metadata jsonb_path_ops);
```

7. **HNSW > IVFFlat for most workloads.** Faster recall at typical scales. Tune `m` and `ef_construction` only after measurement.

8. **Index `metadata` (JSONB) with `gin`.** You will filter by `service`, `kind`, `repo` — without the index it's a sequential scan.

9. **Partition or shard when you cross ~5M rows** in a single table. Postgres handles it but query planning gets sensitive.

---

## Ingestion

```java
@Service
public class CodebaseIngestService {

    private final VectorStore vectorStore;
    private final EmbeddingModel embeddingModel;

    public CodebaseIngestService(VectorStore vectorStore, EmbeddingModel embeddingModel) {
        this.vectorStore = vectorStore;
        this.embeddingModel = embeddingModel;
    }

    public void ingestRepo(Path repoRoot, String service) {
        List<Document> docs = walkJavaSources(repoRoot)
            .map(file -> chunkJavaFile(file, service))
            .flatMap(List::stream)
            .toList();
        vectorStore.add(docs);   // batches embedding + upsert
    }

    private List<Document> chunkJavaFile(Path file, String service) {
        String source = Files.readString(file);
        return treeSitterChunker.chunk(source).stream()
            .map(c -> Document.builder()
                .id(c.deterministicId())
                .text(c.text())
                .metadata(Map.of(
                    "service", service,
                    "repo", file.getName(0).toString(),
                    "path", file.toString(),
                    "kind", c.kind(),                 // "method" | "class" | "file"
                    "symbol", c.symbol(),
                    "git_sha", c.gitSha()
                ))
                .build())
            .toList();
    }
}
```

10. **For code, use a custom tree-sitter chunker, not Spring AI's `TokenTextSplitter`.** Token-based chunking is fine for prose; it ruins code retrieval. See [`rag-for-code`](../../ai-engineering/rag-for-code/SKILL.md).

11. **`Document.id` must be deterministic.** Spring AI `add()` is upsert-aware via the ID. See [`rag-ingestion-pipeline`](../../ai-engineering/rag-ingestion-pipeline/SKILL.md).

12. **Don't ingest in the request thread.** Long-running ingest is a Job (K8s `Job` or Cloud Run job), not a controller. Trigger via Pub/Sub on git push.

---

## RAG Endpoint

The recommended pattern: an advisor on a `ChatClient`.

```java
@Configuration
public class ChatClientConfig {

    @Bean
    public ChatClient ragChatClient(ChatClient.Builder builder, VectorStore vectorStore) {
        QuestionAnswerAdvisor qa = QuestionAnswerAdvisor.builder(vectorStore)
            .searchRequest(SearchRequest.builder()
                .topK(8)
                .similarityThreshold(0.5)
                .build())
            .promptTemplate(PromptTemplate.builder()
                .template("""
                    Answer using ONLY the context. Cite sources as [path:line].
                    If the context does not contain the answer, say "I don't know" and
                    suggest which service or file might have it.

                    Context:
                    {question_answer_context}
                    """)
                .build())
            .build();

        return builder
            .defaultAdvisors(qa, new SimpleLoggerAdvisor())
            .defaultSystem("You are a senior engineer answering questions about the company's microservices.")
            .build();
    }
}
```

```java
@RestController
@RequestMapping("/api/v1/ask")
@Validated
public class AskController {

    private final ChatClient chat;

    public AskController(ChatClient chat) { this.chat = chat; }

    @PostMapping
    public AskResponse ask(@Valid @RequestBody AskRequest req) {
        ChatResponse response = chat.prompt()
            .user(req.question())
            .advisors(a -> a.param("filter_expression",
                "service == '" + req.service() + "'"))
            .call()
            .chatResponse();

        return AskResponse.from(response);
    }

    public record AskRequest(@NotBlank String question, @NotBlank String service) {}
    public record AskResponse(String answer, List<Citation> citations, int tokensUsed) {
        public static AskResponse from(ChatResponse r) { /* ... */ }
    }
}
```

13. **Use `QuestionAnswerAdvisor`, not raw `vectorStore.similaritySearch` + manual prompt assembly.** The advisor handles retrieval, rendering, and prompt injection consistently.

14. **Pass metadata filters via `filter_expression`.** Spring AI parses these into the underlying store's filter (Postgres `WHERE`, Vertex restricts, etc.). Keep filters simple — complex DSL drifts between backends.

15. **`SimpleLoggerAdvisor` in dev only.** It logs the full prompt; in prod it's a PII / cost / log-volume hazard. Replace with structured tracing.

16. **Return citations as a typed field**, not just inline in the answer text. Clients render them; LLM-injected citations should be verified server-side against the retrieved chunks.

---

## Streaming Responses

```java
@PostMapping(path = "", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<String> askStream(@Valid @RequestBody AskRequest req) {
    return chat.prompt()
        .user(req.question())
        .stream()
        .content();
}
```

17. **SSE is the right protocol for token streaming.** WebSocket is overkill; HTTP/2 chunking has client-side issues with proxies.

18. **WebFlux for streaming endpoints.** Don't mix MVC and WebFlux casually — bring up a separate `WebFlux` configuration if your service is otherwise MVC.

19. **Even when streaming, accumulate citations server-side** and emit them as a final SSE event. Clients render text first, then "Sources" once the full set is known.

---

## Observability

```java
@Bean
public ChatClient ragChatClient(ChatClient.Builder builder, VectorStore vs, ObservationRegistry observations) {
    return builder
        .defaultAdvisors(new QuestionAnswerAdvisor(vs), new ObservationAdvisor(observations))
        .build();
}
```

20. **Spring AI 1.0+ emits Micrometer Observations** for chat and embedding calls (`gen_ai.client.operation`). Wire to OpenTelemetry → Cloud Trace as in [`gcp-observability-spring`](../gcp-observability-spring/SKILL.md). One trace per question, with spans for retrieval and generation.

21. **Track**: time-to-first-token, total tokens, retrieval similarity scores, cache hit rate (if caching), refusal rate.

22. **Log the question, the retrieved chunk IDs, and the final answer** — not the full prompt. The prompt is reconstructable from chunk IDs + advisor config; logs should be cheap.

---

## Auth, Rate Limit, Cost

23. **Same `@RestControllerAdvice` and `ProblemDetail`** as the rest of your service. RAG errors are HTTP errors. See [`java-restful-api`](../java-restful-api/SKILL.md).

24. **Rate-limit per user**, not per IP. RAG calls are 100–1000× more expensive than ordinary endpoints; a single bad client drains the budget.

25. **Track cost per request and per user.** Emit a Micrometer `Counter` with `user_id` (low-cardinality bucket) and `model` tags.

26. **Cache where possible.** Spring AI supports response caching via advisors; for code RAG, the same question seconds apart should hit cache. See [`prompt-caching`](../../ai-engineering/prompt-caching/SKILL.md).

---

## Testing

```java
@SpringBootTest
@ActiveProfiles("test")
@Testcontainers
class AskControllerIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("pgvector/pgvector:pg16");

    @MockBean ChatModel chatModel;          // mock the LLM
    @Autowired VectorStore vectorStore;     // real pgvector via Testcontainers
    @Autowired TestRestTemplate rest;

    @Test
    void answersGroundedQuestion() {
        vectorStore.add(List.of(
            Document.builder().text("OrderService.cancel marks the order CANCELLED").metadata(Map.of("service","orders")).build()));

        when(chatModel.call(any(Prompt.class))).thenReturn(stubResponse("Cancels the order."));

        ResponseEntity<AskResponse> res = rest.postForEntity("/api/v1/ask",
            new AskRequest("How do I cancel an order?", "orders"), AskResponse.class);

        assertThat(res.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(res.getBody().citations()).isNotEmpty();
    }
}
```

27. **Mock the chat model, not the vector store.** The vector store is deterministic and worth testing; the LLM is non-deterministic and not the unit under test.

28. **`pgvector/pgvector` Testcontainers image** for repository tests. Don't fake similarity in tests — embedding behaviour is part of the contract.

29. **Eval suite separate from unit tests.** Run on a schedule against a stable index. See [`agent-evaluation`](../../ai-engineering/agent-evaluation/SKILL.md).

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `TokenTextSplitter` slices methods mid-line | Use AST chunker for code; reserve token splitter for prose |
| Embedding dim mismatch errors at insert | Pin `dimensions` in config to the model's actual output |
| Schema auto-init clobbers Flyway-owned table | `initialize-schema: false` in non-local |
| Long ingest blocks an HTTP request | Move to a Job; trigger via Pub/Sub |
| Citations hallucinated by the model | Verify cited path:line exists in retrieved chunks server-side |
| `SearchRequest.topK(50)` blows the prompt budget | Retrieve 20–30, rerank, send 5–8 to the model |
| Streaming endpoint deployed in MVC; clients see one chunk | Use WebFlux for the streaming endpoint |
| Rate limit by IP misses corporate NATs | Rate limit per authenticated user |

---

## Pre-Production Checklist

- [ ] Spring AI 1.0+ pinned in BOM
- [ ] `VectorStore` schema owned by Flyway; `initialize-schema: false`
- [ ] Embedding `dimensions` matches the model
- [ ] AST chunker for code; token splitter only for prose
- [ ] Ingestion runs as a Job, triggered by push events
- [ ] `QuestionAnswerAdvisor` configured with grounding template + filter expressions
- [ ] Citations returned as typed field; server-verified
- [ ] Observation advisor → Micrometer → Cloud Trace
- [ ] Rate limit + cost tracking per user
- [ ] Streaming endpoint uses SSE; WebFlux if mixing
- [ ] Integration tests use Testcontainers pgvector + mock ChatModel
- [ ] Eval suite runs on a schedule

---

## Related Skills

- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — beans, profiles, Actuator
- [`java-restful-api`](../java-restful-api/SKILL.md) — controllers, DTOs, error handling
- [`rag-deep-dive`](../../ai-engineering/rag-deep-dive/SKILL.md) — strategy
- [`rag-for-code`](../../ai-engineering/rag-for-code/SKILL.md) — code-specific chunking and retrieval
- [`gcp-vertex-ai-rag`](../../devops/gcp-vertex-ai-rag/SKILL.md) — Vertex AI / AlloyDB / pgvector choice
- [`gcp-cloud-sql-spring`](../gcp-cloud-sql-spring/SKILL.md) — Postgres connectivity (pgvector lives here)
- [`gcp-observability-spring`](../gcp-observability-spring/SKILL.md) — tracing the RAG endpoint
- [`prompt-caching`](../../ai-engineering/prompt-caching/SKILL.md) — cache stable system prompts
