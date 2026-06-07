package com.codepulse.system.dto;

import java.time.Instant;
import java.util.Map;

public record HealthStatusResponse(
        String service,
        String status,
        Instant checkedAt,
        Map<String, Object> details) {
}
