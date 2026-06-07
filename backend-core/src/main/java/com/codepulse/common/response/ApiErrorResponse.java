package com.codepulse.common.response;

import java.time.Instant;
import java.util.Map;

public record ApiErrorResponse(
        String code,
        String message,
        Instant timestamp,
        Map<String, Object> details) {
}
