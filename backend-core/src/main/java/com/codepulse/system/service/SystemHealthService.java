package com.codepulse.system.service;

import java.time.Instant;
import java.util.Map;

import org.springframework.stereotype.Service;

import com.codepulse.gateway.clients.FastApiClient;
import com.codepulse.system.dto.HealthStatusResponse;

@Service
public class SystemHealthService {

    private static final String STATUS_UP = "UP";
    private static final String STATUS_DOWN = "DOWN";

    private final FastApiClient fastApiClient;

    public SystemHealthService(FastApiClient fastApiClient) {
        this.fastApiClient = fastApiClient;
    }

    public HealthStatusResponse getCoreHealth() {
        return new HealthStatusResponse(
                "backend-core",
                STATUS_UP,
                Instant.now(),
                Map.of("message", "Spring Boot API is healthy"));
    }

    public HealthStatusResponse getAiHealth() {
        try {
            Map<String, Object> aiHealth = fastApiClient.getHealth();
            return new HealthStatusResponse(
                    "backend-ai",
                    STATUS_UP,
                    Instant.now(),
                    Map.of("fastApi", aiHealth));
        } catch (Exception exception) {
            return new HealthStatusResponse(
                    "backend-ai",
                    STATUS_DOWN,
                    Instant.now(),
                    Map.of("error", "FastAPI health check failed"));
        }
    }
}
