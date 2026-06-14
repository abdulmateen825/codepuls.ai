package com.codepulse.scan.domain;

import java.time.Instant;
import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;

@Entity
@Table(name = "findings")
public class FindingEntity {

    @Id
    @GeneratedValue
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "scan_id", nullable = false)
    private ScanEntity scan;

    @Column(name = "rule_id", nullable = false, length = 120)
    private String ruleId;

    @Column(nullable = false, length = 50)
    private String category;

    @Column(nullable = false, length = 30)
    private String severity;

    @Column(nullable = false, length = 300)
    private String title;

    @Column(nullable = false, length = 2000)
    private String description;

    @Column(name = "file_path", nullable = false, length = 1000)
    private String filePath;

    @Column(name = "line_number")
    private Integer lineNumber;

    @Column(name = "code_snippet", length = 4000)
    private String codeSnippet;

    @Column(length = 2000)
    private String recommendation;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    protected FindingEntity() {
    }

    public FindingEntity(
            ScanEntity scan,
            String ruleId,
            String category,
            String severity,
            String title,
            String description,
            String filePath,
            Integer lineNumber,
            String codeSnippet,
            String recommendation) {
        this.scan = scan;
        this.ruleId = ruleId;
        this.category = category;
        this.severity = severity;
        this.title = title;
        this.description = description;
        this.filePath = filePath;
        this.lineNumber = lineNumber;
        this.codeSnippet = codeSnippet;
        this.recommendation = recommendation;
    }

    @PrePersist
    void prePersist() {
        createdAt = Instant.now();
    }

    public UUID getId() {
        return id;
    }

    public ScanEntity getScan() {
        return scan;
    }

    public String getRuleId() {
        return ruleId;
    }

    public String getCategory() {
        return category;
    }

    public String getSeverity() {
        return severity;
    }

    public String getTitle() {
        return title;
    }

    public String getDescription() {
        return description;
    }

    public String getFilePath() {
        return filePath;
    }

    public Integer getLineNumber() {
        return lineNumber;
    }

    public String getCodeSnippet() {
        return codeSnippet;
    }

    public String getRecommendation() {
        return recommendation;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
