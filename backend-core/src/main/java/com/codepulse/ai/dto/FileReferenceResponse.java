package com.codepulse.ai.dto;

public record FileReferenceResponse(
        String filePath,
        Integer startLine,
        Integer endLine,
        String symbolName,
        Double score) {
}
