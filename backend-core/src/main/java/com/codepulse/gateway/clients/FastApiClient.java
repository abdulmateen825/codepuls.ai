package com.codepulse.gateway.clients;

import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class FastApiClient {

    private final RestClient restClient;

    public FastApiClient(
            RestClient.Builder restClientBuilder,
            @Value("${fastapi.base-url}") String fastApiBaseUrl) {
        this.restClient = restClientBuilder
                .baseUrl(fastApiBaseUrl)
                .build();
    }

    public Map<String, Object> getHealth() {
        return restClient.get()
                .uri("/health")
                .retrieve()
                .body(new ParameterizedTypeReference<>() {
                });
    }
}
