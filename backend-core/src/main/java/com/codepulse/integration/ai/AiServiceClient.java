package com.codepulse.integration.ai;

import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class AiServiceClient {

    private final RestClient restClient;

    public AiServiceClient(
            RestClient.Builder restClientBuilder,
            @Value("${fastapi.base-url}") String fastApiBaseUrl) {
        this.restClient = restClientBuilder
                .baseUrl(fastApiBaseUrl)
                .build();
    }

    public void dispatchScan(UUID scanId, UUID repositoryId, String repositoryUrl) {
        restClient.post()
                .uri("/api/analysis/scans")
                .body(new DispatchScanRequest(scanId, repositoryId, repositoryUrl))
                .retrieve()
                .toBodilessEntity();
    }

    private record DispatchScanRequest(
            UUID scanId,
            UUID repositoryId,
            String repositoryUrl) {
    }
}
