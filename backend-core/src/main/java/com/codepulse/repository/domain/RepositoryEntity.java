package com.codepulse.repository.domain;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.auth.entity.User;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

@Entity
@Table(
        name = "repositories",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_repositories_owner_github_repo",
                columnNames = {"owner_id", "github_owner", "github_name"}))
public class RepositoryEntity {

    @Id
    @GeneratedValue
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "owner_id", nullable = false)
    private User owner;

    @Column(name = "github_url", nullable = false, length = 500)
    private String githubUrl;

    @Column(name = "github_owner", nullable = false, length = 120)
    private String githubOwner;

    @Column(name = "github_name", nullable = false, length = 120)
    private String githubName;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private RepositoryStatus status = RepositoryStatus.ACTIVE;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RepositoryEntity() {
    }

    public RepositoryEntity(User owner, String githubUrl, String githubOwner, String githubName) {
        this.owner = owner;
        this.githubUrl = githubUrl;
        this.githubOwner = githubOwner;
        this.githubName = githubName;
    }

    @PrePersist
    void prePersist() {
        Instant now = Instant.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    void preUpdate() {
        updatedAt = Instant.now();
    }

    public UUID getId() {
        return id;
    }

    public User getOwner() {
        return owner;
    }

    public String getGithubUrl() {
        return githubUrl;
    }

    public String getGithubOwner() {
        return githubOwner;
    }

    public String getGithubName() {
        return githubName;
    }

    public RepositoryStatus getStatus() {
        return status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
