package com.codepulse.ai.dto;

import java.util.List;

public record FindingExplanationResponse(
        String summary,
        String whyItMatters,
        String risk,
        String correctiveAction,
        String possibleFixedCode,
        Double confidenceScore,
        List<FileReferenceResponse> fileReferences) {
}
