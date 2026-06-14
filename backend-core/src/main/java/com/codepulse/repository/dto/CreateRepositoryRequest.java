package com.codepulse.repository.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateRepositoryRequest(
        @NotBlank(message = "Repository URL is required")
        @Size(max = 500, message = "Repository URL must be 500 characters or fewer")
        String repositoryUrl) {
}
