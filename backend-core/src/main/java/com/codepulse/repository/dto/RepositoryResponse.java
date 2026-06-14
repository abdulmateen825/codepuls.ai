package com.codepulse.repository.dto;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.repository.domain.RepositoryEntity;

public record RepositoryResponse(
        UUID id,
        String repositoryUrl,
        String githubOwner,
        String githubName,
        String fullName,
        String status,
        Instant createdAt,
        Instant updatedAt) {

    public static RepositoryResponse from(RepositoryEntity repository) {
        return new RepositoryResponse(
                repository.getId(),
                repository.getGithubUrl(),
                repository.getGithubOwner(),
                repository.getGithubName(),
                repository.getGithubOwner() + "/" + repository.getGithubName(),
                repository.getStatus().name(),
                repository.getCreatedAt(),
                repository.getUpdatedAt());
    }
}
