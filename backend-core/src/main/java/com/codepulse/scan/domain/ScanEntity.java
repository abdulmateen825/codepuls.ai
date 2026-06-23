package com.codepulse.scan.domain;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.repository.domain.RepositoryEntity;

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

@Entity
@Table(name = "scans")
public class ScanEntity {

    @Id
    @GeneratedValue
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "repository_id", nullable = false)
    private RepositoryEntity repository;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private ScanStatus status = ScanStatus.QUEUED;

    @Column(name = "quality_score")
    private Integer qualityScore;

    @Column(name = "security_score")
    private Integer securityScore;

    @Column(name = "maintainability_score")
    private Integer maintainabilityScore;

    @Column(name = "started_at")
    private Instant startedAt;

    @Column(name = "completed_at")
    private Instant completedAt;

    @Column(name = "error_message", length = 1000)
    private String errorMessage;

    @Column(name = "metadata_json", columnDefinition = "jsonb")
    private String metadataJson;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected ScanEntity() {
    }

    public ScanEntity(RepositoryEntity repository) {
        this.repository = repository;
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

    public void markFailed(String message) {
        status = ScanStatus.FAILED;
        completedAt = Instant.now();
        errorMessage = message;
    }

    public void markQueued(String metadataJson) {
        status = ScanStatus.QUEUED;
        this.metadataJson = metadataJson;
        errorMessage = null;
    }

    public void markRunning(String metadataJson) {
        status = ScanStatus.RUNNING;
        this.metadataJson = metadataJson;
        startedAt = startedAt == null ? Instant.now() : startedAt;
        errorMessage = null;
    }

    public void markCompleted(
            Integer qualityScore,
            Integer securityScore,
            Integer maintainabilityScore,
            String metadataJson) {
        status = ScanStatus.COMPLETED;
        this.qualityScore = qualityScore;
        this.securityScore = securityScore;
        this.maintainabilityScore = maintainabilityScore;
        this.metadataJson = metadataJson;
        startedAt = startedAt == null ? Instant.now() : startedAt;
        completedAt = Instant.now();
        errorMessage = null;
    }

    public void markFailed(String message, String metadataJson) {
        status = ScanStatus.FAILED;
        this.metadataJson = metadataJson;
        startedAt = startedAt == null ? Instant.now() : startedAt;
        completedAt = Instant.now();
        errorMessage = message;
    }

    public UUID getId() {
        return id;
    }

    public RepositoryEntity getRepository() {
        return repository;
    }

    public ScanStatus getStatus() {
        return status;
    }

    public Integer getQualityScore() {
        return qualityScore;
    }

    public Integer getSecurityScore() {
        return securityScore;
    }

    public Integer getMaintainabilityScore() {
        return maintainabilityScore;
    }

    public Instant getStartedAt() {
        return startedAt;
    }

    public Instant getCompletedAt() {
        return completedAt;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public String getMetadataJson() {
        return metadataJson;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
