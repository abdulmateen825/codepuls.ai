package com.codepulse.ai.dto;

import java.util.List;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RepositoryChatRequest(
        @NotBlank
        @Size(max = 4000)
        String question,

        @Valid
        @Size(max = 20)
        List<ChatMessageRequest> history) {

    public List<ChatMessageRequest> normalizedHistory() {
        return history == null ? List.of() : history;
    }
}
