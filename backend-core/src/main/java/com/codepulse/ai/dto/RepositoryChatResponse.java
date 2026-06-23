package com.codepulse.ai.dto;

import java.util.List;

public record RepositoryChatResponse(
        String answer,
        List<FileReferenceResponse> fileReferences,
        List<String> suggestedQuestions) {
}
