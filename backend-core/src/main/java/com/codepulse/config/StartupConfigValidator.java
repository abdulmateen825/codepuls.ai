package com.codepulse.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;

@Component
public class StartupConfigValidator {

    private final String environment;
    private final String jwtSecret;
    private final String internalApiKey;

    public StartupConfigValidator(
            @Value("${app.environment:local}") String environment,
            @Value("${jwt.secret}") String jwtSecret,
            @Value("${fastapi.internal-api-key}") String internalApiKey) {
        this.environment = environment;
        this.jwtSecret = jwtSecret;
        this.internalApiKey = internalApiKey;
    }

    @PostConstruct
    void validate() {
        if (!isProductionLike()) {
            return;
        }

        if (jwtSecret == null
                || jwtSecret.length() < 32
                || "your-super-secret-key-change-this-to-something-long".equals(jwtSecret)) {
            throw new IllegalStateException("JWT_SECRET must be set to a strong non-default value.");
        }

        if (internalApiKey == null
                || internalApiKey.length() < 24
                || "change-me-internal-api-key".equals(internalApiKey)) {
            throw new IllegalStateException("INTERNAL_API_KEY must be set to a strong non-default value.");
        }
    }

    private boolean isProductionLike() {
        String normalized = environment == null ? "" : environment.trim().toLowerCase();
        return normalized.equals("prod") || normalized.equals("production");
    }
}
