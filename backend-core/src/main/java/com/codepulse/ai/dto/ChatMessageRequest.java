package com.codepulse.ai.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChatMessageRequest(
        @NotBlank
        @Size(max = 20)
        String role,

        @NotBlank
        @Size(max = 4000)
        String content) {
}
