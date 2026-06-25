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

    @Column(name = "start_line")
    private Integer startLine;

    @Column(name = "end_line")
    private Integer endLine;

    @Column(name = "smell_type", length = 80)
    private String smellType;

    @Column(length = 40)
    private String language;

    @Column(name = "evidence_json", columnDefinition = "jsonb")
    private String evidenceJson;

    @Column(name = "metrics_json", columnDefinition = "jsonb")
    private String metricsJson;

    @Column(name = "code_snippet", length = 4000)
    private String codeSnippet;

    @Column(name = "context_before", length = 4000)
    private String contextBefore;

    @Column(name = "context_after", length = 4000)
    private String contextAfter;

    @Column(length = 2000)
    private String recommendation;

    @Column(name = "suggested_refactoring", length = 2000)
    private String suggestedRefactoring;

    @Column
    private Double confidence;

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
        this(
                scan,
                ruleId,
                category,
                severity,
                title,
                description,
                filePath,
                lineNumber,
                null,
                null,
                null,
                null,
                null,
                null,
                codeSnippet,
                null,
                null,
                recommendation,
                null,
                null);
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
            Integer startLine,
            Integer endLine,
            String smellType,
            String language,
            String evidenceJson,
            String metricsJson,
            String codeSnippet,
            String contextBefore,
            String contextAfter,
            String recommendation,
            String suggestedRefactoring,
            Double confidence) {
        this.scan = scan;
        this.ruleId = ruleId;
        this.category = category;
        this.severity = severity;
        this.title = title;
        this.description = description;
        this.filePath = filePath;
        this.lineNumber = lineNumber;
        this.startLine = startLine;
        this.endLine = endLine;
        this.smellType = smellType;
        this.language = language;
        this.evidenceJson = evidenceJson;
        this.metricsJson = metricsJson;
        this.codeSnippet = codeSnippet;
        this.contextBefore = contextBefore;
        this.contextAfter = contextAfter;
        this.recommendation = recommendation;
        this.suggestedRefactoring = suggestedRefactoring;
        this.confidence = confidence;
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

    public Integer getStartLine() {
        return startLine;
    }

    public Integer getEndLine() {
        return endLine;
    }

    public String getSmellType() {
        return smellType;
    }

    public String getLanguage() {
        return language;
    }

    public String getEvidenceJson() {
        return evidenceJson;
    }

    public String getMetricsJson() {
        return metricsJson;
    }

    public String getCodeSnippet() {
        return codeSnippet;
    }

    public String getContextBefore() {
        return contextBefore;
    }

    public String getContextAfter() {
        return contextAfter;
    }

    public String getRecommendation() {
        return recommendation;
    }

    public String getSuggestedRefactoring() {
        return suggestedRefactoring;
    }

    public Double getConfidence() {
        return confidence;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
