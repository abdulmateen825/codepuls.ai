package com.codepulse.scan;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.integration.ai.AiServiceClient;
import com.codepulse.repository.RepositoryRepository;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.scan.domain.FindingEntity;
import com.codepulse.scan.domain.ScanEntity;
import com.codepulse.scan.dto.FindingPageResponse;
import com.codepulse.scan.dto.FindingResponse;
import com.codepulse.scan.dto.ScanResultCallbackRequest;
import com.codepulse.scan.dto.ScanResultFindingRequest;
import com.codepulse.scan.dto.ScanResultScoresRequest;
import com.codepulse.scan.dto.ScanDetailResponse;
import com.codepulse.scan.dto.ScanSummaryResponse;
import com.codepulse.scan.dto.StartScanRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class ScanService {

    private final RepositoryRepository repositoryRepository;
    private final ScanRepository scanRepository;
    private final FindingRepository findingRepository;
    private final AiServiceClient aiServiceClient;
    private final ObjectMapper objectMapper;

    public ScanService(
            RepositoryRepository repositoryRepository,
            ScanRepository scanRepository,
            FindingRepository findingRepository,
            AiServiceClient aiServiceClient,
            ObjectMapper objectMapper) {
        this.repositoryRepository = repositoryRepository;
        this.scanRepository = scanRepository;
        this.findingRepository = findingRepository;
        this.aiServiceClient = aiServiceClient;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public ScanDetailResponse startScan(UUID repositoryId, StartScanRequest request, User currentUser) {
        requireAuthenticated(currentUser);
        RepositoryEntity repository = findRepositoryForAccess(repositoryId, currentUser);

        ScanEntity scan = scanRepository.save(new ScanEntity(repository));
        try {
            aiServiceClient.dispatchScan(
                    scan.getId(),
                    repository.getId(),
                    repository.getGithubUrl(),
                    request.normalizedBranch());
        } catch (RuntimeException exception) {
            scan.markFailed("AI dispatch failed.");
        }

        return ScanDetailResponse.from(scan);
    }

    @Transactional(readOnly = true)
    public List<ScanSummaryResponse> getRepositoryScans(UUID repositoryId, User currentUser) {
        requireAuthenticated(currentUser);
        RepositoryEntity repository = findRepositoryForAccess(repositoryId, currentUser);

        return scanRepository.findAllByRepositoryOrderByCreatedAtDesc(repository)
                .stream()
                .map(ScanSummaryResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public ScanDetailResponse getScan(UUID scanId, User currentUser) {
        ScanEntity scan = findScanForAccess(scanId, currentUser);
        return ScanDetailResponse.from(scan);
    }

    @Transactional(readOnly = true)
    public FindingPageResponse getFindings(
            UUID scanId,
            String severity,
            String category,
            Pageable pageable,
            User currentUser) {
        ScanEntity scan = findScanForAccess(scanId, currentUser);
        Page<FindingResponse> findings = findingRepository.findByScanWithFilters(
                scan,
                normalizeFilter(severity),
                normalizeFilter(category),
                pageable)
                .map(FindingResponse::from);

        return FindingPageResponse.from(findings);
    }

    @Transactional
    public ScanDetailResponse applyScanResults(UUID scanId, ScanResultCallbackRequest request) {
        ScanEntity scan = scanRepository.findById(scanId)
                .orElseThrow(() -> ApiException.notFound("Scan was not found."));
        String metadataJson = toMetadataJson(request);

        switch (request.status()) {
            case QUEUED -> scan.markQueued(metadataJson);
            case RUNNING -> scan.markRunning(metadataJson);
            case COMPLETED -> {
                findingRepository.deleteByScan(scan);
                ScanResultScoresRequest scores = request.scores();
                scan.markCompleted(
                        scores == null ? null : scores.qualityScore(),
                        scores == null ? null : scores.securityScore(),
                        scores == null ? null : scores.maintainabilityScore(),
                        metadataJson);
                findingRepository.saveAll(toFindingEntities(scan, request.normalizedFindings()));
            }
            case FAILED -> {
                findingRepository.deleteByScan(scan);
                scan.markFailed(
                        request.errorMessage() == null || request.errorMessage().isBlank()
                                ? "Scan failed."
                                : request.errorMessage().trim(),
                        metadataJson);
            }
        }

        return ScanDetailResponse.from(scan);
    }

    private RepositoryEntity findRepositoryForAccess(UUID repositoryId, User currentUser) {
        RepositoryEntity repository = repositoryRepository.findById(repositoryId)
                .orElseThrow(() -> ApiException.notFound("Repository was not found."));

        if (!repository.getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this repository.");
        }

        return repository;
    }

    private ScanEntity findScanForAccess(UUID scanId, User currentUser) {
        requireAuthenticated(currentUser);
        ScanEntity scan = scanRepository.findById(scanId)
                .orElseThrow(() -> ApiException.notFound("Scan was not found."));

        if (!scan.getRepository().getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this scan.");
        }

        return scan;
    }

    private String normalizeFilter(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }

        return value.trim();
    }

    private List<FindingEntity> toFindingEntities(ScanEntity scan, List<ScanResultFindingRequest> findings) {
        return findings.stream()
                .map(finding -> new FindingEntity(
                        scan,
                        trimToMax(finding.normalizedRuleId(), 120),
                        trimToMax(finding.category().trim(), 50),
                        trimToMax(finding.severity().trim(), 30),
                        trimToMax(finding.title().trim(), 300),
                        trimToMax(finding.description().trim(), 2000),
                        trimToMax(finding.filePath().trim(), 1000),
                        finding.normalizedLineNumber(),
                        trimToMax(finding.codeSnippet(), 4000),
                        trimToMax(finding.recommendation(), 2000)))
                .toList();
    }

    private String toMetadataJson(ScanResultCallbackRequest request) {
        try {
            return objectMapper.writeValueAsString(request.normalizedMetadata());
        } catch (JsonProcessingException exception) {
            throw ApiException.badRequest("Scan metadata must be valid JSON.");
        }
    }

    private String trimToMax(String value, int maxLength) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.length() <= maxLength ? trimmed : trimmed.substring(0, maxLength);
    }

    private void requireAuthenticated(User currentUser) {
        if (currentUser == null) {
            throw ApiException.unauthorized("Authentication is required.");
        }
    }
}
