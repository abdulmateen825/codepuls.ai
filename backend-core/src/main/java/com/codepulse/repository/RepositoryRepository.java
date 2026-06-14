package com.codepulse.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.codepulse.auth.entity.User;
import com.codepulse.repository.domain.RepositoryEntity;

public interface RepositoryRepository extends JpaRepository<RepositoryEntity, UUID> {

    List<RepositoryEntity> findAllByOwnerOrderByCreatedAtDesc(User owner);

    Optional<RepositoryEntity> findByIdAndOwner(UUID id, User owner);

    boolean existsByOwnerAndGithubOwnerIgnoreCaseAndGithubNameIgnoreCase(
            User owner,
            String githubOwner,
            String githubName);
}
