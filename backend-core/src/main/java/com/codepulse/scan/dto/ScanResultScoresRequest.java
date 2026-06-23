package com.codepulse.scan.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

public record ScanResultScoresRequest(
        @Min(0)
        @Max(100)
        Integer qualityScore,

        @Min(0)
        @Max(100)
        Integer securityScore,

        @Min(0)
        @Max(100)
        Integer maintainabilityScore) {
}
