package com.codepulse.integration.ai;

import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

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

    private record DispatchScanRequest(
            UUID scanId,
            UUID repositoryId,
            String githubUrl,
            String branch) {
    }
}
