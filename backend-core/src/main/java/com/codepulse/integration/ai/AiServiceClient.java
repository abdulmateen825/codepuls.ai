package com.codepulse.integration.ai;

import java.util.List;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import com.codepulse.ai.dto.ChatMessageRequest;
import com.codepulse.ai.dto.FindingExplanationResponse;
import com.codepulse.ai.dto.RepositoryChatResponse;

@Component
public class AiServiceClient {

    private final RestClient restClient;
    private final String internalApiKey;

    public AiServiceClient(
            RestClient.Builder restClientBuilder,
            @Value("${fastapi.base-url}") String fastApiBaseUrl,
            @Value("${fastapi.internal-api-key}") String internalApiKey) {
        this.restClient = restClientBuilder
                .baseUrl(fastApiBaseUrl)
                .build();
        this.internalApiKey = internalApiKey;
    }

    public void dispatchScan(UUID scanId, UUID repositoryId, String githubUrl, String branch) {
        restClient.post()
                .uri("/internal/analyze")
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + internalApiKey)
                .body(new DispatchScanRequest(scanId, repositoryId, githubUrl, branch))
                .retrieve()
                .toBodilessEntity();
    }

    public RepositoryChatResponse chat(UUID repositoryId, String question, List<ChatMessageRequest> history) {
        return restClient.post()
                .uri("/internal/repositories/chat")
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + internalApiKey)
                .body(new InternalChatRequest(repositoryId, question, history == null ? List.of() : history))
                .retrieve()
                .body(RepositoryChatResponse.class);
    }

    public FindingExplanationResponse explainFinding(InternalFindingExplainRequest request) {
        return restClient.post()
                .uri("/internal/findings/explain")
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + internalApiKey)
                .body(request)
                .retrieve()
                .body(FindingExplanationResponse.class);
    }

    public byte[] generateReportPdf(InternalReportRequest request) {
        return restClient.post()
                .uri("/internal/reports/pdf")
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + internalApiKey)
                .body(request)
                .retrieve()
                .body(byte[].class);
    }

    private record DispatchScanRequest(
            UUID scanId,
            UUID repositoryId,
            String githubUrl,
            String branch) {
    }

    private record InternalChatRequest(
            UUID repositoryId,
            String question,
            List<ChatMessageRequest> history) {
    }

    public record InternalFindingExplainRequest(
            UUID repositoryId,
            UUID scanId,
            UUID findingId,
            String severity,
            String category,
            String title,
            String description,
            String recommendation,
            String filePath,
            Integer lineNumber,
            Integer startLine,
            Integer endLine,
            String smellType,
            String language,
            String codeSnippet,
            String contextBefore,
            String contextAfter,
            String suggestedRefactoring,
            Double confidence,
            String ruleId) {
    }

    public record InternalReportRequest(
            UUID scanId,
            UUID repositoryId,
            String repositoryFullName,
            String repositoryUrl,
            String status,
            Integer qualityScore,
            Integer securityScore,
            Integer maintainabilityScore,
            List<InternalReportFinding> findings) {
    }

    public record InternalReportFinding(
            String severity,
            String category,
            String title,
            String description,
            String recommendation,
            String filePath,
            Integer lineNumber,
            String ruleId) {
    }
}
